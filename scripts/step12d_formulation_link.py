"""配方挂接与单位换算（2026-10-31）：把 F 版 30 篇每个配方的组分挂到组分 ID，用量归类，能换算的换成统一量。

方案 §5.8、§8.7（分块表示）、§15.1。只读 F 版冻结候选 recipes/formulations、step12a 的行映射与组分表，不改它们。
分两步：
  density  液体组分的密度（10-31 用户定）：PubChem 实验值优先（只取 15–30 °C 的值，多个取中位数，记原文字符串）；
           查不到用原文报的值（组分核定.json 组分的“原文密度”）；再没有就留空、不估算。结果缓存 work/density_cache.json。
  build    每个配方：组分 ID、原文用量与单位原样保留，单位归类（摩尔浓度/质量摩尔浓度/质量分数/体积份/摩尔比/
           分子数/未报告或不可用），能解析的给数值；真实液体配方（非计算模型）在输入齐全时换算出每种组分在
           “1 L 溶剂混合物”中的物质的量和摩尔分数，标 🧮，并写明用到的前提（盐浓度按每升溶剂近似、wt% 按总电解液质量等）。
输出 output/组分结构表_F版30篇_2026-10-31/：密度表.json、配方组成.json、配方组成表.xlsx。
运行：D:/anaconda/envs/rdkit/python.exe -X utf8 scripts/step12d_formulation_link.py density|build
"""
from __future__ import annotations

import json
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "output" / "F版独立测试30篇_2026-10-29" / "papers"
OUT = ROOT / "output" / "组分结构表_F版30篇_2026-10-31"
WORK = OUT / "work"
DENSITY_CACHE = WORK / "density_cache.json"
VOLUME_UNIT = re.compile(r"体积|vol|v/v|volume", re.I)


