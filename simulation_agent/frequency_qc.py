"""Conservative Gaussian harmonic-frequency screening, not scientific approval.

Only ordinary, single-job harmonic output is supported. Mode numbering and
counts are checked together, so a duplicated block cannot replace a missing one.
Reference energies remain references; no engine or scheduler is invoked.
"""

import hashlib
import math
import re

from .engines import NUMBER, inspect_log


def number(value):
    if not re.fullmatch(NUMBER, value):
        raise ValueError("不支持的频率/能量数字格式")
    result = float(value.replace("D", "E").replace("d", "e"))
    if not math.isfinite(result):
        raise ValueError("数字不是有限值")
    return result


def inspect_frequency(text, expected):
    """Always retain pending scientific review even when all screens pass."""
    n = expected.get("atom_count")
    linear = expected.get("linear")
    if type(n) is not int or n < 2 or type(linear) is not bool:
        raise ValueError("必须明确指定原子数（至少 2）和 linear 布尔值")
    if n == 2 and not linear:
        raise ValueError("双原子分子应指定 linear=true")
    if type(expected.get("charge")) is not int or type(expected.get("multiplicity")) is not int or expected["multiplicity"] < 1:
        raise ValueError("必须指定整数电荷和正整数自旋多重度")
    reference = expected.get("reference_energy_hartree")
    tolerance = expected.get("energy_tolerance_hartree")
    for name, value in (("reference_energy_hartree", reference), ("energy_tolerance_hartree", tolerance)):
        if type(value) not in (float, int) or not math.isfinite(value):
            raise ValueError(name + " 必须是有限数字")
    if tolerance < 0 or not isinstance(expected.get("route"), str) or not expected["route"].strip():
        raise ValueError("需要非负能量调查阈值及完整 route")

    basic = inspect_log("gaussian", text)
    issues = list(basic["issues"])
    checks = []

    def check(name, passed, observed):
        checks.append({"name": name, "passed": bool(passed), "observed": observed})
        if not passed:
            issues.append(name)

    check("single_job_completed", basic["status"] == "SUCCESS_PENDING_QC", basic["status"])
    counts = [int(x) for x in re.findall(r"\bNAtoms=\s*(\d+)", text)]
    check("atom_count_matches", bool(counts) and set(counts) == {n}, sorted(set(counts)))
    states = [(int(a), int(b)) for a, b in re.findall(r"Charge\s*=\s*(-?\d+)\s+Multiplicity\s*=\s*(\d+)", text)]
    check("charge_multiplicity_match", bool(states) and set(states) == {(expected["charge"], expected["multiplicity"])}, states)

    # Route echo is delimited by a dashed line in ordinary Gaussian output.
    routes = re.findall(r"(?m)^\s*#([^\n]*(?:\n(?!\s*-{5,})[^\n]*)*)\n\s*-{5,}", text)
    normalized = lambda s: re.sub(r"\s+", "", s).lower()
    check("route_matches_exactly_after_whitespace_case_normalization",
          len(routes) == 1 and normalized(routes[0]) == normalized(expected["route"]), routes)
    harmonic_sections = len(re.findall(r"(?m)^\s*Harmonic frequencies", text))
    check("single_harmonic_section", harmonic_sections == 1, harmonic_sections)

    frequencies, indices, malformed = [], [], []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        match = re.match(r"^\s*Frequencies\s+--\s*(.*)$", line)
        if not match:
            continue
        tokens = match.group(1).split()
        try:
            if not 1 <= len(tokens) <= 3:
                raise ValueError("仅支持普通 harmonic 每行 1–3 个模式")
            values = [number(token) for token in tokens]
            # The mode-index row precedes an optional symmetry-label row.
            candidates = [lines[j].split() for j in range(max(0, i - 2), i)
                          if re.fullmatch(r"\s*\d+(?:\s+\d+)*\s*", lines[j])]
            if len(candidates) != 1 or len(candidates[0]) != len(values):
                raise ValueError("缺少唯一且等长的模式编号")
            indices.extend(int(x) for x in candidates[0])
            frequencies.extend(values)
        except ValueError as error:
            malformed.append({"line": i + 1, "reason": str(error)})
    expected_count = 3 * n - (5 if linear else 6)
    check("frequency_rows_parseable", not malformed and bool(frequencies), malformed)
    check("complete_unique_ordered_modes", indices == list(range(1, expected_count + 1)),
          {"expected": expected_count, "count": len(frequencies), "indices": indices})
    negatives = [{"mode": idx, "wavenumber_cm_minus_1": value}
                 for idx, value in zip(indices, frequencies) if value < 0]
    check("no_negative_or_zero_modes_for_minimum_candidate",
          bool(frequencies) and all(value > 0 for value in frequencies),
          {"negative_modes": negatives, "zero_modes": [idx for idx, value in zip(indices, frequencies) if value == 0]})
    energy = basic["energy_hartree"]
    delta = abs(energy - reference) if energy is not None else None
    check("reference_energy_within_investigation_threshold", delta is not None and delta <= tolerance,
          {"reference_hartree": reference, "observed_hartree": energy,
           "absolute_difference_hartree": delta, "threshold_hartree": tolerance})
    versions = re.findall(r"Gaussian\s+(?:09|16):\s*([^\n]+)", text)
    passed = all(item["passed"] for item in checks)
    return {"parser_version": "gaussian-harmonic-screen-1", "engine": "gaussian",
            "status": "SCREEN_PASSED_PENDING_REVIEW" if passed else "NEEDS_REVIEW",
            "scientific_qc": "PENDING_REVIEW", "usable_for_analysis": False,
            "engine_status": basic["status"], "engine_version_lines": versions,
            "energy_hartree": energy, "frequency_unit": "cm^-1",
            "frequencies": frequencies, "checks": checks, "issues": issues,
            "remaining_review": ["实际计算输入/日志对应关系和软件版本",
                                 "元素、坐标与参考构型一致性及驻点/梯度检查",
                                 "低频模式与数值精度；不能把无虚频单独当作科学验收",
                                 "调度记录、实耗、实际账单和费用上限"],
            "reference": "https://gaussian.com/wp-content/uploads/dl/vib.pdf"}


def inspect_frequency_files(log_path, input_path, expected, mode):
    if mode not in ("synthetic", "production"):
        raise ValueError("必须明确声明日志来源模式")
    raw = log_path.read_bytes()
    input_raw = input_path.read_bytes()
    result = inspect_frequency(raw.decode("utf-8", errors="replace"), expected)
    actual_hash = hashlib.sha256(input_raw).hexdigest()
    match = actual_hash == expected.get("input_sha256")
    result["checks"].append({"name": "prepared_input_hash_matches", "passed": match, "observed": actual_hash})
    if not match:
        result["status"] = "NEEDS_REVIEW"
        result["issues"].append("prepared_input_hash_matches")
    result.update(mode=mode, provenance={
        "log_path": str(log_path.resolve()), "log_sha256": hashlib.sha256(raw).hexdigest(),
        "input_path": str(input_path.resolve()), "input_sha256": actual_hash,
        "mode_is_caller_declared": True,
        "note": "哈希记录文件身份，不证明日志实际由该输入产生"})
    return result
