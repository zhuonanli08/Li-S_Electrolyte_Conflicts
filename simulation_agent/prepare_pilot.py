"""Prepare discussion candidates with local source locations; never launch jobs."""

import json
from pathlib import Path

from .core import file_hash


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent


def excerpt(stem, start, end, required):
    path = ROOT / "output" / "text_cache" / stem
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    quote = "\n".join(lines[start - 1:end])
    if required not in quote:
        raise ValueError(f"来源行发生变化，请重新核对：{path}:{start}")
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": file_hash(path),
            "line_start": start, "line_end": end, "excerpt": quote}


def build():
    s11 = "10.1002_anie.202309968.si.txt"
    s39 = "10.1021_acsenergylett.5c02200.si.txt"
    s21 = "10.1002_aenm.202500802.si.txt"
    return {
        "date": "2026-10-30", "status": "discussion_only", "submission_enabled": False,
        "selection_scope": "从已有 S11/S21/S33/S39 开发材料定位，再核对 S11/S21/S39 原文缓存；不是全库最优选样。",
        "user_constraints": ["无计算经验或现成脚本", "有超算，费用需控制", "先列小样后讨论"],
        "candidates": [
            {
                "id": "DFT-pilot", "priority": 1,
                "proposal": "DME–Li+、DOL–Li+、TTE/HFE–Li+ 三类 1:1 团簇，先完成一个 DME–Li+ 流程试算再估全批费用。",
                "source_papers": ["S11: 10.1002/anie.202309968", "S39: 10.1021/acsenergylett.5c02200"],
                "purpose": "验证构型生成、相同协议的结合能定义、日志解析和质检；初步比较不同组分与 Li+ 的作用。",
                "limits": "这是本课题新增的小团簇基准，不是对原文 Li2S4/Li2S8 结合能的复现；孤立 Li+ 团簇不能代表混合电解液溶剂化自由能。",
                "job_accounting": "三种复合物、三种自由溶剂、一个 Li+ 为至少七类能量对象；多构型、频率/单点/基组误差及重试另算，不能按三项结合能当成三个作业。",
                "pending": ["结构与 HFE/TTE 同一性核验", "软件可用性", "构型搜索和计算级别", "是否需要频率检查及其阈值", "预算"],
                "evidence": [excerpt(s11, 15, 18, "tetrafluoroethyl"), excerpt(s11, 89, 97, "Ecluster")]
            },
            {
                "id": "MD-pilot", "priority": 2,
                "proposal": "S39 的 DOL/DME=1:1 与 DOL/TTE=4:1 两个无多硫化物 MD 体系；均按表 S1 的 1 M LiTFSI + 0.1 M LiNO3 组成作为待核候选。",
                "source_papers": ["S39: 10.1021/acsenergylett.5c02200"],
                "purpose": "先验证密度、RDF/配位统计；扩散须通过采样验证。先用一个体系测实耗，再决定另一个体系及独立重复。",
                "composition_candidates_from_text": [
                    {"label": "DOL/DME", "DOL": 358, "DME": 241, "TTE": 0, "TFSI-": 50, "NO3-": 5, "Li+": 55},
                    {"label": "DOL/TTE", "DOL": 573, "DME": 0, "TTE": 66, "TFSI-": 50, "NO3-": 5, "Li+": 55}
                ],
                "limits": "表 S1 为 0.1 M LiNO3，Li||S 配方为 0.2 M；不能直接关联为同配方的电池性能特征。表格数字目前仅核原文文本，未视觉验表。原方法为 NAMD/GAAMP，大体系和 64 条轨迹不能照搬成低预算方案。",
                "pending": ["表 S1 视觉核对及组成/总原子数说明核对", "TTE/离子参数可得性与兼容性", "固定力场、电荷方案", "规模及盒子/密度自洽", "采样收敛和独立重复数", "预算"],
                "evidence": [excerpt(s39, 29, 38, "0.2 M LiNO3"), excerpt(s39, 118, 136, "64 independent"),
                             excerpt(s39, 143, 204, "573")]
            },
            {
                "id": "later-polysulfide", "priority": 3,
                "proposal": "基础流程通过后，用 S11 的 Li2S4 与 DME/HFE 团簇做针对性检验；MD 多硫化物探针另立任务。",
                "source_papers": ["S11: 10.1002/anie.202309968"],
                "purpose": "把 Li+ 侧和多硫化物侧的相互作用分开检验。",
                "limits": "S11 表 S6 的 MD 含 Li2S4 或 Li2S8，且未列 LiNO3；与其含 2 wt.% LiNO3 电池配方不同。参数和电荷/拓扑未验证前不启动。",
                "evidence": [excerpt(s11, 22, 26, "2 wt.%"), excerpt(s11, 99, 112, "RESP"),
                             excerpt(s11, 588, 618, "572")]
            }
        ],
        "deferred": [{"paper": "S21: 10.1002/aenm.202500802",
                      "reason": "原文用训练机器学习势的 MD 流程，首轮不复刻训练；可在统一传统力场路线成熟后再评估该配方。",
                      "evidence": [excerpt(s21, 26, 38, "Tesla A100")]}],
        "cost": {"platform": None, "rate": None, "budget_cap": None,
                 "note": "尚不能给出可信金额；需平台计价及一次获准试算的实耗。"}
    }


def main():
    data = build()
    path = OUT / "pilot_candidates.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(path))


if __name__ == "__main__":
    main()
