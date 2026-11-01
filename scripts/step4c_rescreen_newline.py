"""新主线复筛（2026-11-01，用户定）：原 B 步 Ⅰ 类不合格的 171 篇中，除纯计算、综述、电解液固定外的论文，按新主线重判。

新主线（方案 §8.7）：篇内差距训练共同打分函数；四类性能含库仑效率（Li‖Cu）；表述含“配方 → 物性”；
同一配方在不同条件下的差距也进模型。据此复筛三类：
  Ⅰb  配方比较不在 Li‖S 电池：≥2 种电解液在 Li‖Cu / Li‖Li / 物性测量（电导、黏度、多硫化物溶解度、溶剂化谱等）中比较
  Ⅲ   同配方换条件：同一电解液在 Li–S 电池中于 ≥2 种 E/S、硫面载量、锂厚/N/P、温度或电池形式（扣式/软包）下测性能（只换倍率不算）
  机制层  Ⅱ 类合格（失效诊断），进机制解释层
候选：排除理由不属于纯计算 / 综述 / 电解液固定的论文，另加 P486（排除理由写“变量为 E/S 与温度”）。

只读 output/第二阶段_资格筛选.csv、output/text_cache、output/abstracts.json；不改原资格筛选表（方案 §5.3：不能重跑 step4b）。
输出 output/第二阶段_资格筛选_新主线复筛_2026-11-01/：
  候选.csv          候选清单与关键词分类
  摘录_批NN.txt      每批 15 篇，供逐篇判定
  判定.json          Claude 逐篇判定（会话中填写）
  复筛表.csv、统计.json   merge 生成
用法：python -X utf8 step4c_rescreen_newline.py digest | merge
"""
import json
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step1c_checkup as S  # noqa: E402
from step4a_coverage_digest import FORMULA, COMP, sentences, body, clip  # noqa: E402

ROOT = S.ROOT
OUT = os.path.join(ROOT, "output", "第二阶段_资格筛选_新主线复筛_2026-11-01")
TC = os.path.join(ROOT, "output", "text_cache")
BATCH = 15
EXTRA = {"P486"}

CATS = [  # 按排除理由文字归类；顺序即优先级
    ("综述", r"综述|评述|观点|封面|Preview"),
    ("非液态", r"固液混合|非液态"),
    ("有对比无性能", r"有电解液对比但无|±LiNO3 只比较|新鲜 vs 老化"),
    ("单一电解液", r"单一"),
    ("纯计算", r"纯计算|纯模拟|模型计算|模型拟合|纯模型|计算数据库|机器学习|文献数据|DFT 为主"),
    ("电解液固定", r"电解液固定|非电解液变量|配方固定|配方不变|变量为正极|主要变量为正极|基础电解液固定|介体涂于隔膜|加入正极|正极添加剂|正极液中|合成路线|硫同位素"),
    ("无锂硫/对称/物性", r"无电池|无锂硫|仅 Li‖Li|只有 Li‖Ni|无硫正极|原位 TEM|光谱物性|溶液物性|非锂硫|铜离子|Na-S|无电解液配方性能比较"),
]
RESCREEN = {"有对比无性能", "单一电解液", "无锂硫/对称/物性", "未归类"}

