"""组分描述符与复核工作簿（2026-10-31）：读 step12a build 的组分表，给 A 档算 RDKit 描述符，出 Excel。

描述符按方案 §5.8：分子量、O/N/S/F 原子数、环数、可旋转键数、TPSA、氢键受体数，加电解液官能团标签（SMARTS）；
盐整体算一份、阴离子再单独算一份；Morgan 指纹（半径 2、2048 位）只用于结构相似度，不作模型输入。
这些是结构特征，不是配位强度、介电常数或溶解度。
官能团标签按出现的化学类别扩充：每次运行检查 A 档有没有组分一个标签都没命中（烃和不含碳的无机盐除外），
有就打印出来，提示要加标签；加标签只多一列，已有组分的其他数值不变。
复核不要求会读 SMILES：每个 A 档组分画结构图（结构图/），需要人判断的地方写成中文问题（“待你判断”页）。
工作簿里已有用户在 ✍ 列填写的内容时不覆盖，先把填写内容转存到组分核定.json 再重跑。
输出 output/组分结构表_F版30篇_2026-10-31/：描述符.json、结构图/、组分结构表.xlsx。
运行：D:/anaconda/envs/rdkit/python.exe -X utf8 scripts/step12b_component_descriptors.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Font, PatternFill
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import Descriptors, Draw, Lipinski, rdFingerprintGenerator, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "组分结构表_F版30篇_2026-10-31"
IMG = OUT / "结构图"
XLSX = OUT / "组分结构表.xlsx"

# 电解液官能团标签。醚氧排除酯/碳酸酯中的单键氧；“相邻”指直接相连的碳上有 ≥2 个 F（CF₂/CF₃）。
# 磺酰基、胺/铵氮 10-31 由覆盖检查补入（TFSI/FSI/OTf 阴离子、苯乙胺/苄胺/季铵此前一个标签都没命中）
SMARTS = {
    "醚氧数": "[OX2]([#6;!$([#6]=O)])[#6;!$([#6]=O)]",
    "α氟化醚氧数（相邻CF₂/CF₃）": "[OX2]([#6;!$([#6]=O)])[CX4;$(C(F)F)]",
    "羰基数": "[CX3]=[OX1]",
    "碳酸酯基数": "[OX2][CX3](=[OX1])[OX2]",
    "酰胺/脲基数": "[NX3][CX3](=[OX1])",
    "砜/亚砜基数": "[$([SX4](=O)(=O)([#6])[#6]),$([SX3](=O)([#6])[#6])]",
    "磺酰基数（磺酰亚胺/磺酸根等，不含砜）": "[SX4;$(S(=[OX1])=[OX1]);!$(S(=O)(=O)([#6])[#6])]",
    "P=O数": "[PX4]=[OX1]",
    "腈基数": "[CX2]#[NX1]",
    "胺/铵氮数（不含酰胺）": "[NX3,NX4+;!$(N~[!#6;!#1]);!$(N[#6]=[O,S,N])]",
    "硫醚/多硫链S原子数": "[$([SX2]([#6])[#6]),$([SX2][SX2])]",
}
PATTERNS = {k: Chem.MolFromSmarts(v) for k, v in SMARTS.items()}
MORGAN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
EXEMPT = "烃（没有极性官能团，这本身就是信息）和不含碳的无机盐/离子（组分身份本身就是特征）"


def count_atoms(mol, *syms: str) -> int:
    return sum(1 for a in mol.GetAtoms() if a.GetSymbol() in syms)


def describe(mol) -> dict:
    d = {
        "分子量": round(Descriptors.MolWt(mol), 3),
        "O原子数": count_atoms(mol, "O"), "N原子数": count_atoms(mol, "N"),
        "S原子数": count_atoms(mol, "S"), "F原子数": count_atoms(mol, "F"),
        "Cl/Br/I原子数": count_atoms(mol, "Cl", "Br", "I"),
        "环数": rdMolDescriptors.CalcNumRings(mol),
        "芳环数": rdMolDescriptors.CalcNumAromaticRings(mol),
        "可旋转键数": rdMolDescriptors.CalcNumRotatableBonds(mol),
        "TPSA": round(rdMolDescriptors.CalcTPSA(mol), 2),
        "氢键受体数": Lipinski.NumHAcceptors(mol),
    }
    for k, p in PATTERNS.items():
        d[k] = len(mol.GetSubstructMatches(p))
    return d


def gist(d: dict, formula: str) -> str:
    """把描述符写成一句人能读的结构要点。"""
    if not re.search(r"C(?![a-z])", formula):
        return "无机盐/离子（不含碳）" + (f"；F {d['F原子数']}" if d["F原子数"] else "")
    parts = ["无环" if d["环数"] == 0 else f"{d['环数']} 个环" + ("（含芳环）" if d["芳环数"] else "")]
    fg = [f"{re.sub(r'（.*?）', '', k).removesuffix('数')} {d[k]}" for k in SMARTS if d[k]]
    parts += fg or ["无极性官能团"]
    parts.append(f"F {d['F原子数']}" if d["F原子数"] else "无 F")
    if d["Cl/Br/I原子数"]:
        parts.append(f"Cl/Br/I {d['Cl/Br/I原子数']}")
    return "；".join(parts)


def anion_of(mol):
    """盐取带负电的最大碎片作阴离子；不是多碎片或没有阴离子时返回 None。"""
    frags = Chem.GetMolFrags(mol, asMols=True)
    neg = [f for f in frags if Chem.GetFormalCharge(f) < 0]
    if len(frags) < 2 or not neg:
        return None
    return max(neg, key=lambda f: f.GetNumHeavyAtoms())


def guard_user_input() -> None:
    if not XLSX.exists():
        return
    wb = load_workbook(XLSX, read_only=True)
    for ws in wb.worksheets:
        rows = ws.iter_rows(values_only=True)
        cols = [i for i, h in enumerate(next(rows, None) or ()) if isinstance(h, str) and "✍" in h]
        if cols and any(i < len(r) and r[i] not in (None, "") for r in rows for i in cols):
            wb.close()
            sys.exit(f"{XLSX.name} 的「{ws.title}」页 ✍ 列已有用户填写，未覆盖；先把填写内容转存到组分核定.json 再重跑")
    wb.close()


def main() -> None:
    guard_user_input()
    comps = json.loads((OUT / "组分表.json").read_text(encoding="utf-8"))
    aliases = json.loads((OUT / "别名表.json").read_text(encoding="utf-8"))
    excl = json.loads((OUT / "未收录.json").read_text(encoding="utf-8"))
    cover = json.loads((OUT / "行映射.json").read_text(encoding="utf-8"))["覆盖"]

    IMG.mkdir(exist_ok=True)
    desc_rows, fps, uncovered = [], {}, []
    for c in comps:
        if c["档"] != "A" or not c.get("规范SMILES"):
            continue
        mol = Chem.MolFromSmiles(c["规范SMILES"])
        Draw.MolToImage(mol, size=(300, 200)).save(IMG / f"{c['id']}.png")
        d = describe(mol)
        desc_rows.append({"组分": c["id"], "名称": c["名称"], "对象": "整体", "化学类别": c["化学类别"],
                          "SMILES": c["规范SMILES"], **d})
        if not any(d[k] for k in SMARTS) and c["化学类别"] != "烃" and count_atoms(mol, "C"):
            uncovered.append(f"{c['id']}（{c['化学类别']}）")
        an = anion_of(mol)
        if an is not None:
            desc_rows.append({"组分": c["id"], "名称": c["名称"], "对象": "阴离子", "化学类别": c["化学类别"],
                              "SMILES": Chem.MolToSmiles(an), **describe(an)})
        elif "溶剂" in c["类别"]:
            fps[c["id"]] = MORGAN.GetFingerprint(mol)
    (OUT / "描述符.json").write_text(json.dumps(desc_rows, ensure_ascii=False, indent=1), encoding="utf-8")

    ids = sorted(fps, key=lambda i: (next(c["化学类别"] for c in comps if c["id"] == i), i))
    sim = [[round(DataStructs.TanimotoSimilarity(fps[a], fps[b]), 2) for b in ids] for a in ids]

    qs = questions(comps, aliases)
    write_workbook(comps, aliases, excl, cover, desc_rows, ids, sim, qs, uncovered)
    print(f"描述符 {len(desc_rows)} 行（A 档 {sum(r['对象'] == '整体' for r in desc_rows)} 个组分，"
          f"另有阴离子 {sum(r['对象'] == '阴离子' for r in desc_rows)} 行）；溶剂相似度 {len(ids)}×{len(ids)}；"
          f"待你判断 {len(qs)} 条")
    print("官能团标签覆盖检查：" + (f"未覆盖 {len(uncovered)} 个，需要加标签：{'、'.join(uncovered)}"
                                   if uncovered else f"A 档全部至少命中一个标签（{EXEMPT}除外）"))


def evidence(aliases: list[dict], cid: str) -> str:
    for a in aliases:
        for e in a["全称核对"]:
            if e["组分"] == cid and e["全称原句"]:
                return f"{a['论文']} [{e['全称原句']['id']}] …{e['全称原句']['text'].strip()}…"
    return ""


ABBR = "本篇原文未找到全称，按常用含义"


def questions(comps: list[dict], aliases: list[dict]) -> list[list]:
    """把 🔶 改写成不用懂 SMILES 也能回答的问题：问的是“原文用的是不是这个分子”，结构图见看图核对页。"""
    byid = {c["id"]: c for c in comps}
    full = defaultdict(set)
    for a in aliases:
        if a["核验"] == "✅":
            for i in a["组分"]:
                full[i].add(a["论文"])
    qs, abbr, merged = [], defaultdict(list), []

    for c in comps:
        if c["档"] == "A" and c["核验"] != "✅":
            note = "；".join(dict.fromkeys(filter(None, [c.get("说明"), c.get("无SMILES原因"), c.get("备注"),
                                                         c.get("PubChem比对") and f"PubChem：{c['PubChem比对']}"])))
            ask = (f"{c['名称']}（{c['id']}）没有单一结构，按前驱体记录、不算描述符，可以吗？" if not c.get("规范SMILES")
                   else f"「看图核对」页 {c['名称']}（{c['id']}）的结构图对吗？")
            qs.append(["组分结构", ask, note, evidence(aliases, c["id"]), "、".join(c["论文"])])

    for a in aliases:
        if a["核验"] == "✅":
            continue
        note = a["核验说明"]
        if note == ABBR:
            abbr[a["组分"][0]].append(a)
        elif "合成一条" in note:
            merged.append(a)
        else:
            names = "、".join(byid[i]["名称"] for i in a["组分"])
            ev = a["原文写法句"]
            qs.append(["原文写法", f"{a['论文']} 的「{a['写法']}」指的是{names}吗？", note.removeprefix(ABBR + "；"),
                       f"[{ev['id']}] …{ev['text'].strip()}…" if ev else "", a["论文"]])

    for cid, items in abbr.items():
        c, papers = byid[cid], sorted({a["论文"] for a in items})
        others = sorted(full[cid] - set(papers))
        why = "领域通用含义" + (f"；另有 {len(others)} 篇写了全称（{'、'.join(others)}），结构与 PubChem 一致" if others else "")
        qs.append(["只写缩写", f"{'、'.join(papers)} 只写了「{'、'.join(sorted({a['写法'] for a in items}))}」，"
                   f"按{c['名称']}（{c['英文名']}）处理，可以吗？", why, "", "、".join(papers)])

    if merged:
        qs.append(["合写拆分", "下面这些写法把两种溶剂合写成一条，已拆成两个组分分别记录，可以吗？",
                   "；".join(f"{a['论文']}「{a['写法']}」→ {'＋'.join(a['组分'])}" for a in merged), "",
                   "、".join(sorted({a["论文"] for a in merged}))])

    b = [c["id"] for c in comps if c["档"] == "B" and c["核验"] != "✅"]
    if b:
        qs.append(["仅认身份", f"多硫化锂和单列离子（{'、'.join(b)}）只用来认身份、不算描述符，结构按化学式写。一般不用看",
                   "B 档", "", ""])
    return qs


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


def write_workbook(comps, aliases, excl, cover, desc_rows, ids, sim, qs, uncovered) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "说明"
    ws.append(["组分结构表（F 版独立测试集 30 篇，2026-10-31）。全部为 AI 辅助，用户尚未逐项人工确认。"])
    ws.append([])
    guide = [
        ["页", "内容", "你要不要看"],
        ["待你判断", f"{len(qs)} 个问题，问的是“原文用的是不是这个分子”，不用懂 SMILES。在最后一列写同意，或写不同意和原因", "要看，主要就这一页"],
        ["看图核对", "A 档每个组分的结构图、一句话结构要点、原文全称句子、PubChem 链接（点开能看到同一分子的别名和结构）", "扫一眼；图和你认识的分子不一样就在最后一列写"],
        ["组分表", "每个组分的 SMILES、InChIKey、分子式、出现在哪些论文", "不用看，给程序用"],
        ["别名表", "每篇论文里每种写法对应哪个组分（同一分子不同写法都指向同一个 ID）", "不用看"],
        ["未收录", "没收进来的条目和原因（电极材料、NMR 溶剂、计算模型物种、占位词等）", "不用看；觉得哪条该收就告诉我"],
        ["描述符", "A 档组分的结构数字（分子量、原子数、官能团个数等），盐另算阴离子", "不用看"],
        ["溶剂相似度", "溶剂两两的指纹相似度，只作检索参考，不进模型", "不用看"],
    ]
    for r in guide:
        ws.append(r)
    for cell in ws[3]:
        cell.font, cell.fill = HEAD, FILL
    ws.append([])
    notes = [
        "SMILES 是什么：把“哪个原子连哪个原子”写成一行字。同一个分子由 RDKit 统一写法后只有一种写法；InChIKey 是由它算出的定长编号，用来判断两条记录是不是同一个分子。结构图就是从 SMILES 画出来的，图对，SMILES 就对。",
        "机器已经核过的：✅ 的写法同时满足两条——本篇原文里找到了全称，用这个全称去 PubChem 查到的结构和我们写的一致。剩下需要人判断的都写进了“待你判断”页。",
        "同分异构体：分子式一样、结构不同的分子，SMILES 和 InChIKey 都不同，不会被当成同一个。本批就有两对：正己烷与 2,3-二甲基丁烷（都是 C₆H₁₄），PPEO-CF₃ 与 PXEO-CF₃（正丙基与异丙基，都是 C₇H₁₃F₃O₂）。所以身份按结构定，不按化学式定；用哪个异构体看原文全称（如 P510 写明 “n-hexane”“2,3 dimethylbutane”）。",
        "立体异构：PC、FEC 有一个手性碳，商品是两种构型各半的混合物，SMILES 不写构型标记，InChIKey 第二段为 UHFFFAOYSA（表示未指定立体）。以后原文若写明某一构型或顺/反式，再写构型标记，与混合物算不同组分。",
        "描述符怎么定的：分子量、原子数、环数、可旋转键数、TPSA、氢键受体数对任何分子都能算，以后不用改；官能团标签是按锂硫电解液常见类别预先定的，不是按这 30 篇定的（本批没有砜、P=O、腈，这几列都是 0）。全量提取出现新类别时加标签，只多一列，已有组分的其他数值不变。",
        "覆盖检查：每次重跑都检查 A 档有没有组分一个标签都没命中（" + EXEMPT + "除外）。" +
        (f"本次未覆盖：{'、'.join(uncovered)}，需要加标签。" if uncovered else
         "本次全部覆盖；10-31 这项检查查出 TFSI/FSI/OTf 等阴离子的磺酰基、苯乙胺/苄胺/季铵的氮没有标签，已补“磺酰基”“胺/铵氮”两列，另加 Cl/Br/I 原子数、芳环数。"),
        "描述符是结构特征，不等于配位强度、介电常数或溶解度。Morgan 指纹对小分子溶剂很粗：DME 与 DOL 同为醚，相似度却为 0，所以分类别看官能团标签，不看指纹。",
        f"覆盖：组分条目 {cover['组分条目']} 条 → 对应到组分 {cover['已映射到组分']} 条，未收录（有原因）{cover['未收录（有原因）']} 条，对不上 {cover['未映射']} 条。规则见方案 §5.8。",
        "配方挂接与单位换算待 F 版 30 篇人工复核完成后进行；“顺带发现的提取问题_复核完再看.json”请在复核完成后再打开。",
    ]
    for n in notes:
        ws.append([n])
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = WRAP
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width, ws.column_dimensions["C"].width = 18, 90, 40
    for r in range(12, ws.max_row + 1):
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
        ws.row_dimensions[r].height = 48

    sheet(wb, "待你判断", ["类型", "问题", "我的处理和理由", "原文依据", "论文", "你的判断✍（同意／不同意＋原因）"], qs,
          {2: 50, 3: 50, 4: 60, 5: 16, 6: 30})

    desc = {r["组分"]: r for r in desc_rows if r["对象"] == "整体"}
    look = []
    for c in comps:
        if c["档"] != "A":
            continue
        cid = re.search(r"CID (\d+)", c.get("PubChem比对") or "")
        look.append([c["id"], c["名称"], c["英文名"], "", gist(desc[c["id"]], c["分子式"]) if c["id"] in desc else "无 SMILES，见待你判断",
                     evidence(aliases, c["id"]), f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid.group(1)}" if cid else
                     (c.get("PubChem比对") or ""), "、".join(c["论文"]), ""])
    ws = sheet(wb, "看图核对", ["组分ID", "名称", "英文名", "结构图", "结构要点", "原文全称句子", "PubChem", "论文", "不对就写✍"], look,
               {2: 18, 3: 26, 4: 44, 5: 30, 6: 60, 7: 22, 8: 16, 9: 20})
    for r, row in enumerate(look, start=2):
        png = IMG / f"{row[0]}.png"
        if png.exists():
            ws.add_image(XLImage(png), f"D{r}")
            ws.row_dimensions[r].height = 155
        if row[6].startswith("http"):
            ws.cell(r, 7).hyperlink = row[6]

    sheet(wb, "组分表",
          ["组分ID", "名称", "英文名", "档", "类别", "化学类别", "规范SMILES", "InChIKey", "分子式", "分子量",
           "PubChem比对", "论文数", "论文", "条数", "用途（按写法计）", "核验", "备注"],
          [[c["id"], c["名称"], c["英文名"], c["档"], c["类别"], c["化学类别"], c.get("规范SMILES"), c.get("InChIKey"),
            c.get("分子式"), c.get("分子量"), c.get("PubChem比对"), c["论文数"], "、".join(c["论文"]), c["条数"],
            "；".join(f"{k}{v}" for k, v in c["用途"].items()), c["核验"],
            "；".join(dict.fromkeys(filter(None, [c.get("说明"), c.get("无SMILES原因"), c.get("备注")])))] for c in comps],
          {2: 22, 3: 30, 7: 36, 8: 30, 11: 26, 13: 30, 15: 22, 16: 40, 17: 40})

    sheet(wb, "别名表",
          ["论文", "原文写法", "组分ID", "条数", "配方", "用途", "提取角色", "核验", "核验说明", "全称原句"],
          [[a["论文"], a["写法"], "、".join(a["组分"]), a["条数"], "、".join(a["配方"]), "、".join(a["用途"]),
            "、".join(a["提取角色"]), a["核验"], a["核验说明"], evid_text(a["全称核对"])] for a in aliases],
          {2: 26, 3: 16, 5: 24, 9: 36, 10: 80})

    sheet(wb, "未收录",
          ["论文", "原文写法", "原因", "条数", "用途", "提取角色"],
          [[e["论文"], e["写法"], e["原因"], e["条数"], "、".join(e["用途"]), "、".join(e["提取角色"])] for e in excl],
          {2: 30, 3: 44, 5: 20})

    dkeys = [k for k in desc_rows[0] if k not in ("组分", "名称", "对象", "化学类别", "SMILES")]
    sheet(wb, "描述符", ["组分ID", "名称", "对象", "化学类别", "SMILES", *dkeys, "核验"],
          [[r["组分"], r["名称"], r["对象"], r["化学类别"], r["SMILES"], *[r[k] for k in dkeys], "🧮"] for r in desc_rows],
          {2: 22, 5: 36})

    cls = {c["id"]: c["化学类别"] for c in comps}
    sheet(wb, "溶剂相似度", ["组分（化学类别）", *ids],
          [[f"{a}（{cls[a]}）", *row] for a, row in zip(ids, sim)], {1: 24})

    wb.save(XLSX)


if __name__ == "__main__":
    main()
