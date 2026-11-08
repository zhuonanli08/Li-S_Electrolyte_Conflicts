"""11-08 313 篇试跑：修正 DEE 的组分身份（用户：“修”）。

问题：核定表里“DEE”的通用别名（论文 *）指向乙醚（diethyl ether，CCOCC）。逐篇查原文后，8 篇里两种用法都有：
  乙醚：P215、P235、P288、P355、P633 写 “diethyl ether (DEE)”；P185 写 “EE”，原文表格为 “Ethyl ether C4H10O”。这 6 篇不变。
  1,2-二乙氧基乙烷：P303 M0030 “1, 2-Diethoxyethane (DEE)”，S0073 表 S1 给 CAS 629-14-1、密度 0.842 g/mL；
                   P371 M0080 “1,2-diethoxyethane (DEE)”（其 F3/F4/F5/F6DEE 是这个骨架加氟）。这 2 篇原来错映射成乙醚。
改法：新增组分 DEE12（1,2-二乙氧基乙烷，CCOCCOCC），给 P303、P371 加本篇专用别名 “DEE” → DEE12（本篇别名优先于通用别名，
见 step12a 的 lookup）；通用别名不动。只写 KETI2_COMP 指向的试跑组分表文件夹里的 组分核定.json；可重复运行。
之后按顺序重跑：step12a pubchem → build → step12b → step12d density → build（rdkit 环境，同样设 KETI2_PAPERS / KETI2_COMP）。
AI 核定，用户未逐项确认。
用法：KETI2_COMP=<试跑组分表文件夹> python -X utf8 scripts/step12j_trial313_fix_dee.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

OUT = Path(os.environ["KETI2_COMP"])
NOTE = "11-08 Claude 核定（AI，用户未确认）：原文缩写 DEE 在本篇指 1,2-二乙氧基乙烷，不是乙醚"
COMP = {"id": "DEE12", "名称": "1,2-二乙氧基乙烷", "英文名": "1,2-diethoxyethane", "档": "A", "类别": "溶剂", "化学类别": "链醚",
        "smiles": "CCOCCOCC", "pubchem_query": "1,2-diethoxyethane", "全称正则": r"1,\s*2-\s*[Dd]iethoxyethane",
        "原文密度": {"值": 0.842, "依据": "P303 S0073",
                 "原句": "1,2-Diethoxyethane (DEE): 118.17; -74; 121; 0.842; Unknown; 629-14-1."},
        "备注": NOTE + "；P303 S0073 给 CAS 629-14-1"}
ALIASES = [{"论文": "P303", "写法": "DEE", "组分": ["DEE12"], "依据": ["M0030", "S0073"],
            "备注": NOTE + "；M0030 “1.0 m LiTFSI-DOL/1, 2-Diethoxyethane (DEE)”，S0073 CAS 629-14-1"},
           {"论文": "P371", "写法": "DEE", "组分": ["DEE12"], "依据": ["M0080"],
            "备注": NOTE + "；M0080 “longer alkyl spacers in 1,2-diethoxyethane (DEE) and 1,4-dimethoxybutane (DMB)”，F3/F4/F5/F6DEE 为该骨架加氟"}]


def main():
    p = OUT / "组分核定.json"
    k = json.loads(p.read_text(encoding="utf-8"))
    k["组分"] = [c for c in k["组分"] if c["id"] != COMP["id"]] + [COMP]
    keep = [a for a in k["别名"] if not (a["论文"] in {x["论文"] for x in ALIASES} and a["写法"] == "DEE")]
    k["别名"] = keep + ALIASES
    p.write_text(json.dumps(k, ensure_ascii=False, indent=1), encoding="utf-8")
    print("组分 +DEE12；别名", [(a["论文"], a["写法"], a["组分"]) for a in ALIASES])


if __name__ == "__main__":
    main()