def load(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def pubchem_density_strings(cid: str) -> dict:
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON?heading=Density"
    for k in range(4):
        try:
            d = json.load(urllib.request.urlopen(url, timeout=40))
            break
        except urllib.error.HTTPError as e:
            return {"状态": "无密度数据" if e.code == 404 else f"HTTP {e.code}"}
        except Exception:
            time.sleep(1.5 * (k + 1))
    else:
        return {"状态": "网络失败"}
    out = []

    def walk(x):
        if isinstance(x, dict):
            v = x.get("Value", {})
            if isinstance(v, dict):
                out.extend(s["String"] for s in v.get("StringWithMarkup", []))
                if "Number" in v:
                    out.append(" ".join(str(n) for n in v["Number"]) + " " + v.get("Unit", ""))
            for y in x.values():
                walk(y)
        elif isinstance(x, list):
            for y in x:
                walk(y)
    walk(d)
    return {"状态": "找到", "原文": out}


def pick_density(strings: list[str]):
    """依次取：① 15–30 °C、至少 3 位小数的值（°F 换算），多个取中位数；② 其他温度中最接近 25 °C 的值（如 EC 常温为固体，
    只有 39–40 °C 液体值）；③ 未注温度的范围取中值（如“0.765-0.775”）或相对密度（水=1）。排除空气/蒸气/松装密度。
    返回（值，用到的原文字符串，说明）。"""
    room, other, loose = [], [], []
    for s in strings:
        if re.search(r"lb|vapo|bulk|gas|\bair\b", s, re.I):
            continue
        rng = re.fullmatch(r"\s*(\d\.\d+)\s*-\s*(\d\.\d+)\s*", s)
        if rng:
            loose.append(((float(rng.group(1)) + float(rng.group(2))) / 2, s, "范围中值，未注温度"))
            continue
        m = re.search(r"(\d+\.(\d+))", s)
        if not m or not 0.5 < float(m.group(1)) < 2.5:
            continue
        val, decimals = float(m.group(1)), len(m.group(2))
        t = re.search(r"(-?\d+(?:\.\d+)?)\s*°\s*([CF])", s)
        if t:
            tc = float(t.group(1)) if t.group(2) == "C" else (float(t.group(1)) - 32) * 5 / 9
            if 15 <= tc <= 30 and decimals >= 3:
                room.append((val, s))
            elif 0 <= tc <= 60:
                other.append((abs(tc - 25), val, s, f"{tc:.0f} °C 下的值"))
        elif re.search(r"relative density", s, re.I):
            loose.append((val, s, "相对密度（水=1）"))
    if room:
        return round(statistics.median(v for v, _ in room), 4), [s for _, s in room], "15–30 °C 实验值"
    if other:
        _, val, s, note = min(other)
        return val, [s], note
    if loose:
        val, s, note = loose[0]
        return round(val, 4), [s], note
    return None, [], ""


def density() -> None:
    comps = {c["id"]: c for c in load("组分表.json")}
    cur = {c["id"]: c for c in json.loads((OUT / "组分核定.json").read_text(encoding="utf-8"))["组分"]}
    rows = load("work/候选组分.json")
    rmap = {m["row_id"]: m for m in load("行映射.json")["行"]}
    liquid = sorted({cid for r in rows if VOLUME_UNIT.search(r.get("unit", "") or "")  # 按体积配的液体（盐除外）
                     for cid in (rmap.get(r["row_id"]) or {}).get("组分", [])
                     if comps[cid]["档"] == "A" and "盐" not in comps[cid]["类别"]}
                    | {cid for cid, c in comps.items() if c["档"] == "A" and "溶剂" in c["类别"]})
    cache = json.loads(DENSITY_CACHE.read_text(encoding="utf-8")) if DENSITY_CACHE.exists() else {}
    table = {}
    for cid in liquid:
        c = comps[cid]
        m = re.search(r"CID (\d+)", c.get("PubChem比对") or "")
        if m and (m.group(1) not in cache or cache[m.group(1)]["状态"] == "网络失败"):
            cache[m.group(1)] = pubchem_density_strings(m.group(1))
            time.sleep(0.4)
        hit = cache.get(m.group(1)) if m else None
        val, used, note = pick_density(hit.get("原文", [])) if hit and hit["状态"] == "找到" else (None, [], "")
        paper = cur[cid].get("原文密度")
        if val is not None:
            table[cid] = {"名称": c["名称"], "密度_g_mL": val, "来源": f"PubChem 实验值（CID {m.group(1)}；{note}）",
                          "原文字符串": used}
        elif paper:
            table[cid] = {"名称": c["名称"], "密度_g_mL": paper["值"], "来源": f"原文 {paper['依据']}", "原文字符串": [paper["原句"]]}
        else:
            table[cid] = {"名称": c["名称"], "密度_g_mL": None,
                          "来源": "缺：" + ("PubChem " + hit["状态"] if hit else "PubChem 未收录") + "，原文也未找到",
                          "原文字符串": []}
    DENSITY_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "密度表.json").write_text(json.dumps(table, ensure_ascii=False, indent=1), encoding="utf-8")
    for cid, d in table.items():
        print(f"{cid:<12} {d['密度_g_mL']!s:<8} {d['来源']}  {'｜'.join(d['原文字符串'])[:90]}")
    if any(d["来源"].startswith("缺：PubChem 网络失败") for d in table.values()):
        sys.exit("有网络失败的，重跑 density 补齐")


NUM = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:$|[（(\s])")
SCI = re.compile(r"(\d+(?:\.\d+)?)\s*[×x]\s*10\s*[-−]\s*(\d+)")
PAIR = re.compile(r"(\d+(?:\.\d+)?)\s*[:：/]\s*(\d+(?:\.\d+)?)")
SOLE = r"(唯一|单一|全部|纯)(液体)?溶剂"
MG_ML = re.compile(r"(\d+(?:\.\d+)?)\s*mg\s*/\s*(\d+(?:\.\d+)?)?\s*mL")


