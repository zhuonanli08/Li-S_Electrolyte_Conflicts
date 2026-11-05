"""step12h：把全量提取中已完成的论文复制成试跑数据集（只读原数据），格式同 output/试跑243篇_2026-11-04。

11-05 用户要求用最新提取的论文（当时 313 篇）重做条件与建模。243 篇那次是手工复制的，这次写成脚本。
复制 candidate.json、source.json（有 input_meta.json 也复制）；数据集说明.json 记来源、裁定状态、性能分析不可用的论文；
限制.json 合并全量提取的 analysis_exclusions 与 unresolved_scope_restrictions（键名同 243 篇）。
用法：python step12h_trial_dataset.py [输出文件夹名]，默认 试跑<篇数>篇_<今天>。
"""
from __future__ import annotations

import datetime
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
FULL = ROOT / "output" / "F版全量提取_2026-11-02"


def main() -> None:
    man = json.loads((FULL / "dataset_manifest.json").read_text(encoding="utf-8"))
    status = {r["paper"]: r for r in json.loads((FULL / "paper_status.json").read_text(encoding="utf-8"))}
    done = [r for r in man["rows"] if r["extraction_status"] != "not_started"]
    name = sys.argv[1] if len(sys.argv) > 1 else f"试跑{len(done)}篇_{datetime.date.today():%Y-%m-%d}"
    dst = ROOT / "output" / name
    if dst.exists():
        sys.exit(f"{dst} 已存在，不覆盖")
    for r in done:
        p = dst / "papers" / r["paper"]
        p.mkdir(parents=True)
        cand = Path(r["candidate"])
        shutil.copy(cand, p / "candidate.json")
        shutil.copy(r["source"], p / "source.json")
        if (cand.parent / "input_meta.json").exists():
            shutil.copy(cand.parent / "input_meta.json", p / "input_meta.json")
    lim = {k: json.loads((FULL / f"{k}.json").read_text(encoding="utf-8")) for k in ("analysis_exclusions", "unresolved_scope_restrictions")}
    (dst / "限制.json").write_text(json.dumps(lim, ensure_ascii=False, indent=1), encoding="utf-8")
    bad = sorted(p for p, s in status.items() if s.get("performance_analysis_eligible") is False and s["extraction_status"] != "not_started")
    meta = {"说明": f"{len(done)} 篇试跑数据集：全量提取中提取已完成的论文，由 scripts/step12h_trial_dataset.py 于 {datetime.date.today()} 复制；"
                    "原数据不改。新提取的多数尚未裁定，结果一律标“初步、未裁定”。字段限制见同目录 限制.json。",
            "论文数": len(done),
            "来源": {"新提取": sum(r["phase"] != "prior30" for r in done), "原30篇": sum(r["phase"] == "prior30" for r in done)},
            "裁定状态": dict(Counter(r["adjudication_status"] for r in done)),
            "性能分析不可用": bad,
            "manifest_sha256": {r["paper"]: r["candidate_sha256"] for r in done}}
    (dst / "数据集说明.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(dst, meta["论文数"], meta["来源"], "性能分析不可用", bad, {k: len(v) for k, v in lim.items()})


if __name__ == "__main__":
    main()
