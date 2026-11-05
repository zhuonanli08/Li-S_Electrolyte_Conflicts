"""step14 诊断（11-05 用户要求把迭代方法、结果与不采纳理由写进结果网站）：只读，不训练新模型。

1. 同一改动跨篇一致性（只用开发集，考试集论文不读）：改动 = 实验侧比参照侧多了哪些组分、少了哪些组分
   （(加X,去Y) 与 (加Y,去X) 视为同一改动的正反两向）。对在 ≥2 篇出现的改动：
   - 留一篇查表：用其他论文同一改动的平均效果预测本篇，算 R² 与方向一致率；
   - 只靠改动身份的上限 R²：1 − 组内方差 / 总方差（样本内，偏乐观）。
   只改用量（两侧组分集合相同）的配对单独计数，不算一种改动。
2. 迭代记录分组对比：物性/结构描述符 vs 组分身份、加不加测试条件、镜像/每篇等权/截尾、多任务合训，各取开发集最好 R²。
3. 选定配置核对（是否取自过期记录）与圈数泄漏检查（只用 Δln 圈数能解释多少）。
用法：python -X utf8 diagnose.py <改动模型文件夹>　输出：诊断.json
"""
import sys, json
from pathlib import Path
from collections import defaultdict
import numpy as np

D = Path(sys.argv[1])
CLASSES = ["首圈容量", "每圈衰减率", "全电池CE", "LiCu_CE"]
rows = json.loads((D / "改动表.json").read_text(encoding="utf-8"))
test = set(json.loads((D / "划分.json").read_text(encoding="utf-8"))["考试集论文"])
comp = json.loads((D.parent / "组分结构表_试跑313篇_2026-11-05" / "配方组成.json").read_text(encoding="utf-8"))
RECIPE = {(r["论文"], r["配方"]): frozenset(i["组分"] for i in r["组分"]) for r in comp}
dev = [r for r in rows if r["论文"] not in test]


def r2(obs, pred):
    obs, pred = np.asarray(obs, float), np.asarray(pred, float)
    return float(1 - np.sum((obs - pred) ** 2) / np.sum((obs - obs.mean()) ** 2)) if len(obs) > 2 else None


def consistency(cls):
    R = [r for r in dev if r["类别"] == cls and r["配对类型"] != "同配方、换条件"]
    y = np.array([r["dy"] for r in R], float)
    sig, amount_only = [], 0
    for r in R:
        a, b = RECIPE.get((r["论文"], r["实验"]["recipe"])), RECIPE.get((r["论文"], r["参照"]["recipe"]))
        if a is None or b is None:
            sig.append(None); continue
        if a == b:
            amount_only += 1; sig.append(None); continue
        k1, k2 = (tuple(sorted(a - b)), tuple(sorted(b - a))), (tuple(sorted(b - a)), tuple(sorted(a - b)))
        sig.append((k1, 1.0) if k1 <= k2 else (k2, -1.0))
    groups = defaultdict(list)
    for i, s in enumerate(sig):
        if s is not None:
            groups[s[0]].append(i)
    rep = {k: ix for k, ix in groups.items() if len({R[i]["论文"] for i in ix}) >= 2}
    pred, obs = [], []
    for ix in rep.values():
        for i in ix:
            others = [sig[j][1] * y[j] for j in ix if R[j]["论文"] != R[i]["论文"]]
            pred.append(sig[i][1] * np.mean(others)); obs.append(y[i])
    yr = [sig[i][1] * y[i] for ix in rep.values() for i in ix]
    within = sum(np.sum((np.array([sig[i][1] * y[i] for i in ix]) - np.mean([sig[i][1] * y[i] for i in ix])) ** 2) for ix in rep.values())
    ceil = float(1 - within / np.sum((np.array(yr) - np.mean(yr)) ** 2)) if len(yr) > 2 else None
    ex = []
    for k, ix in sorted(rep.items(), key=lambda kv: -len({R[i]["论文"] for i in kv[1]})):
        v = [sig[i][1] * y[i] for i in ix]
        ex.append({"加": list(k[0]), "去": list(k[1]), "论文数": len({R[i]["论文"] for i in ix}), "配对数": len(ix),
                   "效应最小": round(min(v), 3), "效应最大": round(max(v), 3)})
    n_rep = sum(len(ix) for ix in rep.values())
    return {"不同配方配对": len(R), "只改用量配对": amount_only, "不同改动种数": len(groups), "在≥2篇出现的改动种数": len(rep),
            "在≥2篇出现的改动覆盖配对": n_rep, "覆盖比例": round(n_rep / len(R), 3),
            "留一篇查表R2": None if r2(obs, pred) is None else round(r2(obs, pred), 3),
            "方向一致率": round(float(np.mean(np.sign(pred) == np.sign(obs))), 3) if obs else None, "查表配对数": len(obs),
            "只靠改动身份的上限R2": None if ceil is None else round(ceil, 3), "例子": ex}


