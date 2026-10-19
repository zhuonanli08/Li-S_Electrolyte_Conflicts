"""第 1 步 f：研究现状图谱（零成本正则）。

1) 题名+摘要里"穿梭 vs 动力学 / 权衡"说法有多普遍
2) 溶剂、稀释剂、盐、介体：作为研究重点（题名+摘要提到）与实验里用到（实验部分 / SI / 正文自述）各多少篇，按时段、层、条件拆
输出：output/第1步_研究现状图谱.xlsx
"""
import json
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step1c_checkup as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (类别, 名称, 正则)；缩写只取不易混淆的
CHEM = [
    ("线性醚", "DME", r"1,2-dimethoxyethane|\bDME\b"),
    ("线性醚", "二甘醇二甲醚 G2", r"diglyme|diethylene glycol dimethyl ether|\bDEGDME\b|\bG2\b"),
    ("线性醚", "三甘醇二甲醚 G3", r"triglyme|triethylene glycol dimethyl ether|\bTREGDME\b|\bG3\b"),
    ("线性醚", "四甘醇二甲醚 G4", r"tetraglyme|tetraethylene glycol dimethyl ether|\bTEGDME\b|\bG4\b"),
    ("线性醚", "1,2-二乙氧基乙烷 DEE", r"1,2-diethoxyethane|\bDEE\b"),
    ("线性醚", "二甲氧基甲烷 DMM", r"dimethoxymethane|\bDMM\b"),
    ("环醚", "DOL", r"1,3-dioxolane|\bDOL\b"),
    ("环醚", "THF", r"tetrahydrofuran(?!.{0,3}methyl)|\bTHF\b"),
    ("环醚", "2-MeTHF", r"2-methyltetrahydrofuran|2-?MeTHF|\bMTHF\b"),
    ("环醚", "THP", r"tetrahydropyran|\bTHP\b"),
    ("环醚", "1,4-二氧六环", r"1,4-dioxane"),
    ("长链/支链醚", "DBE 二丁醚", r"dibutyl ether|di-n-butyl ether|\bDBE\b"),
    ("长链/支链醚", "DIPE 二异丙醚", r"diisopropyl ether|\bDIPE\b"),
    ("长链/支链醚", "DPE 二丙醚", r"dipropyl ether|di-n-propyl ether"),
    ("长链/支链醚", "MTBE", r"methyl tert-butyl ether|\bMTBE\b"),
    ("长链/支链醚", "CPME", r"cyclopentyl methyl ether|\bCPME\b"),
    ("氟化醚(多作稀释剂)", "TTE", r"\bTTE\b|1,1,2,2-tetrafluoroethyl[\s-]*2,2,3,3-tetrafluoropropyl ether"),
    ("氟化醚(多作稀释剂)", "BTFE", r"\bBTFE\b|bis\s*\(2,2,2-trifluoroethyl\)\s*ether"),
    ("氟化醚(多作稀释剂)", "TFEE/OFE/其他 HFE", r"\bTFEE\b|\bOFE\b|\bHFE\b|hydrofluoroether|octafluoropentyl"),
    ("氟化醚(多作稀释剂)", "TFEO 原甲酸酯", r"\bTFEO\b|tris\s*\(2,2,2-trifluoroethyl\)\s*orthoformate"),
    ("氟化醚(多作稀释剂)", "氟化二醇醚(F-DEE/FDMB等)", r"F\d?DEE\b|\bFDMB\b|fluorinated (?:1,2-)?diethoxy\w*|fluorinated (?:1,2-)?dimethoxy\w*"),  # 括号内不能再用 |，case_split 按 | 切
    ("烃/芳烃稀释剂", "己烷/庚烷/环己烷", r"\bn?-?hexane\b|\bheptane\b|cyclohexane"),
    ("烃/芳烃稀释剂", "苯/甲苯/氟苯/三氟甲苯", r"\bbenzene\b|\btoluene\b|fluorobenzene|trifluorotoluene|\bBTF\b|anisole"),
    ("碳酸酯/酯", "碳酸酯(EC/DEC/DMC/EMC/PC)", r"ethylene carbonate|diethyl carbonate|dimethyl carbonate|ethyl methyl carbonate|propylene carbonate|\bEC\b|\bDEC\b|\bDMC\b|\bEMC\b|\bPC\b"),
    ("碳酸酯/酯", "FEC/VC", r"fluoroethylene carbonate|\bFEC\b|vinylene carbonate|\bVC\b"),
    ("碳酸酯/酯", "羧酸酯", r"ethyl acetate|methyl acetate|ethyl propionate|methyl propionate|methyl butyrate"),
    ("砜/亚砜", "环丁砜 SL", r"sulfolane|tetramethylene sulfone"),
    ("砜/亚砜", "DMSO", r"dimethyl sulfoxide|\bDMSO\b"),
    ("砜/亚砜", "其他砜", r"ethyl methyl sulfone|dimethyl sulfone|\bEMS\b"),
    ("腈", "乙腈 ACN", r"acetonitrile|\bACN\b"),
    ("腈", "二腈/三腈", r"succinonitrile|adiponitrile|glutaronitrile|hexanetrinitrile|\bSN\b|\bHTCN\b"),
    ("酰胺/脲/咪唑(高 DN)", "DMA/DMF", r"dimethylacetamide|dimethylformamide|\bDMAc?\b|\bDMF\b"),
    ("酰胺/脲/咪唑(高 DN)", "TMU/DMI/环脲", r"tetramethylurea|\bTMU\b|imidazolidinone|\bDMI\b|cyclic urea|\bDMPU\b"),
    ("酰胺/脲/咪唑(高 DN)", "1-甲基咪唑", r"1-methylimidazole|N-methylimidazole"),
    ("磷酸酯(阻燃)", "TEP/TMP/磷腈", r"triethyl phosphate|trimethyl phosphate|\bTEP\b|\bTMP\b|phosphazene|\bPFPN\b"),
    ("离子液体", "离子液体", r"ionic liquids?|\bPyr1[34]|\bPYR1[34]|\bEMIm|\bBMIm|\bP13\b|\bP14\b"),
    ("硅氧烷", "硅氧烷/硅烷", r"siloxane|\bsilane\b|trimethylsilyl"),
    ("盐", "LiTFSI", r"\bLiTFSI\b|\bLiTFSA\b|bis\(trifluoromethane\)?sulfonyl\)?imide"),
    ("盐", "LiFSI", r"\bLiFSI\b|\bLiFSA\b|bis\(fluorosulfonyl\)imide"),
    ("盐", "LiNO3", r"LiNO\s*3|lithium nitrate"),
    ("盐", "LiDFOB/LiBOB", r"\bLiDFOB\b|\bLiODFB\b|\bLiBOB\b|oxalato\)?borate"),
    ("盐", "LiPF6/LiBF4/LiClO4", r"\bLiPF6\b|\bLiBF4\b|\bLiClO4\b"),
    ("盐", "LiOTf", r"\bLiOTf\b|\bLiTf\b|\bLiCF3SO3\b|lithium triflate"),
    ("盐", "卤化锂(LiI/LiBr)", r"\bLiI\b|\bLiBr\b|lithium iodide|lithium bromide"),
    ("盐", "Hückel 阴离子(LiTDI等)", r"\bLiTDI\b|\bLiPDI\b|H[üu]ckel"),
    ("介体/均相催化", "醌类", r"quinone|anthraquinone"),
    ("介体/均相催化", "有机硒/有机硫介体", r"diselenide|organoselen|organodisulfide|diphenyl disulfide|dimethyl disulfide|\bDMDS\b|\bDPDS\b|\bDPDSe\b"),
    ("介体/均相催化", "金属有机/金属离子", r"cobaltocene|ferrocene|metallocene|phthalocyanine|porphyrin|Co\(?2\+|Cu\(?2\+|metal ions?"),
    ("介体/均相催化", "吩嗪/吩噻嗪/紫精等", r"phenazine|phenothiazine|viologen|\bTEMPO\b"),
]
TRADE = {
    "提到穿梭": r"shuttl",
    "提到动力学/转化": r"kinetic|conversion",
    "穿梭+动力学都提": None,
    "明确写权衡/两难/平衡": r"trade-?off|dilemma|balanc\w* (?:between|the)|double-edged|contradict|conflict",
    "提到溶解度": r"solubilit|dissolution",
}


