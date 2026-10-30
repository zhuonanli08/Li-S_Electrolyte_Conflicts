"""Deterministic planning, provenance and persistent task lifecycle (stdlib only)."""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


STATES = {"NEEDS_REVIEW", "PENDING", "RUNNING", "SUCCEEDED_PENDING_QC", "PASSED", "FAILED"}
CHECKS = {
    "dft": ("electronic_convergence", "geometry_convergence", "species_preserved",
            "conformer_coverage", "energy_definition", "basis_error_review"),
    "md": ("parameter_coverage", "charge_neutrality", "equilibration",
           "sampling_convergence", "replicate_consistency", "observable_definition"),
}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def now():
    return datetime.now(timezone.utc).isoformat()


def present(value):
    return value is not None and value != "" and value != [] and value != {}


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def validate(spec):
    """Reject malformed contracts; return unresolved scientific inputs as blockers."""
    if spec.get("schema_version") != 1 or spec.get("kind") not in CHECKS:
        raise ValueError("schema_version 必须为 1，kind 必须为 dft/md")
    if spec.get("mode") not in ("production", "synthetic"):
        raise ValueError("mode 必须明确为 production 或 synthetic")
    for field in ("system", "protocol", "resources", "retry_policy"):
        if not isinstance(spec.get(field), dict):
            raise ValueError(f"{field} 必须为对象")
    if not isinstance(spec.get("sources"), list):
        raise ValueError("sources 必须为列表")
    n = spec["retry_policy"].get("max_attempts")
    if type(n) is not int or not 1 <= n <= 5:
        raise ValueError("max_attempts 必须是 1–5 的整数")
    if spec["retry_policy"].get("strategy") != "same_protocol_only":
        raise ValueError("只允许同协议重试；改变科学协议必须登记新任务")
    p, s, r = spec["protocol"], spec["system"], spec["resources"]
    if not isinstance(s.get("components"), list) or not s["components"]:
        raise ValueError("system.components 必须是非空列表")
    ids = []
    for c in s["components"]:
        if not isinstance(c, dict) or not isinstance(c.get("identity"), str) or not c["identity"].strip():
            raise ValueError("每个组分需要 identity")
        ids.append(c["identity"])
    if len(set(ids)) != len(ids):
        raise ValueError("相同 identity 请合并到同一组分并填写计量")
    blockers = []

    def need(container, names, prefix):
        blockers.extend(prefix + key for key in names if not present(container.get(key)))

    need(p, ("id", "version", "engine", "engine_version", "analysis_version", "qc_criteria"), "protocol.")
    if p.get("status") != "frozen":
        blockers.append("protocol.status: 科学协议尚未冻结")
    if s.get("identity_reviewed") is not True:
        blockers.append("system.identity_reviewed: 结构/组分身份尚未核对")
    need(s, ("polysulfide_state",), "system.")
    for key in ("cpus", "memory_gb", "walltime_hours"):
        if not positive(r.get(key)):
            blockers.append("resources." + key)
    if type(r.get("cpus")) is not int:
        blockers.append("resources.cpus: 需要整数")
    for c in s["components"]:
        need(c, ("structure_id",), f"component[{c['identity']}].")
        if spec["kind"] == "md" and (type(c.get("count")) is not int or c["count"] <= 0):
            blockers.append(f"component[{c['identity']}].count")
        if spec["kind"] == "dft" and (type(c.get("stoichiometry")) is not int or c["stoichiometry"] <= 0):
            blockers.append(f"component[{c['identity']}].stoichiometry")
    if spec["kind"] == "dft":
        need(p, ("method", "basis", "dispersion", "environment", "energy_definition",
                 "conformer_search", "bsse_policy"), "protocol.")
        need(s, ("geometry_sha256", "conformer_id", "fragments"), "system.")
        if type(s.get("charge")) is not int:
            blockers.append("system.charge")
        if type(s.get("multiplicity")) is not int or s["multiplicity"] < 1:
            blockers.append("system.multiplicity")
    else:
        need(p, ("force_field", "charge_model", "parameter_hashes", "ensemble_schedule",
                 "timestep_fs", "observables"), "protocol.")
        need(s, ("composition_basis", "concentration", "box", "topology_sha256"), "system.")
        if not positive(s.get("temperature_k")):
            blockers.append("system.temperature_k")
        for key in ("seed", "replica"):
            if type(s.get(key)) is not int or s[key] < 0:
                blockers.append("system." + key)
    # This is a contract check, not molecular or force-field validation.
    canonical(spec)
    return sorted(set(blockers))