def parse_amount(a: str):
    a = (a or "").strip()
    if m := SCI.search(a):
        return float(m.group(1)) * 10 ** -int(m.group(2))
    if m := NUM.match(a):
        return float(m.group(1))
    if re.fullmatch(SOLE, a):
        return 1.0
    if m := re.match(r"与.{1,12}?为\s*(\d+(?:\.\d+)?)\s*[:：]", a):  # “与DOL为1:1”：本组分占前一份
        return float(m.group(1))
    return None


def classify(unit: str, amount: str):
    """单位归类 → (类别, 换算到统一单位的系数, 说明)。统一单位：摩尔浓度 mol/L、质量分数（小数）、
    体积份、摩尔比、分子数。归不进的记“不可用”，原文单位留在说明里。"""
    u = (unit or "").strip()
    if re.fullmatch(SOLE, (amount or "").strip()):
        return "体积份", 1.0, "原文为唯一溶剂"
    if MG_ML.search(f"{amount} {unit}") or re.search(r"mg\s*/\s*\d*\s*mL", u):
        return "质量浓度", None, "mg/mL，按分子量换成 mol/L"
    if re.search(r"分子|粒子|式量单元|^离子|^模型", u):
        return "分子数", 1.0, ""
    if re.search(r"mol\s?S", u):
        return "不可用", None, f"按硫原子计的浓度（{u}）"
    if re.match(r"mM", u):
        return "摩尔浓度", 1e-3, u[2:].strip("（）()，,；; ")
    if re.match(r"M(?![a-z])|mol\s?L|mol/L", u):
        note = re.sub(r"^(M|mol\s?L−1|mol\s?L-1|mol/L)", "", u).strip("（）()，,；; ")
        if re.search(r"主文记m|正文写m|\bm\b", u):
            note = "原文 M 与 m 写法不一致，按 M；" + note
        return "摩尔浓度", 1.0, note
    if re.match(r"m(?![a-zA-Z])", u) and re.search(r"SI\s*写\s*M|m?M（SI）", u):  # 主文小写 m、SI 明确写 M
        return "摩尔浓度", 1.0, "主文写 m、SI 写 M（同篇同一写法按 M）"
    if re.match(r"m(?![a-zA-Z])", u):  # 方案 §5.7：小写 m 可能是 mol/kg，也可能是 Wiley 排版的 mol/L，不换算
        return "不可用", None, "小写 m 含义不明（mol/kg 或 Wiley 排版的 mol/L），按方案规则不换算"
    if re.search(r"wt\.?\s?%", u):
        return "质量分数", 0.01, ("按溶剂质量" if "溶剂质量" in u else
                                  "按总电解液质量（原文未明示分母，按惯例）" if re.search(r"未", u) else "按总电解液质量")
    if re.match(r"%", u):
        return "不可用", None, f"百分比基准不明（{u}）"
    if re.search(r"vol|体积|v/v|volume", u, re.I) and not re.search(r"绝对", u):
        return "体积份", 1.0, ""
    if re.search(r"摩尔比|摩尔份", u):
        return "摩尔比", 1.0, ""
    return "不可用", None, u or "未写单位"


