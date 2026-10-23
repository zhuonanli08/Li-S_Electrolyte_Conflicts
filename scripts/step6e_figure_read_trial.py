# -*- coding: utf-8 -*-
"""读图试读（课题二，2026-10-23）：按师兄的步骤
   切子图 → 先标定坐标轴（刻度线 + 用户/模型给的刻度数字，检查残差）→ 网格
   → 按图例颜色抠出每条曲线的点 → 换算成数据坐标 → 取首点、末点、指定圈的值。
复用 毕设/文献提取/script/取色读图.py（v3）的 找坐标框 / 找刻度 / 标定 / 同色掩膜 / 暗，不改原文件。
任务里的“语义”（子图范围、刻度数字、图例框、要排除的文字框、每条曲线对应哪个配方编号）
正式流程由视觉模型给，这里由 Claude 看图后手填。"""
import sys
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, r"D:\Desktop\毕设\文献提取\script")
import 取色读图 as v3  # noqa: E402


def load(path, crop):
    img = np.array(Image.open(path).convert("RGB"))
    x0, y0, x1, y1 = crop
    return img[y0:y1, x0:x1].copy()


def calib(img, frame, axis, labels):
    ticks, text = v3.找刻度(img, frame, axis)
    left, right, top, bottom = frame
    ends = (bottom, top) if axis == "y" else (left, right)
    a, b = v3.标定(ticks, labels, axis, 端点=ends, 文字=text)[:2]
    # 检查：每个刻度数字反算回像素，再看离最近的刻度线多远（像素）
    cand = np.array(sorted({p for p, _ in ticks} | {e for e in ends if e is not None}), float)
    resid = [float(np.min(np.abs(cand - (v - b) / a))) for v in labels]
    return a, b, resid


def series_mask(img, frame, kind, color=None, excl=()):
    left, right, top, bottom = frame
    if kind == "black":
        m = (img.max(-1) < 90)
    else:
        m = v3.同色掩膜(img, np.array(color, np.uint8))
    m[:, :left + 4] = False
    m[bottom - 3:, :] = False
    if right:
        m[:, right - 3:] = False
    if top:
        m[:top + 4, :] = False
    for x0, y0, x1, y1 in excl:
        m[y0:y1, x0:x1] = False
    # 开运算去掉虚线、库仑效率细线、刻度、细字笔画（≤4 像素粗），留下圆点标记（约 12 像素）
    from scipy import ndimage
    m = ndimage.binary_opening(m, structure=np.ones((5, 5)))
    return m


def read(m, cx, cy, mw):
    """mw = 标记宽（像素）。首点：最左一列起 mw 宽内彩色像素的中位 y；末点：最右像素往回半个标记。"""
    cols = np.nonzero(m.any(0))[0]
    xl, xr = cols.min(), cols.max()
    ys = np.nonzero(m[:, xl:xl + mw].any(1))[0]
    first_y = float(np.median(ys))
    to_x = lambda px: cx[0] * px + cx[1]  # noqa: E731
    to_y = lambda py: cy[0] * py + cy[1]  # noqa: E731
    return {"首点圈数": round(to_x(xl + mw / 2), 1), "首点值": round(to_y(first_y), 1),
            "末点圈数": round(to_x(xr - mw / 2), 1)}


def value_at(m, cx, cy, cycle, mw):
    px = int(round((cycle - cx[1]) / cx[0]))
    ys = np.nonzero(m[:, max(0, px - mw // 2):px + mw // 2 + 1].any(1))[0]
    return None if len(ys) == 0 else round(cy[0] * float(np.median(ys)) + cy[1], 1)


def run(task, out_dir):
    img = load(task["图"], task["子图"])
    frame = v3.找坐标框(img)
    cx = calib(img, frame, "x", task["x刻度"])
    cy = calib(img, frame, "y", task["y刻度"])
    res = {"编号": task["编号"], "坐标框": [int(v) if v is not None else None for v in frame],
           "x 标定残差(像素)": [round(r, 1) for r in cx[2]], "y 标定残差(像素)": [round(r, 1) for r in cy[2]],
           "每格(数据/像素)": {"x": round(cx[0], 4), "y": round(cy[0], 4)}, "曲线": {}}
    im = Image.fromarray(img)
    dr = ImageDraw.Draw(im)
    for s in task["曲线"]:
        color = None
        if s["类型"] == "color":
            color = v3.取图例色(img, s["图例框"])
            res.setdefault("图例色", {})[s["配方编号"]] = color.tolist()
        m = series_mask(img, frame, s["类型"], color, task.get("排除", []))
        r = read(m, cx, cy, task["标记宽"])
        for c in task.get("取圈", []):
            r[f"第{c}圈值"] = value_at(m, cx, cy, c, task["标记宽"])
        res["曲线"][s["配方编号"]] = r
        ys, xs = np.nonzero(m)
        for x, y in zip(xs[::5], ys[::5]):
            dr.point((x, y), fill=(0, 160, 255) if s["类型"] == "black" else (0, 200, 0))
    left, right, top, bottom = frame
    dr.rectangle([left, top or 0, right or img.shape[1] - 1, bottom], outline=(0, 0, 255), width=2)
    # 网格：按标定画出每个刻度位置，核对图上一眼能看出标定准不准
    for v in task["x刻度"]:
        px = (v - cx[1]) / cx[0]
        dr.line([(px, top or 0), (px, bottom)], fill=(255, 140, 0), width=1)
    for v in task["y刻度"]:
        py = (v - cy[1]) / cy[0]
        dr.line([(left, py), (right or img.shape[1] - 1, py)], fill=(255, 140, 0), width=1)
    for x0, y0, x1, y1 in task.get("排除", []):
        dr.rectangle([x0, y0, x1, y1], outline=(160, 160, 160), width=1)
    im.save(Path(out_dir) / f"核对_{task['编号']}.png")
    return res


if __name__ == "__main__":
    tasks = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    for t in tasks:
        try:
            print(json.dumps(run(t, Path(sys.argv[1]).parent), ensure_ascii=False))
        except Exception as e:  # noqa: BLE001
            print(t["编号"], "失败：", e)