def scientific_payload(spec):
    """Source papers, labels and resource allocation do not change the science key."""
    validate(spec)
    system = dict(spec["system"])
    system["components"] = sorted(system["components"], key=canonical)
    return {"schema_version": spec["schema_version"], "kind": spec["kind"],
            "mode": spec["mode"], "system": system, "protocol": spec["protocol"]}


def plan(spec):
    blockers = validate(spec)
    if spec["kind"] == "dft":
        steps = ["核对物种/电荷/自旋", "生成并预筛多构型", "优化复合物与片段",
                 "按协议计算能量/基组误差", "检查构型与物种", "计算明确定义的结合能", "质检与入库"]
    else:
        steps = ["核对配方与浓度基准", "参数化与电中性核对", "建盒与最小化",
                 "平衡", "多重复生产采样", "结构/输运分析", "分块/重复收敛质检与入库"]
    r = spec["resources"]
    upper = None
    if positive(r.get("cpus")) and positive(r.get("walltime_hours")):
        upper = r["cpus"] * r["walltime_hours"] * spec["retry_policy"]["max_attempts"]
    return {"task_id": digest(scientific_payload(spec)), "mode": spec["mode"],
            "initial_state": "NEEDS_REVIEW" if blockers else "PENDING", "blockers": blockers,
            "steps": steps, "required_qc": list(CHECKS[spec["kind"]]),
            "reserved_cpu_hours_upper_bound": upper,
            "resource_note": "资源申请上界，不是运行时间或费用预测；子任务须单独计入。",
            "execution_backend": "not_connected", "can_submit": False}


