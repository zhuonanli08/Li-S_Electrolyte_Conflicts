"""组分身份表（2026-10-31）：F 版独立测试集 30 篇的组分 → SMILES / InChIKey，方案 §5.8“组分收录与身份核实”。

只读 F 版冻结候选（papers/*/candidate.json 的 recipes[].components）和各篇 source.json，不改它们，不碰人工复核表。
分三步：
  collect  收集每条组分（论文号＋配方号＋原文写法）、所在配方的 system 及用途归类，并从本篇原文找出现该名字的原句；
  pubchem  对核定表里写了 pubchem_query（只用全称或 CAS，不用缩写）的组分查 PubChem，结果缓存；
  build    读 Claude 核定表（组分核定.json，AI 辅助、待用户确认），RDKit 规范化 SMILES、生成 InChIKey，
           与 PubChem 结果比对，按 InChIKey 去重，把每条组分映射到组分 ID 或未收录原因，检查覆盖并出复核记录。
运行：D:/anaconda/envs/rdkit/python.exe -X utf8 scripts/step12a_component_identity.py collect|pubchem|build
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "output" / "F版独立测试30篇_2026-10-29" / "papers"
OUT = ROOT / "output" / "组分结构表_F版30篇_2026-10-31"
WORK = OUT / "work"
CANDS = WORK / "候选组分.json"
CURATION = OUT / "组分核定.json"
PUBCHEM_CACHE = WORK / "pubchem_cache.json"

# 配方用途归类：方案 §5.8 按“是否实际配入液体”收录，role 字段不可靠，所以看 formulation 的 system 文字
MODEL_RE = re.compile(r"模型(?!电池)|DFT|\bMD\b|MD模|计算|模拟|理论|聚簇|络合物|轨道|孤立|连续介质|模拟盒|簇", re.I)
SOLID_RE = re.compile(r"干燥碳|非电解液|干态|参考固体|固体光谱|固体中间体|材料；")
CHAR_RE = re.compile(r"NMR|DMSO-d6|CDCl3", re.I)


def system_kind(system: str) -> str:
    if MODEL_RE.search(system):
        return "计算模型"
    if SOLID_RE.search(system):
        return "固体/材料"
    if CHAR_RE.search(system):
        return "表征测量液"
    return "液体"


def base_name(name: str) -> str:
    """去掉括号说明，留下原文写法的主体，用于在原文里找句子。"""
    return re.split(r"[（(]", name)[0].strip()


def find_snippets(sentences: list[dict], token: str, limit: int = 3) -> list[dict]:
    if not token or len(token) < 2:
        return []
    pat = re.compile(r"(?<![A-Za-z0-9])" + re.escape(token) + r"(?![A-Za-z0-9])", re.I)
    defin = re.compile(r"\(\s*" + re.escape(token) + r"\s*\)|" + re.escape(token) + r"\s*\(", re.I)
    hits = []
    for s in sentences:
        t = s.get("text", "")
        m = pat.search(t)
        if not m:
            continue
        a, b = max(0, m.start() - 160), min(len(t), m.end() + 160)
        hits.append({"id": s["id"], "part": s.get("part"), "定义式": bool(defin.search(t)),
                     "text": re.sub(r"\s+", " ", t[a:b])})
    hits.sort(key=lambda h: (not h["定义式"], h["part"] != "main"))
    return hits[:limit]


def collect() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    rows = []
    for cf in sorted(PAPERS.glob("*/candidate.json")):
        d = json.loads(cf.read_text(encoding="utf-8"))
        pid = d["paper_id"]
        src = json.loads((cf.parent / "source.json").read_text(encoding="utf-8"))
        used = defaultdict(list)
        for fm in d.get("formulations", []):
            used[fm["recipe_id"]].append((fm["id"], fm["system"]))
        snip_cache: dict[str, list] = {}
        for r in d.get("recipes", []):
            fms = used.get(r["id"], [])
            kinds = sorted({system_kind(s) for _, s in fms}) or ["未被配方引用"]
            for i, c in enumerate(r.get("components", [])):
                token = base_name(c["name"])
                if token not in snip_cache:
                    snip_cache[token] = find_snippets(src, token)
                rows.append({
                    "row_id": f"{pid}|{r['id']}|{i}", "paper_id": pid, "recipe_id": r["id"],
                    "name": c["name"], "role": c["role"], "amount": c["amount"], "unit": c["unit"],
                    "formulations": [f for f, _ in fms], "systems": [s for _, s in fms],
                    "用途": kinds, "原文片段": snip_cache[token],
                })
    CANDS.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    names = Counter(r["name"] for r in rows)
    papers = defaultdict(set)
    for r in rows:
        papers[r["name"]].add(r["paper_id"])
    print(f"组分条目 {len(rows)} 条，原文写法 {len(names)} 种，论文 {len({r['paper_id'] for r in rows})} 篇 → {CANDS}")
    print("用途归类：", Counter(k for r in rows for k in r["用途"]).most_common())


def pubchem() -> None:
    """只用核定表里的全称查 PubChem；已缓存的不重查。"""
    cur = json.loads(CURATION.read_text(encoding="utf-8"))
    cache = json.loads(PUBCHEM_CACHE.read_text(encoding="utf-8")) if PUBCHEM_CACHE.exists() else {}
    for c in cur["组分"]:
        q = c.get("pubchem_query")
        if not q or q in cache:
            continue
        # 一般只用全称；全称命中不规范记录时，核定表可写 CID:编号 直接核对规范记录
        path = f"cid/{q[4:]}" if q.startswith("CID:") else "name/" + urllib.parse.quote(q)
        url = ("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/" + path
               + "/property/MolecularFormula,IUPACName,InChIKey,SMILES/JSON")
        try:
            props = json.load(urllib.request.urlopen(url, timeout=30))["PropertyTable"]["Properties"]
            cache[q] = {"状态": "找到", "命中数": len(props), **props[0]}
        except urllib.error.HTTPError as e:
            cache[q] = {"状态": "未收录" if e.code == 404 else f"HTTP {e.code}"}
        except Exception as e:  # 网络错误不写缓存，下次重试
            print(f"  {q}: 查询失败 {e}")
            continue
        print(f"  {c['id']:<12} {q[:50]:<50} → {cache[q].get('状态')} {cache[q].get('InChIKey', '')}")
        time.sleep(0.3)
    PUBCHEM_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"PubChem 缓存 {len(cache)} 条 → {PUBCHEM_CACHE}")


LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "−": "-", "‐": "-", "–": "-"}


def norm_text(t: str) -> str:
    for a, b in LIGATURES.items():
        t = t.replace(a, b)
    t = re.sub(r"(?<=[a-z])-\s+(?=[a-z])", "", t)  # 断行连字符：tetrafluor- opropyl
    return re.sub(r"\s+", " ", t)


def first_hit(sentences: list[dict], pattern: str) -> dict | None:
    rx = re.compile(pattern, re.I)
    for s in sentences:
        m = rx.search(s["_norm"])
        if m:
            a, b = max(0, m.start() - 100), min(len(s["_norm"]), m.end() + 100)
            return {"id": s["id"], "text": s["_norm"][a:b]}
    return None


def lookup(table: dict, pid: str, name: str):
    return table.get((pid, name)) or table.get(("*", name))


def build() -> None:
    from rdkit import Chem, RDLogger
    from rdkit.Chem import Descriptors, rdMolDescriptors
    RDLogger.DisableLog("rdApp.*")

    rows = json.loads(CANDS.read_text(encoding="utf-8"))
    cur = json.loads(CURATION.read_text(encoding="utf-8"))
    cache = json.loads(PUBCHEM_CACHE.read_text(encoding="utf-8")) if PUBCHEM_CACHE.exists() else {}
    comps = {c["id"]: dict(c) for c in cur["组分"]}
    aliases = {(a["论文"], a["写法"]): a for a in cur["别名"]}
    excluded = {(e["论文"], e["写法"]): e for e in cur["未收录"]}
    errors = []

    # 1) RDKit 规范化，与 PubChem 比对，InChIKey 去重
    by_key = defaultdict(list)
    for c in comps.values():
        c["核验"] = []
        if not c.get("smiles"):
            c.update(规范SMILES=None, InChIKey=None, 分子式=None, 分子量=None, PubChem比对="无 SMILES")
            c["核验"].append("🔶 " + c["无SMILES原因"])
            continue
        mol = Chem.MolFromSmiles(c["smiles"])
        if mol is None:
            errors.append(f"{c['id']}: SMILES 无法解析 {c['smiles']}")
            continue
        c["规范SMILES"] = Chem.MolToSmiles(mol)
        c["InChIKey"] = Chem.MolToInchiKey(mol)
        c["分子式"] = rdMolDescriptors.CalcMolFormula(mol)
        c["分子量"] = round(Descriptors.MolWt(mol), 3)
        by_key[c["InChIKey"]].append(c["id"])
        q = c.get("pubchem_query")
        hit = cache.get(q) if q else None
        if not q:
            c["PubChem比对"] = "未查询（按化学式书写）"
            c["核验"].append("🔶 未用公共库核对，按化学式书写")
        elif not hit:
            c["PubChem比对"] = "未查询（缓存缺失）"
            c["核验"].append("🔶 PubChem 尚未查询")
        elif hit["状态"] != "找到":
            c["PubChem比对"] = f"PubChem {hit['状态']}"
            c["核验"].append(f"🔶 PubChem 按全称{hit['状态']}，结构以原文为准")
        elif hit["InChIKey"] == c["InChIKey"]:
            c["PubChem比对"] = f"一致（CID {hit['CID']}）"
        elif hit["InChIKey"][:14] == c["InChIKey"][:14]:
            c["PubChem比对"] = f"骨架一致、电荷/立体层不同（CID {hit['CID']}，{hit['InChIKey']}）"
            c["核验"].append("🔶 与 PubChem 骨架一致，电荷或立体层不同")
        else:
            c["PubChem比对"] = f"不一致（CID {hit['CID']} {hit.get('MolecularFormula')}，{hit['InChIKey']}）"
            c["核验"].append("⚠️ 与 PubChem 全称查询结果不一致")
        if c.get("说明"):
            c["核验"].append("🔶 " + c["说明"])
    for k, ids in by_key.items():
        if len(ids) > 1:
            errors.append(f"InChIKey 重复，应合并：{ids} {k}")

    # 2) 每条组分 → 组分 ID 或未收录原因；本篇原文核对全称
    src_cache: dict[str, list] = {}

    def sentences(pid: str) -> list[dict]:
        if pid not in src_cache:
            src = json.loads((PAPERS / pid / "source.json").read_text(encoding="utf-8"))
            for s in src:
                s["_norm"] = norm_text(s.get("text", ""))
            src_cache[pid] = src
        return src_cache[pid]

    row_map, unmapped = [], []
    groups = defaultdict(list)
    for r in rows:
        pid, name = r["paper_id"], r["name"]
        a, e = lookup(aliases, pid, name), lookup(excluded, pid, name)
        if a:
            row_map.append({"row_id": r["row_id"], "组分": a["组分"], "未收录原因": None})
            groups[(pid, name, "收录")].append(r)
        elif e:
            row_map.append({"row_id": r["row_id"], "组分": [], "未收录原因": e["原因"]})
            groups[(pid, name, "未收录")].append(r)
        else:
            unmapped.append(r["row_id"] + " " + name)

    alias_rows, excl_rows, side_notes = [], [], []
    for (pid, name, kind), rs in sorted(groups.items()):
        uses = sorted({k for r in rs for k in r["用途"]})
        roles = sorted({r["role"] for r in rs})
        base = {"论文": pid, "写法": name, "条数": len(rs), "配方": sorted({r["recipe_id"] for r in rs}),
                "用途": uses, "提取角色": roles}
        if kind == "未收录":
            excl_rows.append({**base, "原因": lookup(excluded, pid, name)["原因"]})
            continue
        a = lookup(aliases, pid, name)
        sents = sentences(pid)
        evid, marks = [], []
        name_hit = first_hit(sents, r"(?<![A-Za-z0-9])" + re.escape(norm_text(base_name(name))) + r"(?![A-Za-z0-9])")
        for cid in a["组分"]:
            h = first_hit(sents, comps[cid]["全称正则"])
            evid.append({"组分": cid, "全称原句": h})
            marks.append(bool(h))
        if all(marks):
            status = "✅"
        elif name_hit:
            status = "🔶"
        else:
            status = "❌"
        notes = []
        if not all(marks):
            notes.append("本篇原文未找到全称，按常用含义" if name_hit else "本篇原文找不到该写法")
        if len(a["组分"]) > 1:
            status = "🔶" if status == "✅" else status
            notes.append(a.get("说明", "一条写法对应多个组分"))
            side_notes.append(f"{pid}「{name}」：一条组分记录合并了 {len(a['组分'])} 种溶剂")
        elif a.get("说明"):
            status = "🔶" if status == "✅" else status
            notes.append(a["说明"])
        comp_flags = [f for cid in a["组分"] for f in comps[cid]["核验"]]
        if any(f.startswith("⚠️") for f in comp_flags):
            status = "⚠️"
        if "其他" in roles and comps[a["组分"][0]]["档"] == "A" and comps[a["组分"][0]]["类别"] in ("溶剂", "锂盐"):
            side_notes.append(f"{pid}「{name}」：A 档{comps[a['组分'][0]]['类别']}有记录的提取角色为“其他”")
        if status == "❌":
            side_notes.append(f"{pid}「{name}」：本篇原文找不到该写法")
        alias_rows.append({**base, "组分": a["组分"], "核验": status, "核验说明": "；".join(notes),
                           "原文写法句": name_hit, "全称核对": evid})

    lino3_roles = Counter(r["role"] for r in rows if lookup(aliases, r["paper_id"], r["name"])
                          and lookup(aliases, r["paper_id"], r["name"])["组分"] == ["LiNO3"])
    side_notes.append(f"LiNO₃ 的提取角色不统一：{dict(lino3_roles)}（按条计）")

    # 3) 组分层汇总：出现在哪些论文、哪些用途
    use = defaultdict(lambda: {"论文": set(), "用途": Counter(), "条数": 0})
    for ar in alias_rows:
        for cid in ar["组分"]:
            use[cid]["论文"].add(ar["论文"])
            use[cid]["条数"] += ar["条数"]
            for u in ar["用途"]:
                use[cid]["用途"][u] += 1
    comp_rows = []
    for cid, c in comps.items():
        u = use.get(cid)
        if not u:
            errors.append(f"{cid}: 核定表里有，但 30 篇里没有记录指向它")
            continue
        comp_rows.append({k: v for k, v in c.items() if k not in ("全称正则", "pubchem_query")}
                         | {"论文": sorted(u["论文"]), "论文数": len(u["论文"]), "条数": u["条数"],
                            "用途": dict(u["用途"]), "核验": "；".join(c["核验"]) or "✅",
                            "全称正则": c["全称正则"], "pubchem_query": c.get("pubchem_query")})

    cover = {"组分条目": len(rows), "已映射到组分": sum(1 for m in row_map if m["组分"]),
             "未收录（有原因）": sum(1 for m in row_map if m["未收录原因"]), "未映射": len(unmapped)}
    (OUT / "组分表.json").write_text(json.dumps(comp_rows, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "别名表.json").write_text(json.dumps(alias_rows, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "未收录.json").write_text(json.dumps(excl_rows, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "行映射.json").write_text(json.dumps({"覆盖": cover, "行": row_map}, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
    (OUT / "顺带发现的提取问题_复核完再看.json").write_text(json.dumps(
        {"说明": "建组分表时顺带看到的提取问题；为不影响人工复核，复核 30 篇完成后再看。AI 辅助，未经人工确认。",
         "问题": side_notes}, ensure_ascii=False, indent=1), encoding="utf-8")

    print("覆盖检查：", cover)
    print("组分：", Counter(c["档"] for c in comp_rows), " 别名核验：", Counter(a["核验"] for a in alias_rows))
    for c in comp_rows:
        if c["核验"] != "✅":
            print(f"  {c['id']:<12} {c['核验']}")
    for x in unmapped[:30]:
        print("  未映射：", x)
    for x in errors:
        print("  错误：", x)
    if unmapped or errors:
        sys.exit(1)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"collect": collect, "pubchem": pubchem, "build": build}.get(
        cmd, lambda: sys.exit("用法：collect|pubchem|build"))()
