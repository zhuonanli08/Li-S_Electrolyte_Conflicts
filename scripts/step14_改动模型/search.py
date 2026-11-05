"""step14 迭代搜索：以 V3 R² > 0.8 为目标（11-05 用户定），多种描述符组合 × 模型 × 训练技巧。

防止自欺：按论文随机留出约 20% 作最终考试集（种子 20261105，写入 划分.json，迭代期间不读这些论文）；
迭代只在其余论文上做按论文分组的 5 折交叉验证（整篇留出），指标为折外预测的总体 R²，并按配对类型分开报。
每个配置的结果追加到 迭代记录.jsonl。最终配置选定后由 final.py 在考试集上只算一次。
用法：python -X utf8 search.py <改动模型文件夹> <轮次名> [类别1,类别2]（不写类别 = 四类都跑；r5 = 去圈数后的敏感性检查）
"""
import sys, json, time, random, warnings
from pathlib import Path
from collections import defaultdict
import numpy as np
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, HuberRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor, ExtraTreesRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.svm import SVR
warnings.filterwarnings("ignore")

D = Path(sys.argv[1]); ROUND = sys.argv[2] if len(sys.argv) > 2 else "r1"
ROWS = json.loads((D / "改动表.json").read_text(encoding="utf-8"))
CLASSES = ["首圈容量", "每圈衰减率", "全电池CE", "LiCu_CE"]

# ---------- 固定考试集 ----------
SPLIT = D / "划分.json"
if not SPLIT.exists():
    papers = sorted({r["论文"] for r in ROWS})
    test = sorted(random.Random(20261105).sample(papers, round(0.2 * len(papers))))
    SPLIT.write_text(json.dumps({"种子": 20261105, "考试集论文": test, "说明": "迭代期间不读；final.py 只算一次"}, ensure_ascii=False, indent=1), encoding="utf-8")
TEST = set(json.loads(SPLIT.read_text(encoding="utf-8"))["考试集论文"])
DEV = [r for r in ROWS if r["论文"] not in TEST]

# ---------- 描述符组 ----------
ER = ["sO_不含氟", "sO_β氟化醚", "sO_α氟化醚", "aO", "aC", "sC", "aF", "sF", "F/C", "O/C", "F/O", "InOr"]
RD5 = ["醚氧数", "环数", "可旋转键数", "碳酸酯基数", "硫醚/多硫S"]
ADD = ["LiNO3浓度M", "介体", "其他添加剂", "主盐_M", "阴离子F_每升", "阴离子磺酰_每升", "含碘", "有机硫"]
STATE = ["ln_配位位点每Li", "稀释剂摩尔比例", "Li总浓度"]


def solv_keys():
    return sorted({k for r in ROWS for k in r["实验"]["配方特征"] if k.startswith("溶剂_")})


GROUPS = {"ER": ER, "RD5": RD5, "ADD": ADD, "SOLV": solv_keys(), "STATE": STATE}

# 组分身份（第 2 轮）：配方含哪些组分；词表只取开发集里出现在 ≥2 篇的组分（不看考试集）
_COMPF = D.parent / "组分结构表_试跑313篇_2026-11-05" / "配方组成.json"
RECIPE = {(r["论文"], r["配方"]): {i["组分"] for i in r["组分"]} for r in json.loads(_COMPF.read_text(encoding="utf-8"))}
_cnt = defaultdict(set)
for r in DEV:
    for side in ("实验", "参照"):
        for c in RECIPE.get((r["论文"], r[side]["recipe"]), ()):
            _cnt[c].add(r["论文"])
VOCAB = sorted(c for c, ps in _cnt.items() if len(ps) >= 2)
for r in ROWS:  # 组分有无写进配方特征，featurize 统一处理
    for side in ("实验", "参照"):
        cs = RECIPE.get((r["论文"], r[side]["recipe"]), set())
        r[side]["配方特征"].update({"有_" + c: float(c in cs) for c in VOCAB})
