"""Input rendering and conservative single-job log inspection.

All method/force-field choices must be supplied explicitly. No engine is executed.
"""

import math
import re


ELEMENTS = "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og".split()
NUMBER = r"[-+]?\d+(?:\.\d*)?(?:[EeDd][-+]?\d+)?"


def single_line(value, name):
    if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
        raise ValueError(name + " 必须为非空单行文本")
    return value


def coordinates(atoms, charge, multiplicity):
    if type(charge) is not int or type(multiplicity) is not int or multiplicity < 1:
        raise ValueError("需要整数电荷和正整数自旋多重度")
    if not isinstance(atoms, list) or not atoms:
        raise ValueError("需要实际坐标，不能从名称猜测结构")
    lines, electrons = [], -charge
    for atom in atoms:
        symbol, xyz = atom.get("element"), atom.get("xyz_angstrom")
        if symbol not in ELEMENTS or not isinstance(xyz, list) or len(xyz) != 3:
            raise ValueError("原子必须有合法元素和三个埃单位坐标")
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in xyz):
            raise ValueError("坐标必须为有限数值")
        electrons += ELEMENTS.index(symbol) + 1
        lines.append(symbol + " " + " ".join(f"{v:.10f}" for v in xyz))
    if electrons < 0 or multiplicity - 1 > electrons or (electrons - (multiplicity - 1)) % 2:
        raise ValueError("电子数与电荷/多重度不一致")
    return "\n".join(lines)


def render_dft(engine, atoms, charge, multiplicity, keywords, cpus, memory_gb):
    if type(cpus) is not int or cpus < 1:
        raise ValueError("cpus 必须为正整数")
    if type(memory_gb) not in (int, float) or not math.isfinite(memory_gb) or memory_gb <= 0:
        raise ValueError("memory_gb 必须为有限正数")
    keywords = single_line(keywords, "完整方法/任务关键词")
    xyz = coordinates(atoms, charge, multiplicity)
    if engine == "gaussian":
        if keywords.startswith(("#", "%")) or "--Link1--" in keywords:
            raise ValueError("只支持单个作业的 route 内容，不带 #/Link1/Link0")
        return (f"%chk=calculation.chk\n%nprocshared={cpus}\n%mem={int(memory_gb * 1024 * 0.75)}MB\n"
                f"# {keywords}\n\nLi-S agent prepared single job\n\n{charge} {multiplicity}\n{xyz}\n\n")
    if engine == "orca":
        if keywords.startswith(("!", "%", "*")):
            raise ValueError("keywords 不含 !、块定义或坐标段")
        per_core_mb = int(memory_gb * 1024 * 0.75 / cpus)
        if per_core_mb < 1:
            raise ValueError("每核内存不足")
        return (f"! {keywords}\n%pal nprocs {cpus} end\n%maxcore {per_core_mb}\n"
                f"* xyz {charge} {multiplicity}\n{xyz}\n*\n")
    raise ValueError("DFT 引擎仅支持 gaussian/orca 输入渲染")


def inspect_log(engine, text, expected_optimization=False, expected_steps=None):
    result = {"engine": engine, "status": "INCOMPLETE", "scientific_qc": "NOT_PERFORMED",
              "energy_hartree": None, "issues": [], "usable_for_analysis": False}
    energy = []
    if engine == "gaussian":
        if "Error termination" in text or re.search(r"Convergence failure|SCF has not converged", text, re.I):
            result.update(status="EXECUTION_FAILED", issues=["Gaussian 报错/未收敛"])
            return result
        terminations = text.count("Normal termination of Gaussian")
        if terminations > 1:
            result.update(status="NEEDS_REVIEW", issues=["单作业解析器不接受多段 Link1/拼接日志"])
            return result
        complete = terminations == 1 and bool(re.search(r"Normal termination of Gaussian[^\n]*(?:\n\s*)*\Z", text))
        energy = re.findall(r"SCF Done:\s+E\([^)]+\)\s*=\s*(" + NUMBER + ")", text)
        optimized = "Optimization completed." in text
    elif engine == "orca":
        if re.search(r"ORCA finished by error termination|SCF NOT CONVERGED|SCF CONVERGENCE FAILURE", text, re.I):
            result.update(status="EXECUTION_FAILED", issues=["ORCA 报错/未收敛"])
            return result
        terminations = text.count("ORCA TERMINATED NORMALLY")
        if terminations > 1:
            result.update(status="NEEDS_REVIEW", issues=["单作业解析器不接受拼接日志"])
            return result
        complete = terminations == 1 and bool(re.search(
            r"ORCA TERMINATED NORMALLY[^\n]*(?:\n\s*(?:TOTAL RUN TIME:[^\n]*)?)*\Z", text))
        energy = re.findall(r"FINAL SINGLE POINT ENERGY\s+(" + NUMBER + ")", text)
        optimized = "THE OPTIMIZATION HAS CONVERGED" in text
    elif engine == "lammps":
        if re.search(r"(^|\n)\s*ERROR|Lost atoms|Non-numeric", text, re.I):
            result.update(status="EXECUTION_FAILED", issues=["LAMMPS 报错或原子/数值异常"])
            return result
        runs = re.findall(r"Loop time of .*? for (\d+) steps", text)
        result["observed_run_steps"] = [int(value) for value in runs]
        if not re.search(r"Total wall time:[^\n]*(?:\n\s*)*\Z", text):
            return result
        if expected_steps is None:
            result.update(status="NEEDS_REVIEW", issues=["未指定应完成的各段步数"])
        elif result["observed_run_steps"] != expected_steps:
            result.update(status="NEEDS_REVIEW", issues=["完成步数与预期不符"])
        else:
            result["status"] = "SUCCESS_PENDING_QC"
        return result
    else:
        raise ValueError("未知引擎")
    if not complete:
        return result
    if not energy:
        result.update(status="NEEDS_REVIEW", issues=["未找到支持格式的最终电子能量"])
        return result
    value = float(energy[-1].replace("D", "E").replace("d", "e"))
    if not math.isfinite(value):
        result.update(status="NEEDS_REVIEW", issues=["最终能量不是有限数值"])
        return result
    result["energy_hartree"] = value
    if expected_optimization and not optimized:
        result.update(status="NEEDS_REVIEW", issues=["缺少几何优化收敛标记"])
    else:
        result["status"] = "SUCCESS_PENDING_QC"
    return result
