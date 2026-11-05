"""配方挂接与单位换算（2026-10-31）：把 F 版 30 篇每个配方的组分挂到组分 ID，用量归类，能换算的换成统一量。

方案 §5.8、§8.7（分块表示）、§15.1。只读 step12a 收集的组分（来自 F 版 30 篇当前数据集）、行映射与组分表，不改它们。
分两步：
  density  液体组分的密度（10-31、11-01 用户定）：PubChem 实验值优先（只取 15–30 °C 的值，多个取中位数，记原文字符串）；
           查不到用原文报的值（组分核定.json 组分的“原文密度”）；再查不到用厂商目录值（“厂商密度”）；再没有就留空、
           不估算。两种来源都有时并排记录相差多少。结果缓存 work/density_cache.json。
  build    每个配方：组分 ID、原文用量与单位原样保留，单位归类（摩尔浓度/质量摩尔浓度/质量分数/体积份/摩尔比/
           分子数/未报告或不可用），能解析的给数值；真实液体配方（非计算模型）在输入齐全时换算出每种组分在
           “1 L 溶剂混合物”中的物质的量和摩尔分数，标 🧮，并写明用到的前提（盐浓度按每升溶剂近似、wt% 按总电解液质量等）。
           11-01 加配方级元素比例（方案 §8.7）：按 Kim 等 PNAS 2023 的定义，只算溶剂＋主盐（LiNO₃、添加剂、介体、
           B 档硫物种与离子不计入），原子计数用 step12b 的 element_counts；每次先用 Kim SI 的 3 个例子自检，不通过就停止。
输出 output/组分结构表_F版30篇_2026-10-31/：密度表.json、配方组成.json、配方组成表.xlsx。
运行：D:/anaconda/envs/rdkit/python.exe -X utf8 scripts/step12d_formulation_link.py density|build
"""
from __future__ import annotations

import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Descriptors

sys.path.insert(0, str(Path(__file__).resolve().parent))
from step12b_component_descriptors import element_counts  # noqa: E402  与描述符同一套原子计数和 α/β 定义

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("KETI2_COMP") or ROOT / "output" / "组分结构表_F版30篇_2026-10-31")  # 环境变量 KETI2_COMP 可改读写其他数据集（11-04 220 篇试跑），不设时同原值
WORK = OUT / "work"
DENSITY_CACHE = WORK / "density_cache.json"
VOLUME_UNIT = re.compile(r"体积|vol|v/v|volume", re.I)