GROUPS["COMP"] = ["有_" + c for c in VOCAB]
# 第 4 轮：组分用量（每升溶剂中的物质的量，配方组成算得出的才有）与 组分有无 × 参照条件（ln E/S、载量）交互
AMT = {(r["论文"], r["配方"]): (r.get("每升溶剂物质的量_mol") or {}) for r in json.loads(_COMPF.read_text(encoding="utf-8"))}
for r in ROWS:
    es, ld = r["参照"]["条件"].get("ln_ES"), r["参照"]["条件"].get("载量")
    for side in ("实验", "参照"):
        a = AMT.get((r["论文"], r[side]["recipe"]), {})
        f = r[side]["配方特征"]
        f.update({"量_" + c: (a.get(c, 0.0) if c in a or not f["有_" + c] else None) for c in VOCAB})
        f.update({"有ES_" + c: (f["有_" + c] * es if es is not None else None) for c in VOCAB})
        f.update({"有载量_" + c: (f["有_" + c] * ld if ld is not None else None) for c in VOCAB})
GROUPS["AMT"] = ["量_" + c for c in VOCAB]
GROUPS["COMPxCOND"] = ["有ES_" + c for c in VOCAB] + ["有载量_" + c for c in VOCAB]


def num(v):
    return np.nan if v is None or isinstance(v, bool) and False else float(v) if isinstance(v, (int, float)) else np.nan


# 11-06 修：衰减类不用圈数（11-05 用户定，feats.py 第 63 行同规则）。跨论文看圈数是结果的代理（好电池测得更久，
# 总损失 9–59% 基本不随圈数变 → 每圈衰减率 ≈ 总损失 ÷ 圈数），放进输入等于泄漏答案。
# 改动模型_313篇_2026-11-05 的结果（commit 9afef39）是修正前跑的，保留作历史记录。
DROP_COND = {"每圈衰减率": {"ln_圈数"}}


def featurize(rows, groups, use_cond=True, use_base=True, mirror=False):
    keys = [k for g in groups for k in GROUPS[g]]
    ck = sorted({k for r in rows for k in r["参照"]["条件"] if k not in DROP_COND.get(r["类别"], ())})
    X, y, meta = [], [], []
    for r in rows:
        drop = DROP_COND.get(r["类别"], ())
        cv_ = lambda side, k: np.nan if k in drop else num(side["条件"].get(k))
        for a, b, s in ((r["实验"], r["参照"], 1.0), (r["参照"], r["实验"], -1.0)) if mirror else ((r["实验"], r["参照"], 1.0),):
            fa, fb = a["配方特征"], b["配方特征"]
            row = [num(fa.get(k)) - num(fb.get(k)) for k in keys]
            if use_base:
                row += [num(fb.get(k)) for k in keys]
            if use_cond:
                row += [cv_(b, k) for k in ck] + [cv_(a, k) - cv_(b, k) for k in ck]
            X.append(row); y.append(s * r["dy"]); meta.append(r)
    return np.array(X, float), np.array(y, float), meta


MODELS = {
    "零": None,
    "岭回归a1": lambda: make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(), Ridge(alpha=1.0)),
    "岭回归a10": lambda: make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(), Ridge(alpha=10.0)),
    "Huber": lambda: make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(), HuberRegressor(alpha=1.0, max_iter=2000)),
    "HGB浅": lambda: HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=300, min_samples_leaf=10, l2_regularization=1.0),
    "HGB深": lambda: HistGradientBoostingRegressor(max_depth=None, learning_rate=0.05, max_iter=400, min_samples_leaf=5),
    "RF": lambda: make_pipeline(SimpleImputer(strategy="median", add_indicator=True), RandomForestRegressor(n_estimators=400, min_samples_leaf=2, n_jobs=1, random_state=0)),
    "ET": lambda: make_pipeline(SimpleImputer(strategy="median", add_indicator=True), ExtraTreesRegressor(n_estimators=400, min_samples_leaf=2, n_jobs=1, random_state=0)),
    "kNN5": lambda: make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), KNeighborsRegressor(5, weights="distance")),
    "SVR": lambda: make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(), SVR(C=3.0, epsilon=0.05)),
}


