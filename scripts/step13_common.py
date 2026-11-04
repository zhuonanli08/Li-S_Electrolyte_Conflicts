"""step13 系列共用：路径、读数据、数值解析、写 Excel。

只读：规则处理版 30 篇（candidate.json / source.json）、组分结构表（配方组成.json 等）。
所有结果写到 OUT（新文件夹），不改任何已有文件。
运行环境：D:\\anaconda\\envs\\papertrail\\python.exe
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
DATA = ROOT / "output" / "F版30篇_规则处理版_2026-11-01" / "papers"
COMP = ROOT / "output" / "组分结构表_F版30篇_2026-10-31"
OUT = ROOT / "output" / "表述与矛盾试跑_F版30篇_2026-11-04"
OUT.mkdir(parents=True, exist_ok=True)

LABEL = "初步，30 篇（F 版规则处理版）"


def load_papers() -> dict[str, dict]:
    return {p.name: json.loads((p / "candidate.json").read_text(encoding="utf-8"))
            for p in sorted(DATA.iterdir()) if (p / "candidate.json").exists()}


def load_sources() -> dict[str, dict[str, dict]]:
    out = {}
    for p in sorted(DATA.iterdir()):
        f = p / "source.json"
        if f.exists():
            out[p.name] = {s["id"]: s for s in json.loads(f.read_text(encoding="utf-8"))}
    return out


def read_json(name: str, base: Path = OUT):
    return json.loads((base / name).read_text(encoding="utf-8"))


def write_json(name: str, obj, base: Path = OUT) -> None:
    (base / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------- 数值解析 ----------
NUM = r"[-−–]?\d+(?:\.\d+)?(?:\s*[×x]\s*10\s*[−-]?\d+)?"
_num_re = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)")


def to_float(s: str) -> float:
    s = s.replace("−", "-").replace("–", "-").replace(" ", "")
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)(?:[×x]10(-?\d+))?", s)
    if not m:
        return float(s)
    v = float(m.group(1))
    return v * 10 ** int(m.group(2)) if m.group(2) else v


def parse_value(raw) -> dict:
    """把提取的数值原文解析成 {值, 类型, 下, 上}。

    类型：精确 / 约数 / 下限 / 上限 / 范围 / 非数值。
    规则：只认一个数（或一个区间）；出现序列（→）、多个不相干数字、相对说法（“约 X 的 1/3”）一律记非数值。
    """
    if raw is None:
        return {"值": None, "类型": "无"}
    if isinstance(raw, (int, float)):
        return {"值": float(raw), "类型": "精确"}
    s = str(raw).strip()
    if not s or s in ("未报告", "未给", "—", "-"):
        return {"值": None, "类型": "无"}
    t = s.replace("−", "-").replace("～", "~").replace("∼", "~").replace("，", ",")
    if "→" in t or "的1/" in t or "倍" in t or re.search(r"(?:lower|higher|times|fold)", t, re.I):
        return {"值": None, "类型": "非数值", "原因": "序列或相对说法"}
    # 去掉括号里的附注再判断
    core = re.sub(r"[（(].*?[)）]", "", t).replace("%", "").strip()
    approx = bool(re.search(r"约|~|≈|接近|大约|近|nearly|about|approx|around", core, re.I))
    lower = bool(re.search(r">|≥|至少|超过|大于|以上|>=|over|more than|above|at least", core, re.I))
    upper = bool(re.search(r"<|≤|不足|至多|小于|以下|内恶化|<=|up to|below|less than", core, re.I))
    rng = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|–|~|至|到)\s*(\d+(?:\.\d+)?)", core)
    nums = _num_re.findall(core)
    if rng and len(nums) == 2:
        a, b = float(rng.group(1)), float(rng.group(2))
        return {"值": (a + b) / 2, "类型": "范围", "下": min(a, b), "上": max(a, b)}
    if len(nums) != 1:
        return {"值": None, "类型": "非数值", "原因": "无数字" if not nums else "多个数字"}
    v = float(nums[0])
    if re.search(r"(?<!\d)-\s*" + re.escape(nums[0]), core) and not rng:
        v = -v
    if lower and not upper:
        return {"值": v, "类型": "下限"}
    if upper and not lower:
        return {"值": v, "类型": "上限"}
    if lower and upper:
        return {"值": None, "类型": "非数值", "原因": "上下限同时出现"}
    return {"值": v, "类型": "约数" if approx else "精确"}


# ---------- Excel ----------
def write_xlsx(path: Path, sheets: list[tuple[str, list[str], list[list]]], widths: dict | None = None,
               notes: list[str] | None = None) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    wb = Workbook()
    wb.remove(wb.active)
    if notes:
        ws = wb.create_sheet("说明")
        for line in notes:
            ws.append([line])
        ws.column_dimensions["A"].width = 140
        for row in ws.iter_rows():
            for c in row:
                c.alignment = Alignment(wrap_text=True, vertical="top")
    for name, header, rows in sheets:
        ws = wb.create_sheet(name[:31])
        ws.append(header)
        for r in rows:
            ws.append([("；".join(map(str, v)) if isinstance(v, (list, tuple)) else
                        (json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else v)) for v in r])
        for c in ws[1]:
            c.font = Font(bold=True)
            c.fill = PatternFill("solid", fgColor="DDEBF7")
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = Alignment(wrap_text=True, vertical="top")
        for i, h in enumerate(header):
            col = ws.cell(row=1, column=i + 1).column_letter
            ws.column_dimensions[col].width = (widths or {}).get(h, max(10, min(40, len(str(h)) * 2 + 4)))
        ws.freeze_panes = "B2"
        ws.auto_filter.ref = ws.dimensions
    wb.save(path)


def sentences(src: dict[str, dict], ids, limit: int = 400) -> str:
    """把句子编号换成原文（压缩空白、截断），供复核表贴原句。"""
    out = []
    for i in ids or []:
        s = src.get(i)
        if s:
            t = re.sub(r"\s+", " ", s["text"]).strip()
            out.append(f"[{i}] {t[:limit]}{'…' if len(t) > limit else ''}")
        else:
            out.append(f"[{i}] （source.json 中无此编号）")
    return "\n".join(out)
