"""按“两个配方差在哪里”给 V3 配对分类，分别算 V3（读 run2 结果；配对按 run2 同样规则重建，顺序一致）。"""
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
from feats2 import *
from v3net import fkey

CNAME, TAG = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]
res = json.loads((Path(__file__).parent / "结果_243篇" / f"V3_{TAG}.json").read_text(encoding="utf-8"))
rows = class_rows2(CNAME)
for r in rows:
    r["fk"] = fkey(r["s"]["论文"], r["s"]["recipe"])
g = np.array([r["s"]["论文"] for r in rows])
by = defaultdict(list)
for i, r in enumerate(rows):
    if not r["noncomp"] and r["fk"]:
        by[(g[i], r["s"]["测试"], r["s"]["圈数"])].append(i)
pairs = []
for k, idx in by.items():
    ref = next((i for i in idx if rows[i]["s"]["是否对照"]), idx[0])
    pairs += [(k[0], i, ref) for i in idx if i != ref and rows[i]["fk"] != rows[ref]["fk"]]
npap = defaultdict(set)
for p, i, j in pairs:
    npap[frozenset((rows[i]["fk"], rows[j]["fk"]))].add(p)
V3 = [t for t in pairs if len(npap[frozenset((rows[t[1]]["fk"], rows[t[2]]["fk"]))]) == 1]
assert len(V3) == res["V3配对"], (len(V3), res["V3配对"])


def parts(i):
    out = defaultdict(dict)
    for c, u, x in rows[i]["fk"]:
        cat = CTAB.get(c, {}).get("类别", "")
        k = "LiNO3" if c == "LiNO3" else "溶剂" if cat in ("溶剂", "溶剂/添加剂") else "锂盐" if cat == "锂盐" else "添加剂/介体"
        out[k][c] = x
    return out


def kind(i, j):
    a, b = parts(i), parts(j)
    diff = [k for k in ("溶剂", "锂盐", "LiNO3", "添加剂/介体") if a.get(k, {}) != b.get(k, {})]
    if diff == ["添加剂/介体"]:
        ids = set(a.get("添加剂/介体", {})) ^ set(b.get("添加剂/介体", {})) or set(a.get("添加剂/介体", {}))
        return "只改添加剂/介体（结构未写）" if ids & {"ADD_TRIAL", "MED_TRIAL"} else "只改添加剂/介体（有结构）"
    return "只改" + diff[0] if len(diff) == 1 else ("同时改" + "+".join(diff) if diff else "组成相同")


kinds = [kind(i, j) for _, i, j in V3]
obs = np.array(res["模型"]["线性岭回归"]["obs"])
print(f"## {TAG}：V3 {len(V3)} 对；类型分布 {Counter(kinds).most_common()}")
for mn in ("线性岭回归", "单调约束梯度提升", "随机森林", "高斯过程"):
    pr = np.array(res["模型"][mn]["pred"])
    line = []
    for k in sorted(set(kinds), key=lambda k: -kinds.count(k)):
        m = np.array([x == k for x in kinds])
        if m.sum() >= 4:
            o, p = obs[m], pr[m]
            r2 = 1 - ((o - p) ** 2).sum() / ((o - o.mean()) ** 2).sum()
            line.append(f"{k}({m.sum()}) R²={r2:+.2f} RMSE={np.sqrt(np.mean((o - p) ** 2)):.2f}")
    print(f"   {mn:8s} " + " | ".join(line))
