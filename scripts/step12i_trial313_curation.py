"""11-05 313 篇试跑：Claude 补充核定新增 70 篇的组分写法（方案 §5.8），只写试跑文件夹里的核定表副本。

起点是 243 篇的核定表副本（已含 step12g 的核定），在 step12f 规则映射之后运行，处理 work/待核定写法.json 里剩下的写法。
与 step12g 的不同（11-05 用户要求“分子结构描述符算准”）：能确定结构的添加剂、介体一律写真实 SMILES，
不再归入“试跑未核定添加剂”；只有多金属氧酸盐、大环金属配合物、蛋白、化学计量不明的无机物等没有单一分子结构的才归通用组分。
缩写都回原文找定义句（见各条备注里的句子编号）；按原文推定、没有直接写出结构式的标“推定”。
全部为 AI 核定，用户未确认。
用法：KETI2_PAPERS=<试跑论文文件夹> KETI2_COMP=<试跑组分表文件夹> python -X utf8 scripts/step12i_trial313_curation.py
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

OUT = Path(os.environ["KETI2_COMP"])
CURATION = OUT / "组分核定.json"
LEFT = OUT / "work" / "待核定写法.json"
TFSI = "O=S(=O)([N-]S(=O)(=O)C(F)(F)F)C(F)(F)F"
NOTE = "11-05 313 篇试跑 Claude 核定（AI，用户未确认）"
MED, ADD = "MED_TRIAL", "ADD_TRIAL"

# id, 名称, 英文名(=pubchem_query), 类别, 化学类别, SMILES, 全称正则, 依据
NEW = [
    ("BENZENETETRATHIOL", "1,2,4,5-苯四硫酚", "1,2,4,5-benzenetetrathiol", "添加剂", "有机硫（硫酚）", "Sc1cc(S)c(S)cc1S", r"benzenetetrathiol", "P368 S0024"),
    ("TRIOXANE", "1,3,5-三噁烷", "1,3,5-trioxane", "溶剂", "环缩醛", "C1OCOCO1", r"1,3,5-\s?trioxane", "P311、P377 定义句"),
    ("PYRAZINE", "吡嗪", "pyrazine", "添加剂", "含氮杂环", "c1cnccn1", r"\bpyrazine\b", "P332"),
    ("CLPYRAZINE2", "2-氯吡嗪", "2-chloropyrazine", "添加剂", "含氮杂环", "Clc1cnccn1", r"2-chloropyrazine", "P332"),
    ("DCLPYRAZINE25", "2,5-二氯吡嗪", "2,5-dichloropyrazine", "添加剂", "含氮杂环", "Clc1cnc(Cl)cn1", r"2,5-dichloropyrazine", "P332"),
    ("ATP2", "2-氨基苯硫酚", "2-aminothiophenol", "添加剂", "有机硫（硫酚）", "Nc1ccccc1S", r"2-amino\s?thiophenol", "P340 M0006"),
    ("ATP3", "3-氨基苯硫酚", "3-aminothiophenol", "添加剂", "有机硫（硫酚）", "Nc1cccc(S)c1", r"3-amino\s?thiophenol", "P340 M0006"),
    ("ATP4", "4-氨基苯硫酚", "4-aminothiophenol", "添加剂", "有机硫（硫酚）", "Nc1ccc(S)cc1", r"4-amino\s?thiophenol", "P340 M0006"),
    ("PPD", "对苯二胺", "p-phenylenediamine", "添加剂", "芳胺", "Nc1ccc(N)cc1", r"p-phenylenediamine", "P340 M0006"),
    ("ABA4", "4-氨基苯甲酸", "4-aminobenzoic acid", "添加剂", "芳胺（羧酸）", "Nc1ccc(cc1)C(=O)O", r"4-aminobenzoic acid", "P322"),
    ("MPY4", "4-巯基吡啶", "4-mercaptopyridine", "添加剂", "有机硫（硫酚）", "Sc1ccncc1", r"4-mercaptopyridine", "P385"),
    ("AZAURACIL6", "6-氮杂尿嘧啶", "6-azauracil", "添加剂", "含氮杂环", "O=C1C=NNC(=O)N1", r"6-azauracil", "P356"),
    ("DMMS", "二甲基二甲氧基硅烷", "dimethyldimethoxysilane", "溶剂", "硅氧烷", "CO[Si](C)(C)OC",
     r"dimethyl\s?dimethoxy\s?silane|dimethoxy\s?dimethyl\s?silane", "P369 M0003；原文密度 0.865 g cm⁻³（M0052）"),
    ("DPDTE", "二苯基二碲醚", "diphenyl ditelluride", "添加剂", "有机碲（二碲醚）", "c1ccc(cc1)[Te][Te]c1ccccc1", r"diphenyl ditelluride", "P317"),
    ("DPYDS", "2,2′-二吡啶二硫醚", "2,2'-dipyridyl disulfide", "添加剂", "有机硫（二硫醚）", "c1ccc(nc1)SSc1ccccn1",
     r"dipyridyl disulfide|dithiodipyridine", "P329 M0005：锂化生成吡啶-2-硫醇锂，推定为 2,2′ 异构体"),
    ("F3DEE", "1-乙氧基-2-(2,2,2-三氟乙氧基)乙烷", "1-ethoxy-2-(2,2,2-trifluoroethoxy)ethane", "溶剂", "氟化醚", "CCOCCOCC(F)(F)F",
     r"1-ethoxy-2-\(2,2,2-trifluoroethoxy\)ethane", "P371 M0083：DEE 骨架引入 –CF3/–CHF2、F 数 3–6，结构式在图 1B，推定"),
    ("F4DEE", "1,2-双(2,2-二氟乙氧基)乙烷", "1,2-bis(2,2-difluoroethoxy)ethane", "溶剂", "氟化醚", "FC(F)COCCOCC(F)F",
     r"bis\(2,2-difluoroethoxy\)ethane", "P371 M0083，推定"),
    ("F5DEE", "1-(2,2-二氟乙氧基)-2-(2,2,2-三氟乙氧基)乙烷", "1-(2,2-difluoroethoxy)-2-(2,2,2-trifluoroethoxy)ethane", "溶剂", "氟化醚",
     "FC(F)COCCOCC(F)(F)F", r"1-\(2,2-difluoroethoxy\)-2-\(2,2,2-trifluoroethoxy\)ethane", "P371 M0083，推定"),
    ("F4DMB", "2,2,3,3-四氟-1,4-二甲氧基丁烷", "2,2,3,3-tetrafluoro-1,4-dimethoxybutane", "溶剂", "氟化醚", "COCC(F)(F)C(F)(F)COC",
     r"tetrafluoro-1,4-dimethoxybutane", "P371 M0024（fluorinated-1,4-dimethoxybutane，F 数 4），推定"),
    ("HFME", "六氟异丙基甲基醚", "hexafluoroisopropyl methyl ether", "溶剂", "氟化醚", "COC(C(F)(F)F)C(F)(F)F",
     r"hexafluoroisopropyl methyl ether", "P339 M0005"),
    ("FLUORENONE", "9-芴酮", "9-fluorenone", "添加剂（介体）", "芳酮", "O=C1c2ccccc2-c2ccccc12", r"fluorenone", "P331：原位生成自由基调控反应路径"),
    ("TBAQ", "2-叔丁基蒽醌", "2-tert-butylanthraquinone", "添加剂（介体）", "醌", "CC(C)(C)c1ccc2c(c1)C(=O)c1ccccc1C2=O",
     r"tert-butyl\s?anthraquinone", "P387"),
    ("I2", "碘", "iodine", "添加剂", "卤素单质", "II", r"\biodine\b", "P391"),
    ("KTFSI", "双(三氟甲磺酰)亚胺钾", "potassium bis(trifluoromethanesulfonyl)imide", "其他盐/添加剂", "TFSI 盐", "[K+]." + TFSI,
     r"potassium bis\(trifluoromethanesulfonyl\)\s?imide", "P351"),
    ("LI2CO3", "碳酸锂", "lithium carbonate", "其他盐/添加剂", "碳酸盐", "[Li+].[Li+].[O-]C([O-])=O", r"lithium carbonate", "P392"),
    ("LIBETI", "双(五氟乙磺酰)亚胺锂", "lithium bis(pentafluoroethanesulfonyl)imide", "盐", "磺酰亚胺盐",
     "[Li+].O=S(=O)([N-]S(=O)(=O)C(F)(F)C(F)(F)F)C(F)(F)C(F)(F)F", r"bis\(pentafluoroethane\s?sulfonyl\)\s?imide", "P390"),
    ("LISCN", "硫氰酸锂", "lithium thiocyanate", "盐", "硫氰酸盐", "[Li+].[S-]C#N", r"lithium thiocyanate", "P302"),
    ("MGNO32", "硝酸镁", "magnesium nitrate", "其他盐/添加剂", "硝酸盐", "[Mg+2].[O-][N+](=O)[O-].[O-][N+](=O)[O-]", r"magnesium nitrate", "P353"),
    ("RBNO3", "硝酸铷", "rubidium nitrate", "其他盐/添加剂", "硝酸盐", "[Rb+].[O-][N+](=O)[O-]", r"rubidium nitrate", "P333"),
    ("PHSEBR", "苯基溴化硒", "phenylselenyl bromide", "添加剂", "有机硒", "Br[Se]c1ccccc1", r"phenyl\s?selen(?:yl|ium) bromide", "P392"),
    ("SN_QAN", "十八烷基二甲基羟乙基季铵硝酸盐", "octadecyl dimethyl hydroxyethyl quaternary ammonium nitrate", "添加剂", "季铵盐",
     "CCCCCCCCCCCCCCCCCC[N+](C)(C)CCO.[O-][N+](=O)[O-]", r"octadecyl dimethyl hydroxyethyl", "P335"),
    ("TEABR", "四乙基溴化铵", "tetraethylammonium bromide", "其他盐/添加剂", "季铵盐", "CC[N+](CC)(CC)CC.[Br-]", r"tetraethylammonium bromide", "P312"),
    ("TPABR", "四丙基溴化铵", "tetrapropylammonium bromide", "其他盐/添加剂", "季铵盐", "CCC[N+](CCC)(CCC)CCC.[Br-]", r"tetrapropyl\s?ammonium bromide", "P312"),
    ("TBABR", "四丁基溴化铵", "tetrabutylammonium bromide", "其他盐/添加剂", "季铵盐", "CCCC[N+](CCCC)(CCCC)CCCC.[Br-]", r"tetrabutylammonium bromide", "P312"),
    ("TOABR", "四辛基溴化铵", "tetraoctylammonium bromide", "其他盐/添加剂", "季铵盐",
     "CCCCCCCC[N+](CCCCCCCC)(CCCCCCCC)CCCCCCCC.[Br-]", r"tetraoctylammonium bromide", "P312"),
    ("TMACL", "四甲基氯化铵", "tetramethylammonium chloride", "其他盐/添加剂", "季铵盐", "C[N+](C)(C)C.[Cl-]", r"tetramethylammonium chloride", "P312"),
    ("TEACL", "四乙基氯化铵", "tetraethylammonium chloride", "其他盐/添加剂", "季铵盐", "CC[N+](CC)(CC)CC.[Cl-]", r"tetraethylammonium chloride", "P312"),
    ("TPACL", "四丙基氯化铵", "tetrapropylammonium chloride", "其他盐/添加剂", "季铵盐", "CCC[N+](CCC)(CCC)CCC.[Cl-]", r"tetrapropylammonium chloride", "P312"),
    ("TBACL", "四丁基氯化铵", "tetrabutylammonium chloride", "其他盐/添加剂", "季铵盐", "CCCC[N+](CCCC)(CCCC)CCCC.[Cl-]", r"tetrabutylammonium chloride", "P312"),
    ("TPATFSI", "四丙基铵 TFSI", "tetrapropylammonium bis(trifluoromethanesulfonyl)imide", "其他盐/添加剂", "季铵盐", "CCC[N+](CCC)(CCC)CCC." + TFSI,
     r"tetrapropylammonium bis", "P312"),
    ("TAHP", "四甲基铵六氟磷酸盐", "tetramethylammonium hexafluorophosphate", "其他盐/添加剂", "季铵盐", "C[N+](C)(C)C.F[P-](F)(F)(F)(F)F",
     r"tetramethylammonium hexafluorophosphate", "P344"),
    ("TBBT", "4,4′-硫代二苯硫酚", "4,4'-thiodibenzenethiol", "添加剂", "有机硫（硫酚）", "Sc1ccc(Sc2ccc(S)cc2)cc1", r"thiodibenzenethiol", "P366"),
    ("TTCALI", "三硫氰尿酸三锂盐", "trithiocyanuric acid trilithium salt", "添加剂", "有机硫（硫醇盐）", "[Li+].[Li+].[Li+].[S-]c1nc([S-])nc([S-])n1",
     r"trithiocyanuric acid trilithium", "P305 M0008、M0041"),
    ("ZNI2", "碘化锌", "zinc iodide", "其他盐/添加剂", "碘化物", "[Zn+2].[I-].[I-]", r"zinc iodide", "P298"),
    ("MTFP", "3,3,3-三氟丙酸甲酯", "methyl 3,3,3-trifluoropropionate", "溶剂", "羧酸酯", "COC(=O)CC(F)(F)F", r"methyl 3,3,3-trifluoropro", "P388"),
    ("MP", "丙酸甲酯", "methyl propionate", "溶剂", "羧酸酯", "CCC(=O)OC", r"methyl propionate", "P388"),
    ("MF", "甲酸甲酯", "methyl formate", "溶剂", "羧酸酯", "COC=O", r"methyl formate", "P388"),
    ("MPFP", "五氟丙酸甲酯", "methyl pentafluoropropionate", "溶剂", "羧酸酯", "COC(=O)C(F)(F)C(F)(F)F", r"methyl pentafluoropropionate", "P388"),
    ("TEG", "四乙二醇", "tetraethylene glycol", "溶剂", "醇醚", "OCCOCCOCCOCCO", r"tetraethylene glycol(?!\s*dimethyl)", "P328"),
]

ALIAS = {
    "1 M DpyDS储备液": "DPYDS", "DpyDS": "DPYDS", "1,2,4,5-benzenetetrathiol (tetrathiol)": "BENZENETETRATHIOL",
    "1,3,5-trioxane (TO)": "TRIOXANE", "TXA": "TRIOXANE", "TXA (1,3,5-trioxane)": "TRIOXANE",
    "1,3-dioxyethane (DOL; original wording)": "DOL", "PZ": "PYRAZINE", "2-CP": "CLPYRAZINE2", "2,5-DCP": "DCLPYRAZINE25",
    "2-ATP": "ATP2", "3-ATP": "ATP3", "4-ATP": "ATP4", "PPD": "PPD", "4-aminobenzoic acid (4-ABA)": "ABA4", "4Mpy": "MPY4",
    "6-AU": "AZAURACIL6", "6-azauracil (6-AU)": "AZAURACIL6", "AN": "ACN", "BME": "MBE",  # 243 篇已有 MBE（同 InChIKey）
    "D2": "TTE",  # P351 M0029：1,1,2,2-tetrafluoroethyl-2,2,3,3-tetrafluoropropyl ether (D2) 即 TTE
    "DMDSe": "ME2SE2", "DMMS": "DMMS", "DPDTe": "DPDTE", "diphenyl ditelluride (DPDTe)": "DPDTE",
    "F3DEE": "F3DEE", "F4DEE": "F4DEE", "F5DEE": "F5DEE", "F4DMB": "F4DMB", "HFME": "HFME",
    "F6DEE": "DTFEG",  # 243 篇已有 DTFEG（同 InChIKey）
    "FL": "FLUORENONE", "fluorenone (FL)": "FLUORENONE", "HEX": "NHEXANE", "NH": "NHEXANE",  # P321 M0003、P319：n-hexane
    "I2": "I2", "KTFSI": "KTFSI", "Li2CO3": "LI2CO3", "LiBETI": "LIBETI", "LiFSA": "LiFSI", "LiSCN": "LISCN", "LiSO3CF3": "LiCF3SO3",
    "Mg(NO3)2": "MGNO32", "PhSeBr": "PHSEBR", "RbNO3": "RBNO3",
    "SN": "SN_QAN", "SN (octadecyl dimethyl hydroxyethyl quaternary ammonium nitrate)": "SN_QAN",
    "T2Br": "TEABR", "T3Br": "TPABR", "T4Br": "TBABR", "T8Br": "TOABR",
    "T1Br": "TMABr",  # 243 篇已有 TMABr（同 InChIKey）
    "T1Cl": "TMACL", "T2Cl": "TEACL", "T3Cl": "TPACL", "T4Cl": "TBACL", "T3TFSI": "TPATFSI", "T4TFSI": "TBATFSI",
    "TAHP": "TAHP", "tetramethylammonium hexafluorophosphate (TAHP)": "TAHP", "TBAQ": "TBAQ", "TBAQ（2-tert-butylanthraquinone）": "TBAQ",
    "TBBT": "TBBT", "TTCA-Li": "TTCALI", "ZnI2": "ZNI2", "fluoroethylene carbonate (FEC)": "FEC",
    "methyl 3,3,3-trifluoropionate (MTFP)": "MTFP", "methyl propionate (MP)": "MP", "methyl formate": "MF",
    "methyl pentafluoropropionate": "MPFP", "tetraethylene glycol": "TEG", "四乙二醇二甲醚": "TEGDME",
}
# 没有单一分子结构：多金属氧酸盐、大环 Cu(II) 配合物（P301）、茂金属 → 介体；蛋白、化学计量不明的无机多碲化物 → 添加剂
MEDIATORS = {"(TBA)3[PW12O40]", "Co-POMs", "Co-POMs（(TBA)5[PW11CoO39]）", "TBA-POMs", "TBA-POMs（(TBA)7[PW11O39]）", "CuL",
             "cobaltocene (CoCp2)"}
GENERIC_ADD = {"LiTe3": "P297 无机多碲化物，原文名 LiTe3，化学计量与结构未写明", "fibroin": "P348 丝素蛋白（>200 kDa），无单一结构"}
EXCL = {
    "BHT": "商品 DOL 中约 75 ppm 的阻聚剂（P352 M0030），不是刻意配入的组分",
    "BTF": "19F NMR 定量内标（P382，表征用）",
    "DME或BME（原文冲突）": "身份未决：原文冲突", "Li2S8（方法）/Li2S6（图注及讨论）": "身份未决：原文冲突（多硫化物）",
    "FL•−": "原位生成的自由基，不是配入组分", "LiPyS": "原位反应产物（吡啶-2-硫醇锂）", "DpyDS/LiPyS（反应生成）": "原位反应产物",
    "LiPyS/DpyDS": "原位反应产物与添加剂混写", "LiPyS簇沉淀": "原位反应产物（沉淀）",
    "TTCA": "合成 TTCA-Li 的原料，不在电解液中（P305 M0041）", "diethylamine": "合成用催化剂（P366）",
    "asymmetric_Br": "非对称季铵溴盐，原文未写明结构", "chloropyrazine身份与浓度": "身份或浓度未决",
    "pyrazine additive identity/presence": "身份或有无未决", "salt/solvent/pyrazine身份浓度": "身份或浓度未决",
    "glyme (Gn; n未明)": "身份未写明（n 未明）", "ether solvent(s), identity/ratio unspecified": "身份未写明",
    "SL-based solvent": "身份未写明", "stock solvent": "身份未写明", "TTE是否存在": "身份未决", "Ag+来源": "身份未决",
    "Li-Nafion": "膜材料", "PAA": "黏结剂（正极材料）", "CNTs": "碳纳米管（P376 正极宿主材料）", "Ni-PCTs": "正极催化剂材料", "CB (Super P/ketjen black=1:1)": "导电碳（正极材料）",
}
# 厂商密度（11-01 用户批准的第三来源）：只补缺密度、挡住建模数据最多的几个，网页搜索结果交叉核对；
# DTFEG 只有预测值、F4DMB 未查到，不补
DENSITY = {
    "DMI": {"值": 1.056, "条件": "25 °C (lit.)", "来源": "Sigma-Aldrich 193453 / 40727 / 40725", "链接": "https://www.sigmaaldrich.com/product/aldrich/40727",
            "说明": "三个货号同值"},
    "FPY3": {"值": 1.13, "条件": "25 °C (lit.)", "来源": "Sigma-Aldrich 196665", "链接": "https://sigmaaldrich.com/catalog/product/ALDRICH/196665",
             "说明": "ChemicalBook 同值（比重 1.130）"},
    "MBE": {"值": 0.744, "条件": "25 °C (lit.)", "来源": "Sigma-Aldrich 235377", "链接": "https://b2b.sigmaaldrich.com/US/en/product/aldrich/235377",
            "说明": "ChemicalBook 同值"},
    "MPE": {"值": 0.712, "条件": "25 °C", "来源": "Sigma-Aldrich 709158", "链接": "https://sigmaaldrich.com/catalog/product/ALDRICH/709158",
            "说明": "TCI 写 0.73（20 °C 比重），维基 0.7356，相差约 3%；取写明 25 °C 的值"},
    "F4DEE": {"值": 1.24, "条件": "25 °C (lit.)", "来源": "MSE Supplies（电池研究用）",
              "链接": "https://msesupplies.com/products/mse-pro-1-2-bis2-2-difluoroethoxy-ethane-c-6-h-10-f-4-o-2-for-battery-research",
              "说明": "单一来源，未能交叉核对"},
}
PLACEHOLDER = re.compile(r"wash|solute|cycled|unknown|normal electrolyte|species|[一-鿿]", re.I)


def main() -> None:
    cur = json.loads(CURATION.read_text(encoding="utf-8"))
    left = json.loads(LEFT.read_text(encoding="utf-8"))
    have = {c["id"] for c in cur["组分"]}
    for cid, zh, en, cat, chem, smi, rx, why in NEW:
        if cid not in have:
            cur["组分"].append({"id": cid, "名称": zh, "英文名": en, "档": "A", "类别": cat, "化学类别": chem, "smiles": smi,
                               "pubchem_query": en, "全称正则": rx, "备注": f"{NOTE}；依据 {why}"})
    for c in cur["组分"]:
        if c["id"] in DENSITY and not c.get("厂商密度"):
            c["厂商密度"] = dict(DENSITY[c["id"]], 说明=DENSITY[c["id"]]["说明"] + "；" + NOTE)
    ids = {c["id"] for c in cur["组分"]}
    alias_keys = {(a["论文"], a["写法"]) for a in cur["别名"]}
    excl_keys = {(e["论文"], e["写法"]) for e in cur["未收录"]}
    stat = {"别名": 0, "介体": 0, "通用添加剂": 0, "未收录": 0, "剩余": []}
    for name, v in left.items():
        if ("*", name) in alias_keys or ("*", name) in excl_keys:
            continue
        if name in ALIAS:
            assert ALIAS[name] in ids, (name, ALIAS[name])
            cur["别名"].append({"论文": "*", "写法": name, "组分": [ALIAS[name]], "备注": NOTE})
            stat["别名"] += 1
        elif name in MEDIATORS:
            cur["别名"].append({"论文": "*", "写法": name, "组分": [MED], "备注": NOTE + "；多金属氧酸盐/金属配合物/茂金属，无单一分子结构"})
            stat["介体"] += 1
        elif name in GENERIC_ADD:
            cur["别名"].append({"论文": "*", "写法": name, "组分": [ADD], "备注": NOTE + "；" + GENERIC_ADD[name]})
            stat["通用添加剂"] += 1
        elif name in EXCL or PLACEHOLDER.search(name):
            why = EXCL.get(name, "占位、身份未决、残留/洗脱液或电极，不是配入电解液的确定组分")
            cur["未收录"].append({"论文": "*", "写法": name, "原因": f"{why}（{NOTE}）"})
            stat["未收录"] += 1
        else:
            stat["剩余"].append(name)
    CURATION.write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"新组分 {len(NEW)}；处理写法：别名 {stat['别名']}、介体 {stat['介体']}、通用添加剂 {stat['通用添加剂']}、未收录 {stat['未收录']}；"
          f"未处理 {len(stat['剩余'])}：{stat['剩余']}")


if __name__ == "__main__":
    main()
