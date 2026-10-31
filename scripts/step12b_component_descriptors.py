"""组分描述符与复核工作簿（2026-10-31）：读 step12a build 的组分表，给 A 档算 RDKit 描述符，出 Excel。

描述符按方案 §5.8：分子量、O/N/S/F 原子数、环数、可旋转键数、TPSA、氢键受体数，加电解液官能团标签（SMARTS）；
盐整体算一份、阴离子再单独算一份；Morgan 指纹（半径 2、2048 位）只用于结构相似度，不作模型输入。
这些是结构特征，不是配位强度、介电常数或溶解度。
输出 output/组分结构表_F版30篇_2026-10-31/：描述符.json、组分结构表.xlsx（说明、组分表、别名表、未收录、描述符、溶剂相似度、复核表）。
运行：D:/anaconda/envs/rdkit/python.exe -X utf8 scripts/step12b_component_descriptors.py
"""
from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import Descriptors, Lipinski, rdFingerprintGenerator, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "组分结构表_F版30篇_2026-10-31"

# 电解液官能团标签。醚氧排除酯/碳酸酯中的单键氧；“相邻”指直接相连的碳上有 ≥2 个 F（CF₂/CF₃）
SMARTS = {
    "醚氧数": "[OX2]([#6;!$([#6]=O)])[#6;!$([#6]=O)]",
    "α氟化醚氧数（相邻CF₂/CF₃）": "[OX2]([#6;!$([#6]=O)])[CX4;$(C(F)F)]",
    "羰基数": "[CX3]=[OX1]",
    "碳酸酯基数": "[OX2][CX3](=[OX1])[OX2]",
    "酰胺/脲基数": "[NX3][CX3](=[OX1])",
    "砜/亚砜基数": "[$([SX4](=O)(=O)([#6])[#6]),$([SX3](=O)([#6])[#6])]",
    "P=O数": "[PX4]=[OX1]",
    "腈基数": "[CX2]#[NX1]",
    "硫醚/多硫链S原子数": "[$([SX2]([#6])[#6]),$([SX2][SX2])]",
}
PATTERNS = {k: Chem.MolFromSmarts(v) for k, v in SMARTS.items()}
MORGAN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def count_atoms(mol, sym: str) -> int:
    return sum(1 for a in mol.GetAtoms() if a.GetSymbol() == sym)


def describe(mol) -> dict:
    d = {
        "分子量": round(Descriptors.MolWt(mol), 3),
        "O原子数": count_atoms(mol, "O"), "N原子数": count_atoms(mol, "N"),
        "S原子数": count_atoms(mol, "S"), "F原子数": count_atoms(mol, "F"),
        "环数": rdMolDescriptors.CalcNumRings(mol),
        "可旋转键数": rdMolDescriptors.CalcNumRotatableBonds(mol),
        "TPSA": round(rdMolDescriptors.CalcTPSA(mol), 2),
        "氢键受体数": Lipinski.NumHAcceptors(mol),
    }
    for k, p in PATTERNS.items():
        d[k] = len(mol.GetSubstructMatches(p))
    return d


def anion_of(mol):
    """盐取带负电的最大碎片作阴离子；不是多碎片或没有阴离子时返回 None。"""
    frags = Chem.GetMolFrags(mol, asMols=True)
    neg = [f for f in frags if Chem.GetFormalCharge(f) < 0]
    if len(frags) < 2 or not neg:
        return None
    return max(neg, key=lambda f: f.GetNumHeavyAtoms())