class Store:
    """Single local SQLite authority; state changes and audit events are atomic."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
              id TEXT PRIMARY KEY, spec TEXT NOT NULL, state TEXT NOT NULL,
              attempts INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sources (
              task_id TEXT NOT NULL REFERENCES tasks(id), value TEXT NOT NULL,
              PRIMARY KEY(task_id,value));
            CREATE TABLE IF NOT EXISTS events (
              sequence INTEGER PRIMARY KEY AUTOINCREMENT,
              task_id TEXT NOT NULL REFERENCES tasks(id), time TEXT NOT NULL,
              state TEXT NOT NULL, detail TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS results (
              task_id TEXT NOT NULL REFERENCES tasks(id), attempt INTEGER NOT NULL,
              payload TEXT NOT NULL, PRIMARY KEY(task_id,attempt));
        """)

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _event(self, task_id, state, detail):
        self.db.execute("INSERT INTO events(task_id,time,state,detail) VALUES(?,?,?,?)",
                        (task_id, now(), state, canonical(detail)))

    def register(self, spec):
        planned = plan(spec)
        key = planned["task_id"]
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO tasks(id,spec,state,created_at) VALUES(?,?,?,?)",
                            (key, canonical(spec), planned["initial_state"], now()))
            for source in spec["sources"]:
                self.db.execute("INSERT OR IGNORE INTO sources VALUES(?,?)", (key, canonical(source)))
            self._event(key, self.get(key)["state"], {"action": "register", "blockers": planned["blockers"]})
        return key

    def get(self, key):
        row = self.db.execute("SELECT * FROM tasks WHERE id=?", (key,)).fetchone()
        if row is None:
            raise ValueError("未知任务 " + key)
        result = dict(row)
        result["spec"] = json.loads(result["spec"])
        result["sources"] = [json.loads(r[0]) for r in self.db.execute(
            "SELECT value FROM sources WHERE task_id=? ORDER BY value", (key,))]
        result["events"] = [dict(r) for r in self.db.execute(
            "SELECT time,state,detail FROM events WHERE task_id=? ORDER BY sequence", (key,))]
        for event in result["events"]:
            event["detail"] = json.loads(event["detail"])
        return result

    def list(self):
        return [dict(r) for r in self.db.execute(
            "SELECT id,state,attempts,created_at FROM tasks ORDER BY created_at,id")]

    def start_synthetic(self, key):
        """Only test fixtures can run before a real, validated backend is connected."""
        task = self.get(key)
        if task["spec"]["mode"] != "synthetic":
            raise ValueError("真实计算后端尚未接入，不能启动 production 任务")
        if validate(task["spec"]):
            raise ValueError("任务仍有未解决的输入项")
        with self.db:
            changed = self.db.execute(
                "UPDATE tasks SET state='RUNNING',attempts=attempts+1 "
                "WHERE id=? AND state='PENDING' AND attempts<?",
                (key, task["spec"]["retry_policy"]["max_attempts"])).rowcount
            if changed != 1:
                raise ValueError("只能领取待执行且未超重试上限的任务")
            self._event(key, "RUNNING", {"action": "synthetic_start", "not_scientific_data": True})

    def finish_synthetic(self, key, checks, artifacts):
        task = self.get(key)
        if task["state"] != "RUNNING" or task["spec"]["mode"] != "synthetic":
            raise ValueError("只有运行中的 synthetic 任务可写入演示结果")
        if not isinstance(checks, dict):
            raise ValueError("checks 必须为对象")
        files = []
        for file in artifacts:
            path = Path(file).resolve(strict=True)
            files.append({"path": str(path), "sha256": file_hash(path)})
        if not files:
            raise ValueError("结果必须附带实际存在的日志或文件")
        payload = {"not_scientific_data": True, "checks": checks, "artifacts": files,
                   "spec_hash": digest(scientific_payload(task["spec"]))}
        with self.db:
            changed = self.db.execute(
                "UPDATE tasks SET state='SUCCEEDED_PENDING_QC' WHERE id=? AND state='RUNNING' AND attempts=?",
                (key, task["attempts"])).rowcount
            if changed != 1:
                raise ValueError("任务状态已改变")
            self.db.execute("INSERT INTO results VALUES(?,?,?)", (key, task["attempts"], canonical(payload)))
            self._event(key, "SUCCEEDED_PENDING_QC", {"action": "synthetic_finish"})

    def qc(self, key):
        task = self.get(key)
        if task["state"] != "SUCCEEDED_PENDING_QC":
            raise ValueError("只能质检成功待质检的任务")
        row = self.db.execute("SELECT payload FROM results WHERE task_id=? AND attempt=?",
                              (key, task["attempts"])).fetchone()
        result = json.loads(row[0])
        problems = []
        for check in CHECKS[task["spec"]["kind"]]:
            if result["checks"].get(check) is not True:
                problems.append(check)
        for artifact in result["artifacts"]:
            path = Path(artifact["path"])
            if not path.is_file() or file_hash(path) != artifact["sha256"]:
                problems.append("artifact_changed:" + str(path))
        state = "NEEDS_REVIEW" if problems else "PASSED"
        with self.db:
            changed = self.db.execute(
                "UPDATE tasks SET state=? WHERE id=? AND state='SUCCEEDED_PENDING_QC' AND attempts=?",
                (state, key, task["attempts"])).rowcount
            if changed != 1:
                raise ValueError("任务状态已改变")
            self._event(key, state, {"action": "synthetic_qc", "problems": problems,
                                    "not_scientific_data": True})
        return state

    def fail(self, key, reason):
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("必须记录失败原因")
        with self.db:
            changed = self.db.execute("UPDATE tasks SET state='FAILED' WHERE id=? AND state='RUNNING'",
                                      (key,)).rowcount
            if changed != 1:
                raise ValueError("只能将运行中任务标为失败")
            self._event(key, "FAILED", {"action": "fail", "reason": reason})

    def retry(self, key, reason):
        task = self.get(key)
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("重试必须说明原因")
        with self.db:
            changed = self.db.execute(
                "UPDATE tasks SET state='PENDING' WHERE id=? AND state='FAILED' AND attempts<?",
                (key, task["spec"]["retry_policy"]["max_attempts"])).rowcount
            if changed != 1:
                raise ValueError("仅可重试 FAILED 任务，且不得超过次数上限")
            self._event(key, "PENDING", {"action": "same_protocol_retry", "reason": reason})

    def cached(self, key):
        """Recheck artifacts on every cache read; synthetic never supplies production data."""
        task = self.get(key)
        if task["state"] != "PASSED":
            return None
        row = self.db.execute("SELECT payload FROM results WHERE task_id=? AND attempt=?",
                              (key, task["attempts"])).fetchone()
        result = json.loads(row[0])
        if any(not Path(a["path"]).is_file() or file_hash(a["path"]) != a["sha256"]
               for a in result["artifacts"]):
            with self.db:
                self.db.execute("UPDATE tasks SET state='NEEDS_REVIEW' WHERE id=?", (key,))
                self._event(key, "NEEDS_REVIEW", {"action": "cache_invalidated", "reason": "artifact_changed"})
            return None
        return result
