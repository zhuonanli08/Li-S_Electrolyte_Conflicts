"""草稿：V3 所需的跨篇连接统计。配方身份 = 组分 + 用量（体积分数取 0.05、浓度取 0.05 M 精度）。"""
from xdata import *


def fkey(pid, rid):
    r = COMPREC.get((pid, rid))
    if not r:
        return None
    vf = r.get("体积分数") or {}
    parts = []
    for i in r["组分"]:
        c = i["组分"]
        cat = CTAB.get(c, {}).get("类别", "")
        if cat in ("硫物种", "离子"):
            continue
        if c in vf:
            parts.append((c, "v", round(vf[c] * 20) / 20))
        elif i["单位类别"] == "摩尔浓度" and i["数值"] is not None:
            parts.append((c, "M", round(i["数值"] * 20) / 20))
        else:
            parts.append((c, i["单位类别"], i["数值"]))
    return tuple(sorted(parts, key=str))


def pairs_of(rows):
    """同篇同测试：实验样都和对比样比（方案 11-02）；返回 (论文, 测试, i, j)。"""
    by = defaultdict(list)
    for i, r in enumerate(rows):
        by[(r["s"]["论文"], r["s"]["测试"], r["s"]["圈数"])].append(i)
    out = []
    for (p, t, _), idx in by.items():
        ref = next((i for i in idx if rows[i]["s"]["是否对照"]), idx[0])
        for i in idx:
            if i != ref and rows[i]["fk"] != rows[ref]["fk"]:
                out.append((p, t, i, ref))
    return out


if __name__ == "__main__":
    for cname in ("放电容量类", "衰减类", "库仑效率类·全电池", "库仑效率类·Li‖Cu"):
        rows = rows_for(cname)
        for r in rows:
            r["fk"] = fkey(r["s"]["论文"], r["s"]["recipe"])
        papers_of = defaultdict(set)
        for r in rows:
            papers_of[r["fk"]].add(r["s"]["论文"])
        shared = {k: v for k, v in papers_of.items() if len(v) >= 2}
        prs = pairs_of(rows)
        cnt = Counter(frozenset((rows[i]["fk"], rows[j]["fk"])) for _, _, i, j in prs)
        npaper = defaultdict(set)
        for p, _, i, j in prs:
            npaper[frozenset((rows[i]["fk"], rows[j]["fk"]))].add(p)
        uniq = [k for k, v in npaper.items() if len(v) == 1]
        both_elsewhere = [k for k in uniq if all(len(papers_of[f] - npaper[k]) >= 1 for f in k)]
        one_elsewhere = [k for k in uniq if sum(len(papers_of[f] - npaper[k]) >= 1 for f in k) == 1]
        print(f"## {cname}: 配方 {len(papers_of)} 个，出现在 ≥2 篇的 {len(shared)} 个；配对 {len(npaper)} 种，只在一篇比过的 {len(uniq)} 种；"
              f"其中两个配方在别的论文都出现过 {len(both_elsewhere)} 种，只有一个出现过 {len(one_elsewhere)} 种")
        for k, v in sorted(((k, v) for k, v in shared.items() if k), key=lambda kv: -len(kv[1]))[:6]:
            print("     共同配方", len(v), "篇", sorted(v), "：", "；".join(f"{a} {u}{x}" for a, u, x in k)[:120])