# 配方级元素比例（方案 §8.7，11-01）：只算溶剂＋主盐。“溶剂/添加剂”（FEC、DMTS）按体积份或摩尔比给出（共溶剂用量）时
# 计入溶剂，按 wt%/M 少量加入时算添加剂；“锂盐/添加剂”（LiI）、LiNO₃、其他添加剂、介体、B 档不计入。
SOLVENT_CATS, CO_SOLVENT_CATS, SALT_CATS = {"溶剂"}, {"溶剂/添加剂"}, {"锂盐"}
CO_SOLVENT_UNITS = {"体积份", "摩尔比"}
RATIO_MAIN = ["sO", "sO_不含氟", "sO_β氟化醚", "sO_α氟化醚", "aC", "F/O", "InOr"]
RATIO_ARCHIVE = ["O", "aO", "C", "sC", "F", "sF", "aF", "F/C", "O/C"]
LITFSI, LIFSI = "O=S(=O)([N-]S(=O)(=O)C(F)(F)F)C(F)(F)F.[Li+]", "O=S(=O)(F)[N-]S(=O)(=O)F.[Li+]"
# 自检：Kim 等 SI 的 Supporting Note 与 sd01.xlsx Dataset 第 4、151 行（密度取 Kim 分子库值；Note 中 Kim 把 LiNO₃ 计为盐，
# 0.466 mol 与其 N、O 总数一致）。溶剂给每升克数，盐给 mol。11-01 已手工复算一致。
KIM_CHECK = [
    ("Supporting Note：1 M LiTFSI DOL-DME (1:1 vol) 3 wt% LiNO3",
     [("C1COCO1", 0.5 * 1060), ("COCCOC", 0.5 * 868)], [(LITFSI, 1.0), ("O=[N+]([O-])[O-].[Li+]", 0.466)],
     {"sC": 0.234}, 5e-4),
    ("Dataset 第 4 行：1 M LiPF6 EC-DMC (1:1 v) 2% VC",
     [("O=C1OCCO1", 660.0), ("COC(=O)OC", 535.0), ("O=C1OC=CO1", 27.0)], [("F[P-](F)(F)(F)(F)F.[Li+]", 1.0)],
     {"sO": 0.26315101, "aO": 0.0, "sF": 0.0, "aF": 0.03828263, "aC": 0.0, "F/O": 0.14547780, "InOr": 1.16972410,
      "O": 0.26315101, "C": 0.26315101, "sC": 0.26315101, "F": 0.03828263, "F/C": 0.14547780, "O/C": 1.0}, 2e-4),
    ("Dataset 第 151 行：1.2 M LiFSI F4DEE",
     [("FC(F)COCCOCC(F)F", 1240.0)], [(LIFSI, 1.2)],
     {"sO": 0.08389239, "aO": 0.03087348, "sF": 0.16778478, "aF": 0.01543674, "aC": 0.0, "F/O": 1.59648089,
      "InOr": 1.27600968, "O": 0.11476587, "C": 0.25167717, "sC": 0.25167717, "F": 0.18322152, "F/C": 0.72800215,
      "O/C": 0.45600430}, 2e-4),
]


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
        paper, sup = cur[cid].get("原文密度"), cur[cid].get("厂商密度")
        if val is not None:
            table[cid] = {"名称": c["名称"], "密度_g_mL": val, "来源": f"PubChem 实验值（CID {m.group(1)}；{note}）",
                          "原文字符串": used}
        elif paper:
            table[cid] = {"名称": c["名称"], "密度_g_mL": paper["值"], "来源": f"原文 {paper['依据']}", "原文字符串": [paper["原句"]]}
        elif sup:  # 11-01 用户同意：PubChem 和原文都没有时用厂商目录值
            table[cid] = {"名称": c["名称"], "密度_g_mL": sup["值"], "来源": f"厂商值：{sup['来源']}，{sup['条件']}",
                          "原文字符串": []}
        else:
            table[cid] = {"名称": c["名称"], "密度_g_mL": None,
                          "来源": "缺：" + ("PubChem " + hit["状态"] if hit else "PubChem 未收录") + "，原文和厂商都没有",
                          "原文字符串": []}
        if sup:  # 两种来源都有时并排记录，看差多少
            table[cid]["厂商值"] = {**sup, "与采用值相差": round((sup["值"] - table[cid]["密度_g_mL"]) /
                                                      table[cid]["密度_g_mL"] * 100, 2)}
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
    if re.search(r"未明示.{0,4}质量|质量\s*/\s*体积", u):  # 如“混合比例份数，原文未明示质量/体积基准”
        return "不可用", None, f"比例基准不明（{u}）"
    if re.search(r"vol|体积|v/v|volume", u, re.I) and not re.search(r"绝对", u):
        return "体积份", 1.0, ""
    if re.search(r"摩尔比|摩尔份", u):
        return "摩尔比", 1.0, ""
    return "不可用", None, u or "未写单位"


SOLVENT_DEFAULT = os.environ.get("KETI2_SOLVENT_DEFAULT") == "1"
DEFAULT_OK = re.compile(r"^(未写单位|比例基准不明.*|合写的两种溶剂，比例未写)$")