PATS = [
    ("Li‖Cu/对称", r"Li\s*(?:‖|\|\||//|/|-)\s*Cu|Cu\s*(?:‖|\|\||//|/)\s*Li|Coulombic efficienc|symmetric(?:al)? cells?|Li\s*(?:‖|\|\||//|/)\s*Li\b|plating[/\s-]*stripping|stripping[/\s-]*plating"),
    ("物性", r"(?:ionic )?conductivit|viscosit|solubilit|transference number|diffusion coefficient|Raman|solvation (?:structure|sheath|number)|coordination number|\bNMR\b|density of the electrolyte"),
    ("条件", r"E\s*/\s*S|electrolyte[\s/-]*(?:to[\s-]*)?sulfur ratio|μL\s*mg|µL\s*mg|uL\s*mg|mg\s*cm\s*[-−–]?\s*2|sulfur loading|areal loading|N\s*/\s*P|lithium (?:foil|metal) (?:with a thickness|thickness)|\d+\s*(?:μm|µm)\s*(?:thick\s*)?(?:Li|lithium)|pouch cell|\d+\s*°C|low[\s-]*temperature|lean[\s-]*electrolyte"),
    ("Li-S 电池", r"Li[\s–-]*S (?:cells?|batter)|galvanostatic|discharge capacity|capacity retention|cycling (?:performance|stability)|mAh\s*g"),
]
PATS = [(k, re.compile(p, re.I)) for k, p in PATS]


def classify(reason):
    for name, pat in CATS:
        if re.search(pat, reason):
            return name
    return "未归类"


def load_text(doi):
    key = doi.replace("/", "_")
    parts = {}
    for part in ("main", "si"):
        p = os.path.join(TC, f"{key}.{part}.txt")
        if os.path.exists(p):
            parts[part] = open(p, encoding="utf-8", errors="ignore").read()
    return parts