def convert(items: list[dict], dens: dict) -> dict:
    """真实液体配方：体积份 → 体积分数；有密度和分子量时算 1 L 溶剂混合物中各组分的物质的量（mol）与摩尔分数。"""
    pre, miss = [], []
    by_cat = lambda c: [i for i in items if i["单位类别"] == c]
    if items and all(i["单位类别"] == "摩尔比" and i["数值"] is not None for i in items):
        tot = sum(i["数值"] for i in items)
        return {"状态": "完整", "摩尔分数": {i["组分"]: i["数值"] / tot for i in items}, "缺": [], "前提": ["原文给摩尔比"]}
    sol = by_cat("体积份")
    phi = {}
    if sol and all(i["数值"] is not None for i in sol):
        tot = sum(i["数值"] for i in sol)
        phi = {i["组分"]: i["数值"] / tot for i in sol}
    elif sol:
        miss.append("溶剂体积比未报告")
    n, mass = {}, 0.0
    for i in sol:
        rho = dens.get(i["组分"], {}).get("密度_g_mL")
        if i["组分"] not in phi:
            continue
        if rho is None or not i["分子量"]:
            miss.append(f"{i['组分']} 缺密度")
            continue
        n[i["组分"]] = phi[i["组分"]] * rho * 1000 / i["分子量"]
        mass += phi[i["组分"]] * rho * 1000
    solvent_ok = bool(sol) and len(n) == len(sol)
    if not sol:
        miss.append("没有按体积给出的溶剂")
    for i in by_cat("摩尔浓度"):
        if i["数值"] is None or not i["分子量"]:
            miss.append(f"{i['组分']} 浓度或分子量缺")
            continue
        n[i["组分"]] = n.get(i["组分"], 0) + i["数值"]
        if "按溶剂体积" not in i["说明"]:
            pre.append("摩尔浓度按每升溶剂近似（忽略盐和添加剂的体积）")
    for i in by_cat("质量摩尔浓度"):
        if i["数值"] is None or not i["分子量"] or not solvent_ok:
            miss.append(f"{i['组分']} 质量摩尔浓度缺溶剂质量")
            continue
        n[i["组分"]] = n.get(i["组分"], 0) + i["数值"] * mass / 1000
    wts = by_cat("质量分数")
    if wts:
        if not solvent_ok or any(i["数值"] is None or not i["分子量"] for i in wts):
            miss += [f"{i['组分']} 质量分数缺分母或数值" for i in wts]
        else:
            base = mass + sum(n[k] * next(i["分子量"] for i in items if i["组分"] == k)
                              for k in n if k not in {j["组分"] for j in sol})
            tw = sum(i["数值"] for i in wts if "溶剂质量" not in i["说明"])
            total = base / (1 - tw) if tw < 1 else None
            for i in wts:
                denom = mass if "溶剂质量" in i["说明"] else total
                n[i["组分"]] = n.get(i["组分"], 0) + i["数值"] * denom / i["分子量"]
            pre.append("质量分数按总电解液质量（原文写明按溶剂质量的除外）")
    for i in items:
        if i["单位类别"] in ("不可用", "分子数", "摩尔比"):
            miss.append(f"{i['组分']} 用量不可换算（{i['说明'] or i['单位类别']}）")
    complete = not miss and n and len(n) == len({i["组分"] for i in items})
    out = {"状态": "完整" if complete else ("部分" if phi or n else "不可换算"), "体积分数": phi,
           "每升溶剂物质的量_mol": n, "缺": sorted(set(miss)), "前提": sorted(set(pre))}
    if complete:
        tot = sum(n.values())
        out["摩尔分数"] = {k: v / tot for k, v in n.items()}
    return out


