import json, sys
from rdkit import Chem
from rdkit.Chem import AllChem
S = sys.argv[1]
d = json.load(open(f"{S}/溶剂分子性质.json", encoding="utf-8"))
COORD = Chem.MolFromSmarts("[$([OX2]([#6;!$([#6]=O)])[#6;!$([#6]=O)]),$([OX1]=[#6,#16,#15]),$([NX1]#C)]")
for k, r in d.items():
    m = Chem.AddHs(Chem.MolFromSmiles(r["SMILES"]))
    AllChem.ComputeGasteigerCharges(m)
    idx = [t[0] for t in m.GetSubstructMatches(COORD)]
    qs = [m.GetAtomWithIdx(i).GetDoubleProp("_GasteigerCharge") for i in idx]
    r["最负配位原子电荷"] = round(min(qs), 4) if qs else None
json.dump(d, open(f"{S}/溶剂分子性质.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("电荷已算", sum(r["最负配位原子电荷"] is not None for r in d.values()), "/", len(d))
