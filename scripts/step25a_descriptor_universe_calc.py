"""step25a（rdkit 环境）：描述符版分子宇宙的背景坐标与补画结构式（11-08 夜用户：分子宇宙“先保留，再换其它的描述符试试，横纵坐标都用两个比较重要的描述符”
“用我现有的描述符”“可以直接改吧，确保像分子宇宙就好了”）。

坐标 = 用户 28 个描述符里元素比例一族的两个（Kim 2023 定义，step12d 已用）：
  sO   = 溶剂 O 原子 ÷ 全部原子（含 H）；
  InOr = 除 C、H（、Li）外的原子 ÷ C 原子。
选它们的理由（数据）：可信度检验（step15 E）里 Li‖Cu 篇内比较 sO 越多 CE 越差（q = 0.01）、InOr 越大 CE 越好（q = 0.10），方向与 Kim 一致；
  计票（step17 v2）里对应的“非氟醚氧越多越差”“F 原子数越多越好”都有多数。含氟比例不能当轴：文献分子 72%、QM9 98% 不含氟，会挤在 0。
背景 = QM9 全部含碳分子（与原版分子宇宙同一数据源 外部数据/qm9.csv）；另存是否含 O–H、N–H（protic），画图时可选。
  11-08 夜第一版只用非质子分子（5.5 万），点太稀、像网格，不像分子宇宙 → 改为全部画，与原版一致。
文献分子的坐标在 step25b 里直接用描述符表（step13h DWHOLE）的原子数算，这里只算背景。
输出：output/分子宇宙_描述符版_2026-11-08/背景_sO_InOr.npz、结构图/<id>.png（补 DEE12、DTFEG；其余沿用 SES 式的结构图）。
用法：D:/anaconda/envs/rdkit/python.exe -X utf8 scripts/step25a_descriptor_universe_calc.py
"""
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np
from rdkit import Chem, RDLogger
from rdkit.Chem.Draw import rdMolDraw2D

RDLogger.DisableLog("rdApp.*")
ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
OUT = ROOT / "output" / "分子宇宙_描述符版_2026-11-08"
QM9 = ROOT / "外部数据" / "qm9.csv"
LIT = ROOT / "output" / "分子宇宙_SES式_2026-11-08" / "分子.json"
PROTIC = Chem.MolFromSmarts("[#7,#8;!H0]")
EXTRA = ["DEE12", "DTFEG"]  # SES 式结构图里没有的


def draw(smi, f):
    m = Chem.MolFromSmiles(smi)
    d = rdMolDraw2D.MolDraw2DCairo(300, 220)
    o = d.drawOptions()
    o.setBackgroundColour((1, 1, 1, 1))
    o.bondLineWidth = 2.4
    o.minFontSize = 18
    o.padding = 0.12
    d.DrawMolecule(m)
    d.FinishDrawing()
    f.write_bytes(d.GetDrawingText())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "结构图").mkdir(exist_ok=True)
    xs, ys, pr, n_all, n_protic = [], [], [], 0, 0
    with QM9.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            m = Chem.MolFromSmiles(r["smiles"])
            if m is None:
                continue
            n_all += 1
            pr.append(m.HasSubstructMatch(PROTIC))
            n_protic += pr[-1]
            m = Chem.AddHs(m)
            s = Counter(a.GetSymbol() for a in m.GetAtoms())
            tot = m.GetNumAtoms()
            if s["C"] == 0:
                pr.pop()
                continue
            xs.append(s["O"] / tot)
            ys.append((tot - s["C"] - s["H"]) / s["C"])
    np.savez_compressed(OUT / "背景_sO_InOr.npz", sO=np.array(xs, np.float32), InOr=np.array(ys, np.float32), protic=np.array(pr, bool), n_qm9=n_all, n_protic=n_protic)
    lit = {m["id"]: m["smiles"] for m in json.loads(LIT.read_text(encoding="utf-8"))["文献分子"]}
    for i in EXTRA:
        draw(lit[i], OUT / "结构图" / f"{i}.png")
    print(f"QM9 {n_all}，其中质子性 {n_protic}，有碳的背景 {len(xs)}；补画 {EXTRA}")


if __name__ == "__main__":
    main()