def build() -> None:
    comps = {c["id"]: c for c in load("组分表.json")}
    dens = load("密度表.json")
    rows = load("work/候选组分.json")
    rmap = {m["row_id"]: m for m in load("行映射.json")["行"]}
    recipes = {}
    for r in rows:
        m = rmap[r["row_id"]]
        rec = recipes.setdefault((r["paper_id"], r["recipe_id"]), {"论文": r["paper_id"], "配方": r["recipe_id"],
                                                                   "配方名": set(), "用途": set(), "组分": []})
        rec["配方名"].update(r.get("formulations") or [])
        rec["用途"].update(r.get("用途") or [])
        if not m["组分"]:
            continue
        cat, factor, note = classify(r["unit"], r["amount"])
        val = parse_amount(r["amount"])
        parts = [val] * len(m["组分"])
        if len(m["组分"]) == 2:  # 合写的两种溶剂（如“DME/DOL”）：用量写成 a:b 时拆开，否则不可用
            p = PAIR.search(r["amount"] or "") or PAIR.search(r["unit"] or "")
            parts = [float(p.group(1)), float(p.group(2))] if p else [None, None]
            if p is None:
                cat, note = "不可用", "合写的两种溶剂，比例未写"
        for cid, v in zip(m["组分"], parts):
            c = comps[cid]
            cat_i, factor_i, v_i = cat, factor, v
            if cat == "质量浓度":  # “8 mg/2 mL 电解液”“10 mg / 2.5 mL”：mg/mL = g/L，除以分子量得 mol/L
                mm = MG_ML.search(f"{r['amount']} {r['unit']}")
                mg = float(mm.group(1)) if mm else parse_amount(r["amount"])
                vol = float(mm.group(2)) if mm and mm.group(2) else 1.0
                ok = mg is not None and c.get("分子量")
                cat_i, factor_i, v_i = ("摩尔浓度", 1.0, mg / vol / c["分子量"]) if ok else ("不可用", None, None)
            rec["组分"].append({"组分": cid, "名称": c["名称"], "档": c["档"], "分子量": c.get("分子量"),
                               "原文写法": r["name"], "原文用量": r["amount"], "原文单位": r["unit"], "单位类别": cat_i,
                               "数值": None if v_i is None or factor_i is None else v_i * factor_i, "说明": note})
    out = []
    for (pid, rid), rec in sorted(recipes.items()):
        if not rec["组分"]:
            continue
        kind = "计算模型" if (rec["用途"] <= {"计算模型"} or all(i["单位类别"] == "分子数" for i in rec["组分"])) else "液体"
        if kind == "计算模型":
            items = rec["组分"]
            ok = items and all(i["单位类别"] == "分子数" and i["数值"] is not None for i in items)
            tot = sum(i["数值"] for i in items) if ok else 0
            conv = {"状态": "完整（计算模型盒子组成）" if ok else "不换算（计算模型）",
                    "摩尔分数": {i["组分"]: i["数值"] / tot for i in items} if ok else {}, "缺": [], "前提": []}
        else:
            merged = {}
            for i in rec["组分"]:  # 同一配方里同一组分写了两次的合并
                if i["组分"] in merged and i["单位类别"] == merged[i["组分"]]["单位类别"] and i["数值"] is not None \
                        and merged[i["组分"]]["数值"] is not None:
                    merged[i["组分"]]["数值"] += i["数值"]
                else:
                    merged.setdefault(i["组分"], dict(i))
            conv = convert(list(merged.values()), dens)
        out.append({"论文": pid, "配方": rid, "配方名": sorted(rec["配方名"]), "用途": sorted(rec["用途"]), "类型": kind,
                    "组分": rec["组分"], **conv})
    (OUT / "配方组成.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    write_xlsx(out, dens)
    from collections import Counter
    print("配方", len(out), "：", Counter((r["类型"], r["状态"]) for r in out))
    print("缺项（按配方计）：", Counter(m for r in out for m in r["缺"]).most_common(12))


def write_xlsx(out: list[dict], dens: dict) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    head, fill, wrap = Font(bold=True), PatternFill("solid", fgColor="DDEBF7"), Alignment(wrap_text=True, vertical="top")

    def sheet(wb, title, header, rows, widths):
        ws = wb.create_sheet(title)
        ws.append(header)
        for c in ws[1]:
            c.font, c.fill = head, fill
        for r in rows:
            ws.append(r)
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = wrap
        ws.freeze_panes = "C2"
        for i in range(1, len(header) + 1):
            ws.column_dimensions[ws.cell(1, i).column_letter].width = widths.get(i, 12)

    pct = lambda x: f"{x:.3f}"
    wb = Workbook()
    ws = wb.active
    ws.title = "说明"
    from collections import Counter
    cnt = Counter((r["类型"], r["状态"]) for r in out)
    for line in [
        "配方组成表（F 版 30 篇，2026-10-31）。全部为 AI 辅助，用户尚未逐项确认。",
        "用途：把每个配方的组分挂到组分结构表的组分 ID，用量换成统一的量，后面按“分块表示”（方案 §8.7）比较配方。原文用量和单位原样保留。",
        "统计：" + "；".join(f"{k[0]}·{k[1]} {v} 个" for k, v in sorted(cnt.items())) + "。",
        "单位归类：摩尔浓度（M、mol/L、mM，统一为 mol/L；mg/mL 按分子量换成 mol/L）、质量分数（wt%，统一为小数）、体积份（体积比、vol%、v/v、单一溶剂等）、摩尔比、分子数（计算模型盒子）、不可用（未报告、基准不明、比例冲突等）。原文小写 m 含义不明（mol/kg 或 Wiley 排版的 mol/L），按方案 §5.7 不换算；SI 明确写 M 的按 M。",
        "换算（🧮）：只对真实液体配方做。体积份 → 体积分数；有密度和分子量时，算出 1 L 溶剂混合物里每种组分的物质的量（mol），全部组分都算出来时再给摩尔分数。",
        "前提：摩尔浓度按每升溶剂近似（忽略盐和添加剂占的体积，原文写明按溶剂体积的除外）；质量分数按总电解液质量（原文写明按溶剂质量的除外）；盐按一个式量单元计（不拆成离子）。这些前提会让高浓度电解液的数值有偏差，比较时注意。",
        "密度（10-31 用户定）：PubChem 实验值优先，查不到用原文报的值，再没有就留空、不估算。TTE、TEGDME、FEC、PPEO-CF₃、PXEO-CF₃ 目前缺密度，含它们的配方只能给体积分数，见“密度表”页。",
        "计算模型（MD/DFT 盒子）按分子个数直接给摩尔分数，和真实液体分开，不混在一起比较。",
    ]:
        ws.append([line])
        ws.cell(ws.max_row, 1).alignment = wrap
    ws.column_dimensions["A"].width = 130

    sheet(wb, "配方汇总", ["论文", "配方", "配方名", "类型", "用途", "组分", "换算状态", "摩尔分数🧮", "缺什么", "前提"],
          [[r["论文"], r["配方"], "、".join(r["配方名"]), r["类型"], "、".join(r["用途"]),
            "、".join(dict.fromkeys(i["组分"] for i in r["组分"])), r["状态"],
            "；".join(f"{k} {pct(v)}" for k, v in r.get("摩尔分数", {}).items()), "；".join(r["缺"]), "；".join(r["前提"])]
           for r in out], {3: 24, 6: 30, 8: 50, 9: 40, 10: 40})

    sheet(wb, "配方组分", ["论文", "配方", "组分ID", "名称", "档", "原文写法", "原文用量", "原文单位", "单位类别", "统一后的值",
                       "体积分数🧮", "每升溶剂物质的量 mol🧮", "摩尔分数🧮", "说明"],
          [[r["论文"], r["配方"], i["组分"], i["名称"], i["档"], i["原文写法"], i["原文用量"], i["原文单位"], i["单位类别"],
            i["数值"], r.get("体积分数", {}).get(i["组分"]), r.get("每升溶剂物质的量_mol", {}).get(i["组分"]),
            r.get("摩尔分数", {}).get(i["组分"]), i["说明"]] for r in out for i in r["组分"]],
          {4: 18, 6: 22, 7: 22, 8: 22, 14: 30})

    sheet(wb, "密度表", ["组分ID", "名称", "密度 g/mL", "来源", "PubChem 原文"],
          [[k, d["名称"], d["密度_g_mL"], d["来源"], "｜".join(d["原文字符串"])] for k, d in dens.items()],
          {2: 22, 4: 40, 5: 80})
    wb.save(OUT / "配方组成表.xlsx")


if __name__ == "__main__":
    {"density": density, "build": build}[sys.argv[1]]()
