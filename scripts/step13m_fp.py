"""step13m 第一步（rdkit 环境）：313 篇用到的组分 → Morgan 指纹（半径 2，2048 位），供分子宇宙图降维（11-06 用户要求：聚类从分子结构层面做，参照 SES AI 的 Molecular Universe）。
输入：output/组分结构表_试跑313篇_2026-11-05/组分表.json（规范SMILES）；输出：output/表述试跑313篇_2026-11-05/结构描述符图/v2/指纹.json。
用法：D:/anaconda/envs/rdkit/python.exe -X utf8 scripts/step13m_fp.py
"""
import json
from pathlib import Path
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator
RDLogger.DisableLog("rdApp.*")
ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
C = json.loads((ROOT / "output" / "组分结构表_试跑313篇_2026-11-05" / "组分表.json").read_text(encoding="utf-8"))
gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
out, bad = [], []
for c in C:
    smi = c.get("规范SMILES") or c.get("smiles")
    m = Chem.MolFromSmiles(smi) if smi else None
    if m is None:
        bad.append(c["id"]); continue
    out.append({"id": c["id"], "bits": list(gen.GetFingerprint(m).GetOnBits()), "heavy": m.GetNumHeavyAtoms()})
p = ROOT / "output" / "表述试跑313篇_2026-11-05" / "结构描述符图" / "v2" / "指纹.json"
p.write_text(json.dumps({"说明": "Morgan r=2, 2048 bits（RDKit）", "分子": out, "无结构式": bad}, ensure_ascii=False), encoding="utf-8")
print(len(out), "molecules;", len(bad), "without SMILES:", bad)