for _a in (0.3, 3.0, 30.0, 100.0):  # 第 4 轮岭回归正则强度网格
    MODELS[f"岭回归a{_a:g}"] = (lambda a=_a: make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(), Ridge(alpha=a)))


class Ens:
    """第 3 轮：岭回归、随机森林、浅层梯度提升的预测取平均。"""
    def __init__(self):
        self.ms = [MODELS[k]() for k in ("岭回归a10", "RF", "HGB浅")]

    def fit(self, X, y, sample_weight=None):
        for m in self.ms:
            fit_model_obj(m, X, y, sample_weight if sample_weight is not None else np.ones(len(y)))
        return self

    def predict(self, X):
        return np.mean([m.predict(X) for m in self.ms], axis=0)


MODELS["集成"] = Ens


def fit_model_obj(m, X, y, w):
    try:
        last = m.steps[-1][0] if hasattr(m, "steps") else None
        m.fit(X, y, **({f"{last}__sample_weight": w} if last else {"sample_weight": w}))
    except TypeError:
        m.fit(X, y)
    return m


def cv_multi(classes, groups, model, mirror=False, paper_w=False, winsor=False):
    """第 3 轮多任务：几类配对合在一起训练（加类别独热），按论文分组 5 折，各类分别算折外 R²。
    截尾按类分别做（各类目标量纲不同）。"""
    rows = [r for r in DEV if r["类别"] in classes]
    paps = np.array([r["论文"] for r in rows])
    pred = np.zeros(len(rows))
    oh = lambda rs: np.array([[float(r["类别"] == c) for c in classes] for r in rs])
    for tr, te in GroupKFold(5).split(rows, groups=paps):
        trr, ter = [rows[i] for i in tr], [rows[i] for i in te]
        Xtr, ytr, mtr = featurize(trr, groups, True, True, mirror)
        Xte, _, _ = featurize(ter, groups, True, True, False)
        Xtr = np.hstack([Xtr, oh(mtr)]); Xte = np.hstack([Xte, oh(ter)])
        if winsor:
            for c in classes:
                k = np.array([r["类别"] == c for r in mtr])
                lo, hi = np.percentile(ytr[k], [5, 95]); ytr[k] = np.clip(ytr[k], lo, hi)
        npp = defaultdict(int)
        for r in mtr: npp[(r["论文"], r["类别"])] += 1
        w = np.array([1.0 / npp[(r["论文"], r["类别"])] for r in mtr]) if paper_w else np.ones(len(ytr))
        pred[te] = fit_model_obj(MODELS[model](), Xtr, ytr, w).predict(Xte)
    obs = np.array([r["dy"] for r in rows])
    out = {}
    for c in classes:
        k = np.array([r["类别"] == c for r in rows])
        kk = k & np.array([r["配对类型"] != "同配方、换条件" for r in rows])
        out[c] = {"总体": r2_score(obs[k], pred[k]), "不同配方合计": r2_score(obs[kk], pred[kk]), "n": int(k.sum())}
    return out


def fit_model(model, X, y, w):
    m = MODELS[model]()
    try:
        last = m.steps[-1][0] if hasattr(m, "steps") else None
        m.fit(X, y, **({f"{last}__sample_weight": w} if last else {"sample_weight": w}))
    except TypeError:  # kNN 等不支持样本权重
        m.fit(X, y)
    return m


