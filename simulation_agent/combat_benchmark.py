"""Pinned ComBat reference audit and a single DME input preparation, never a job runner.

Only public derived data are checked. No source JSON is promoted to scientific QC
PASSED and no reference value is represented as a new simulation result.
"""

import argparse
import ast
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import urllib.request

from .engines import coordinates, render_dft
from .mispr_adapter import normalize_gaussian

HERE = Path(__file__).resolve().parent
BUNDLE = HERE / "benchmarks" / "combat_dme"
CACHE = HERE / "work" / "combat_source"
# CODATA conversions; rounding of upstream constants is covered by audit tolerances.
HARTREE_TO_EV = 27.211386245988
HARTREE_TO_KCAL_MOL = 627.5094740631


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False) + "\n", encoding="utf-8")


def verify_sources(cache, lock):
    for item in lock["files"]:
        path = Path(cache) / item["path"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("参考文件缺失或哈希不符：" + item["path"])


def download(cache, lock):
    """Explicit bounded download of pinned public data; never import upstream scripts."""
    for item in lock["files"]:
        path = Path(cache) / item["path"]
        if path.exists():
            if hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]:
                continue
            raise ValueError("拒绝覆盖已变化的参考文件：" + str(path))
        url = "https://raw.githubusercontent.com/rashatwi/combat/" + lock["commit"] + "/" + item["path"]
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read(item["bytes"] + 1)
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError("下载内容与锁定版本不符：" + item["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    verify_sources(cache, lock)


def finite(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("参考值必须是有限数值")
    return number


def csv_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sum_duplicate_column(path, label):
    # csv.DictReader would silently discard same-named atom-site columns.
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))
    if len(rows) != 2 or len(rows[0]) != len(rows[1]):
        raise ValueError("配位数文件应只有一行统计数据且列数一致")
    indices = [i for i, name in enumerate(rows[0]) if name == label]
    if not indices:
        raise ValueError("缺少配位列：" + label)
    return sum(finite(rows[1][i]) for i in indices)


def check(name, actual, expected, unit, tolerance):
    actual, expected = finite(actual), finite(expected)
    delta = abs(actual - expected)
    return {"name": name, "reconstructed": actual, "reference": expected,
            "unit": unit, "absolute_difference": delta, "absolute_tolerance": tolerance,
            "passed": delta <= tolerance}


def formula(molecule):
    return Counter(site["species"][0]["element"] for site in molecule["sites"])


def reference_audit(cache):
    cache = Path(cache)
    rows = csv_rows(cache / "data.csv")
    candidates = [r for r in rows if r["Abbreviation"] == "DME"]
    if len(candidates) != 1:
        raise ValueError("DME 必须唯一")
    row = candidates[0]
    dme = read_json(cache / "binding_energy/single_molecules/dme.json")
    checks = []
    for ligand, directory, column in (("salt", "solvent_salt", "BE_Salt"),
                                       ("ps", "solvent_polysulfide", "BE_PS")):
        fragment = read_json(cache / f"binding_energy/single_molecules/{ligand}.json")
        complex_doc = read_json(cache / f"binding_energy/{directory}/dme_{ligand}.json")
        for key in ("functional", "basis", "phase"):
            if len({dme[key], fragment[key], complex_doc[key]}) != 1:
                raise ValueError("参考能量方法不一致：" + key)
        molecules = [d["output"]["output"]["molecule"] for d in (dme, fragment)]
        if formula(molecules[0]) + formula(molecules[1]) != formula(complex_doc["molecule"]):
            raise ValueError("结合能片段元素计量不守恒")
        if sum(m["charge"] for m in molecules) != complex_doc["molecule"]["charge"]:
            raise ValueError("结合能片段电荷不守恒")
        energy = finite(complex_doc["energy"]) - sum(
            finite(d["output"]["output"]["final_energy"]) for d in (dme, fragment))
        checks.append(check(column + " vs be_eV", energy * HARTREE_TO_EV,
                            complex_doc["be_eV"]["value"], "eV", 1e-4))
        checks.append(check(column + " vs data.csv", energy * HARTREE_TO_KCAL_MOL,
                            row[column], "kcal/mol", 1e-3))
    for label, column in (("O (DOL)", "Li - O (DOL)"), ("O (DME)", "Li - X (Solvent)"),
                          ("O (TFSI)", "Li - O (TFSI)"), ("S out (PS)", "Li - S (PS)"),
                          ("Li", "Li - Li")):
        checks.append(check(column, sum_duplicate_column(cache / "coordination_numbers/dme.csv", label),
                            row[column], "dimensionless", 1e-10))
    diffusion = {r[""]: r for r in csv_rows(cache / "diffusion/dme.csv")}
    for species, column in (("dol", "Diffusion_DOL"), ("dme", "Diffusion_Solvent"),
                            ("tfsi", "Diffusion_TFSI"), ("ps", "Diffusion_PS"), ("li", "Diffusion_Li")):
        checks.append(check(column, diffusion[species]["diffusion (m2/s)"], row[column], "m2/s", 1e-18))
    checks.append(check("Diffusion_Ratio", finite(diffusion["dme"]["diffusion (m2/s)"]) /
                        finite(diffusion["li"]["diffusion (m2/s)"]), row["Diffusion_Ratio"], "dimensionless", 1e-10))
    return {"status": "REFERENCE_TABLES_CONSISTENT" if all(c["passed"] for c in checks) else "NEEDS_REVIEW",
            "scope": "作者公开派生数据的算术、单位与表间一致性；不是新计算或独立物理验证",
            "checks": checks, "real_jobs_submitted": 0, "new_scientific_results": 0,
            "raw_log_reparsed": False, "trajectory_reanalyzed": False,
            "limitations": [
                "复合物摘要未包含完整 route，不能仅靠同名 functional/basis 证明所有计算参数一致",
                "原始 Gaussian 日志、MD 轨迹未在锁定仓库目录中发现；Minimum 是作者摘要标记，尚未独立核查频率",
                "MD 的 std 字段不在本轮解释为重复模拟置信区间",
                "run_md.py 引用旧接口和大小写不同的文件名；epsilon.py 查找 DOL 行，而锁定 data.csv 无该行，禁止原样执行",
                "data.csv 的配位/扩散含 0.25 M Li2S8，电导/黏度对应无多硫化物体系，不混作同一配方"],
            "dme_inchi": row["InChI"], "dme_smiles": row["CanonicalSMILES"],
            "dol_row_present": any(r["Abbreviation"] == "DOL" for r in rows)}


def literal_assignment(path, name):
    for node in ast.parse(Path(path).read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("作者脚本缺少参数字典：" + name)


def prepare_dme(cache, out, lock):
    """Render only the published-geometry frequency job, using the real MISPR utility."""
    doc = read_json(Path(cache) / "binding_energy/single_molecules/dme.json")
    molecule = doc["input"]["molecule"]
    atoms = [{"element": s["species"][0]["element"], "xyz_angstrom": s["xyz"]} for s in molecule["sites"]]
    request = {"gaussian_inputs": {}, "solvent_gaussian_inputs": None}
    for stage, name in (("opt", "opt_gaussian_inputs"), ("freq", "freq_gaussian_inputs")):
        settings = literal_assignment(Path(cache) / "scripts/calc_be.py", name)
        settings["link0_parameters"] = {"%chk": stage + ".chk", "%mem": "3072MB", "%NProcShared": "2"}
        request["gaussian_inputs"][stage] = settings
    settings = request["gaussian_inputs"]["freq"]
    if settings["route_parameters"] != doc["input"]["route_parameters"]:
        raise ValueError("脚本与 DME 参考频率计算的 route 不一致")
    normalized = normalize_gaussian(request)
    if normalized["gaussian_inputs"]["freq"] != settings:
        raise ValueError("MISPR 改变了频率输入，需复核")
    route = settings["functional"] + "/" + settings["basis_set"] + " " + " ".join(
        key if value is None else key + "=" + value for key, value in settings["route_parameters"].items())
    content = render_dft("gaussian", atoms, doc["input"]["charge"], doc["input"]["spin_multiplicity"], route, 2, 4)
    content = content.replace("%chk=calculation.chk", "%chk=freq.chk")
    (out / "dme_frequency.gjf").write_text(content, encoding="ascii")
    (out / "dme_reference.xyz").write_text(str(len(atoms)) + "\nComBat published geometry, not generated by us\n" +
                                          coordinates(atoms, 0, 1) + "\n", encoding="ascii")
    write_json(out / "mispr_request.json", request)
    write_json(out / "mispr_normalized.json", normalized)
    write_json(out / "pilot.json", {
        "status": "PREPARED_NOT_SUBMITTED", "sample": "DME", "atoms": len(atoms),
        "source_commit": lock["commit"], "source_file": "binding_energy/single_molecules/dme.json",
        "reference_engine": doc["gauss_version"], "reference_energy_hartree": doc["output"]["output"]["final_energy"],
        "reference_stationary_type_reported": doc["output"]["output"]["stationary_type"],
        "task": "Frequency calculation on published DME geometry, gas phase, B3LYP/6-31+G* + GD3",
        "scope": "检验输入/引擎/输出链路及测实耗；不代表从零优化、多构型搜索、结合能或 MD 流程验收",
        "resource_draft": {"cpus": 2, "allocated_memory_gb": 4, "gaussian_memory_mb": 3072,
                           "walltime_minutes": 30, "maximum_core_hours_if_core_billed": 1.0},
        "price_per_core_hour": None, "spend_cap": None, "can_submit": False,
        "changes_from_author": ["28 核/45GB 改为待平台核实的 2 核/3072MB；调度申请内存 4GB",
                                "只从公开几何运行频率阶段，不执行全库脚本或几何优化"],
        "required_before_submission": ["确认 Gaussian 可用及版本、许可证、队列、最低资源和计费规则",
                                       "按实际计价形成费用上界和限时脚本", "检查资源草案是否足够并确认最终单样本费用上限"],
        "validation_after_run": ["保留原始日志、命令、版本、输入哈希与计费记录",
                                 "检查正常结束、全部振动频率及能量；能量差异调查阈值暂设 1e-5 Hartree，非物理精度标准",
                                 "频率/几何/科学质检尚待实现；不得凭正常退出自动标记科学 PASSED"],
        "real_jobs_submitted": 0, "full_mispr_execution_connected": False})


def main():
    parser = argparse.ArgumentParser(description="ComBat 小样：公开数据核对与输入准备，不提交计算")
    parser.add_argument("--cache", type=Path, default=CACHE)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--download", action="store_true", help="显式下载固定版本的 25 个小文件")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("输出目录已存在，请另选目录，避免覆盖证据")
    lock = read_json(BUNDLE / "source.lock.json")
    if args.download:
        download(args.cache, lock)
    verify_sources(args.cache, lock)
    report = reference_audit(args.cache)
    report["source_commit"] = lock["commit"]
    report["verified_source_files"] = len(lock["files"])
    args.out.mkdir(parents=True)
    write_json(args.out / "reference_audit.json", report)
    if report["status"] != "REFERENCE_TABLES_CONSISTENT":
        raise SystemExit("参考表出现不一致，请复核 reference_audit.json，未生成试算输入")
    prepare_dme(args.cache, args.out, lock)
    print(json.dumps({"reference_checks": len(report["checks"]), "passed": sum(c["passed"] for c in report["checks"]),
                      "out": str(args.out), "real_jobs_submitted": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
