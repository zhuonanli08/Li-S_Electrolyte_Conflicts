"""step23 第一步（rdkit 环境）：SES 式分子宇宙的指纹与结构小图（11-08 用户：分子宇宙“你看看人家 SES 怎么画的，你完全是两模两样”）。

SES 的做法（NVIDIA 技术博客 2025-05 图 2）：背景是枚举出的上千万个小分子（UMAP 后按密度着色），文献报道过的电解液分子以亮点叠在上面，
常用分子用方框配结构图标出 → 一眼看出“人类试过的分子只占化学空间的一小角”。我们照这个思路：
  背景 = QM9（133,885 个 ≤ 9 个重原子 C/N/O/F 的稳定小分子，取自 GDB-17 化学宇宙；外部数据/qm9.csv，来自 DeepChem 公开数据集）；
  叠加 = 313 篇用到的中性有机分子（溶剂、稀释剂、添加剂、介体；锂盐、离子、多硫化物、S8 不放，它们不在同一类化学空间）。
指纹与旧分子宇宙一致：Morgan r = 2、2048 位（RDKit）。
输出：output/分子宇宙_SES式_2026-11-08/指纹.npz（packbits）、分子.json、结构图/<id>.png（白底 2D 结构式，供标注框用）。
用法：D:/anaconda/envs/rdkit/python.exe -X utf8 scripts/step23_universe_fp.py [--draw-only 只重画结构小图]
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Draw import rdMolDraw2D

RDLogger.DisableLog("rdApp.*")
ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
OUT = ROOT / "output" / "分子宇宙_SES式_2026-11-08"
COMP = ROOT / "output" / "组分结构表_试跑313篇_2026-11-05" / "组分表.json"
QM9 = ROOT / "外部数据" / "qm9.csv"
SKIP_ROLES = {"锂盐", "离子", "硫物种", "盐", "锂盐/添加剂"}
# 标注框里画结构式的分子：最常用的溶剂各一个代表 + 问题 1 的对照分子
DRAW = ["DME", "DOL", "TEGDME", "TTE", "EC", "DMC", "FEC", "SULFOLANE", "DMSO", "THF", "DBE", "DEE", "F3DEE", "F4DEE", "F5DEE", "F6DEE", "BTFE"]

gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def fp(m):
    a = np.zeros(2048, bool)
    a[list(gen.GetFingerprint(m).GetOnBits())] = True
    return a


def draw(lit):
    """结构小图：白底、黑色键线、杂原子按 RDKit 默认配色（11-08 晚用户：不要黑底，改白底）。"""
    (OUT / "结构图").mkdir(exist_ok=True)
    ids = {x["id"]: x for x in lit}
    for i in DRAW:
        if i not in ids:
            print("no structure:", i)
            continue
        m = Chem.MolFromSmiles(ids[i]["smiles"])
        d = rdMolDraw2D.MolDraw2DCairo(300, 220)
        o = d.drawOptions()
        o.setBackgroundColour((1, 1, 1, 1))
        o.bondLineWidth = 2.4
        o.minFontSize = 18
        o.padding = 0.12
        d.DrawMolecule(m)
        d.FinishDrawing()
        (OUT / "结构图" / f"{i}.png").write_bytes(d.GetDrawingText())


def main():
    if "--draw-only" in sys.argv:  # 只重画结构小图，不重算指纹
        draw(json.loads((OUT / "分子.json").read_text(encoding="utf-8"))["文献分子"])
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "结构图").mkdir(exist_ok=True)
    # 文献分子
    lit, lit_fp, lit_key = [], [], {}
    for c in json.loads(COMP.read_text(encoding="utf-8")):
        smi = c.get("规范SMILES") or c.get("smiles")
        if not smi or c.get("类别") in SKIP_ROLES or "+" in smi or "-" in smi:
            continue
        m = Chem.MolFromSmiles(smi)
        if m is None or not any(a.GetSymbol() == "C" for a in m.GetAtoms()):
            continue
        lit.append({"id": c["id"], "名称": c.get("英文名") or c.get("名称"), "角色": c.get("类别"), "化学类别": c.get("化学类别"),
                    "论文数": c.get("论文数") or 0, "smiles": Chem.MolToSmiles(m), "重原子": m.GetNumHeavyAtoms(),
                    "元素": sorted({a.GetSymbol() for a in m.GetAtoms()})})
        lit_fp.append(fp(m))
        lit_key[Chem.MolToInchiKey(m)] = c["id"]
    # 背景
    bg_smi, bg_fp, in_qm9 = [], [], set()
    with QM9.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            m = Chem.MolFromSmiles(r["smiles"])
            if m is None:
                continue
            k = Chem.MolToInchiKey(m)
            if k in lit_key:
                in_qm9.add(lit_key[k])
            bg_smi.append(r["smiles"])
            bg_fp.append(fp(m))
    for x in lit:
        x["在QM9中"] = x["id"] in in_qm9
    X = np.vstack([np.array(bg_fp), np.array(lit_fp)])
    np.savez_compressed(OUT / "指纹.npz", bits=np.packbits(X, axis=1), n_bg=len(bg_fp), n_lit=len(lit_fp))
    (OUT / "分子.json").write_text(json.dumps({"说明": "背景 QM9（行 0..n_bg-1）＋ 313 篇中性有机分子（之后各行，顺序同 文献分子）；Morgan r=2, 2048 位",
                                             "背景数": len(bg_fp), "文献分子": lit}, ensure_ascii=False, indent=1), encoding="utf-8")
    draw(lit)
    print(f"background {len(bg_fp)}; literature {len(lit)} (in QM9: {len(in_qm9)}); drawn {sum(i in ids for i in DRAW)}")


if __name__ == "__main__":
    main()