L_ALL = [json.loads(l) for l in (D / "迭代记录.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
for i, x in enumerate(L_ALL):
    x["行"] = i
# 过期记录（11-05 夜发现）：r2 的全电池 CE、Li‖Cu 有一批是在剔除首圈 CE 之前的数据上跑的（n 与现行开发集不符），
# 与现行数据上的同一配置重复且分数不同。分组对比只用 n 与现行开发集一致的记录。
N_DEV = {c: sum(r["类别"] == c for r in dev) for c in CLASSES}
L = [x for x in L_ALL if x.get("n") == N_DEV[x["类别"]]]
STALE = [x for x in L_ALL if x.get("n") != N_DEV[x["类别"]]]
PHYS, IDENT = {"ER", "RD5", "SOLV", "STATE"}, {"COMP", "AMT", "COMPxCOND"}


def family(x):
    g = set(x["描述符"].split("+"))
    return "物性/结构＋组分身份" if g & PHYS and g & IDENT else "只有物性/结构" if g & PHYS else "只有组分身份"


def best(xs):
    xs = [x for x in xs if x.get("模型") != "零"]
    if not xs:
        return None
    b = max(xs, key=lambda x: x["总体"])
    keep = ("行", "轮次", "描述符", "模型", "条件", "镜像", "每篇等权", "截尾", "总体", "同测试、不同配方", "跨测试、不同配方", "同配方、换条件", "合训", "n")
    return {**{k: b.get(k) for k in keep if k in b}, "配置数": len(xs)}


def compare(cls):
    C = [x for x in L if x["类别"] == cls]
    single = [x for x in C if x["轮次"] != "r3多任务"]
    out = {"按描述符与条件": {}, "训练技巧": {}, "多任务": {}}
    for fam in ("只有物性/结构", "物性/结构＋组分身份", "只有组分身份"):
        for cond in (False, True):
            b = best([x for x in single if family(x) == fam and x.get("条件") == cond])
            if b:
                out["按描述符与条件"][f"{fam}｜{'加条件' if cond else '不加条件'}"] = b
    # 只在 r1 里同时有“加/不加条件”，单独给同一轮的对比
    out["第1轮加不加条件"] = {("加条件" if c else "不加条件"): best([x for x in C if x["轮次"] == "r1" and x.get("条件") == c]) for c in (False, True)}
    for flag in ("镜像", "每篇等权", "截尾"):
        rr = [x for x in single if x["轮次"] in ("r2", "r4") and (flag != "截尾" or x["轮次"] == "r2")]
        out["训练技巧"][flag] = {"开": best([x for x in rr if x.get(flag)]), "关": best([x for x in rr if not x.get(flag)])}
    for g in ("ER+RD5+ADD+SOLV", "ER+RD5+ADD+SOLV+COMP"):
        out["多任务"][g] = {"单类": best([x for x in single if x["描述符"] == g and x.get("条件")]),
                          "多任务": best([x for x in C if x["轮次"] == "r3多任务" and x["描述符"] == g])}
    st = [x for x in C if x["轮次"] == "r1" and "STATE" in x["描述符"]]
    st0 = [x for x in C if x["轮次"] == "r1" and x["描述符"] == "ER+RD5+ADD+SOLV"]
    out["溶剂化状态STATE"] = {"加之前": best(st0), "加之后": best(st)}
    out["零基线"] = best([dict(x, 模型="_") for x in C if x.get("模型") == "零"])
    return out


def cycle_leak(cls):
    """圈数泄漏检查（11-05 夜，另一会话发现、此处复核）：只用两侧 ln 圈数之差做线性拟合，样本内 R²。
    衰减类按 11-05 用户定不该用圈数：跨论文总损失基本不随圈数变，每圈衰减率 ≈ 总损失 ÷ 圈数，圈数等于泄漏答案。"""
    lc = lambda s: s["条件"].get("ln_圈数")
    R = [r for r in dev if r["类别"] == cls and lc(r["实验"]) is not None and lc(r["参照"]) is not None]
    out = {}
    for name, sub in [("总体", R)] + [(t, [r for r in R if r["配对类型"] == t]) for t in ("同测试、不同配方", "跨测试、不同配方", "同配方、换条件")]:
        if len(sub) < 3:
            continue
        y = np.array([r["dy"] for r in sub]); d = np.array([lc(r["实验"]) - lc(r["参照"]) for r in sub])
        A = np.c_[np.ones(len(d)), d]
        p = A @ np.linalg.lstsq(A, y, rcond=None)[0]
        out[name] = {"n": len(sub), "圈数不同": int((np.abs(d) > 1e-9).sum()), "只用Δln圈数R2": round(r2(y, p), 3)}
    return out


def same_cfg(x, s):
    return all(x.get(k) == s.get(k) for k in ("轮次", "描述符", "模型", "镜像", "每篇等权", "截尾")) and x.get("条件", True) == s.get("条件", True)


sel = json.loads((D / "选定配置.json").read_text(encoding="utf-8"))
check = {}
for c, s in sel.items():
    used = [x for x in L_ALL if x["类别"] == c and same_cfg(x, s) and round(x["总体"], 4) == s["开发集R2"]]
    cur = [x for x in L if x["类别"] == c and same_cfg(x, s)]
    single = [x for x in L if x["类别"] == c and x["轮次"] != "r3多任务"]
    check[c] = {"选定时所用记录": {"行": used[0]["行"], "n": used[0].get("n"), "开发集R2": used[0]["总体"]} if used else None,
                "选定时用了过期记录": bool(used) and used[0].get("n") != N_DEV[c],
                "同一配置在现行数据上": {"行": cur[0]["行"], "开发集R2": cur[0]["总体"]} if cur else None,
                "现行数据上按规则应选": best(single)}

res = {"说明": "只读诊断；一致性只用开发集（考试集论文不读）；迭代记录分组取开发集按论文 5 折的最好总体 R²（从多个配置中挑最好，偏乐观）；"
               "分组对比只用 n 与现行开发集一致的记录",
       "开发集": {"配对": len(dev), "论文": len({r["论文"] for r in dev}), "各类配对": N_DEV},
       "同一改动跨篇一致性": {c: consistency(c) for c in CLASSES},
       "迭代记录对比": {c: compare(c) for c in CLASSES},
       "组分词表大小": len({c for c in {c for r in dev for s in ("实验", "参照") for c in RECIPE.get((r["论文"], r[s]["recipe"]), ())}
                       if len({r["论文"] for r in dev for s in ("实验", "参照") if c in RECIPE.get((r["论文"], r[s]["recipe"]), ())}) >= 2}),
       "迭代配置总数": len(L_ALL), "现行数据上的配置数": len(L),
       "各轮配置数": {k: sum(x["轮次"] == k for x in L) for k in sorted({x["轮次"] for x in L})},
       "各轮内容": {k: {"描述符组": sorted({x["描述符"] for x in L if x["轮次"] == k}), "模型": sorted({x["模型"] for x in L if x["轮次"] == k})}
                for k in sorted({x["轮次"] for x in L})},
       "过期记录": {"条数": len(STALE), "分布": {f"{x['轮次']}｜{x['类别']}｜n={x.get('n')}": sum(1 for y in STALE if (y["轮次"], y["类别"], y.get("n")) == (x["轮次"], x["类别"], x.get("n"))) for x in STALE},
                "说明": "在剔除首圈 CE 之前的数据上跑的 r2 记录（n 与现行开发集不符），与现行数据上的同一配置重复"},
       "选定配置核对": check,
       "圈数泄漏检查": {c: cycle_leak(c) for c in CLASSES}}
(D / "诊断.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
for c in CLASSES:
    s = res["同一改动跨篇一致性"][c]
    print(f"{c}：覆盖 {s['覆盖比例']:.0%}，查表 R² {s['留一篇查表R2']}，方向一致 {s['方向一致率']}，上限 {s['只靠改动身份的上限R2']}")
    for k, v in res["迭代记录对比"][c]["按描述符与条件"].items():
        print(f"   {k}: {v['总体']:+.3f}（{v['配置数']} 个配置）")
    for k, v in res["迭代记录对比"][c]["训练技巧"].items():
        print(f"   {k} 开 {v['开']['总体']:+.3f} / 关 {v['关']['总体']:+.3f}")
    for k, v in res["迭代记录对比"][c]["多任务"].items():
        print(f"   多任务 {k}: 单类 {v['单类']['总体']:+.3f} / 合训 {v['多任务']['总体']:+.3f}")
print("过期记录", res["过期记录"])
for c, v in check.items():
    print(c, "选定时用了过期记录" if v["选定时用了过期记录"] else "选定记录有效", v["选定时所用记录"], "→ 现行同配置", v["同一配置在现行数据上"],
          "→ 现行应选", {k: v["现行数据上按规则应选"][k] for k in ("行", "轮次", "描述符", "模型", "总体")})
for c, v in res["圈数泄漏检查"].items():
    print("圈数泄漏", c, v)
print("→", D / "诊断.json")
