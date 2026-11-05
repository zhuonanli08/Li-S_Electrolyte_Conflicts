"""step14 改动表（11-05 用户定：跨条件配对；目标 V3 R² > 0.8，以目标为导向迭代）。

一行 = 一篇论文里的一次比较：输出 = 实验测量 y − 参照测量 y（容量 ln 比、每圈衰减率 −ln 比、CE 损失比）。
配对规则（方案 §8.7，11-02“实验样都和对比样比、允许跨条件”）：每篇 n 个测量 → n−1 对；
  同测试同圈数同指标里有对照配方 → 和它比（同测试、不同配方）；否则和本篇参照测量比（跨测试、不同配方，或同配方换条件），
  参照 = 本篇对照配方在配方数最多的那个测试里的测量。提取标“非同条件”的结果不进（两侧条件可能没分开记）。
特征（每行都存两侧原值，建模时再组合）：配方描述符（元素比例、RDKit 5 项、xdata.struct 溶剂加权官能团/主盐/阴离子/添加剂、
feats3.state 溶剂化状态）、测试条件；另存默认值标记（E/S、温度、溶剂比例）。
用法：KETI2_PAPERS=… KETI2_COMP=… KETI2_OUT=… python -X utf8 pairs.py <输出文件夹>
"""
import sys, json, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "step13g_试跑243篇建模"))
from feats3 import *  # noqa: F401,F403  （含 feats2.class_rows2、xdata.struct、state）

OUT = Path(sys.argv[1])
CLS = {"放电容量类": "首圈容量", "衰减类": "每圈衰减率", "库仑效率类·全电池": "全电池CE", "库仑效率类·Li‖Cu": "LiCu_CE"}


def form_feats(r):
    s = r["s"]
    f = {k: r["x"].get(k) for k in ER + list(RD5) + OTHER}
    st, _ = struct(s["论文"], s["recipe"])
    f.update({k: v for k, v in st.items() if isinstance(v, (int, float)) or v is None})
    f.update(state(s["论文"], s["recipe"]))
    return f


def flags(r):
    s = r["s"]; c = s["条件"]
    rec = COMPREC.get((s["论文"], s["recipe"])) or {}
    return {"ES默认": bool(c.get("ES", {}).get("默认")), "温度默认": bool(c.get("temperature", {}).get("默认")),
            "溶剂比例默认": bool((rec.get("元素比例") or {}).get("默认")), "元素比例可算": r["x"].get("sO") is not None}


def build(cname):
    cu = "Li‖Cu" in cname
    cond_keys = N.COND_CU if cu else COND_LIS
    # 体检剔除（11-05）：硫比容量 <10 mAh g⁻¹ 为单位错误（P344 1.51）；CE 只用循环 CE，首圈 CE 反映首圈不可逆损失（P017 8.8%–79.9%），
    # 跨测试配对时还会和第 100 圈的 CE 配在一起
    rows = [r for r in class_rows2(cname) if not r["noncomp"]
            and not (cname == "放电容量类" and r["s"]["数值"] < 10)
            and not ("库仑效率" in cname and r["s"]["阶段"] == "首圈")]
    byp = defaultdict(list)
    for i, r in enumerate(rows):
        byp[r["s"]["论文"]].append(i)
    out = []
    for p, idx in byp.items():
        grp = defaultdict(list)
        for i in idx:
            grp[(rows[i]["s"]["测试"], rows[i]["s"]["圈数"], rows[i]["s"]["标准指标"])].append(i)
        ctl = [i for i in idx if rows[i]["s"]["是否对照"]] or idx
        big = max(grp.values(), key=lambda g: len({rows[i]["s"]["recipe"] for i in g}))
        ref = next((i for i in big if i in ctl), ctl[0])
        for g in grp.values():
            gref = next((i for i in g if rows[i]["s"]["是否对照"]), None)
            for i in g:
                if i == ref:
                    continue
                if gref is not None and i != gref and rows[i]["s"]["recipe"] != rows[gref]["s"]["recipe"]:
                    j, kind = gref, "同测试、不同配方"
                else:
                    j = ref
                    kind = "同配方、换条件" if rows[i]["s"]["recipe"] == rows[j]["s"]["recipe"] else "跨测试、不同配方"
                a, b = rows[i], rows[j]
                out.append({"类别": CLS[cname], "论文": p, "配对类型": kind,
                            "实验": {"表述": a["s"]["表述编号"], "配方": a["s"]["配方"], "recipe": a["s"]["recipe"], "测试": a["s"]["测试"],
                                   "数值": a["s"]["数值"], "y": a["y"], "配方特征": form_feats(a),
                                   "条件": {k: a["x"].get(k) for k in cond_keys}, "标记": flags(a)},
                            "参照": {"表述": b["s"]["表述编号"], "配方": b["s"]["配方"], "recipe": b["s"]["recipe"], "测试": b["s"]["测试"],
                                   "数值": b["s"]["数值"], "y": b["y"], "配方特征": form_feats(b),
                                   "条件": {k: b["x"].get(k) for k in cond_keys}, "标记": flags(b)},
                            "dy": a["y"] - b["y"]})
    return out


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    allrows = []
    for cname in N.CLASSES:
        rs = build(cname)
        allrows += rs
        print(f"{CLS[cname]}：{len(rs)} 对 / {len({r['论文'] for r in rs})} 篇；" + "，".join(f"{k} {v}" for k, v in Counter(r['配对类型'] for r in rs).items()))
    (OUT / "改动表.json").write_text(json.dumps(allrows, ensure_ascii=False), encoding="utf-8")
    print("→", OUT / "改动表.json", len(allrows), "行")
