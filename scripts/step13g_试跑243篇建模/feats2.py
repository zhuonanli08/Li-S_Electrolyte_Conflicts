"""243 篇试跑的建模数据（运行前设好 KETI2_PAPERS / KETI2_COMP / KETI2_OUT 指向试跑文件夹）。
在 feats.py 基础上：① 主层筛选（Li‖S、硫碳正极；Li‖Cu 单列）；② 去掉不能做性能分析的论文；
③ 执行字段限制：不能进模型的结果剔除、有冲突的条件当缺失、非同条件结果不作 V3 直接比较；
④ BASIS_LOOSE=1 时把“比放电容量（基准未写明）”当作按硫计（对照版本）。"""
import os
from pathlib import Path
from feats import *

TRIAL = Path(os.environ["KETI2_PAPERS"]).parent
LOOSE = os.environ.get("BASIS_LOOSE") == "1"
META = json.loads((TRIAL / "数据集说明.json").read_text(encoding="utf-8"))
LIM = json.loads((TRIAL / "限制.json").read_text(encoding="utf-8"))
BAD_PAPERS = set(META["性能分析不可用"])


def _rid(pid, path):
    m = re.match(r"/tests/(\d+)/results/(\d+)", path or "")
    if not m or pid not in PAPERS:
        return None
    try:
        return str(PAPERS[pid]["tests"][int(m.group(1))]["results"][int(m.group(2))]["id"]).lower()
    except (IndexError, KeyError):
        return None


EXCL_RES, NONCOMP, EXCL_COND = set(), set(), set()
for e in LIM["analysis_exclusions"]:
    p, path, kind = e["paper"], e["path"], e["restriction"]
    rid = (e.get("id") or "").lower() or _rid(p, path)
    if kind.startswith("exclude_from_performance_models"):
        EXCL_RES.add((p, rid))
    elif kind.startswith("exclude_from_same_noncomposition"):
        NONCOMP.add((p, rid))
    elif kind.startswith("exclude_as_certain_numeric"):
        m = re.match(r"/condition_definitions/([^/]+)", path)
        if m:
            EXCL_COND.add((p, m.group(1)))
for u in LIM["unresolved_scope_restrictions"]:
    for path in u["field_paths"]:
        m = re.match(r"/condition_definitions/([^/]+)", path)
        if m:
            EXCL_COND.add((u["paper"], m.group(1)))
        elif "/results/" in path:
            EXCL_RES.add((u["paper"], _rid(u["paper"], path)))

FIELD2FEAT = {"ES": "ln_ES", "sulfur_loading": "载量", "S_content": "含硫", "rate": "ln_倍率", "temperature": "温度",
              "cell_format": "软包", "voltage_window": "截止下限V", "current": "ln_电流", "Li_Cu_capacity": "ln_沉积容量"}
STATS = Counter()


def class_rows2(cname):
    spec = N.CLASSES[cname]
    cu = "Li‖Cu" in cname
    std = list(spec["std"]) + (["比放电容量（基准未写明）"] if LOOSE and spec.get("cap") else [])
    rows = []
    for s in N.dedup(read_json("表述.json")):
        if s["标准指标"] not in std or s["数值类型"] not in ("精确", "约数", "范围") or N.yval(s, spec["y"]) is None:
            continue
        if spec.get("stage") and s["阶段"] != spec["stage"]:
            continue
        if s["论文"] in BAD_PAPERS:
            STATS["论文不可用"] += 1; continue
        if not cu and (s["电池类型"] != "Li‖S" or s["正极类型"] != "硫碳类"):
            STATS["非主层（SPAN/Li2S/非锂负极）"] += 1; continue
        res = {(s["论文"], str(r).lower()) for r in s.get("来源结果") or []}
        if res & EXCL_RES:
            STATS["结果被限制剔除"] += 1; continue
        er = s["元素比例"] or {}
        x = {k: er.get(k) for k in ER}
        x.update(rd5(s["论文"], s["recipe"]))
        x.update(other(s["论文"], s["recipe"]))
        x.update(N.Feat.cond(s, cu))
        x["截止下限V"] = None if cu else cutoff(s["论文"], s["测试"])
        t = next((t for t in PAPERS[s["论文"]]["tests"] if t["id"] == s["测试"]), {})
        for f, cid in (t.get("condition_refs") or {}).items():
            if (s["论文"], cid) in EXCL_COND and FIELD2FEAT.get(f) in x:
                x[FIELD2FEAT[f]] = None
                STATS["条件因冲突置空"] += 1
        rows.append(dict(s=s, y=N.yval(s, spec["y"]), x=x, noncomp=bool(res & NONCOMP)))
    pc = Counter(r["s"]["论文"] for r in rows)
    return [r for r in rows if pc[r["s"]["论文"]] >= 2]