def solvent_defaults(items: list[dict], solvent_ids: set) -> tuple[list[dict], list[str]]:
    """11-05（方案 §7.2“按报告习惯近似”，带标记；KETI2_SOLVENT_DEFAULT=1 时用）：
    ① 溶剂用量有数值但未写单位或基准（如“DOL 1、DME 1”“1:1”未注 v/v）→ 按体积份（同 11-02 用户批准的 P315 口径）；
    ② 配方里只有一个溶剂且用量不明 → 占全部溶剂体积；③ 只有 DOL、DME 两个溶剂且比例都不明 → 1:1 体积。
    小写 m、基准不明的百分数、按硫原子计的浓度不套。返回 (新组分列表, 用到的默认值)。"""
    out, flags = [dict(i) for i in items], []
    sol = [i for i in out if i["组分"] in solvent_ids]
    if not any(i["单位类别"] == "不可用" for i in sol):
        return items, flags
    for i in sol:
        if i["单位类别"] == "不可用" and i.get("原始数值") is not None and DEFAULT_OK.match(i["说明"] or "未写单位"):
            i.update({"单位类别": "体积份", "数值": i["原始数值"], "说明": "默认：未写单位的溶剂比例按体积份（11-05）"})
            flags.append("溶剂比例未写单位按体积份")
    unk = [i for i in sol if i["单位类别"] == "不可用"]
    ids = {i["组分"] for i in sol}
    if unk and len(ids) == 1:
        for i in unk:
            i.update({"单位类别": "体积份", "数值": 1.0, "说明": "默认：唯一溶剂占全部体积（11-05）"})
        flags.append("唯一溶剂占全部体积")
    elif unk and ids == {"DOL", "DME"} and len(unk) == len(sol):
        for i in unk:
            i.update({"单位类别": "体积份", "数值": 1.0, "说明": "默认：DOL/DME 比例未写按 1:1 体积（11-05）"})
        flags.append("DOL/DME 比例未写按 1:1 体积")
    return out, sorted(set(flags))


def convert(items: list[dict], dens: dict, solvent_ids: set) -> dict:
    """真实液体配方：体积份 → 体积分数；有密度和分子量时算 1 L 溶剂混合物中各组分的物质的量（mol）与摩尔分数。"""
    pre, miss = [], []
    by_cat = lambda c: [i for i in items if i["单位类别"] == c]
    if items and all(i["单位类别"] == "摩尔比" and i["数值"] is not None for i in items):
        tot = sum(i["数值"] for i in items)
        return {"状态": "完整", "摩尔分数": {i["组分"]: i["数值"] / tot for i in items}, "缺": [], "前提": ["原文给摩尔比"]}
    sol = by_cat("体积份")
    phi = {}
    # 11-01 修：原文单位带 % 的（vol%）是占全部体积的百分数，其余是比例份数，两者不能直接相加（10-31 版把
    # “DME:DOL=1:1 加 10 vol% DMTS”算成 DMTS 10 份、占 83%）。vol% 先占掉对应体积，剩下的按份数分。
    pct = [i for i in sol if "%" in (i["原文单位"] or "")]
    parts = [i for i in sol if i not in pct]
    # 另有溶剂用量不明时，已知份数归一出的体积分数不对；添加剂（如 1 % PEA）用量不明不拦，与 LiNO₃ 缺用量同样处理
    unknown = [i["组分"] for i in items if i["单位类别"] == "不可用" and i["组分"] in solvent_ids]
    if sol and all(i["数值"] is not None for i in sol):
        sp = sum(i["数值"] for i in pct) / 100
        if unknown:
            miss += [f"{i['组分']} 体积分数无法归一（{'、'.join(unknown)} 用量不明）" for i in sol]
        elif pct and not parts and abs(sp - 1) > 0.01:
            miss += [f"{i['组分']} 体积百分数合计 {sp * 100:g}%，其余组分未记录" for i in sol]
        elif pct and parts and sp >= 1:
            miss += [f"{i['组分']} 体积百分数已达 {sp * 100:g}%，与比例份数冲突" for i in sol]
        elif pct and parts:
            tp = sum(i["数值"] for i in parts)
            phi = {**{i["组分"]: i["数值"] / 100 for i in pct}, **{i["组分"]: (1 - sp) * i["数值"] / tp for i in parts}}
            pre.append("vol% 按占全部溶剂体积计，其余体积按比例份数分")
        else:
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


