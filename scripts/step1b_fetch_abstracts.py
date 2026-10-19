"""第 1 步 b：从 OpenAlex 批量取 02 库 669 篇的摘要（免费，可续跑）。

输出：output/abstracts.json  {doi: {"title":..., "abstract":...}}；OpenAlex 没摘要的记空串，由 step1c 从 PDF 首页兜底。
"""
import csv
import json
import os
import time

import requests

LIB = r"D:\Desktop\锂电催化\机器学习\skills\Open-Papertrail\Open-Papertrail\corpus\library"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "abstracts.json")
KEY = os.environ.get("OPENALEX_KEY", "") or os.environ.get("OPENALEX_API_KEY", "")
SEL = "id,doi,title,abstract_inverted_index"


def rebuild(inv):
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def main():
    with open(os.path.join(LIB, "library_index.csv"), encoding="utf-8-sig") as fh:
        dois = [r["doi"].lower() for r in csv.DictReader(fh) if r["topic"] == "electrolyte"]
    got = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    todo = [d for d in dois if d not in got]
    print(f"{len(dois)} dois, {len(todo)} to fetch", flush=True)
    for i in range(0, len(todo), 50):
        chunk = todo[i:i + 50]
        params = {"filter": "doi:" + "|".join(chunk), "per-page": 50, "select": SEL, "api_key": KEY}
        for attempt in range(3):
            try:
                r = requests.get("https://api.openalex.org/works", params=params, timeout=90)
                r.raise_for_status()
                break
            except Exception as ex:
                print("retry", attempt, ex, flush=True)
                time.sleep(5)
        else:
            continue
        for w in r.json().get("results", []):
            d = (w.get("doi") or "").lower().replace("https://doi.org/", "")
            got[d] = {"title": w.get("title") or "", "abstract": rebuild(w.get("abstract_inverted_index"))}
        for d in chunk:  # OpenAlex 查不到的也记一笔，避免反复请求
            got.setdefault(d, {"title": "", "abstract": ""})
        json.dump(got, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
        time.sleep(0.5)
    n_abs = sum(1 for d in dois if got.get(d, {}).get("abstract"))
    print(f"done; with OpenAlex abstract: {n_abs}/{len(dois)}", flush=True)


if __name__ == "__main__":
    main()