def cv(cls, groups, model, use_cond=True, use_base=True, mirror=False, rows=None, paper_w=False, winsor=False):
    """paper_w：每篇等权（样本权重 = 1 / 本篇配对数）；winsor：训练目标截到训练集 5–95% 分位（评估仍用原值）。"""
    rows = [r for r in (rows or DEV) if r["类别"] == cls]
    paps = np.array([r["论文"] for r in rows])
    pred = np.zeros(len(rows))
    for tr, te in GroupKFold(5).split(rows, groups=paps):
        trr = [rows[i] for i in tr]
        Xtr, ytr, mtr = featurize(trr, groups, use_cond, use_base, mirror)
        Xte, _, _ = featurize([rows[i] for i in te], groups, use_cond, use_base, False)
        if MODELS[model] is None:
            pred[te] = 0.0
            continue
        if winsor:
            lo, hi = np.percentile(ytr, [5, 95]); ytr = np.clip(ytr, lo, hi)
        npp = defaultdict(int)
        for r in mtr: npp[r["论文"]] += 1
        w = np.array([1.0 / npp[r["论文"]] for r in mtr]) if paper_w else np.ones(len(ytr))
        pred[te] = fit_model(model, Xtr, ytr, w).predict(Xte)
    obs = np.array([r["dy"] for r in rows])
    res = {"总体": r2_score(obs, pred), "n": len(rows)}
    for t in ("同测试、不同配方", "跨测试、不同配方", "同配方、换条件"):
        k = np.array([r["配对类型"] == t for r in rows])
        res[t] = r2_score(obs[k], pred[k]) if k.sum() > 2 else None
    k = np.array([r["配对类型"] != "同配方、换条件" for r in rows])
    res["不同配方合计"] = r2_score(obs[k], pred[k])
    return res, pred, obs, rows


def log(entry):
    with open(D / "迭代记录.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


ROUNDS = {
    "r1": [(g, m, c, b, mi) for g in (("ER",), ("ER", "ADD"), ("ER", "RD5", "ADD"), ("ER", "RD5", "ADD", "SOLV"), ("ER", "RD5", "ADD", "SOLV", "STATE"))
           for m in MODELS for c in (False, True) for b in (True,) for mi in (False,)],
    # 第 2 轮：加组分身份；镜像增广、每篇等权、训练目标截尾
    "r2": [(g, m, True, True, mi, pw, ws) for g in (("COMP",), ("ER", "RD5", "ADD", "COMP"), ("ER", "RD5", "ADD", "SOLV", "COMP"))
           for m in ("岭回归a10", "HGB浅", "HGB深", "RF", "ET") for mi in (False, True) for pw in (False, True) for ws in (False, True)],
    # 第 4 轮：组分有无 + 用量 + 组分×条件交互，线性为主（第 2 轮衰减率上岭回归最好）
    "r4": [(g, m, True, True, mi, pw, ws)
           for g in (("COMP",), ("COMP", "AMT"), ("COMP", "COMPxCOND"), ("COMP", "AMT", "COMPxCOND"), ("ER", "ADD", "COMP", "AMT", "COMPxCOND"))
           for m in ("岭回归a0.3", "岭回归a3", "岭回归a10", "岭回归a30", "岭回归a100", "集成")
           for mi in (False, True) for pw in (False, True) for ws in (False,)],
}

def run_r3():
    sets = [("每圈衰减率", "全电池CE", "LiCu_CE"), ("首圈容量", "每圈衰减率", "全电池CE", "LiCu_CE")]
    for cs in sets:
        for g in (("ER", "RD5", "ADD", "SOLV"), ("ER", "RD5", "ADD", "SOLV", "COMP")):
            for m in ("RF", "ET", "HGB浅", "集成"):
                for mi, pw, ws in ((False, False, False), (True, False, False), (False, True, True), (True, True, True)):
                    res = cv_multi(cs, g, m, mi, pw, ws)
                    for c, v in res.items():
                        log({"轮次": "r3多任务", "合训": "+".join(cs), "类别": c, "描述符": "+".join(g), "模型": m, "镜像": mi, "每篇等权": pw,
                             "截尾": ws, **{k: (round(x, 4) if isinstance(x, float) else x) for k, x in v.items()}})
                    print("+".join(cs)[:20], "+".join(g)[-12:], m, mi, pw, ws, " | ".join(f"{c} {v['总体']:+.3f}" for c, v in res.items()), flush=True)


def cyc_ratio(r):
    a, b = r["实验"]["条件"].get("ln_圈数"), r["参照"]["条件"].get("ln_圈数")
    return None if a is None or b is None else float(np.exp(abs(a - b)))


def run_r5(cls):
    """11-06 敏感性（衰减类去圈数后）：① 只用条件的基线；② 各轮开发集前 5 名配置在“两边圈数相差 ≤5 倍”的配对上重跑。"""
    recs = [json.loads(l) for l in open(D / "迭代记录.jsonl", encoding="utf-8")]
    recs = [e for e in recs if e["类别"] == cls and e["轮次"] in ("r1", "r2", "r4")]
    for c, m in ((False, "零"), (True, "岭回归a10"), (True, "RF")):  # 零模型 = 预测“没差别”
        res, *_ = cv(cls, (), m, c, False)
        log({"轮次": "r5敏感性", "类别": cls, "检查": "只用条件" if c else "零模型", "描述符": "", "模型": m, "条件": c,
             **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items()}})
        print(f"{'只用条件 ' + m if c else '零模型'}：R² 总体 {res['总体']:+.3f}，同测试 {res['同测试、不同配方']}", flush=True)
    sub = [r for r in DEV if r["类别"] == cls and (cyc_ratio(r) is None or cyc_ratio(r) <= 5)]
    print(f"圈数相差 ≤5 倍：{len(sub)} / {sum(r['类别'] == cls for r in DEV)} 对", flush=True)
    for e in sorted(recs, key=lambda e: -e["总体"])[:5]:
        g = tuple(e["描述符"].split("+"))
        res, *_ = cv(cls, g, e["模型"], e["条件"], e.get("原配方", True), e["镜像"], rows=sub, paper_w=e["每篇等权"], winsor=e["截尾"])
        log({"轮次": "r5敏感性", "类别": cls, "检查": "圈数相差≤5倍", "原轮次": e["轮次"], "原总体": e["总体"], "描述符": e["描述符"],
             "模型": e["模型"], "条件": e["条件"], "镜像": e["镜像"], "每篇等权": e["每篇等权"], "截尾": e["截尾"],
             **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items()}})
        print(f"  {e['描述符']} {e['模型']}：全部 {e['总体']:+.3f} → ≤5 倍 {res['总体']:+.3f}", flush=True)