def case_split(pat):
    """全称（含 ≥4 个连续小写字母）不分大小写；缩写（PC、EC、SN…）严格大小写，免得把多孔碳 PC、锡 Sn 算进来"""
    alts = pat.split("|")
    return "|".join(f"(?i:{a})" if re.search(r"[a-z]{4}", a) else a for a in alts)


def main():
    base = pd.read_pickle(os.path.join(ROOT, "output", "step1_rows_derived.pkl"))
    base = base[base["正文字数"] > 5000]
    ab = json.load(open(os.path.join(ROOT, "output", "abstracts.json"), encoding="utf-8"))
    rows = []
    for _, r in base.iterrows():
        key = re.sub(r"[^\w.-]+", "_", r.doi)
        raw = open(os.path.join(S.CACHE, f"{key}.main.txt"), encoding="utf-8").read()
        p = os.path.join(S.CACHE, f"{key}.si.txt")
        exp, rest = S.zones(raw)
        si = S.norm(open(p, encoding="utf-8").read()) if os.path.exists(p) else ""
        a = ab.get(r.doi.lower(), {}).get("abstract", "") or S.pdf_abstract(raw)
        ta = S.norm(r["题名"] + " . " + a)
        Z = [("EXP", exp), ("SI", si), ("MAIN", rest)]
        d = {"doi": r.doi}
        for k, pat in TRADE.items():
            if pat:
                d[k] = bool(re.search(pat, ta, re.I))
        d["穿梭+动力学都提"] = d["提到穿梭"] and d["提到动力学/转化"]
        for cls, name, pat in CHEM:
            cs = case_split(pat)
            d["重点|" + name] = bool(re.search(cs, ta))
            d["用到|" + name] = any(h[0] in "AB" for h in S.find_all(cs, Z, None, flags=0))
        rows.append(d)
    X = base.merge(pd.DataFrame(rows), on="doi")
    X.to_pickle(os.path.join(ROOT, "output", "step1_landscape.pkl"))

    # 1 权衡说法
    t1 = []
    for k in TRADE:
        for lab, sub in [("全部", X), ("主层", X[X["主层"]])]:
            t1.append((k, lab, f"{sub[k].sum()} ({sub[k].mean():.0%})"))
    t1 = pd.DataFrame(t1, columns=["题名+摘要里", "范围", "篇数"])
    print(t1.to_string(index=False))

    # 2 化学空间
    m = X
    per = {"2016–2019": m["年份"] <= 2019, "2020–2022": (m["年份"] >= 2020) & (m["年份"] <= 2022), "2023–2026": m["年份"] >= 2023}
    t2 = []
    for cls, name, _ in CHEM:
        f, u = m["重点|" + name], m["用到|" + name]
        row = {"类别": cls, "名称": name, "研究重点(题名摘要)": int(f.sum()), "实验里用到": int(u.sum())}
        for pn, pm in per.items():
            row[f"用到 {pn}"] = f"{int((u & pm).sum())} ({(u & pm).sum() / pm.sum():.0%})"
        row["用到且SPAN层"] = int((u & (m["正极层"] == "SPAN")).sum())
        row["用到且有贫液实验"] = int((u & m["贫液实验"].fillna(False)).sum())
        row["用到且负极受限"] = int((u & m["负极受限(薄锂/N/P≤3/无负极)"].fillna(False)).sum())
        t2.append(row)
    t2 = pd.DataFrame(t2)
    pd.set_option("display.width", 250)
    print(t2.to_string(index=False))
    with pd.ExcelWriter(os.path.join(ROOT, "output", "第1步_研究现状图谱.xlsx"), engine="openpyxl") as xw:
        t1.to_excel(xw, sheet_name="权衡说法", index=False)
        t2.to_excel(xw, sheet_name="溶剂盐介体", index=False)


if __name__ == "__main__":
    main()
