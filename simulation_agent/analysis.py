"""Explicit energy definitions; no inference of scientific pass from engine exit."""

import math

from .core import digest


def binding_energy(complex_result, fragments):
    """Isolated optimized fragments only, in Hartree; no silent unit conversion."""
    if not fragments:
        raise ValueError("需要全部片段及其化学计量")
    inputs = [complex_result] + [f["result"] for f in fragments]
    for result in inputs:
        if result.get("qc_status") != "PASSED":
            raise ValueError("所有能量对象均需先通过各自科学质检")
        if result.get("unit") != "hartree" or result.get("geometry_basis") != "isolated_optimized":
            raise ValueError("本函数只接受孤立优化对象的 Hartree 电子能量，不能混入 E_int 或自由能")
        energy = result.get("electronic_energy")
        if type(energy) not in (float, int) or not math.isfinite(energy):
            raise ValueError("能量必须为有限数值")
        if not result.get("protocol_hash") or result.get("mode") not in ("production", "synthetic"):
            raise ValueError("缺少协议/来源类型")
        if not result.get("source_sha256"):
            raise ValueError("缺少原始产物哈希")
        if type(result.get("charge")) is not int or not isinstance(result.get("formula"), dict):
            raise ValueError("需要电荷和元素计量以核对守恒")
        if not result["formula"] or any(type(n) is not int or n <= 0 for n in result["formula"].values()):
            raise ValueError("元素计量必须是正整数")
    if len({r["protocol_hash"] for r in inputs}) != 1 or len({r["mode"] for r in inputs}) != 1:
        raise ValueError("不能混用协议或将测试数据混入真实结果")
    formula, charge, sum_energy = {}, 0, 0.0
    for fragment in fragments:
        count, result = fragment["coefficient"], fragment["result"]
        if type(count) is not int or count < 1:
            raise ValueError("片段系数必须为正整数")
        charge += count * result["charge"]
        sum_energy += count * result["electronic_energy"]
        for element, n in result["formula"].items():
            formula[element] = formula.get(element, 0) + count * n
    if formula != complex_result["formula"] or charge != complex_result["charge"]:
        raise ValueError("复合物与片段的元素计量/电荷不守恒")
    return {"name": "E_bind", "definition": "E_AB(opt) - sum(n_i * E_i(opt))",
            "value": complex_result["electronic_energy"] - sum_energy, "unit": "hartree",
            "mode": complex_result["mode"], "input_hash": digest({"complex": complex_result, "fragments": fragments}),
            "qc_status": "DERIVED_PENDING_REVIEW", "is_solvation_free_energy": False}
