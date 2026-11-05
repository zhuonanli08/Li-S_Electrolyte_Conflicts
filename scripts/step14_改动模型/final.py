"""step14 最终考试：用迭代选定的配置（选定配置.json）在全部开发集论文上训练，预测留出的考试集论文，只算一次。
输出 考试结果.json：各类总体 R²、按配对类型的 R²、按论文重抽样的 95% 区间，以及运行次数（重复运行要 --force，并记入次数）。
用法：python -X utf8 final.py <改动模型文件夹> [--force]
"""
import sys, json
import numpy as np
from pathlib import Path
from sklearn.metrics import r2_score

D = Path(sys.argv[1])
sys.argv = [sys.argv[0], str(D), "final"] + sys.argv[2:]
exec(open(Path(__file__).with_name("search.py"), encoding="utf-8").read().split("ROUNDS = {")[0])

OUTF = D / "考试结果.json"
prev = json.loads(OUTF.read_text(encoding="utf-8")) if OUTF.exists() else None
if prev and "--force" not in sys.argv:
    sys.exit(f"考试集已经算过 {prev['运行次数']} 次；如确需重算加 --force（会记入次数）")
CFG = json.loads((D / "选定配置.json").read_text(encoding="utf-8"))
TESTROWS = [r for r in ROWS if r["论文"] in TEST]
out = {"运行次数": (prev["运行次数"] + 1) if prev else 1, "配置": CFG, "类别": {}}
rng = np.random.default_rng(0)
for cls, c in CFG.items():
    g = tuple(c["描述符"].split("+"))
    tr = [r for r in DEV if r["类别"] == cls]; te = [r for r in TESTROWS if r["类别"] == cls]
    Xtr, ytr, mtr = featurize(tr, g, c.get("条件", True), True, c.get("镜像", False))
    Xte, yte, _ = featurize(te, g, c.get("条件", True), True, False)
    if c.get("截尾"):
        lo, hi = np.percentile(ytr, [5, 95]); ytr = np.clip(ytr, lo, hi)
    npp = defaultdict(int)
    for r in mtr: npp[r["论文"]] += 1
    w = np.array([1.0 / npp[r["论文"]] for r in mtr]) if c.get("每篇等权") else np.ones(len(ytr))
    pred = fit_model(c["模型"], Xtr, ytr, w).predict(Xte)
    res = {"n": len(te), "论文": len({r['论文'] for r in te}), "总体": r2_score(yte, pred)}
    for t in ("同测试、不同配方", "跨测试、不同配方", "同配方、换条件"):
        k = np.array([r["配对类型"] == t for r in te])
        res[t] = r2_score(yte[k], pred[k]) if k.sum() > 2 else None
    paps = sorted({r["论文"] for r in te}); idx = {p: [i for i, r in enumerate(te) if r["论文"] == p] for p in paps}
    bs = []
    for _ in range(500):
        s = sum((idx[p] for p in rng.choice(paps, len(paps))), [])
        if len(set(yte[s])) > 1: bs.append(r2_score(yte[s], pred[s]))
    res["总体95%区间"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    out["类别"][cls] = res
    print(f"{cls}：考试集 {res['n']} 对 / {res['论文']} 篇，R² {res['总体']:+.3f}（95% 区间 {res['总体95%区间'][0]:+.2f}～{res['总体95%区间'][1]:+.2f}）")
OUTF.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