def element_ratios(parts: list[tuple[dict, str, float]]) -> dict:
    """parts：(element_counts 结果, "s" 溶剂 / "a" 盐, 物质的量)。比例 = 该元素原子数 ÷ 全部原子数（含 H、Li）；
    盐中除 Li 外的原子记为阴离子部分；无机 = 除 C、H、Li 外的元素（Kim 等 Methods）。比例与总量无关，摩尔分数也可代入。"""
    s, a, li, fa, fb = Counter(), Counter(), 0.0, 0.0, 0.0
    for ec, role, n in parts:
        for el, k in ec["原子"].items():
            if el == "Li" and role == "a":
                li += k * n
            else:
                (s if role == "s" else a)[el] += k * n
        if role == "s":
            fa += ec["α氟化醚氧"] * n
            fb += ec["β氟化醚氧"] * n
    t = s + a
    tot = sum(t.values()) + li
    c, o, f = t["C"], t["O"], t["F"]
    inorg = sum(v for el, v in t.items() if el not in ("C", "H", "Li"))
    r = {"sO": s["O"] / tot, "sO_β氟化醚": fb / tot, "sO_α氟化醚": fa / tot, "aC": a["C"] / tot,
         "F/O": f / o if o else None, "InOr": inorg / c if c else None,
         "O": o / tot, "aO": a["O"] / tot, "C": c / tot, "sC": s["C"] / tot, "F": f / tot, "sF": s["F"] / tot,
         "aF": a["F"] / tot, "F/C": f / c if c else None, "O/C": o / c if c else None}
    r["sO_不含氟"] = r["sO"] - r["sO_β氟化醚"] - r["sO_α氟化醚"]
    return r


def kim_selfcheck() -> str:
    """用 Kim SI 的 3 个例子检查 element_ratios 与原子计数；不一致就停止，不出结果。"""
    for label, solvents, salts, expect, tol in KIM_CHECK:
        parts = [(element_counts(smi), "s", g / Descriptors.MolWt(Chem.MolFromSmiles(smi))) for smi, g in solvents]
        parts += [(element_counts(smi), "a", n) for smi, n in salts]
        got = element_ratios(parts)
        bad = {k: (round(got[k], 6), v) for k, v in expect.items() if abs(got[k] - v) > tol * max(1.0, abs(v))}
        if bad:
            sys.exit(f"Kim 自检不通过：{label} {bad}（算得, 原值）")
    return f"Kim 等 SI 自检 {len(KIM_CHECK)}/{len(KIM_CHECK)} 通过（Supporting Note 示例与数据集第 4、151 行）"


def recipe_ratios(rec: dict, comps: dict, counts) -> dict:
    """一个真实液体配方的配方级元素比例：判定哪些组分计入（溶剂＋主盐），用量取 1 L 溶剂中的物质的量，原文给摩尔比时取摩尔分数。"""
    units = {}
    for i in rec["组分"]:
        units.setdefault(i["组分"], set()).add(i["单位类别"])
    base, skipped, unclear = {}, {}, []
    for cid, us in units.items():
        c = comps[cid]
        if c["档"] != "A":
            skipped[cid] = "B 档（硫物种或单列离子）"
        elif c["类别"] in SOLVENT_CATS or (c["类别"] in CO_SOLVENT_CATS and us & CO_SOLVENT_UNITS):
            base[cid] = "s"
        elif c["类别"] in SALT_CATS:
            base[cid] = "a"
        elif c["类别"] in CO_SOLVENT_CATS and us <= {"不可用"}:
            skipped[cid] = c["类别"] + "（用量不明，无法判断是共溶剂还是添加剂）"
            unclear.append(cid)
        else:
            skipped[cid] = c["类别"] + ("（按 wt% 或 M 给出，按添加剂）" if c["类别"] in CO_SOLVENT_CATS else "")
    out = {"计入": {k: ("溶剂" if v == "s" else "主盐") for k, v in base.items()}, "未计入": skipped,
           "含主盐": "a" in base.values()}
    amt = rec.get("每升溶剂物质的量_mol") or {}
    if not all(k in amt for k in base) and all(k in rec.get("摩尔分数", {}) for k in base):
        amt = rec["摩尔分数"]
    if unclear:
        return {**out, "状态": "不可算", "原因": "、".join(unclear) + " 用量不明，无法判断是共溶剂还是添加剂"}
    if "s" not in base.values():
        return {**out, "状态": "不可算", "原因": "没有计入的溶剂（本配方记录只有：" + "、".join(units) + "）"}
    miss = [k for k in base if k not in amt]
    if miss:
        why = [m for m in rec.get("缺", []) if any(m.startswith(k + " ") for k in miss)]
        return {**out, "状态": "不可算", "原因": "；".join(why) or "用量缺：" + "、".join(miss)}
    ratios = element_ratios([(counts(cid), role, amt[cid]) for cid, role in base.items()])
    return {**out, "状态": "可算", "原因": "", "比例": ratios}


