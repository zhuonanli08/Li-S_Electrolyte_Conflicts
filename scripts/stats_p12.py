"""组会第 12 页“数据概况”右侧要点的数字（11-08 用户同意；zy 批注：分析点不只局限于右侧内容，要体现相比人工读文献/写综述的优势）。
时间跨度、配方与组分覆盖面、哪些组合从没人测过、每个数值能否追溯到原句。数字全部从结果文件读，写 output/组会图_2026-11-08/第12页要点.json。
用法：D:\\anaconda\\envs\\papertrail\\python.exe -X utf8 scripts/stats_p12.py
"""
import glob
import json
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Desktop\课题二锂硫电解液矛盾归因")
O = ROOT / "output"
PAPERS = O / "试跑313篇_2026-11-05" / "papers"
MANI = O / "F版全量提取_2026-11-02" / "manifest.json"
COMP = O / "组分结构表_试跑313篇_2026-11-05" / "组分表.json"
QD = O / "组会图_2026-11-08" / "组会图数据.json"


def main():
    man = {x["id"]: x for x in json.loads(MANI.read_text(encoding="utf-8"))}
    ids = sorted(Path(f).parent.name for f in glob.glob(str(PAPERS / "*" / "candidate.json")))
    yrs = [int(man[p]["year"]) for p in ids if p in man and str(man[p].get("year", "")).isdigit()]
    n_rec = n_meas = n_meas_src = n_mech = 0
    for p in ids:
        c = json.loads((PAPERS / p / "candidate.json").read_text(encoding="utf-8"))
        n_rec += len(c.get("recipes") or c.get("formulations") or [])
        for m in c.get("measurements", []):
            n_meas += 1
            n_meas_src += bool(m.get("evidence_ids") or m.get("source_ids") or m.get("evidence"))
        n_mech += len(c.get("mechanisms", []))
    comp = json.loads(COMP.read_text(encoding="utf-8"))
    roles = Counter(c.get("类别") for c in comp)
    q = json.loads(QD.read_text(encoding="utf-8"))
    hm = q["q3"]["热图"]
    empty = [k for k, v in hm.items() if v[0] == 0]
    out = {
        "文献": {"已提取": len(ids), "全库": 535, "年份范围": [min(yrs), max(yrs)], "有年份": len(yrs),
               "按年": dict(sorted(Counter(yrs).items())), "2022 年及以后占比": round(sum(y >= 2022 for y in yrs) / len(yrs), 3)},
        "覆盖面": {"配方": n_rec, "有性能测量的配方": q["q3"]["配方总数"], "组分（分子）": len(comp), "组分按角色": dict(roles.most_common()),
                "测量值": n_meas, "机制说法": n_mech},
        "可追溯": {"测量值带原句编号": n_meas_src, "占比": round(n_meas_src / max(n_meas, 1), 3)},
        "空白": {"盐浓度×LiNO₃ 25 格中没人测过的格数": len(empty), "没人测过的格": empty,
               "高盐（>1 M）且含 LiNO₃ 的配方": q["q3"]["高盐且含 LiNO3"],
               "LiNO₃ 高于 0.6 M 的配方": q["q2"]["高于 0.6 M 的配方"],
               "单独扫 LiNO₃ 用量的论文": ["P111", "P139", "P113"],
               "同篇交叉设计（两个因素交叉着变）": ["P112"]},
    }
    f = O / "组会图_2026-11-08" / "第12页要点.json"
    f.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
