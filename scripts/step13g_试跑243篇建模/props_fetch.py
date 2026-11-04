"""草稿：溶剂分子性质。PubChem 实验值（介电常数、动力黏度，15–30 °C）＋ RDKit Gasteiger 最负配位原子电荷（给电子能力的粗略近似）。"""
import json, re, sys, time, statistics, urllib.request, urllib.error
C, S = sys.argv[1], sys.argv[2]
comps = [c for c in json.load(open(f"{C}/组分表.json", encoding="utf-8")) if c["类别"] in ("溶剂", "溶剂/添加剂") and c.get("规范SMILES")]
cache = json.load(open(f"{C}/work/pubchem_cache.json", encoding="utf-8"))

def strings(cid, heading):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON?heading={urllib.request.quote(heading)}"
    for k in range(4):
        try:
            d = json.load(urllib.request.urlopen(url, timeout=40)); break
        except urllib.error.HTTPError:
            return []
        except Exception:
            time.sleep(1.5 * (k + 1))
    else:
        return None
    out = []
    def walk(x):
        if isinstance(x, dict):
            v = x.get("Value", {})
            if isinstance(v, dict):
                out.extend(s["String"] for s in v.get("StringWithMarkup", []))
                if "Number" in v: out.append(" ".join(map(str, v["Number"])) + " " + v.get("Unit", ""))
            for y in x.values(): walk(y)
        elif isinstance(x, list):
            for y in x: walk(y)
    walk(d); return out

def temp_ok(s):
    t = re.search(r"(-?\d+(?:\.\d+)?)\s*°\s*([CF])", s)
    if not t: return None
    tc = float(t.group(1)) if t.group(2) == "C" else (float(t.group(1)) - 32) * 5 / 9
    return 15 <= tc <= 30

def pick_eps(ss):
    room, loose = [], []
    for s in ss:
        m = re.search(r"(\d+(?:\.\d+)?)", s)
        if not m or not 1 <= float(m.group(1)) <= 200 or re.search(r"vapor|gas", s, re.I): continue
        ok = temp_ok(s)
        (room if ok else loose if ok is None else []).append(float(m.group(1)))
    v = room or loose
    return (round(statistics.median(v), 3), "15–30 °C" if room else "未注温度") if v else (None, "")

def pick_visc(ss):
    room, loose = [], []
    for s in ss:
        if re.search(r"mm2|mm\^2|cSt|centistoke|kinematic|vapor|gas", s, re.I): continue
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:cP|mPa|centipoise|mPa\s*[·.]?\s*s)", s, re.I)
        if not m or not 0.1 <= float(m.group(1)) <= 5000: continue
        ok = temp_ok(s)
        (room if ok else loose if ok is None else []).append(float(m.group(1)))
    v = room or loose
    return (round(statistics.median(v), 4), "15–30 °C" if room else "未注温度") if v else (None, "")

out = {}
for c in comps:
    cid = (cache.get(c.get("pubchem_query") or "") or {}).get("CID")
    rec = {"CID": cid, "SMILES": c["规范SMILES"]}
    if cid:
        oth = strings(cid, "Other Experimental Properties") or []
        e = [s for s in oth if re.search(r"dielectric const", s, re.I)]
        v = (strings(cid, "Viscosity") or []) + [s for s in oth if re.search(r"viscosity", s, re.I)]
        rec["介电常数"], rec["介电常数说明"] = pick_eps(e or [])
        rec["黏度cP"], rec["黏度说明"] = pick_visc(v or [])
        time.sleep(0.25)
    out[c["id"]] = rec
    print(c["id"], rec.get("介电常数"), rec.get("黏度cP"), flush=True)
json.dump(out, open(f"{S}/溶剂分子性质.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