def main() -> None:
    comps = json.loads((OUT / "组分表.json").read_text(encoding="utf-8"))
    aliases = json.loads((OUT / "别名表.json").read_text(encoding="utf-8"))
    excl = json.loads((OUT / "未收录.json").read_text(encoding="utf-8"))
    cover = json.loads((OUT / "行映射.json").read_text(encoding="utf-8"))["覆盖"]

    desc_rows, fps = [], {}
    for c in comps:
        if c["档"] != "A" or not c.get("规范SMILES"):
            continue
        mol = Chem.MolFromSmiles(c["规范SMILES"])
        desc_rows.append({"组分": c["id"], "名称": c["名称"], "对象": "整体", "化学类别": c["化学类别"],
                          "SMILES": c["规范SMILES"], **describe(mol)})
        an = anion_of(mol)
        if an is not None:
            desc_rows.append({"组分": c["id"], "名称": c["名称"], "对象": "阴离子", "化学类别": c["化学类别"],
                              "SMILES": Chem.MolToSmiles(an), **describe(an)})
        elif "溶剂" in c["类别"]:
            fps[c["id"]] = MORGAN.GetFingerprint(mol)
    (OUT / "描述符.json").write_text(json.dumps(desc_rows, ensure_ascii=False, indent=1), encoding="utf-8")

    ids = sorted(fps, key=lambda i: (next(c["化学类别"] for c in comps if c["id"] == i), i))
    sim = [[round(DataStructs.TanimotoSimilarity(fps[a], fps[b]), 2) for b in ids] for a in ids]

    write_workbook(comps, aliases, excl, cover, desc_rows, ids, sim)
    print(f"描述符 {len(desc_rows)} 行（A 档 {sum(r['对象'] == '整体' for r in desc_rows)} 个组分，"
          f"另有阴离子 {sum(r['对象'] == '阴离子' for r in desc_rows)} 行）；溶剂相似度 {len(ids)}×{len(ids)}")


HEAD = Font(bold=True)
FILL = PatternFill("solid", fgColor="DDEBF7")
WRAP = Alignment(wrap_text=True, vertical="top")


