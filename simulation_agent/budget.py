"""Allocation ceilings, not measured runtime predictions. No submission capability."""

from .core import positive


def estimate(request):
    billing = request.get("billing", {})
    unit = billing.get("unit")
    if unit not in ("cpu_core_hour", "gpu_hour", "node_hour"):
        raise ValueError("请先明确按 CPU 核时、GPU 时还是节点时计费")
    rate = billing.get("price_per_unit_hour")
    cap = request.get("budget_cap")
    if rate is not None and not positive(rate):
        raise ValueError("计费单价必须为有限正数；未确认时填 null")
    if cap is not None and not positive(cap):
        raise ValueError("预算上限必须为有限正数；未确认时填 null")
    jobs = request.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ValueError("jobs 必须包含实际待估算任务")
    rows = []
    for job in jobs:
        for key in ("billable_units", "walltime_hours"):
            if not positive(job.get(key)):
                raise ValueError("每个任务必须填写 " + key)
        for key in ("replicas", "max_attempts"):
            if type(job.get(key)) is not int or job[key] < 1:
                raise ValueError("每个任务必须填写正整数 " + key)
        hours = job["billable_units"] * job["walltime_hours"] * job["replicas"] * job["max_attempts"]
        rows.append({"label": job.get("label"), "billable_unit_hours": hours,
                     "allocation_cost_ceiling": None if rate is None else hours * rate})
    total_hours = sum(row["billable_unit_hours"] for row in rows)
    cost = None if rate is None else total_hours * rate
    return {"unit": unit, "currency": billing.get("currency"), "jobs": rows,
            "total_billable_unit_hours": total_hours,
            "allocation_cost_ceiling": cost, "budget_cap": cap,
            "within_cap": None if cap is None or cost is None else cost <= cap,
            "submission_enabled": False,
            "note": "仅按申请时长给出计算费上界；不预测实际耗时，未包括最低计费时段、存储、软件许可及其他平台费用。单价和任务规模须由平台核实。"}
