"""11-04 243 篇试跑：Claude 补充核定（方案 §5.8），只写试跑文件夹里的核定表副本，不改 30 篇核定表。

在 step12f 规则映射之后运行，处理 work/待核定写法.json 里剩下的写法：
  1) 新组分：按原文全称写 SMILES，pubchem_query 只用全称（build 时自动与 PubChem 比对 InChIKey，不一致标 ⚠️）；
  2) 写法 → 组分：同物异名、缩写（有歧义的缩写按论文单独定，如 HFE：P185 为 TFTFE，其余 9 篇为 TTE，均核过定义句）；
  3) 结构复杂或只在一篇出现的添加剂归入两个通用组分：试跑未核定介体（茂金属、醌、TTF、酞菁、芳烃自由基前体）、
     试跑未核定添加剂（其余），保留“含介体/含其他添加剂”信息，不算描述符；
  4) 占位、身份未决、残留/浸出/洗脱液、材料与电极、氘代溶剂 → 未收录（写原因）。
全部为 AI 核定，用户未确认；试跑结果标“初步、未裁定”。
用法：KETI2_COMP=<试跑组分表文件夹> python -X utf8 scripts/step12g_trial_curation.py
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
NOTE = "11-04 试跑 Claude 核定（AI，用户未确认）"

# id, 名称, 英文名(=pubchem_query), 类别, 化学类别, SMILES, 全称正则
NEW = [
    ("DMSO", "二甲基亚砜", "dimethyl sulfoxide", "溶剂", "亚砜", "CS(C)=O", r"dimethyl\s?sulfoxide"),
    ("SULFOLANE", "环丁砜", "sulfolane", "溶剂", "砜", "O=S1(=O)CCCC1", r"sulfolane|tetramethylene sulfone|tetramethyl sulfone"),
    ("DIGLYME", "二乙二醇二甲醚", "diethylene glycol dimethyl ether", "溶剂", "链醚", "COCCOCCOC", r"diglyme|diethylene glycol dimethyl ether"),
    ("TRIGLYME", "三乙二醇二甲醚", "triethylene glycol dimethyl ether", "溶剂", "链醚", "COCCOCCOCCOC", r"triglyme|triethylene glycol dimethyl ether"),
    ("EMC", "碳酸甲乙酯", "ethyl methyl carbonate", "溶剂", "链状碳酸酯", "CCOC(=O)OC", r"ethyl methyl carbonate|methyl ethyl carbonate"),
    ("ACN", "乙腈", "acetonitrile", "溶剂", "腈", "CC#N", r"acetonitrile"),
    ("PRN", "丙腈", "propionitrile", "溶剂", "腈", "CCC#N", r"propionitrile|propanenitrile"),
    ("DMF", "N,N-二甲基甲酰胺", "N,N-dimethylformamide", "溶剂", "酰胺", "CN(C)C=O", r"dimethyl\s?formamide"),
    ("DMAC", "N,N-二甲基乙酰胺", "N,N-dimethylacetamide", "溶剂", "酰胺", "CC(=O)N(C)C", r"dimethyl\s?-?\s?acetamide"),
    ("ACETAMIDE", "乙酰胺", "acetamide", "溶剂", "酰胺", "CC(N)=O", r"(?<![a-z\s])acetamide|^acetamide"),
    ("CAPROLACTAM", "ε-己内酰胺", "caprolactam", "溶剂", "酰胺（内酰胺）", "O=C1CCCCCN1", r"caprolactam"),
    ("NMA", "N-甲基乙酰胺", "N-methylacetamide", "溶剂", "酰胺", "CNC(C)=O", r"N-methyl\s?acetamide"),
    ("TMU", "四甲基脲", "tetramethylurea", "溶剂", "酰胺（脲）", "CN(C)C(=O)N(C)C", r"tetramethyl\s?urea"),
    ("DMI", "1,3-二甲基-2-咪唑啉酮", "1,3-dimethyl-2-imidazolidinone", "溶剂", "酰胺（环脲）", "CN1CCN(C)C1=O", r"dimethyl-2-imidazolidinone"),
    ("DIPE", "二异丙醚", "diisopropyl ether", "溶剂", "链醚", "CC(C)OC(C)C", r"di-?\s?isopropyl ether|isopropyl ether"),
    ("DIPS", "二异丙基硫醚", "diisopropyl sulfide", "溶剂", "有机硫（硫醚）", "CC(C)SC(C)C", r"di-?\s?isopropyl sul(?:f|ph)ide"),
    ("MTBE", "甲基叔丁基醚", "methyl tert-butyl ether", "溶剂", "链醚", "COC(C)(C)C", r"methyl\s?tert(?:iary)?-?\s?butyl ether"),
    ("MBE", "甲基正丁基醚", "butyl methyl ether", "溶剂", "链醚", "CCCCOC", r"methyl butyl ether|butyl methyl ether"),
    ("MPE", "甲基正丙基醚", "methyl propyl ether", "溶剂", "链醚", "CCCOC", r"methyl propyl ether"),
    ("PBE", "丙基丁基醚", "butyl propyl ether", "溶剂", "链醚", "CCCCOCCC", r"propyl butyl ether|butyl propyl ether"),
    ("TBIE", "叔丁基异丙基醚", "tert-butyl isopropyl ether", "溶剂", "链醚", "CC(C)OC(C)(C)C", r"tert-butyl isopropyl ether"),
    ("DIBE", "二异丁醚", "diisobutyl ether", "溶剂", "链醚", "CC(C)COCC(C)C", r"isobutyl ether"),
    ("NPENTANE", "正戊烷", "pentane", "溶剂", "烃", "CCCCC", r"n-pentane"),
    ("NHEPTANE", "正庚烷", "heptane", "溶剂", "烃", "CCCCCCC", r"n-heptane"),
    ("NOCTANE", "正辛烷", "octane", "溶剂", "烃", "CCCCCCCC", r"n-octane"),
    ("TOLUENE", "甲苯", "toluene", "溶剂", "芳烃", "Cc1ccccc1", r"toluene"),
    ("MXYLENE", "间二甲苯", "m-xylene", "溶剂", "芳烃", "Cc1cccc(C)c1", r"m-xylene"),
    ("FB", "氟苯", "fluorobenzene", "溶剂", "氟代芳烃", "Fc1ccccc1", r"(?<!di)(?<!tri)(?<!hexa)fluorobenzene"),
    ("DFB14", "1,4-二氟苯", "1,4-difluorobenzene", "溶剂", "氟代芳烃", "Fc1ccc(F)cc1", r"difluorobenzene"),
    ("HFB", "六氟苯", "hexafluorobenzene", "溶剂", "氟代芳烃", "Fc1c(F)c(F)c(F)c(F)c1F", r"hexafluorobenzene"),
    ("CS2", "二硫化碳", "carbon disulfide", "溶剂", "二硫化碳", "S=C=S", r"carbon disulfide"),
    ("CHCL3", "氯仿", "chloroform", "溶剂", "卤代烃", "ClC(Cl)Cl", r"chloroform"),
    ("H2O", "水", "water", "溶剂", "水", "O", r"\bwater\b"),
    ("ETOH", "乙醇", "ethanol", "溶剂", "醇", "CCO", r"ethanol"),
    ("MEOH", "甲醇", "methanol", "溶剂", "醇", "CO", r"methanol"),
    ("NBUOH", "正丁醇", "1-butanol", "溶剂", "醇", "CCCCO", r"n-butanol|1-butanol"),
    ("DIOXANE", "1,4-二氧六环", "1,4-dioxane", "溶剂", "环醚", "C1COCCO1", r"1,4-dioxane"),
    ("METHF", "2-甲基四氢呋喃", "2-methyltetrahydrofuran", "溶剂", "环醚", "CC1CCCO1", r"2-methyl\s?-?tetrahydrofuran"),
    ("MEDOL", "2-甲基-1,3-二氧戊环", "2-methyl-1,3-dioxolane", "溶剂", "环醚", "CC1OCCO1", r"2-methyl-\s?1,3-\s?dioxolane"),
    ("DMP22", "2,2-二甲氧基丙烷", "2,2-dimethoxypropane", "溶剂", "链醚（缩酮）", "COC(C)(C)OC", r"2,2-dimeth\w*oxypropane"),
    ("ETOAC", "乙酸乙酯", "ethyl acetate", "溶剂", "酯", "CCOC(C)=O", r"ethyl acetate"),
    ("BUTANAL", "丁醛", "butanal", "溶剂", "醛", "CCCC=O", r"butanal|butyraldehyde"),
    ("BUTANONE", "丁酮", "2-butanone", "溶剂", "酮", "CCC(C)=O", r"butanone"),
    ("PRCOCL", "丙酰氯", "propionyl chloride", "添加剂", "酰氯", "CCC(Cl)=O", r"propionyl chloride"),
    ("NBUNH2", "正丁胺", "butylamine", "添加剂", "胺", "CCCCN", r"n-butylamine|butylamine"),
    ("TBUAMINE", "三丁胺", "tributylamine", "添加剂", "胺", "CCCCN(CCCC)CCCC", r"tributylamine"),
    ("PYRIDINE", "吡啶", "pyridine", "溶剂", "吡啶", "c1ccncc1", r"(?<!fluoro)pyridine"),
    ("FPY2", "2-氟吡啶", "2-fluoropyridine", "溶剂", "氟代吡啶", "Fc1ccccn1", r"2-fluoropyridine"),
    ("FPY3", "3-氟吡啶", "3-fluoropyridine", "溶剂", "氟代吡啶", "Fc1cccnc1", r"3-fluoropyridine"),
    ("FPY4", "4-氟吡啶", "4-fluoropyridine", "溶剂", "氟代吡啶", "Fc1ccncc1", r"4-fluoropyridine"),
    ("IMIDAZOLE", "咪唑", "imidazole", "添加剂", "咪唑", "c1c[nH]cn1", r"(?<!methyl)(?<!methyl-)imidazole"),
    ("MEIM", "1-甲基咪唑", "1-methylimidazole", "溶剂", "咪唑", "Cn1ccnc1", r"methylimidazole"),
    ("ISOXAZOLE", "异噁唑", "isoxazole", "溶剂", "异噁唑", "c1cnoc1", r"isoxazole"),
    ("TEP", "磷酸三乙酯", "triethyl phosphate", "溶剂", "磷酸酯", "CCOP(=O)(OCC)OCC", r"triethyl phosphate"),
    ("TMP", "磷酸三甲酯", "trimethyl phosphate", "溶剂", "磷酸酯", "COP(=O)(OC)OC", r"trimethyl phosphate"),
    ("VC", "碳酸亚乙烯酯", "vinylene carbonate", "溶剂/添加剂", "环状碳酸酯", "O=c1occo1", r"vinylene carbonate"),
    ("DFEC", "4,5-二氟碳酸乙烯酯", "4,5-difluoro-1,3-dioxolan-2-one", "溶剂", "环状碳酸酯", "O=C1OC(F)C(F)O1", r"di-?\s?fluoro\s?ethylene carbonate|4,5-difluoro-1,3-dioxolan-2-one"),
    ("TFPC", "3,3,3-三氟碳酸丙烯酯", "4-(trifluoromethyl)-1,3-dioxolan-2-one", "溶剂", "环状碳酸酯", "O=C1OCC(C(F)(F)F)O1", r"trifluoropropylene carbonate|3,3,3-\s?trifluoropro"),
    ("FEMC", "甲基 2,2,2-三氟乙基碳酸酯", "methyl 2,2,2-trifluoroethyl carbonate", "溶剂", "链状碳酸酯", "COC(=O)OCC(F)(F)F", r"methyl\s?\(?2,2,2-"),
    ("CROWN155", "15-冠-5", "15-crown-5", "溶剂/添加剂", "冠醚", "C1COCCOCCOCCOCCO1", r"15-crown-5"),
    ("UG", "二乙二醇乙基正丁基醚", "diethylene glycol butyl ethyl ether", "溶剂", "链醚", "CCCCOCCOCCOCC", r"ethyl-n-butyl ether|unsymmetric"),
    ("ANL1NM2", "2,2-二甲基-3,6,9-三氧杂-2-硅杂癸烷", "2,2-dimethyl-3,6,9-trioxa-2-siladecane", "溶剂", "硅氧烷醚", "C[Si](C)(C)OCCOCCOC", r"trioxa-2-siladecane"),
    ("ANL1NM3", "2,2-二甲基-3,6,9,12-四氧杂-2-硅杂十三烷", "2,2-dimethyl-3,6,9,12-tetraoxa-2-silatridecane", "溶剂", "硅氧烷醚", "C[Si](C)(C)OCCOCCOCCOC", r"tetraoxa-2-silatridecane"),
    ("TMSN3", "叠氮三甲基硅烷", "azidotrimethylsilane", "添加剂", "有机硅", "C[Si](C)(C)N=[N+]=[N-]", r"azidotrimethylsilane|trimethylsilyl azide"),
    ("TFMTMS", "三氟甲基三甲基硅烷", "(trifluoromethyl)trimethylsilane", "添加剂", "有机硅", "C[Si](C)(C)C(F)(F)F", r"trifluoromethyl\)?\s?trimethylsilane"),
    ("DMTFA", "N,N-二甲基三氟甲磺酰胺", "N,N-dimethyltrifluoromethanesulfonamide", "溶剂", "磺酰胺", "CN(C)S(=O)(=O)C(F)(F)F", r"dimethyl triflamide|dimethyltrifluoromethanesulfonamide"),
    ("DPTFA", "N,N-二丙基三氟甲磺酰胺", "N,N-dipropyltrifluoromethanesulfonamide", "溶剂", "磺酰胺", "CCCN(CCC)S(=O)(=O)C(F)(F)F", r"dipropyl triflamide"),
    ("TEOA", "三乙醇胺", "triethanolamine", "溶剂", "胺（醇胺）", "OCCN(CCO)CCO", r"triethanolamine"),
    # 氟化醚
    ("TFEE", "1,2-双(1,1,2,2-四氟乙氧基)乙烷", "1,2-bis(1,1,2,2-tetrafluoroethoxy)ethane", "溶剂", "氟化醚", "FC(F)C(F)(F)OCCOC(F)(F)C(F)F", r"(?:bis)?\(?1,1,2,2-\s?tetrafluoroethoxy\)?\s?ethane"),
    ("BTFE", "双(2,2,2-三氟乙基)醚", "bis(2,2,2-trifluoroethyl) ether", "溶剂", "氟化醚", "FC(F)(F)COCC(F)(F)F", r"bis\s?\(2,2,2-\s?trifluoroethyl\)\s?ether"),
    ("OFE", "1H,1H,5H-八氟戊基 1,1,2,2-四氟乙基醚", "1H,1H,5H-octafluoropentyl 1,1,2,2-tetrafluoroethyl ether", "溶剂", "氟化醚", "FC(F)C(F)(F)OCC(F)(F)C(F)(F)C(F)(F)C(F)F", r"octa-?\s?fluoropentyl"),
    ("THE", "2,2,2-三氟乙基 1,1,2,3,3,3-六氟丙基醚", "2,2,2-trifluoroethyl 1,1,2,3,3,3-hexafluoropropyl ether", "溶剂", "氟化醚", "FC(F)(F)COC(F)(F)C(F)C(F)(F)F", r"hexafluoropropyl ether"),
    ("ETFEE", "乙基 1,1,2,2-四氟乙基醚", "ethyl 1,1,2,2-tetrafluoroethyl ether", "溶剂", "氟化醚", "CCOC(F)(F)C(F)F", r"ethyl 1,1,2,2-tetrafluoroethyl ether"),
    ("TPE", "1,1,2,2-四氟乙基 2,2,3,3,3-五氟丙基醚", "1,1,2,2-tetrafluoroethyl 2,2,3,3,3-pentafluoropropyl ether", "溶剂", "氟化醚", "FC(F)C(F)(F)OCC(F)(F)C(F)(F)F", r"pentafluoropropyl ether"),
    ("TFTFE", "1,1,2,2-四氟乙基 2,2,2-三氟乙基醚", "1,1,2,2-tetrafluoroethyl 2,2,2-trifluoroethyl ether", "溶剂", "氟化醚", "FC(F)C(F)(F)OCC(F)(F)F", r"tetrafluoroethyl\s?2,2,2-\s?trifluoroethyl ether|2,2,2-\s?tri-?fluor-?\s?oethyl ether"),
    ("TFEME", "1,1,2,2-四氟乙基甲基醚", "1,1,2,2-tetrafluoroethyl methyl ether", "溶剂", "氟化醚", "COC(F)(F)C(F)F", r"tetrafluoroethyl\s?methyl ether"),
    ("TFEPE", "1-(1,1,2,2-四氟乙氧基)丙烷", "1-(1,1,2,2-tetrafluoroethoxy)propane", "溶剂", "氟化醚", "CCCOC(F)(F)C(F)F", r"1-\(1,1,2,2-tetrafluoroethoxy\)propane"),
    ("TFEIBE", "2-甲基-1-(1,1,2,2-四氟乙氧基)丙烷", "2-methyl-1-(1,1,2,2-tetrafluoroethoxy)propane", "溶剂", "氟化醚", "CC(C)COC(F)(F)C(F)F", r"2-methyl-1-\(1,1,2,2-tetrafluoroethoxy\)propane"),
    ("TFEG", "1-甲氧基-2-(2,2,2-三氟乙氧基)乙烷", "1-methoxy-2-(2,2,2-trifluoroethoxy)ethane", "溶剂", "氟化醚", "COCCOCC(F)(F)F", r"trifluoroethyl methyl ether ethylene glycol"),
    ("TFPG", "1-甲氧基-2-(2,2,3,3-四氟丙氧基)乙烷", "1-methoxy-2-(2,2,3,3-tetrafluoropropoxy)ethane", "溶剂", "氟化醚", "COCCOCC(F)(F)C(F)F", r"2,2,3,3-tetrafluoropropyl methyl ether"),
    ("DTFEG", "1,2-双(2,2,2-三氟乙氧基)乙烷", "1,2-bis(2,2,2-trifluoroethoxy)ethane", "溶剂", "氟化醚", "FC(F)(F)COCCOCC(F)(F)F", r"di\(2,2,2-trifluoroethyl\) ether"),
    ("DTFPG", "1,2-双(2,2,3,3-四氟丙氧基)乙烷", "1,2-bis(2,2,3,3-tetrafluoropropoxy)ethane", "溶剂", "氟化醚", "FC(F)C(F)(F)COCCOCC(F)(F)C(F)F", r"di\(2,2,3,3-tetrafluoropropyl\) ether"),
    ("TFEPG", "1-(2,2,2-三氟乙氧基)-2-(2,2,3,3-四氟丙氧基)乙烷", "1-(2,2,2-trifluoroethoxy)-2-(2,2,3,3-tetrafluoropropoxy)ethane", "溶剂", "氟化醚", "FC(F)(F)COCCOCC(F)(F)C(F)F", r"2,2,2-trifluoroethyl-2,2,3,3-tetrafluoropropyl ether"),
    ("F4EO2", "九氟-6-(2-甲氧基乙氧基)己烷（F4EO2）", "1,1,1,2,2,3,3,4,4-nonafluoro-6-(2-methoxyethoxy)hexane", "溶剂", "氟化醚", "COCCOCCC(F)(F)C(F)(F)C(F)(F)C(F)(F)F", r"nonafluoro-6-\(2-methoxyethoxy\)hexane"),
    ("F3EO1", "七氟-4-(2-甲氧基乙氧基)丁烷（F3EO1）", "1,1,1,2,2,3,3-heptafluoro-4-(2-methoxyethoxy)butane", "溶剂", "氟化醚", "COCCOCC(F)(F)C(F)(F)C(F)(F)F", r"heptafluoro-4-\(2-methoxyethoxy\)butane"),
    ("F8EO4", "十七氟-2,5,8,11-四氧杂二十一烷（F8EO4）", "14,14,15,15,16,16,17,17,18,18,19,19,20,20,21,21,21-heptadecafluoro-2,5,8,11-tetraoxahenicosane", "溶剂", "氟化醚",
     "COCCOCCOCCOCCC(F)(F)C(F)(F)C(F)(F)C(F)(F)C(F)(F)C(F)(F)C(F)(F)C(F)(F)F", r"heptadecafluoro-\s?2,5,8,11-tetraoxahenicosane"),
    # 离子液体（整体按溶剂计，阴离子另算）
    ("PYR14TFSI", "1-丁基-1-甲基吡咯烷鎓双(三氟甲磺酰)亚胺盐", "1-butyl-1-methylpyrrolidinium bis(trifluoromethylsulfonyl)imide", "溶剂", "离子液体", "CCCC[N+]1(C)CCCC1." + TFSI, r"butyl-1-methyl-?\s?pyrrolidinium"),
    ("PP14TFSI", "1-丁基-1-甲基哌啶鎓双(三氟甲磺酰)亚胺盐", "1-butyl-1-methylpiperidinium bis(trifluoromethylsulfonyl)imide", "溶剂", "离子液体", "CCCC[N+]1(C)CCCCC1." + TFSI, r"methylpiperidinium"),
    ("EMIMTFSI", "1-乙基-3-甲基咪唑鎓双(三氟甲磺酰)亚胺盐", "1-ethyl-3-methylimidazolium bis(trifluoromethylsulfonyl)imide", "溶剂", "离子液体", "CCn1cc[n+](C)c1." + TFSI, r"1-ethyl-3-methylimidazolium"),
    ("BMIMTFSI", "1-丁基-3-甲基咪唑鎓双(三氟甲磺酰)亚胺盐", "1-butyl-3-methylimidazolium bis(trifluoromethylsulfonyl)imide", "溶剂", "离子液体", "CCCCn1cc[n+](C)c1." + TFSI, r"1-butyl-3-methylimidazolium"),
    ("AMIMTFSI", "1-烯丙基-3-甲基咪唑鎓双(三氟甲磺酰)亚胺盐", "1-allyl-3-methylimidazolium bis(trifluoromethylsulfonyl)imide", "溶剂", "离子液体", "C=CCn1cc[n+](C)c1." + TFSI, r"allyl-3-methylimidazolium"),
    ("DEMETFSI", "N,N-二乙基-N-甲基-N-(2-甲氧基乙基)铵双(三氟甲磺酰)亚胺盐", "N,N-diethyl-N-methyl-N-(2-methoxyethyl)ammonium bis(trifluoromethylsulfonyl)imide", "溶剂", "离子液体", "CC[N+](C)(CC)CCOC." + TFSI, r"\(2-methoxyethyl\)ammonium"),
    ("PYR12O1TFSI", "N-(2-甲氧基乙基)-N-甲基吡咯烷鎓双(三氟甲磺酰)亚胺盐", "1-(2-methoxyethyl)-1-methylpyrrolidinium bis(trifluoromethylsulfonyl)imide", "溶剂", "离子液体", "COCC[N+]1(C)CCCC1." + TFSI, r"methoxyethyl\)?-?1?-?methylpyrrolidinium"),
    ("TBATFSI", "四丁基铵双(三氟甲磺酰)亚胺盐", "tetrabutylammonium bis(trifluoromethylsulfonyl)imide", "其他盐/添加剂", "季铵盐", "CCCC[N+](CCCC)(CCCC)CCCC." + TFSI, r"tetrabutylammonium"),
    # 盐
    ("LiClO4", "高氯酸锂", "lithium perchlorate", "锂盐", "高氯酸盐", "[Li+].[O-]Cl(=O)(=O)=O", r"perchlorate"),
    ("LiTDI", "4,5-二氰基-2-三氟甲基咪唑锂", "lithium 4,5-dicyano-2-(trifluoromethyl)imidazolide", "锂盐", "咪唑盐", "[Li+].N#Cc1nc(C(F)(F)F)[n-]c1C#N", r"dicyano-2-\(?trifluoromethyl\)?imidazol"),
    ("LiCl", "氯化锂", "lithium chloride", "锂盐", "卤化物", "[Li+].[Cl-]", r"lithium chloride"),
    ("LiHFDF", "1,1,2,2,3,3-六氟丙烷-1,3-二磺酰亚胺锂", "lithium 1,1,2,2,3,3-hexafluoropropane-1,3-disulfonimide", "锂盐", "磺酰亚胺盐（环状）", "[Li+].O=S1(=O)[N-]S(=O)(=O)C(F)(F)C(F)(F)C1(F)F", r"hexafluoropropane-1,3-disulfonimide"),
    ("LiTFA", "三氟乙酸锂", "lithium trifluoroacetate", "锂盐", "羧酸盐", "[Li+].[O-]C(=O)C(F)(F)F", r"lithium trifluoroacetate"),
    ("LiAlOhfip", "四(六氟异丙氧基)铝酸锂", "lithium tetrakis(hexafluoroisopropoxy)aluminate", "锂盐", "铝酸盐",
     "[Li+].FC(F)(F)C(O[Al-](OC(C(F)(F)F)C(F)(F)F)(OC(C(F)(F)F)C(F)(F)F)OC(C(F)(F)F)C(F)(F)F)C(F)(F)F", r"hexafluoroisopropoxy\)?\s?aluminate|Al\(O?hfip\)"),
    ("LiBOB", "双草酸硼酸锂", "lithium bis(oxalato)borate", "锂盐/添加剂", "硼酸盐", "[Li+].O=C1O[B-]2(OC1=O)OC(=O)C(=O)O2", r"bis\(oxalato\)\s?borate"),
    ("LiPO2F2", "二氟磷酸锂", "lithium difluorophosphate", "锂盐/添加剂", "磷酸盐", "[Li+].[O-]P(=O)(F)F", r"difluorophosphate"),
    ("MgTFSI2", "双(三氟甲磺酰)亚胺镁", "magnesium bis(trifluoromethylsulfonyl)imide", "其他盐/添加剂", "磺酰亚胺盐", "[Mg+2]." + TFSI + "." + TFSI, r"magnesium bis"),
    ("NaTFSI", "双(三氟甲磺酰)亚胺钠", "sodium bis(trifluoromethylsulfonyl)imide", "其他盐/添加剂", "磺酰亚胺盐", "[Na+]." + TFSI, r"sodium bis"),
    ("NH4TFSI", "双(三氟甲磺酰)亚胺铵", "ammonium bis(trifluoromethylsulfonyl)imide", "其他盐/添加剂", "磺酰亚胺盐", "[NH4+]." + TFSI, r"ammonium bis\(trifluoromethyl"),
    ("NaClO4", "高氯酸钠", "sodium perchlorate", "其他盐/添加剂", "高氯酸盐", "[Na+].[O-]Cl(=O)(=O)=O", r"sodium perchlorate"),
    ("CsClO4", "高氯酸铯", "cesium perchlorate", "其他盐/添加剂", "高氯酸盐", "[Cs+].[O-]Cl(=O)(=O)=O", r"c(?:a|ae)esium perchlorate"),
    ("NH4TFA", "三氟乙酸铵", "ammonium trifluoroacetate", "其他盐/添加剂", "羧酸盐", "[NH4+].[O-]C(=O)C(F)(F)F", r"ammonium trifluoroacetate"),
    ("NH4NO3", "硝酸铵", "ammonium nitrate", "其他盐/添加剂", "硝酸盐", "[NH4+].[O-][N+](=O)[O-]", r"ammonium nitrate"),
    ("NaNO3", "硝酸钠", "sodium nitrate", "其他盐/添加剂", "硝酸盐", "[Na+].[O-][N+](=O)[O-]", r"sodium nitrate"),
    ("KNO3", "硝酸钾", "potassium nitrate", "其他盐/添加剂", "硝酸盐", "[K+].[O-][N+](=O)[O-]", r"potassium nitrate"),
    ("CsNO3", "硝酸铯", "cesium nitrate", "其他盐/添加剂", "硝酸盐", "[Cs+].[O-][N+](=O)[O-]", r"c(?:a|ae)esium nitrate"),
    ("TEANO3", "四乙基硝酸铵", "tetraethylammonium nitrate", "其他盐/添加剂", "硝酸盐", "CC[N+](CC)(CC)CC.[O-][N+](=O)[O-]", r"tetraethylammonium nitrate"),
    ("NH4I", "碘化铵", "ammonium iodide", "其他盐/添加剂", "卤化物", "[NH4+].[I-]", r"ammonium iodide"),
    ("KBrO3", "溴酸钾", "potassium bromate", "其他盐/添加剂", "溴酸盐", "[K+].[O-]Br(=O)=O", r"potassium bromate"),
    ("NaIO4", "高碘酸钠", "sodium periodate", "其他盐/添加剂", "高碘酸盐", "[Na+].[O-]I(=O)(=O)=O", r"periodate"),
    ("SnI4", "四碘化锡", "tin(IV) iodide", "添加剂（介体）", "金属卤化物", "I[Sn](I)(I)I", r"tin\s?\(?IV\)?\s?iodide|stannic iodide"),
    ("SnI2", "二碘化锡", "tin(II) iodide", "添加剂（介体）", "金属卤化物", "I[Sn]I", r"tin\s?\(?II\)?\s?iodide"),
    ("AlI3", "三碘化铝", "aluminum iodide", "添加剂（介体）", "金属卤化物", "I[Al](I)I", r"alumin(?:i)?um iodide"),
    ("MgI2", "碘化镁", "magnesium iodide", "添加剂（介体）", "金属卤化物", "[Mg+2].[I-].[I-]", r"magnesium iodide"),
    ("TiI4", "四碘化钛", "titanium(IV) iodide", "添加剂（介体）", "金属卤化物", "I[Ti](I)(I)I", r"titanium\s?\(?IV\)?\s?iodide"),
    ("SbI3", "三碘化锑", "antimony triiodide", "添加剂（介体）", "金属卤化物", "I[Sb](I)I", r"antimony\s?\(?III\)?\s?iodide|antimony triiodide"),
    ("InBr3", "三溴化铟", "indium(III) bromide", "添加剂（介体）", "金属卤化物", "Br[In](Br)Br", r"indium\s?\(?III\)?\s?bromide"),
    # 有机添加剂（结构简单、原文有全称的）
    ("PH2S2", "二苯基二硫醚", "diphenyl disulfide", "添加剂", "有机硫（二硫醚）", "c1ccc(SSc2ccccc2)cc1", r"diphenyl disulfide"),
    ("DPRDS", "二正丙基二硫醚", "dipropyl disulfide", "添加剂", "有机硫（二硫醚）", "CCCSSCCC", r"dipropyl disulfide"),
    ("DADS", "二烯丙基二硫醚", "diallyl disulfide", "添加剂", "有机硫（二硫醚）", "C=CCSSCC=C", r"diallyl disulfide"),
    ("DTBDS", "二叔丁基二硫醚", "di-tert-butyl disulfide", "添加剂", "有机硫（二硫醚）", "CC(C)(C)SSC(C)(C)C", r"di-?\s?tert-?\s?butyl disulfide"),
    ("C12F10S2", "双(五氟苯基)二硫醚", "bis(pentafluorophenyl) disulfide", "添加剂", "有机硫（二硫醚）", "Fc1c(F)c(F)c(SSc2c(F)c(F)c(F)c(F)c2F)c(F)c1F", r"pentafluorophenyl\)?\s?disulfide"),
    ("LIC6F5S", "五氟苯硫酚锂", "lithium pentafluorobenzenethiolate", "添加剂", "有机硫（硫酚盐）", "[Li+].[S-]c1c(F)c(F)c(F)c(F)c1F", r"pentafluorophenyl sulfide|pentafluorobenzenethiolate"),
    ("ME2SE2", "二甲基二硒醚", "dimethyl diselenide", "添加剂", "有机硒（二硒醚）", "C[Se][Se]C", r"dimethyl diselenide"),
    ("PH2SE2", "二苯基二硒醚", "diphenyl diselenide", "添加剂", "有机硒（二硒醚）", "c1ccc([Se][Se]c2ccccc2)cc1", r"diphenyl diselenide"),
    ("THIOPHENOL", "苯硫酚", "thiophenol", "添加剂", "有机硫（硫酚）", "Sc1ccccc1", r"thiophenol"),
    ("BDT12", "1,2-苯二硫酚", "1,2-benzenedithiol", "添加剂", "有机硫（硫酚）", "Sc1ccccc1S", r"1,2-benzenedithiol"),
    ("BDT13", "1,3-苯二硫酚", "1,3-benzenedithiol", "添加剂", "有机硫（硫酚）", "Sc1cccc(S)c1", r"1,3-benzenedithiol"),
    ("BDT14", "1,4-苯二硫酚", "1,4-benzenedithiol", "添加剂", "有机硫（硫酚）", "Sc1ccc(S)cc1", r"benzene-1,4-dithiol|1,4-benzenedithiol"),
    ("BTT", "1,3,5-苯三硫酚", "1,3,5-benzenetrithiol", "添加剂", "有机硫（硫酚）", "Sc1cc(S)cc(S)c1", r"benzenetrithiol"),
    ("BPD", "联苯-4,4′-二硫酚", "biphenyl-4,4'-dithiol", "添加剂", "有机硫（硫酚）", "Sc1ccc(-c2ccc(S)cc2)cc1", r"biphenyl-4,4.?-dithiol"),
    ("BTB", "3,5-双(三氟甲基)苯硫酚", "3,5-bis(trifluoromethyl)thiophenol", "添加剂", "有机硫（硫酚）", "Sc1cc(C(F)(F)F)cc(C(F)(F)F)c1", r"bis\(trifluoromethyl\)\s?thiophenol|bis\(trifluoromethyl\)benzenethiol"),
    ("TMTD", "二硫化四甲基秋兰姆", "tetramethylthiuram disulfide", "添加剂", "有机硫（秋兰姆）", "CN(C)C(=S)SSC(=S)N(C)C", r"tetramethylthiuram disulfide"),
    ("TMTM", "一硫化四甲基秋兰姆", "tetramethylthiuram monosulfide", "添加剂", "有机硫（秋兰姆）", "CN(C)C(=S)SC(=S)N(C)C", r"tetramethylthiuram monosulfide"),
    ("MBT", "2-巯基苯并噻唑", "2-mercaptobenzothiazole", "添加剂", "有机硫（噻唑）", "S=c1[nH]c2ccccc2s1", r"2-mercaptobenzothiazole"),
    ("THIOUREA", "硫脲", "thiourea", "添加剂", "有机硫（硫脲）", "NC(N)=S", r"(?<!methyl)thiourea"),
    ("DMTU", "1,3-二甲基硫脲", "1,3-dimethylthiourea", "添加剂", "有机硫（硫脲）", "CNC(=S)NC", r"dimethylthiourea|dimethyl thiourea"),
    ("TMTU", "四甲基硫脲", "tetramethylthiourea", "添加剂", "有机硫（硫脲）", "CN(C)C(=S)N(C)C", r"tetramethylthiourea|tetramethyl thiourea"),
    ("TAA", "硫代乙酰胺", "thioacetamide", "添加剂", "有机硫（硫代酰胺）", "CC(N)=S", r"thioacetamide"),
    ("TFACAM", "三氟乙酰胺", "2,2,2-trifluoroacetamide", "添加剂", "酰胺", "NC(=O)C(F)(F)F", r"trifluoroacetamide"),
    ("KEX", "乙基黄原酸钾", "potassium ethyl xanthate", "添加剂", "有机硫（黄原酸盐）", "CCOC(=S)[S-].[K+]", r"ethyl\s?xanthate"),
    ("PYRROLE", "吡咯", "pyrrole", "添加剂", "吡咯", "c1cc[nH]c1", r"\bpyrrole\b"),
    ("SOCL2", "氯化亚砜", "thionyl chloride", "添加剂", "亚硫酰氯", "O=S(Cl)Cl", r"thionyl chloride"),
    ("HFPP", "六氟环三磷腈", "hexafluorocyclotriphosphazene", "添加剂", "磷腈", "FP1(F)=NP(F)(F)=NP(F)(F)=N1", r"hexafluoro-?\s?cyclo-?\s?triphosphazene"),
    ("TMSPI", "亚磷酸三(三甲基硅基)酯", "tris(trimethylsilyl) phosphite", "添加剂", "有机硅/亚磷酸酯", "C[Si](C)(C)OP(O[Si](C)(C)C)O[Si](C)(C)C", r"tris\(trimethylsilyl\)\s?phosphite"),
    ("BNC", "双(4-硝基苯基)碳酸酯", "bis(4-nitrophenyl) carbonate", "添加剂", "碳酸酯（芳基）", "O=C(Oc1ccc([N+](=O)[O-])cc1)Oc1ccc([N+](=O)[O-])cc1", r"bis\(4-nitrophenyl\)\s?carbonate"),
    ("METFA", "三氟乙酸甲酯", "methyl trifluoroacetate", "添加剂", "酯", "COC(=O)C(F)(F)F", r"methyl trifluoroacetate"),
    ("METF", "三氟甲磺酸甲酯", "methyl trifluoromethanesulfonate", "添加剂", "磺酸酯", "COS(=O)(=O)C(F)(F)F", r"methyl trifl(?:ate|uoromethanesulfonate)"),
    ("DFAQ", "1,4-二氟蒽醌", "1,4-difluoroanthraquinone", "添加剂（介体）", "醌", "O=C1c2ccccc2C(=O)c2c(F)ccc(F)c21", r"difluoroanthraquinone"),
    ("TTF", "四硫富瓦烯", "tetrathiafulvalene", "添加剂（介体）", "有机硫（四硫富瓦烯）", "C1=CSC(=C2SC=CS2)S1", r"tetrathiafulvalene"),
]

MED = "MED_TRIAL"
ADD = "ADD_TRIAL"
GENERIC = [
    {"id": MED, "名称": "试跑未核定介体", "英文名": "redox mediator (identity not curated in 11-04 trial)", "档": "B", "类别": "添加剂（介体）",
     "化学类别": "介体（未核定）", "smiles": None, "无SMILES原因": "11-04 试跑：茂金属、醌、酞菁、芳烃自由基前体等介体未逐一写结构，只记“含介体”",
     "全称正则": r"(?!x)x"},
    {"id": ADD, "名称": "试跑未核定添加剂", "英文名": "additive (identity not curated in 11-04 trial)", "档": "B", "类别": "添加剂",
     "化学类别": "添加剂（未核定）", "smiles": None, "无SMILES原因": "11-04 试跑：结构复杂或只在一篇出现的添加剂、聚合物、纳米颗粒未逐一写结构，只记“含其他添加剂”",
     "全称正则": r"(?!x)x"},
]

# 写法 → 组分（论文 * 通配）；值为组分 ID 或 ID 列表
ALIAS = {
    "DMSO": "DMSO", "dimethyl sulfoxide": "DMSO", "Dimethyl sulfoxide (DMSO)": "DMSO",
    "tetramethylene sulfone (TMS)": "SULFOLANE", "SL": "SULFOLANE", "sulfolane": "SULFOLANE", "sulfolane (SL)": "SULFOLANE",
    "Sulfolane (SL)": "SULFOLANE", "Sulfolane": "SULFOLANE", "SUL": "SULFOLANE", "TMS": "SULFOLANE", "SL（原文称sulfone）": "SULFOLANE",
    "TMS（原文称tetramethyl sulfone）": "SULFOLANE", "正极液：TMS（原文称tetramethyl sulfone）": "SULFOLANE", "正极液：TMS": "SULFOLANE",
    "TMS液：TMS（原文称tetramethyl sulfone）": "SULFOLANE", "碳纸工作液：TMS（原文称tetramethyl sulfone）": "SULFOLANE",
    "TMS正极液": "SULFOLANE", "正极TMS液": "SULFOLANE", "Li侧TMS液": "SULFOLANE",
    "G4": "TEGDME", "tetraethylene glycol dimethyl ether (TEGDME)": "TEGDME", "tetraethylene glycol dimethyl ether (tetraglyme)": "TEGDME",
    "G4 (tetraethylene glycol dimethyl ether)": "TEGDME",
    "G2": "DIGLYME", "diglyme (G2)": "DIGLYME", "diglyme": "DIGLYME", "DEGDME": "DIGLYME",
    "G3": "TRIGLYME", "triglyme": "TRIGLYME", "TREGDME": "TRIGLYME", "monoglyme (G1)": "DME", "dimethyl ether (DME)（名称照录原文）": "DME",
    "PS stock carried DME": "DME",
    "EMC": "EMC", "ethyl methyl carbonate (EMC)": "EMC",
    "ACN": "ACN", "MeCN": "ACN", "acetonitrile (MeCN)": "ACN", "acetonitrile": "ACN", "ACN (positive)": "ACN", "propionitrile": "PRN",
    "DMF": "DMF", "N,N-dimethylformamide": "DMF", "N,N-Dimethylformamide (DMF)": "DMF",
    "DMA": "DMAC", "DMAc": "DMAC", "N,N-dimethylacetamide": "DMAC", "dimethylacetamide (DMA)": "DMAC",
    "acetamide": "ACETAMIDE", "ε-caprolactam": "CAPROLACTAM", "CPL": "CAPROLACTAM", "N-methylacetamide": "NMA", "TMU": "TMU", "DMI": "DMI",
    "DIPE": "DIPE", "IPE": "DIPE", "DIPS": "DIPS", "MTBE": "MTBE", "MtBE": "MTBE", "MBE": "MBE", "MPE": "MPE", "PBE": "PBE", "TBIE": "TBIE",
    "IE": "DIBE", "DE": "DPE", "DIE": "DBE", "EE": "DEE", "HE": "NHEXANE", "PE": "NPENTANE", "HEP": "NHEPTANE", "OCT": "NOCTANE",
    "toluene": "TOLUENE", "m-Xylene": "MXYLENE", "FB": "FB", "fluorobenzene": "FB", "DFB": "DFB14", "1,4-difluorobenzene (DFB)": "DFB14",
    "HFB（hexafluorobenzene）": "HFB", "HFB": "HFB", "CS2": "CS2", "CHCl3": "CHCL3",
    "H2O": "H2O", "water": "H2O", "去离子水": "H2O", "DI water": "H2O", "distilled water": "H2O", "ultrapure water": "H2O", "水": "H2O",
    "ethanol": "ETOH", "absolute ethanol": "ETOH", "乙醇": "ETOH", "anhydrous methanol": "MEOH", "n-butanol": "NBUOH",
    "1,4-Dioxane": "DIOXANE", "Diox": "DIOXANE", "DIOX": "DIOXANE", "MeTHF": "METHF", "METHF": "METHF", "MEDOL": "MEDOL",
    "2,2-Dimethyoxypropane（原文拼写）": "DMP22", "Ethyl acetate": "ETOAC", "Butanal": "BUTANAL", "Butanone": "BUTANONE",
    "Propionyl chloride": "PRCOCL", "n-Butylamine": "NBUNH2", "Tributylamine (TBA)": "TBUAMINE", "TBA": "TBUAMINE",
    "pyridine": "PYRIDINE", "2-fluoropyridine": "FPY2", "3-fluoropyridine": "FPY3", "4-fluoropyridine": "FPY4", "imidazole": "IMIDAZOLE",
    "MeIm": "MEIM", "1-methylimidazole (Me-Im)": "MEIM", "isoxazole (IZ)": "ISOXAZOLE", "IZ": "ISOXAZOLE",
    "TEP": "TEP", "TMP": "TMP", "VC": "VC", "vinylene carbonate (VC)": "VC", "DFEC": "DFEC", "TFPC": "TFPC", "FEMC": "FEMC",
    "15-crown-5": "CROWN155", "diethylene glycol ethyl-n-butyl ether (UG)": "UG", "UG": "UG",
    "ANL-1NM2": "ANL1NM2", "ANL-1NM2 (2,2-dimethyl-3,6,9-trioxa-2-siladecane)": "ANL1NM2", "2,2-dimethyl-3,6,9,12-tetraoxa-2-silatridecane": "ANL1NM3",
    "TMS-N3": "TMSN3", "TFMTMS": "TFMTMS", "DMT": "DMTFA", "DPT": "DPTFA",
    "TFEE": "TFEE", "1,2-(1,1,2,2-tetrafluoroethoxy)ethane (TFEE)": "TFEE", "TFEE (1,2-bis(1,1,2,2-tetrafluoroethoxy)ethane)": "TFEE",
    "TTFE (1,2-(1,1,2,2-tetrafluoroethoxy)ethane)": "TFEE",
    "BTFE": "BTFE", "BTFE [bis(2,2,2-trifluoroethyl) ether]": "BTFE", "OFE": "OFE",
    "THE (2,2,2-trifluoroethyl-1,1,2,3,3,3-hexafluoropropyl ether)": "THE", "THE": "THE",
    "ethyl 1,1,2,2-tetrafluoroethyl ether (ETFE)": "ETFEE", "1,1,2,2-tetrafluoroethyl-2,2,3,3,3-pentafluoropropyl ether (TPE)": "TPE",
    "1,1,2,2-tetrafluoroethyl 2,2,2-trifluoroethyl ether (TFTFE)": "TFTFE", "TFTFE": "TFTFE", "TFETFE": "TFTFE",
    "1,1,2,2-tetrafluoroethylmethyl ether (TFEME)": "TFEME", "TME (1,1,2,2-tetrafluoroethyl methyl ether)": "TFEME",
    "TFEPE": "TFEPE", "TFEiBE": "TFEIBE",
    "2,2,2-trifluoroethyl methyl ether ethylene glycol (TFEG)": "TFEG", "ethylene glycol 2,2,3,3-tetrafluoropropyl methyl ether (TFPG)": "TFPG",
    "ethylene glycol di(2,2,2-trifluoroethyl) ether (DTFEG)": "DTFEG", "ethylene glycol di(2,2,3,3-tetrafluoropropyl) ether (DTFPG)": "DTFPG",
    "ethylene glycol 2,2,2-trifluoroethyl-2,2,3,3-tetrafluoropropyl ether (TFEPG)": "TFEPG",
    "F4EO2": "F4EO2", "F3EO1": "F3EO1", "F8EO4": "F8EO4", "HFE": "TTE",
    "Pyr14TFSI": "PYR14TFSI", "PYR14TFSI": "PYR14TFSI", "Py1,4TFSI": "PYR14TFSI", "BMPTFSi": "PYR14TFSI",
    "1-butyl-1-methylpyrrolidinium bis(trifluoromethylsulfonyl)imide (Py14TFSI)": "PYR14TFSI",
    "PYR14TFSI (1-butyl 1-methyl pyrrolidinium bis(trifluoromethylsulfonyl)imide)": "PYR14TFSI",
    "1-butyl-1-methyl-pyrrolidinium-bis(trifluoromethanesulfonyl)imide": "PYR14TFSI",
    "C4mpyr-TFSI（1-butyl-1-methylpyrrolidinium bis(trifluoromethanesulfonyl)imide）": "PYR14TFSI",
    "PP14TFSI": "PP14TFSI", "1-ethyl-3-methylimidazolium bis(trifluoromethylsulfonyl)imide (EMITFSI)": "EMIMTFSI",
    "1-butyl-3-methylimidazolium bis(trifluoromethylsulfonyl)imide (BmimTFSI)": "BMIMTFSI", "AMImTFSI": "AMIMTFSI",
    "N,N-Diethyl-N-methyl-N-(2-methoxyethyl)ammonium bis(trifluoromethanesulfonyl)imide ([DEME][TFSI])": "DEMETFSI",
    "Pyr1,2O1TFSI": "PYR12O1TFSI", "TBATFSI": "TBATFSI",
    "LiTFSA": "LiTFSI", "LiTFSA (LiN(SO2CF3)2)": "LiTFSI", "LiN(CF3SO2)2": "LiTFSI", "lithium bis(trifluoromethylsulfonyl) amide (LiTFSI)": "LiTFSI",
    "LiTFSA（lithium bis(trifluoromethanesulfonyl)amide）": "LiTFSI", "lithium bis(trifluoromethanesulfonyl)imide (LiTFSI)": "LiTFSI",
    "bis(trifluoro-methane)-sulfonimide (LiTSFI, 原文拼写)": "LiTFSI", "DBE相LiTFSI": "LiTFSI", "TMS相LiTFSI": "LiTFSI", "正极液：LiTFSI": "LiTFSI",
    "TMS液：LiTFSI": "LiTFSI", "碳纸工作液：LiTFSI": "LiTFSI", "负极GPE：LiTFSI": "LiTFSI", "负极GPE：LiTFSI（DBE相与DOL相各自）": "LiTFSI",
    "GPE：LiTFSI（DBE相与DOL相各自）": "LiTFSI", "负极GPE：DBE（前驱液溶剂份额）": "DBE", "GPE：DBE（前驱液溶剂份额）": "DBE",
    "负极GPE：DOL→poly(DOL)（前驱液溶剂份额）": "DOL", "GPE：DOL→poly(DOL)（前驱液溶剂份额）": "DOL", "DOL→poly(DOL)（前驱液溶剂份额）": "DOL",
    "负极GPE：DOL→polyDOL": "DOL", "负极GPE：LiPF6": "LiPF6", "GPE：LiPF6": "LiPF6",
    "LiClO4": "LiClO4", "LiTDI": "LiTDI", "LiCl": "LiCl", "LiTfO": "LiCF3SO3", "LiTf": "LiCF3SO3", "LiTF": "LiCF3SO3", "CF3SO3Li": "LiCF3SO3",
    "LiHFDF": "LiHFDF", "LiHDFD": "LiHFDF", "LiHDFD / LiHFDF（原文两种拼写）": "LiHFDF", "LiTFA": "LiTFA", "Li[Al(Ohfip)4]": "LiAlOhfip",
    "LiODFB": "LiDFOB", "LiBOB": "LiBOB", "LiPO2F2": "LiPO2F2", "MgTFSI2": "MgTFSI2", "NaTFSI": "NaTFSI", "NH4TFSI": "NH4TFSI",
    "NaClO4": "NaClO4", "CsClO4": "CsClO4", "NH4TFA": "NH4TFA", "正极液：NH4TFA": "NH4TFA", "碳纸工作液：NH4TFA": "NH4TFA", "正极NH4TFA": "NH4TFA",
    "NH4NO3": "NH4NO3", "NaNO3": "NaNO3", "KNO3": "KNO3", "CsNO3": "CsNO3", "TEANO3": "TEANO3", "NH4I": "NH4I", "KBrO3": "KBrO3", "NaIO4": "NaIO4",
    "SnI4": "SnI4", "SnI2": "SnI2", "AlI3": "AlI3", "MgI2": "MgI2", "TiI4": "TiI4", "SbI3": "SbI3", "InBr3": "InBr3",
    "Ph2S2": "PH2S2", "DPDS": "PH2S2", "DprDS": "DPRDS", "DADS": "DADS", "DtbDS": "DTBDS", "C12F10S2": "C12F10S2",
    "bis(pentafluorophenyl) disulfide (C12F10S2)": "C12F10S2", "LiC6F5S": "LIC6F5S", "lithium pentafluorophenyl sulfide (LiC6F5S)": "LIC6F5S",
    "dimethyl diselenide (Me-Se)": "ME2SE2", "diphenyl diselenide (Ph-Se)": "PH2SE2", "diphenyl diselenide (PDSe)": "PH2SE2", "PDSe": "PH2SE2",
    "thiophenol (TP)": "THIOPHENOL", "TP": "THIOPHENOL", "1,2-BDT": "BDT12", "1,3-BDT": "BDT13", "1,4-BDT": "BDT14", "BD": "BDT14",
    "benzene-1,4-dithiol (BD)": "BDT14", "1,3,5-benzenetrithiol (BTT)": "BTT", "BTT": "BTT", "BPD": "BPD", "biphenyl-4,4′-dithiol (BPD)": "BPD",
    "3,5-bis(trifluoromethyl)thiophenol (BTB)": "BTB", "BTB": "BTB", "tetramethylthiuram disulfide": "TMTD", "tetramethylthiuram monosulfide": "TMTM",
    "2-mercaptobenzothiazole": "MBT", "TU": "THIOUREA", "DMTU": "DMTU", "TMTU": "TMTU", "thioacetamide (TAA)": "TAA",
    "trifluoroacetamide (TFA)": "TFACAM", "potassium ethylxanthate": "KEX", "pyrrole (Py)": "PYRROLE", "thionyl chloride (SOCl2)": "SOCL2",
    "hexafluoro-cyclo-triphosphazene (HFPP)": "HFPP", "tris(trimethylsilyl) phosphite (TMSP)": "TMSPI", "bis(4-nitrophenyl) carbonate (BNC)": "BNC",
    "BNC": "BNC", "CH3TFA": "METFA", "CH3TF": "METF", "TfOMe": "METF", "DFAQ": "DFAQ", "1,4-difluoroanthraquinone (DFAQ)": "DFAQ", "TTF": "TTF",
    "D1-1 ionic dendrimer (TFSI salt)": ADD, "D1-3 ionic dendrimer (TFSI salt)": ADD, "D1-5 ionic dendrimer (TFSI salt)": ADD,
    "D1-7 ionic dendrimer (TFSI salt)": ADD, "D2-1 ionic dendrimer (TFSI salt)": ADD, "D2-3 ionic dendrimer (TFSI salt)": ADD,
    "D2-5 ionic dendrimer (TFSI salt)": ADD, "D2-7 ionic dendrimer (TFSI salt)": ADD,
}
PER_PAPER = {("P185", "HFE"): "TFTFE"}  # P185 表 S3：HFE 写作 1,1,2,2-Tetrafluoroe…，分子式 C4H3F7O，即 TFTFE；其余 9 篇定义句均为 TTE
MEDIATORS = {"CoCp2", "CoCp2 (cobaltocene)", "补入CoCp2", "ferrocene", "DmFc", "NiCp2", "AQT", "AQC", "DCBQ", "CoPc", "CoPcCl", "Naph",
             "naphthalene (NP)", "Li-Naph", "9,10-dimethylanthracene", "4,4′-dimethylbiphenyl (4,4′-DMBP)", "DPPF", "MEP-Br"}
EXCL = {  # 身份未决、非配入
    "FB（方法段写TTE，未裁定）": "身份未决：方法段写 TTE、正文写 FB（试跑不判）",
    "HFE（具体分子未逐组指明）": "身份未决：原文未逐组指明是哪种氢氟醚",
    "ethyl methyl carbonate（方法原文全名）；缩写原文为DMC，身份未决": "身份未决：全称与缩写矛盾",
    "锂盐：正文LiTFSI，图注LiFSI，待裁定": "身份未决：正文与图注矛盾", "SnI2或SnI4（原文冲突）": "身份未决：原文冲突",
    "PEGDME (MW约500 Da)": "聚合物溶剂，分子量分布，无单一结构（试跑）", "polyDOL": "聚合物（DOL 开环产物）",
    "LPSCl": "固态电解质颗粒（材料）", "F3B": "三氟苯异构体原文未写明（试跑不判）",
    "d-THF": "NMR 氘代溶剂（表征用）", "D6-DMSO": "NMR 氘代溶剂（表征用）", "d6-DMSO": "NMR 氘代溶剂（表征用）",
    "d-DME": "NMR 氘代溶剂（表征用）", "1,4-dioxane-d8": "NMR 氘代溶剂（表征用）", "TEA": None,
}
MATERIAL = re.compile(r"carbon|graphene|CNT|Ketjen|PVDF|PTFE|separator|foil|metal\b|membrane|TiO2|TiC|TiB2|SnS2?\b|Sb2S3|In2S3|SiO2|"
                      r"leachate|supernatant|electrolyte|species|precursor|liquid|medium|sample|膜|隔膜|浸|残|提取|上清|电解液|样品|物种|产物|分散",
                      re.I)
CJK = re.compile(r"[一-鿿]")
# 厂商密度（11-01 用户定的第三来源；11-04 试跑只补缺密度影响配方最多的 5 个，网页搜索结果交叉核对）
DENSITY = {
    "EMC": {"值": 1.006, "条件": "25 °C (lit.)", "来源": "Sigma-Aldrich 752002 / 754935",
            "链接": "https://www.sigmaaldrich.com/product/aldrich/752002", "说明": "部分页面另写 1.022；取两货号一致的 1.006"},
    "BTFE": {"值": 1.404, "条件": "25 °C (lit.)", "来源": "Sigma-Aldrich 287571", "链接": "https://www.sigmaaldrich.com/US/en/product/aldrich/287571",
             "说明": "ChemicalBook 同值"},
    "TFEE": {"值": 1.48, "条件": "25 °C", "来源": "Apollo Scientific（VWR 34610126）", "链接": "https://www.avantorsciences.com/cz/en/product/34610126/12-1122-tetrafluoroethoxyethane",
             "说明": "ChemicalBook 另写 1.418（未注温度）"},
    "OFE": {"值": 1.66, "条件": "20 °C（比重 20/20）", "来源": "TCI（VWR 30013948）", "链接": "https://b2b-no.vwr.com/store/product/30013948/null",
            "说明": "ChemicalBook 只有预测值 1.532"},
    "PYR14TFSI": {"值": 1.40, "条件": "未注温度", "来源": "Sigma-Aldrich 491046（high purity）", "链接": "https://sigmaaldrich.com/US/en/product/mm/490046",
                  "说明": "Sigma-Aldrich 900873 写 1.378，相差 1.6%"},
}


def main() -> None:
    cur = json.loads(CURATION.read_text(encoding="utf-8"))
    left = json.loads(LEFT.read_text(encoding="utf-8"))
    have = {c["id"] for c in cur["组分"]}
    for t in NEW:
        cid, zh, en, cat, chem, smi, rx = t
        if cid in have:
            continue
        cur["组分"].append({"id": cid, "名称": zh, "英文名": en, "档": "A", "类别": cat, "化学类别": chem, "smiles": smi,
                           "pubchem_query": en, "全称正则": rx, "备注": NOTE})
    for g in GENERIC:
        if g["id"] not in have:
            cur["组分"].append(dict(g, 备注=NOTE))
    for c in cur["组分"]:
        if c["id"] in DENSITY and not c.get("厂商密度"):
            c["厂商密度"] = dict(DENSITY[c["id"]], 说明=DENSITY[c["id"]]["说明"] + "；" + NOTE)
    ids = {c["id"] for c in cur["组分"]}
    alias_keys = {(a["论文"], a["写法"]) for a in cur["别名"]}
    excl_keys = {(e["论文"], e["写法"]) for e in cur["未收录"]}
    stat = {"别名": 0, "介体": 0, "添加剂": 0, "未收录": 0}
    for (pid, name), cid in PER_PAPER.items():
        if (pid, name) not in alias_keys:
            cur["别名"].append({"论文": pid, "写法": name, "组分": [cid], "备注": NOTE + "；P185 表 S3 分子式 C4H3F7O"})
    TEOA_NOTE = "P009 原文 triethanolamine (TEA)"
    for name, v in left.items():
        if ("*", name) in alias_keys or ("*", name) in excl_keys:
            continue
        roles = set(v["角色"])
        if name in ALIAS or name == "TEA":
            cid = "TEOA" if name == "TEA" else ALIAS[name]
            assert cid in ids, (name, cid)
            cur["别名"].append({"论文": "*", "写法": name, "组分": [cid], "备注": NOTE + ("；" + TEOA_NOTE if name == "TEA" else "")})
            stat["别名"] += 1
        elif name in MEDIATORS:
            cur["别名"].append({"论文": "*", "写法": name, "组分": [MED], "备注": NOTE + "；介体，结构未逐一写"})
            stat["介体"] += 1
        elif name in EXCL and EXCL[name]:
            cur["未收录"].append({"论文": "*", "写法": name, "原因": EXCL[name] + "（" + NOTE + "）"})
            stat["未收录"] += 1
        elif CJK.search(name) or MATERIAL.search(name):
            cur["未收录"].append({"论文": "*", "写法": name, "原因": "占位、身份未决、残留/浸出液或材料，不是配入电解液的确定组分（" + NOTE + "）"})
            stat["未收录"] += 1
        elif "添加剂" in roles or "其他" in roles:
            cur["别名"].append({"论文": "*", "写法": name, "组分": [ADD], "备注": NOTE + "；结构未逐一写"})
            stat["添加剂"] += 1
        else:  # 溶剂/盐角色但未列入：不猜
            cur["未收录"].append({"论文": "*", "写法": name, "原因": "试跑未核定的溶剂/盐写法（" + NOTE + "）"})
            stat["未收录"] += 1
    CURATION.write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"新组分 {len(NEW)}＋通用 2；处理写法 {sum(stat.values())}：{stat}")


if __name__ == "__main__":
    main()