def sheet(wb, title: str, header: list[str], rows: list[list], widths: dict[int, int] | None = None):
    ws = wb.create_sheet(title)
    ws.append(header)
    for cell in ws[1]:
        cell.font, cell.fill = HEAD, FILL
    for r in rows:  # 原文片段里有 PDF 抽取残留的控制字符，Excel 不接受
        ws.append(["" if v is None else ILLEGAL_CHARACTERS_RE.sub(" ", v) if isinstance(v, str) else v for v in r])
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = WRAP
    ws.freeze_panes = "B2"
    for i in range(1, len(header) + 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = (widths or {}).get(i, 14)
    return ws


def evid_text(ev: list[dict]) -> str:
    out = []
    for e in ev:
        h = e["全称原句"]
        out.append(f"{e['组分']}：" + (f"[{h['id']}] …{h['text']}…" if h else "本篇未找到全称"))
    return "\n".join(out)


def write_workbook(comps, aliases, excl, cover, desc_rows, ids, sim) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "说明"
    notes = [
        "组分结构表（F 版独立测试集 30 篇，2026-10-31）",
        "用途：把提取结果里每条组分（论文号＋配方号＋原文写法）对应到一个确定的分子（SMILES / InChIKey），再给 A 档算 RDKit 描述符。规则见方案 §5.8“组分收录与身份核实”。",
        "来源：只读 F 版冻结候选 recipes[].components 与各篇 source.json；未改冻结候选、人工复核表和评分。",
        f"覆盖检查：组分条目 {cover['组分条目']} 条 → 映射到组分 {cover['已映射到组分']} 条，未收录（有原因）{cover['未收录（有原因）']} 条，未映射 {cover['未映射']} 条。",
        "三档：A 档 = 实际配入液体的分子（盐含 LiNO₃、溶剂、稀释剂、离子液体、添加剂、介体），做身份＋描述符；B 档 = 多硫化锂（名义物种）、溶于测量液的 S₈、单独列出的离子，只做身份；C 档 = 电极材料、表征溶剂、计算模型物种、占位词，不收录，见“未收录”页。",
        "核验：✅ 本篇原文找到全称，且结构与 PubChem 全称查询一致｜🧮 RDKit 由 SMILES 计算｜🔶 需人看（原文只有缩写、自合成按原文画、原文拼写有误、按化学式书写等）｜⚠️ 与 PubChem 不一致｜❌ 本篇原文找不到该写法。",
        "PubChem 只用全称查询（缩写查询会返回错误化合物）；LiTFSI 全称命中一条不规范记录，改按规范记录 CID 3816071 核对，见组分表备注。",
        "描述符是结构特征，不等于配位强度、介电常数或溶解度；Morgan 指纹只用于“溶剂相似度”页，不作模型输入。",
        "Morgan 指纹对小分子溶剂很粗：DME 与 DOL 同为醚，Tanimoto 却为 0（链状与环状原子环境不同）。区分醚、碳酸酯等类别应看官能团标签和化学类别，不看指纹相似度。",
        "✍ 列由用户填写，Claude 不改。全部内容为 AI 辅助，用户尚未逐项人工确认。",
        "配方挂接与单位换算待 F 版 30 篇人工复核完成后进行；“顺带发现的提取问题_复核完再看.json”请在复核完成后再打开。",
    ]
    for n in notes:
        ws.append([n])
        ws.cell(ws.max_row, 1).alignment = WRAP
    ws.column_dimensions["A"].width = 120

    sheet(wb, "组分表",
          ["组分ID", "名称", "英文名", "档", "类别", "化学类别", "规范SMILES", "InChIKey", "分子式", "分子量",
           "PubChem比对", "论文数", "论文", "条数", "用途（按写法计）", "核验", "备注", "复核✍"],
          [[c["id"], c["名称"], c["英文名"], c["档"], c["类别"], c["化学类别"], c.get("规范SMILES"), c.get("InChIKey"),
            c.get("分子式"), c.get("分子量"), c.get("PubChem比对"), c["论文数"], "、".join(c["论文"]), c["条数"],
            "；".join(f"{k}{v}" for k, v in c["用途"].items()), c["核验"],
            c.get("备注") or c.get("无SMILES原因") or "", ""] for c in comps],
          {2: 22, 3: 30, 7: 36, 8: 30, 11: 26, 13: 30, 15: 22, 16: 40, 17: 40})

    sheet(wb, "别名表",
          ["论文", "原文写法", "组分ID", "条数", "配方", "用途", "提取角色", "核验", "核验说明", "全称原句", "复核✍"],
          [[a["论文"], a["写法"], "、".join(a["组分"]), a["条数"], "、".join(a["配方"]), "、".join(a["用途"]),
            "、".join(a["提取角色"]), a["核验"], a["核验说明"], evid_text(a["全称核对"]), ""] for a in aliases],
          {2: 26, 3: 16, 5: 24, 9: 36, 10: 80})

    sheet(wb, "未收录",
          ["论文", "原文写法", "原因", "条数", "用途", "提取角色", "复核✍"],
          [[e["论文"], e["写法"], e["原因"], e["条数"], "、".join(e["用途"]), "、".join(e["提取角色"]), ""] for e in excl],
          {2: 30, 3: 44, 5: 20})

    dkeys = [k for k in desc_rows[0] if k not in ("组分", "名称", "对象", "化学类别", "SMILES")]
    sheet(wb, "描述符", ["组分ID", "名称", "对象", "化学类别", "SMILES", *dkeys, "核验"],
          [[r["组分"], r["名称"], r["对象"], r["化学类别"], r["SMILES"], *[r[k] for k in dkeys], "🧮"] for r in desc_rows],
          {2: 22, 5: 36})

    cls = {c["id"]: c["化学类别"] for c in comps}
    sheet(wb, "溶剂相似度", ["组分（化学类别）", *ids],
          [[f"{a}（{cls[a]}）", *row] for a, row in zip(ids, sim)], {1: 24})

    review = []
    for c in comps:
        if c["核验"] != "✅":
            review.append(["组分", c["id"], "", c["核验"], c.get("备注") or "", "核对结构与来源"])
    for a in aliases:
        if a["核验"] != "✅":
            review.append(["写法", "、".join(a["组分"]), f"{a['论文']}「{a['写法']}」", a["核验"], a["核验说明"],
                           evid_text(a["全称核对"])])
    sheet(wb, "复核表", ["层级", "组分ID", "论文与写法", "核验", "说明", "证据/建议", "复核✍"], review,
          {2: 16, 3: 30, 4: 30, 5: 50, 6: 70})

    wb.save(OUT / "组分结构表.xlsx")


if __name__ == "__main__":
    main()
