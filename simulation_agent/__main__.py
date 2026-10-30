"""Planning CLI. No quantum chemistry/MD executable is launched by this version."""

import argparse
import json
import platform
import shutil
import sqlite3
import sys
from pathlib import Path

from . import __version__
from .core import Store, load_json, plan
from .budget import estimate
from .workflow import WorkflowRun, build_workflow, export_workflow
from .engines import inspect_log, render_dft
from .scheduler import render_slurm
from .mispr_adapter import normalize_gaussian
from .frequency_qc import inspect_frequency_files


def main(argv=None):
    parser = argparse.ArgumentParser(description="DFT/MD agent 基础层：检查、规划与登记")
    parser.add_argument("--db", default="simulation_agent/work/tasks.sqlite3")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="只读检查本机 Python 与命令路径")
    for name in ("plan", "register", "estimate", "mispr-inputs"):
        commands.add_parser(name).add_argument("spec", type=Path)
    commands.add_parser("list")
    commands.add_parser("show").add_argument("task_id")
    workflow_cmd = commands.add_parser("workflow", help="导出依赖图，未提交任务")
    workflow_cmd.add_argument("spec", type=Path)
    workflow_cmd.add_argument("--out", type=Path, required=True)
    workflow_cmd.add_argument("--replicas", type=int, default=2)
    demo_cmd = commands.add_parser("demo", help="两条全流程演示，所有产物标记 synthetic")
    demo_cmd.add_argument("--out", type=Path, default=Path("simulation_agent/work/demo"))
    inspect_cmd = commands.add_parser("inspect-log", help="引擎单作业日志初检，不能替代科学质检")
    inspect_cmd.add_argument("engine", choices=("gaussian", "orca", "lammps"))
    inspect_cmd.add_argument("log", type=Path)
    inspect_cmd.add_argument("--optimization", action="store_true")
    inspect_cmd.add_argument("--steps", type=int, nargs="+")
    frequency_cmd = commands.add_parser("inspect-frequency", help="Gaussian 频率筛查与参考对比，仍需科学复核")
    frequency_cmd.add_argument("config", type=Path)
    frequency_cmd.add_argument("log", type=Path)
    frequency_cmd.add_argument("--input", type=Path, required=True)
    frequency_cmd.add_argument("--mode", choices=("synthetic", "production"), required=True)
    frequency_cmd.add_argument("--out", type=Path, required=True)
    for name in ("render-dft", "render-slurm"):
        render_cmd = commands.add_parser(name, help="从显式配置渲染，禁止覆盖已存在文件")
        render_cmd.add_argument("config", type=Path)
        render_cmd.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            result = {"agent_version": __version__, "python": sys.version,
                      "python_executable": sys.executable, "platform": platform.platform(),
                      "commands": {name: shutil.which(name) for name in
                                   ("g16", "g09", "orca", "lmp", "lmp_mpi", "gmx", "sbatch", "qsub", "ssh")},
                      "note": "仅检查 PATH，缺失不代表服务器未安装；不尝试登录或执行计算。",
                      "execution_backend": "not_connected"}
        elif args.command == "plan":
            result = plan(load_json(args.spec))
        elif args.command == "estimate":
            result = estimate(load_json(args.spec))
        elif args.command == "mispr-inputs":
            result = normalize_gaussian(load_json(args.spec))
        elif args.command == "workflow":
            workflow = build_workflow(load_json(args.spec), args.replicas)
            result = {"path": str(export_workflow(workflow, args.out)), "workflow_id": workflow["workflow_id"],
                      "stage_count": len(workflow["stages"]), "submitted": False}
        elif args.command == "demo":
            result = {}
            for kind in ("dft", "md"):
                spec = load_json(Path(__file__).parent / "examples" / f"{kind}_draft.json")
                spec["mode"] = "synthetic"
                workflow = build_workflow(spec)
                with WorkflowRun(workflow, args.out) as run:
                    report = run.run_synthetic()
                    result[kind] = {k: v for k, v in report.items() if k != "stages"}
                    result[kind]["report_path"] = str(run.root / "report.json")
        elif args.command == "inspect-log":
            result = inspect_log(args.engine, args.log.read_text(encoding="utf-8", errors="replace"),
                                 args.optimization, args.steps)
        elif args.command == "inspect-frequency":
            result = inspect_frequency_files(args.log, args.input, load_json(args.config), args.mode)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with args.out.open("x", encoding="utf-8") as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
                stream.write("\n")
        elif args.command in ("render-dft", "render-slurm"):
            config = load_json(args.config)
            content = render_dft(**config) if args.command == "render-dft" else render_slurm(config)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with args.out.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
            result = {"path": str(args.out), "submitted": False, "scientifically_validated": False}
        else:
            with Store(args.db) as store:
                if args.command == "register":
                    result = store.get(store.register(load_json(args.spec)))
                elif args.command == "list":
                    result = store.list()
                else:
                    result = store.get(args.task_id)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        if args.command == "inspect-frequency" and result["status"] == "NEEDS_REVIEW":
            return 3
        return 0
    except (ValueError, OSError, TypeError, sqlite3.Error) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
