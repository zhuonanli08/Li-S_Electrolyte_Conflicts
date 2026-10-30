"""Call a pinned upstream MISPR utility without installing its full compute stack."""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from .core import digest, load_json


HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE / "work" / "vendor" / "mispr"


def verify_source(source=DEFAULT_SOURCE):
    source = Path(source).resolve()
    lock = load_json(HERE / "mispr_source.lock.json")
    for name, expected in lock["files"].items():
        path = source / name
        if not path.is_file():
            raise ValueError("缺少已锁定的 MISPR 源码：" + str(path))
        actual = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if actual != expected:
            raise ValueError("MISPR 模块与已核查版本不符：" + name)
    return source, lock


def normalize_gaussian(request, source=DEFAULT_SOURCE):
    """Real upstream call; no Gaussian invocation, database, or remote submission."""
    inputs = request.get("gaussian_inputs")
    if not isinstance(inputs, dict) or "opt" not in inputs or not inputs:
        raise ValueError("需要显式 opt 配置；支持 opt/freq/sp/esp 子集")
    if set(inputs) - {"opt", "freq", "sp", "esp"}:
        raise ValueError("当前适配器只开放已检查的 opt/freq/sp/esp")
    for stage, settings in inputs.items():
        if not isinstance(settings, dict):
            raise ValueError("每个阶段需完整参数对象")
        for field in ("functional", "basis_set"):
            if not isinstance(settings.get(field), str) or not settings[field].strip():
                raise ValueError(f"{stage}.{field} 必须显式提供，禁止继承上游默认科学参数")
        if not isinstance(settings.get("route_parameters"), dict):
            raise ValueError("route_parameters 必须显式提供")
        if any(k.lower() == "scrf" for k in settings["route_parameters"]):
            raise ValueError("溶剂参数须通过独立 solvent_gaussian_inputs 提供")
        link = settings.get("link0_parameters", {})
        if not isinstance(link, dict):
            raise ValueError("link0_parameters 必须为对象")
        cpus, memory = link.get("%NProcShared"), link.get("%mem")
        if not isinstance(cpus, str) or not re.fullmatch(r"[1-9]\d*", cpus):
            raise ValueError("必须显式指定 %NProcShared，不能继承 24 核默认值")
        if not isinstance(memory, str) or not re.fullmatch(r"[1-9]\d*(MB|GB)", memory):
            raise ValueError("必须显式指定 %mem，例如 2GB，不能继承 45GB 默认值")
        if not isinstance(link.get("%chk"), str) or not re.fullmatch(r"[A-Za-z0-9_-]+\.chk", link["%chk"]):
            raise ValueError("必须显式指定当前任务目录内的 checkpoint 文件名")
    if "solvent_gaussian_inputs" not in request:
        raise ValueError("环境必须显式提供；气相使用 solvent_gaussian_inputs: null")
    solvent = request["solvent_gaussian_inputs"]
    if solvent is not None and (not isinstance(solvent, str) or not solvent.strip()):
        raise ValueError("溶剂参数必须为非空字符串或明确的 null")
    source, lock = verify_source(source)
    # -I and a subprocess keep upstream module globals/imports out of our controller.
    code = (
        "import json,sys; sys.path.insert(0,sys.argv[1]); "
        "from mispr.gaussian.utilities.inputs import handle_gaussian_inputs; "
        "r=json.load(sys.stdin); "
        "out=handle_gaussian_inputs(r['gaussian_inputs'],r['solvent_gaussian_inputs'],r.get('solvent_properties')); "
        "print(json.dumps(out,allow_nan=False))"
    )
    completed = subprocess.run([sys.executable, "-I", "-c", code, str(source)],
                               input=json.dumps(request, allow_nan=False), text=True,
                               capture_output=True, timeout=30)
    if completed.returncode:
        raise ValueError("MISPR 输入整理失败：" + completed.stderr.strip()[-1500:])
    output = json.loads(completed.stdout)
    for stage, settings in inputs.items():
        for field in ("functional", "basis_set", "link0_parameters"):
            if output[stage][field] != settings[field]:
                raise ValueError("上游意外改变了显式方法或资源，拒绝继续")
    return {"provider": "MISPR", "commit": lock["commit"],
            "callable": lock["module"] + "." + lock["callable"],
            "input_hash": digest(request), "gaussian_inputs": output,
            "scientific_protocol_approved": False, "jobs_submitted": 0,
            "note": "实际调用上游输入整理函数；没有运行 DFT，也没有完成科学协议验收。"}
