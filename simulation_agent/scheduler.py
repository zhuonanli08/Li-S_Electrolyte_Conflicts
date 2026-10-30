"""Render bounded single-node Slurm scripts. Never call sbatch.

Site launchers, modules and tariff must be supplied after actual platform inspection.
"""

import re
import shlex

from .budget import estimate


def token(value, name):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:/+-]+", value):
        raise ValueError(name + " 含不支持字符或尚未配置")
    return value


def render_slurm(config):
    for key in ("cpus", "memory_mb", "walltime_minutes"):
        if type(config.get(key)) is not int or config[key] < 1:
            raise ValueError(key + " 必须为正整数")
    if config.get("billing_verified") is not True:
        raise ValueError("尚未核实队列最小分配/计费规则，不能导出可提交脚本")
    # Bound one attempt; production retries need a separate batch budget reservation.
    billing, cap = config.get("billing", {}), config.get("approved_cap")
    units = config.get("billable_units")
    if billing.get("unit") not in ("cpu_core_hour", "node_hour"):
        raise ValueError("当前脚本只申请 CPU 资源，请明确核时/节点时计价")
    if type(units) is not int or units < (config["cpus"] if billing["unit"] == "cpu_core_hour" else 1):
        raise ValueError("计费资源不得小于申请核数/节点数；整节点收费须按平台规则填写")
    quote = estimate({"billing": billing, "budget_cap": cap, "jobs": [{"label": "single_attempt",
        "billable_units": units, "walltime_hours": config["walltime_minutes"] / 60,
        "replicas": 1, "max_attempts": 1}]})
    if quote["within_cap"] is not True:
        raise ValueError("计费单价/费用上限未确定或计算费用超过上限")
    name, partition, account = [token(config.get(k), k) for k in ("job_name", "partition", "account")]
    engine, executable = config.get("engine"), config.get("executable")
    if not isinstance(executable, str) or not executable.startswith("/") or "\n" in executable:
        raise ValueError("需要平台核实后的绝对可执行文件路径")
    input_name = token(config.get("input_file"), "input_file")
    if "/" in input_name or input_name.startswith("-"):
        raise ValueError("input_file 必须为当前任务目录内的文件名")
    modules = config.get("modules", [])
    if not isinstance(modules, list):
        raise ValueError("modules 必须是列表")
    module_lines = ["module load " + shlex.quote(token(module, "module")) for module in modules]
    qexe, qinput = shlex.quote(executable), shlex.quote(input_name)
    if engine == "gaussian":
        run = f"{qexe} < {qinput} > engine.log 2>&1"
    elif engine == "orca":
        # ORCA starts MPI itself; do not wrap the driver in mpirun/srun blindly.
        run = f"{qexe} {qinput} > engine.log 2>&1"
    elif engine == "lammps":
        if config["cpus"] != 1:
            raise ValueError("LAMMPS 多核启动需平台 MPI 适配；当前只导出单核试验脚本")
        run = f"{qexe} -in {qinput} -log lammps.log > engine.log 2>&1"
    else:
        raise ValueError("引擎必须为 gaussian/orca/lammps")
    lines = ["#!/usr/bin/env bash", f"#SBATCH --job-name={name}", f"#SBATCH --partition={partition}",
             f"#SBATCH --account={account}", "#SBATCH --nodes=1", "#SBATCH --ntasks=1",
             f"#SBATCH --cpus-per-task={config['cpus']}", f"#SBATCH --mem={config['memory_mb']}M",
             f"#SBATCH --time={config['walltime_minutes']}", "#SBATCH --output=scheduler-%j.out",
             "#SBATCH --error=scheduler-%j.err", "set -euo pipefail", 'cd "${SLURM_SUBMIT_DIR:?}"',
             f"# Compute-only cost ceiling: {quote['allocation_cost_ceiling']}; excludes platform extras.",
             *module_lines, 'test -f ' + qinput,
             'test ! -e engine.log || { echo "Existing engine.log: use a fresh attempt directory" >&2; exit 2; }',
             "export OMP_NUM_THREADS=1" if engine == "orca" else f"export OMP_NUM_THREADS={config['cpus']}",
             '# Each attempt keeps its own files. Scheduler walltime bounds resource occupancy.',
             "date -u +%FT%TZ > started_at.txt", run, "date -u +%FT%TZ > finished_at.txt"]
    return "\n".join(lines) + "\n"
