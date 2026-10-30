"""Dependency graphs and resumable end-to-end dry runs.

Production graphs are preparation artifacts, not evidence of executed science.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from .core import canonical, digest, file_hash, now, plan


def stage(name, operation, dependencies=(), description=""):
    return {"id": name, "operation": operation, "depends_on": list(dependencies), "description": description}


def build_workflow(spec, replicas=2):
    if type(replicas) is not int or not 1 <= replicas <= 20:
        raise ValueError("MD 独立重复数必须为 1–20 的整数；默认 2 仅供规划，不代表科学验收要求")
    planned = plan(spec)
    steps = [stage("identity", "identity_review", description="身份、结构、电荷/计量、来源关联"),
             stage("protocol", "freeze_protocol", ["identity"], "冻结科学协议、分析方法、软件版本与文件哈希"),
             stage("budget", "check_budget", ["protocol"], "按平台计价与申请资源核对批次上界")]
    if spec["kind"] == "dft":
        steps += [
            stage("conformers", "generate_conformers", ["budget"], "生成孤立片段与复合物候选；保留构型编号"),
            stage("opt_complex", "optimize_complex", ["conformers"], "多构型优化复合物；失败构型不静默丢弃"),
            stage("opt_fragments", "optimize_fragments", ["conformers"], "相同环境/级别优化各片段；可复用相同片段"),
            stage("geometry_qc", "check_geometry", ["opt_complex", "opt_fragments"], "收敛、物种/连通性、构型覆盖与协议要求的频率检查"),
            stage("energy_complex", "single_point_complex", ["geometry_qc"], "按固定协议计算复合物能量"),
            stage("energy_fragments", "single_point_fragments", ["geometry_qc"], "相同级别计算孤立片段能量"),
            stage("basis_check", "check_basis_error", ["energy_complex", "energy_fragments"], "按协议实施 BSSE/基组检查或记录经论证的不适用"),
            stage("binding", "derive_binding_energy", ["basis_check"], "E_bind=E_AB(opt)-sum(E_fragment(opt))；与冻结片段 E_int 分开"),
            stage("science_qc", "validate_dft", ["binding"], "单位、环境、构型/方法敏感性和基准核查")]
    else:
        steps += [
            stage("parameterize", "parameterize_system", ["budget"], "核对参数覆盖/来源、原子类型、部分电荷与兼容性"),
            stage("composition", "resolve_composition", ["parameterize"], "将有明确基准的配方转成分子数；记录取整偏差及盐的解离表示"),
            stage("pack", "pack_box", ["composition"], "组装拓扑/坐标，检查电中性、原子数与短距离碰撞"),
            stage("minimize", "minimize_system", ["pack"], "最小化；记录输入输出与引擎日志")]
        production_ids = []
        for replica in range(replicas):
            eq, prod = f"equilibrate_r{replica}", f"production_r{replica}"
            steps += [stage(eq, "equilibrate", ["minimize"], f"重复 {replica}：独立种子/初始化，执行协议平衡阶段"),
                      stage(prod, "production", [eq], f"重复 {replica}：生产轨迹与 checkpoint，记录实际采样长度")]
            production_ids.append(prod)
        steps += [
            stage("structure", "analyze_structure", production_ids, "RDF/配位数/离子聚集；明确定义原子选择和截断"),
            stage("transport", "analyze_transport", production_ids, "扩散拟合窗口、周期边界与单位；其他输运量按启用协议分析"),
            stage("science_qc", "validate_md", ["structure", "transport"], "平衡、独立重复/分块收敛、尺寸效应及参考数据；不收敛转复核")]
    steps += [stage("archive", "archive_results", ["science_qc"], "保存原始产物、分析版本、来源和质检；只有合格结果可进入分析集")]
    payload = {"workflow_schema": 1, "task_id": planned["task_id"], "kind": spec["kind"],
               "mode": spec["mode"], "stages": steps, "max_attempts": spec["retry_policy"]["max_attempts"],
               "configuration_blockers": planned["blockers"], "remote_submission_enabled": False}
    validate_graph(payload)
    return {"workflow_id": digest(payload), **payload}


def validate_graph(workflow):
    steps = workflow.get("stages", [])
    ids = [s["id"] for s in steps]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("工作流阶段必须非空且 ID 唯一")
    visited = set()
    # Export order is topological; enforcing it also rejects cycles/unknown deps.
    for item in steps:
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", item["id"]):
            raise ValueError("阶段 ID 必须为安全的英文标识符")
        if not set(item["depends_on"]).issubset(visited):
            raise ValueError("依赖不存在、存在循环或阶段不是拓扑顺序")
        visited.add(item["id"])


def export_workflow(workflow, target):
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    output = target / "workflow.json"
    content = canonical(workflow) + "\n"
    if output.exists() and output.read_text(encoding="utf-8") != content:
        raise ValueError("目标目录已有不同工作流；请使用新的目录，不能覆盖旧定义")
    output.write_text(content, encoding="utf-8")
    diagram = ["flowchart TD"]
    for item in workflow["stages"]:
        diagram.append(f'  {item["id"]}["{item["description"]}"]')
        diagram += [f'  {dep} --> {item["id"]}' for dep in item["depends_on"]]
    (target / "workflow.mmd").write_text("\n".join(diagram) + "\n", encoding="utf-8")
    return output


class WorkflowRun:
    """Persistent synthetic executor. Never launches a real engine or submits jobs."""

    def __init__(self, workflow, root):
        validate_graph(workflow)
        original = {k: v for k, v in workflow.items() if k != "workflow_id"}
        if digest(original) != workflow["workflow_id"]:
            raise ValueError("工作流定义哈希不符")
        self.workflow = workflow
        self.root = Path(root).resolve() / workflow["workflow_id"]
        export_workflow(workflow, self.root)
        self.db = sqlite3.connect(self.root / "workflow.sqlite3", timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS stages (
              id TEXT PRIMARY KEY, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
              artifact TEXT, sha256 TEXT, error TEXT);
            CREATE TABLE IF NOT EXISTS audit (
              seq INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT NOT NULL,
              stage TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL);
        """)
        with self.db:
            for item in workflow["stages"]:
                self.db.execute("INSERT OR IGNORE INTO stages(id,status) VALUES(?,'PENDING')", (item["id"],))

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.db.close()

    def log(self, name, action, detail):
        self.db.execute("INSERT INTO audit(time,stage,action,detail) VALUES(?,?,?,?)",
                        (now(), name, action, canonical(detail)))

    def statuses(self):
        return {row["id"]: dict(row) for row in self.db.execute("SELECT * FROM stages")}

    def retry(self, name, reason):
        if not reason.strip():
            raise ValueError("需要填写同协议重试原因")
        with self.db:
            count = self.db.execute("UPDATE stages SET status='PENDING',error=NULL WHERE id=? "
                                    "AND status='FAILED' AND attempts<?",
                                    (name, self.workflow["max_attempts"])).rowcount
            if count != 1:
                raise ValueError("只可重试未超次数限制的失败阶段")
            self.log(name, "retry", {"reason": reason})

    def verify_artifacts(self):
        changed = []
        for name, row in self.statuses().items():
            if row["status"] == "DRY_RUN_PASSED":
                artifact = self.root / row["artifact"]
                if not artifact.is_file() or file_hash(artifact) != row["sha256"]:
                    changed.append(name)
        invalid = set(changed)
        for item in self.workflow["stages"]:
            if invalid.intersection(item["depends_on"]):
                invalid.add(item["id"])
        if invalid:
            with self.db:
                for name in invalid:
                    self.db.execute("UPDATE stages SET status='NEEDS_REVIEW' WHERE id=?", (name,))
                    self.log(name, "artifact_invalidated", {"changed_upstream": changed})
        return sorted(invalid)

    def run_synthetic(self, fail_at=None):
        if self.workflow["mode"] != "synthetic":
            raise ValueError("真实工作流只能导出规划；禁止用演示执行器产生 production 结果")
        known = {s["id"] for s in self.workflow["stages"]}
        if fail_at is not None and fail_at not in known:
            raise ValueError("故障注入阶段不存在")
        if self.verify_artifacts():
            return self.report()
        for item in self.workflow["stages"]:
            states = self.statuses()
            row = states[item["id"]]
            if row["status"] != "PENDING":
                continue
            if any(states[d]["status"] != "DRY_RUN_PASSED" for d in item["depends_on"]):
                continue
            with self.db:
                claimed = self.db.execute("UPDATE stages SET status='RUNNING',attempts=attempts+1 "
                                          "WHERE id=? AND status='PENDING' AND attempts<?",
                                          (item["id"], self.workflow["max_attempts"])).rowcount
                if claimed != 1:
                    continue
                self.log(item["id"], "claim", {"synthetic": True})
            attempt = self.statuses()[item["id"]]["attempts"]
            try:
                if item["id"] == fail_at:
                    raise RuntimeError("synthetic injected failure")
                artifact = self.root / item["id"] / f"attempt_{attempt}" / "output.json"
                artifact.parent.mkdir(parents=True, exist_ok=True)
                payload = {"mode": "synthetic", "not_scientific_data": True,
                           "workflow_id": self.workflow["workflow_id"], "stage": item["id"],
                           "operation": item["operation"], "numeric_results": None,
                           "dependency_artifacts": {d: states[d]["sha256"] for d in item["depends_on"]},
                           "note": "只验证阶段连接/产物/续接；未执行物理计算或科学质检。"}
                artifact.write_text(canonical(payload) + "\n", encoding="utf-8")
                with self.db:
                    self.db.execute("UPDATE stages SET status='DRY_RUN_PASSED',artifact=?,sha256=? WHERE id=?",
                                    (artifact.relative_to(self.root).as_posix(), file_hash(artifact), item["id"]))
                    self.log(item["id"], "dry_run_passed", {"attempt": attempt})
            except Exception as error:
                with self.db:
                    self.db.execute("UPDATE stages SET status='FAILED',error=? WHERE id=?", (str(error), item["id"]))
                    self.log(item["id"], "failed", {"attempt": attempt, "error": str(error)})
        return self.report()

    def report(self):
        states = self.statuses()
        passed = sum(row["status"] == "DRY_RUN_PASSED" for row in states.values())
        result = {"workflow_id": self.workflow["workflow_id"], "mode": self.workflow["mode"],
                  "not_scientific_data": True, "status": "DRY_RUN_PASSED" if passed == len(states) else "INCOMPLETE",
                  "passed_stages": passed, "total_stages": len(states), "stages": states,
                  "real_jobs_submitted": 0, "scientific_results": 0}
        path = self.root / "report.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result