def build() -> None:
    check = kim_selfcheck()
    print(check)
    comps = {c["id"]: c for c in load("组分表.json")}
    dens = load("密度表.json")
    rows = load("work/候选组分.json")
    rmap = {m["row_id"]: m for m in load("行映射.json")["行"]}
    solvent_ids = {k for k, c in comps.items() if c["类别"] in SOLVENT_CATS | CO_SOLVENT_CATS}
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
                               "数值": None if v_i is None or factor_i is None else v_i * factor_i, "说明": note, "原始数值": v_i})
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
            flags = []
            if SOLVENT_DEFAULT:
                rec["组分"], flags = solvent_defaults(rec["组分"], solvent_ids)
            merged = {}
            for i in rec["组分"]:  # 同一配方里同一组分写了两次的合并
                if i["组分"] in merged and i["单位类别"] == merged[i["组分"]]["单位类别"] and i["数值"] is not None \
                        and merged[i["组分"]]["数值"] is not None:
                    merged[i["组分"]]["数值"] += i["数值"]
                else:
                    merged.setdefault(i["组分"], dict(i))
            conv = convert(list(merged.values()), dens, solvent_ids)
            if flags:
                conv["默认"] = flags
        out.append({"论文": pid, "配方": rid, "配方名": sorted(rec["配方名"]), "用途": sorted(rec["用途"]), "类型": kind,
                    "组分": rec["组分"], **conv})
    cache = {}

    def counts(cid):
        if cid not in cache:
            cache[cid] = element_counts(comps[cid]["规范SMILES"])
        return cache[cid]
    for r in out:
        if r["类型"] == "液体":
            r["元素比例"] = recipe_ratios(r, comps, counts)
            if r.get("默认"):
                r["元素比例"]["默认"] = r["默认"]  # 11-05：用了溶剂比例默认值的配方带标记，建模可分含/不含两版
    from step12e_reviewed_units import apply_review, add_review_sheet
    apply_review(out, comps, dens, convert, recipe_ratios, counts, solvent_ids)
    (OUT / "配方组成.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    write_xlsx(out, dens, check)
    add_review_sheet(OUT / "配方组成表.xlsx", out)
    print("配方", len(out), "：", Counter((r["类型"], r["状态"]) for r in out))
    print("缺项（按配方计）：", Counter(m for r in out for m in r["缺"]).most_common(12))
    er = [r["元素比例"] for r in out if "元素比例" in r]
    print("配方级元素比例（真实液体）：", Counter(e["状态"] for e in er), "；其中不含主盐",
          sum(1 for e in er if e["状态"] == "可算" and not e["含主盐"]), "个")
    print("不可算原因：", Counter(e["原因"] for e in er if e["状态"] == "不可算").most_common(8))
    print("未计入的组分（按配方计）：", Counter(f"{k}（{v}）" for e in er for k, v in e["未计入"].items()).most_common(12))


def write_xlsx(out: list[dict], dens: dict, check: str) -> None:
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
    cnt = Counter((r["类型"], r["状态"]) for r in out)
    er = Counter(r["元素比例"]["状态"] for r in out if "元素比例" in r)
    for line in [
        "配方组成表（F 版 30 篇，2026-10-31；11-01 加配方级元素比例）。全部为 AI 辅助，用户尚未逐项确认。",
        "与组分结构表的分工：组分结构表每个分子一行，记它是谁和只由结构决定的数字（描述符），与用量无关；本表每个配方一行，记用了哪些组分（用组分 ID 引用组分结构表）、各用多少、换算成统一的量，以及按用量加权得到的配方级元素比例。同一个分子出现在很多配方里，分子信息只在组分结构表记一次。",
        "用途：配方字段（组分、原文用量、统一后的量）用于记录、生成表述、判断一次比较改变了什么和指导实验配方；配方级元素比例是打分模型对溶剂＋主盐的输入（方案 §8.7）。原文用量和单位原样保留。",
        "统计：" + "；".join(f"{k[0]}·{k[1]} {v} 个" for k, v in sorted(cnt.items())) + "。",
        "单位归类：摩尔浓度（M、mol/L、mM，统一为 mol/L；mg/mL 按分子量换成 mol/L）、质量分数（wt%，统一为小数）、体积份（体积比、vol%、v/v、单一溶剂等）、摩尔比、分子数（计算模型盒子）、不可用（未报告、基准不明、比例冲突等）。原文小写 m 含义不明（mol/kg 或 Wiley 排版的 mol/L），按方案 §5.7 不换算；SI 明确写 M 的按 M。",
        "换算（🧮）：只对真实液体配方做。体积份 → 体积分数：vol% 按占全部溶剂体积计，同一配方里另有比例份数的（如 DME:DOL=1:1 加 10 vol% DMTS），剩下的体积再按份数分（DMTS 0.10、DME 0.45、DOL 0.45）；只写了百分数且合计不到 100% 的、另有溶剂用量不明的，不给体积分数（添加剂用量不明不影响）（11-01 修正，10-31 版把百分数和份数直接相加）。比例基准不明（原文未写是质量比还是体积比）的记不可用。有密度和分子量时，算出 1 L 溶剂混合物里每种组分的物质的量（mol），全部组分都算出来时再给摩尔分数。",
        "前提：摩尔浓度按每升溶剂近似（忽略盐和添加剂占的体积，原文写明按溶剂体积的除外）；质量分数按总电解液质量（原文写明按溶剂质量的除外）；盐按一个式量单元计（不拆成离子）。这些前提会让高浓度电解液的数值有偏差，比较时注意。",
        "密度（10-31、11-01 用户定）：PubChem 实验值优先，查不到用原文报的值，再查不到用厂商目录值（Sigma-Aldrich 等），再没有就留空、不估算。TTE、TEGDME、FEC 用厂商值；PPEO-CF₃、PXEO-CF₃ 是作者自合成，没有厂商值，仍缺，含它们的配方只能给体积分数。7 种常用溶剂 PubChem 值与厂商值相差都在 1% 以内，见“密度表”页。",
        "计算模型（MD/DFT 盒子）按分子个数直接给摩尔分数，和真实液体分开，不混在一起比较。",
        "配方级元素比例（11-01，“配方级元素比例”页）：按 Kim 等 PNAS 2023（10.1073/pnas.2214357120）的定义，把 1 L 电解液里溶剂＋主盐的全部原子（含 H、Li）数一遍，算各元素所占比例。原子数由组分结构表的 SMILES 自动计数（描述符页的 C、H、原子总数等列），用量取“每升溶剂物质的量”，原文给摩尔比的取摩尔分数（比例与总量无关）。",
        "进模型的 4 个：sO 溶剂带来的 O ÷ 全部原子（再分三档：不含氟、β 氟化醚氧、α 氟化醚氧，三档之和 = sO；醚氧按离它最近的 CF₂/CF₃ 分档，直接相连为 α，隔一个碳为 β）；aC 盐阴离子带来的 C ÷ 全部原子；F/O 全部 F ÷ 全部 O；InOr 除 C、H、Li 外的原子 ÷ C。其余 9 个（O、aO、C、sC、F、sF、aF、F/C、O/C）为 Kim 的其他特征，计算存档、暂不进模型。",
        "计入哪些组分：类别为“溶剂”的、类别为“锂盐”的计入；“溶剂/添加剂”（FEC、DMTS）在该配方里按体积份或摩尔比给出（共溶剂用量）时计入溶剂，按 wt% 或 M 少量加入时算添加剂（11-01 用户确认：5–10 wt% 一类少量加入算添加剂；写成与其他组分的比例、或按 vol% 给出的（含 10 vol%）算共溶剂）。LiNO₃（按添加剂，方案 §5.8）、其他添加剂、介体、LiI 等“锂盐/添加剂”、B 档硫物种与单列离子不计入，它们只按身份与用量记录（少量组分按组成加权会被稀释，方案 §8.7）。计入的组分有一个缺用量就整条不算，原因写在“不可算原因”列；“溶剂/添加剂”用量不明时判断不了角色，也不算。局限：共溶剂量级却按 wt% 给出的“溶剂/添加剂”会被当成添加剂（本批只有 P034 R_ST 的 20 wt% DMTS，该记录本身缺其他组分）。“含主盐”为否的是不含锂盐的液体（物性测量液等），分析时按需筛选。",
        f"统计（真实液体）：" + "；".join(f"{k} {v} 个" for k, v in sorted(er.items())) + f"。{check}。",
    ]:
        ws.append([line])
        ws.cell(ws.max_row, 1).alignment = wrap
    ws.column_dimensions["A"].width = 130

    sheet(wb, "配方汇总", ["论文", "配方", "配方名", "类型", "用途", "组分", "换算状态", "摩尔分数🧮", "缺什么", "前提"],
          [[r["论文"], r["配方"], "、".join(r["配方名"]), r["类型"], "、".join(r["用途"]),
            "、".join(dict.fromkeys(i["组分"] for i in r["组分"])), r["状态"],
            "；".join(f"{k} {pct(v)}" for k, v in r.get("摩尔分数", {}).items()), "；".join(r["缺"]), "；".join(r["前提"])]
           for r in out], {3: 24, 6: 30, 8: 50, 9: 40, 10: 40})

    f4 = lambda x: None if x is None else round(x, 4)
    names = {"sO": "sO 溶剂氧", "sO_不含氟": "其中 不含氟", "sO_β氟化醚": "其中 β氟化醚氧", "sO_α氟化醚": "其中 α氟化醚氧",
             "aC": "aC 阴离子碳", "F/O": "F/O", "InOr": "InOr 无机/有机"}
    sheet(wb, "配方级元素比例",
          ["论文", "配方", "配方名", "状态", "含主盐", "计入的溶剂", "计入的主盐", "未计入（原因）",
           *[names[k] for k in RATIO_MAIN], *[f"存档 {k}" for k in RATIO_ARCHIVE], "不可算原因"],
          [[r["论文"], r["配方"], "、".join(r["配方名"]), e["状态"], "是" if e["含主盐"] else "否",
            "、".join(k for k, v in e["计入"].items() if v == "溶剂"), "、".join(k for k, v in e["计入"].items() if v == "主盐"),
            "；".join(f"{k}（{v}）" for k, v in e["未计入"].items()),
            *[f4(e.get("比例", {}).get(k)) for k in RATIO_MAIN], *[f4(e.get("比例", {}).get(k)) for k in RATIO_ARCHIVE],
            e["原因"]] for r in out if (e := r.get("元素比例"))],
          {3: 20, 6: 22, 7: 14, 8: 40, 25: 40})

    sheet(wb, "配方组分", ["论文", "配方", "组分ID", "名称", "档", "原文写法", "原文用量", "原文单位", "单位类别", "统一后的值",
                       "体积分数🧮", "每升溶剂物质的量 mol🧮", "摩尔分数🧮", "说明"],
          [[r["论文"], r["配方"], i["组分"], i["名称"], i["档"], i["原文写法"], i["原文用量"], i["原文单位"], i["单位类别"],
            i["数值"], r.get("体积分数", {}).get(i["组分"]), r.get("每升溶剂物质的量_mol", {}).get(i["组分"]),
            r.get("摩尔分数", {}).get(i["组分"]), i["说明"]] for r in out for i in r["组分"]],
          {4: 18, 6: 22, 7: 22, 8: 22, 14: 30})

    sheet(wb, "密度表", ["组分ID", "名称", "采用密度 g/mL", "来源", "PubChem 原文", "厂商值 g/mL", "厂商来源与链接",
                       "厂商值与采用值相差 %"],
          [[k, d["名称"], d["密度_g_mL"], d["来源"], "｜".join(d["原文字符串"]),
            (d.get("厂商值") or {}).get("值"),
            "；".join(filter(None, [(d.get("厂商值") or {}).get(x) for x in ("来源", "条件", "链接", "说明")])),
            (d.get("厂商值") or {}).get("与采用值相差")] for k, d in dens.items()],
          {2: 22, 4: 40, 5: 60, 7: 70})
    wb.save(OUT / "配方组成表.xlsx")


if __name__ == "__main__":
    {"density": density, "build": build}[sys.argv[1]]()