ONLY = sys.argv[3].split(",") if len(sys.argv) > 3 else CLASSES  # 11-06：可只跑指定类别

if __name__ == "__main__" and ROUND == "r3":
    run_r3(); sys.exit()

if __name__ == "__main__" and ROUND == "r5":
    for c in ONLY: run_r5(c)
    sys.exit()

if __name__ == "__main__":
    print(f"开发集 {len(DEV)} 对（{len({r['论文'] for r in DEV})} 篇）；考试集留出 {len(TEST)} 篇，不参与")
    for cls in ONLY:
        best = []
        for cfg in ROUNDS[ROUND]:
            g, m, c, b, mi, pw, ws = (tuple(cfg) + (False, False))[:7]
            t0 = time.time()
            res, *_ = cv(cls, g, m, c, b, mi, paper_w=pw, winsor=ws)
            e = {"轮次": ROUND, "类别": cls, "描述符": "+".join(g), "条件": c, "原配方": b, "镜像": mi, "每篇等权": pw, "截尾": ws, "模型": m,
                 **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items()}, "秒": round(time.time() - t0, 1)}
            log(e); best.append(e)
        best.sort(key=lambda e: -e["总体"])
        print(f"\n## {cls}（n={best[0]['n']}）前 6：")
        for e in best[:6]:
            print(f"   R²总体 {e['总体']:+.3f} | 不同配方 {e['不同配方合计']:+.3f} | 同测试 {e['同测试、不同配方'] if e['同测试、不同配方'] is None else round(e['同测试、不同配方'], 3)} "
                  f"| 换条件 {e['同配方、换条件'] if e['同配方、换条件'] is None else round(e['同配方、换条件'], 3)} | {e['描述符']} 条件={e['条件']} 镜像={e['镜像']} 等权={e['每篇等权']} 截尾={e['截尾']} {e['模型']}")