def digest():
    os.makedirs(OUT, exist_ok=True)
    df = pd.read_csv(os.path.join(ROOT, "output", "第二阶段_资格筛选.csv"), encoding="utf-8-sig", dtype=str).fillna("")
    ab = json.load(open(os.path.join(ROOT, "output", "abstracts.json"), encoding="utf-8"))
    n = df[df["Ⅰ类"] == "N"].copy()
    n["关键词分类"] = n["备注或排除理由"].map(classify)
    cand = n[n["关键词分类"].isin(RESCREEN) | n["编号"].isin(EXTRA)].copy()
    cand[["编号", "关键词分类", "Ⅱ类", "备注或排除理由", "题名", "doi", "正极层", "负极", "主层"]].to_csv(
        os.path.join(OUT, "候选.csv"), index=False, encoding="utf-8-sig")
    print("不合格", len(n), n["关键词分类"].value_counts().to_dict())
    print("候选", len(cand))
    blocks = []
    for _, r in cand.iterrows():
        parts = load_text(r["doi"])
        a = (ab.get(r["doi"]) or {}).get("abstract", "")
        lines = [f"===== {r['编号']} | 原分类 {r['关键词分类']} | Ⅱ {r['Ⅱ类']} | 正极 {r['正极层']} | 负极 {r['负极']} | 主层 {r['主层']}",
                 f"题名：{r['题名']}", f"原排除理由：{r['备注或排除理由']}", f"摘要：{clip(a, 900)}"]
        if not parts:
            lines.append("（全文缺失）")
        for part, raw in parts.items():
            sents = sentences(body(raw) if part == "main" else raw)
            form = [s for s in sents if FORMULA.search(s)]
            comp = [s for s in sents if COMP.search(s)]
            lines.append(f"--[{part}] 配方句 {len(form)}，对照句 {len(comp)}")
            for s in form[:6]:
                lines.append(f"  [配方] {clip(s, 260)}")
            for s in comp[:4]:
                lines.append(f"  [对照] {clip(s, 260)}")
            for k, pat in PATS:
                hits = [s for s in sents if pat.search(s)]
                lim = 6 if k == "条件" else 4
                if hits:
                    lines.append(f"  <{k}> 命中 {len(hits)} 句")
                for s in hits[:lim]:
                    lines.append(f"    · {clip(s, 240)}")
        blocks.append("\n".join(lines))
    for i in range(0, len(blocks), BATCH):
        with open(os.path.join(OUT, f"摘录_批{i // BATCH + 1:02d}.txt"), "w", encoding="utf-8") as f:
            f.write("\n\n".join(blocks[i:i + BATCH]))
    print("摘录批数", (len(blocks) + BATCH - 1) // BATCH)


def merge():
    cand = pd.read_csv(os.path.join(OUT, "候选.csv"), encoding="utf-8-sig", dtype=str).fillna("")
    J = json.load(open(os.path.join(OUT, "判定.json"), encoding="utf-8"))
    rows = []
    for _, r in cand.iterrows():
        j = J.get(r["编号"])
        if j is None:
            raise SystemExit(f"缺判定：{r['编号']}")
        rows.append({**r.to_dict(), "新判定": "、".join(j["类"]) or "仍不适用", "说明": j["说明"], "依据原句": j.get("依据", ""),
                     "待核": j.get("待核", ""), "判定者": "Claude（AI 判定，用户未复核）"})
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUT, "复筛表.csv"), index=False, encoding="utf-8-sig")

    def ids(mask):
        return sorted(out[mask]["编号"].tolist())
    j = out["新判定"]
    hold = out["待核"].ne("")
    upgrade = j.str.contains("改判Ⅰ")
    ib = j.str.contains("Ⅰb") & ~upgrade
    iii = j.str.contains("Ⅲ") & ~upgrade & ~ib
    mech = (j == "机制层")
    # 原 498 篇 Ⅰ 类按层拆分（主层 = 液态＋硫碳＋锂金属）
    df = pd.read_csv(os.path.join(ROOT, "output", "第二阶段_资格筛选.csv"), encoding="utf-8-sig", dtype=str).fillna("")
    y = df[df["Ⅰ类"] == "Y"]
    main = y["主层"] == "True"
    core = y["层"].str.contains("C")
    span = y["正极层"].str.contains("SPAN")
    # Ⅰ 不合格但 Ⅱ 合格、不在本次候选内的（如 P239，电解液固定类）也进机制层
    mech_extra = sorted(df[(df["Ⅰ类"] == "N") & (df["Ⅱ类"] == "Y") & ~df["编号"].isin(out["编号"])]["编号"].tolist())
    stat = {
        "候选": len(out), "按新判定": j.value_counts().to_dict(),
        "改判Ⅰ类": {"篇数": int(upgrade.sum()), "其中待核": ids(upgrade & hold), "编号": ids(upgrade)},
        "Ⅰb 非全电池配方比较": {"篇数": int(ib.sum()), "其中待核": ids(ib & hold), "编号": ids(ib)},
        "Ⅲ 同配方换条件": {"篇数": int(iii.sum()), "其中待核": ids(iii & hold), "编号": ids(iii)},
        "仅机制层": {"篇数": int(mech.sum()) + len(mech_extra), "编号": ids(mech) + mech_extra},
        "仍不适用": {"篇数": int((j == "仍不适用").sum()), "其中待核": ids((j == "仍不适用") & hold)},
        "原Ⅰ类498按层": {"主层": int(main.sum()), "主层含核心层": int((main & core).sum()), "主层其余": int((main & ~core).sum()),
                       "非主层": int((~main).sum()), "非主层中含SPAN正极": int((~main & span).sum()),
                       "非主层其余": int((~main & ~span).sum())},
    }
    n_extra = int(upgrade.sum() + ib.sum() + iii.sum()) + stat["仅机制层"]["篇数"]
    n_hold = len(stat["改判Ⅰ类"]["其中待核"]) + len(stat["Ⅰb 非全电池配方比较"]["其中待核"]) + len(stat["Ⅲ 同配方换条件"]["其中待核"])
    stat["提取总量"] = {"含SPAN": len(y) + n_extra, "不含SPAN": len(y) - stat["原Ⅰ类498按层"]["非主层中含SPAN正极"] + n_extra,
                     "其中复筛收回": n_extra, "复筛收回中待核": n_hold,
                     "说明": "不含 §14 ② 约 19 篇顶刊漏检候选；Ⅲ 中待核的 P646 同属机制层，无论如何都提取"}
    json.dump(stat, open(os.path.join(OUT, "统计.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(stat, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    {"digest": digest, "merge": merge}[sys.argv[1]]()
