"""调色板校验（移植自 dataviz 技能的 validate_palette.js；本机没有 node）。
检查：OKLCH 亮度带、色度下限、Machado 2009 色盲模拟下的 OKLab ΔE×100（相邻或全部配对）、正常视觉下限、与底色的 WCAG 对比度。
用法：python palette_check.py "#hex,#hex,..." [all]
"""
import sys
import math

BAND = (0.43, 0.77)
CHROMA_FLOOR, CVD_TARGET, CVD_FLOOR, NORMAL_FLOOR, CONTRAST_MIN = 0.10, 8.0, 6.0, 15.0, 3.0
MACHADO = {"protan": [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
           "deutan": [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
           "tritan": [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]]}


def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def oklab_lin(rgb):
    r, g, b = rgb
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return [0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s]


def oklch(h):
    L, a, b = oklab_lin(lin(h))
    return L, math.hypot(a, b)


def sim(h, kind):
    r, g, b = lin(h)
    M = MACHADO[kind]
    return [min(1, max(0, M[i][0] * r + M[i][1] * g + M[i][2] * b)) for i in range(3)]


def dE(h1, h2, kind=None):
    a = oklab_lin(sim(h1, kind) if kind else lin(h1))
    b = oklab_lin(sim(h2, kind) if kind else lin(h2))
    return 100 * math.dist(a, b)


def lum(h):
    r, g, b = lin(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    x, y = sorted([lum(a), lum(b)], reverse=True)
    return (x + 0.05) / (y + 0.05)


def validate(pal, pairs="adjacent", surface="#ffffff"):
    n = len(pal)
    pl = [(i, j) for i in range(n) for j in range(i + 1, n)] if pairs == "all" else [(i, i + 1) for i in range(n - 1)]
    rep = {}
    rep["亮度带"] = [(c, round(oklch(c)[0], 3)) for c in pal if not BAND[0] <= oklch(c)[0] <= BAND[1]]
    rep["色度下限"] = [(c, round(oklch(c)[1], 3)) for c in pal if oklch(c)[1] < CHROMA_FLOOR]
    cvd = min((dE(pal[i], pal[j], k), k, pal[i], pal[j]) for k in ("protan", "deutan") for i, j in pl)
    rep["色盲分离"] = ("通过" if cvd[0] >= CVD_TARGET else "下限（需辅助编码）" if cvd[0] >= CVD_FLOOR else "失败", round(cvd[0], 1), cvd[1:])
    nor = min((dE(pal[i], pal[j]), pal[i], pal[j]) for i, j in pl)
    rep["正常视觉"] = ("通过" if nor[0] >= NORMAL_FLOOR else "失败", round(nor[0], 1), nor[1:])
    rep["对比度不足3:1"] = [(c, round(contrast(c, surface), 2)) for c in pal if contrast(c, surface) < CONTRAST_MIN]
    ok = not rep["亮度带"] and not rep["色度下限"] and rep["色盲分离"][0] != "失败" and rep["正常视觉"][0] == "通过"
    return ok, rep


if __name__ == "__main__":
    ok, rep = validate(sys.argv[1].split(","), "all" if len(sys.argv) > 2 and sys.argv[2] == "all" else "adjacent")
    for k, v in rep.items():
        print(k, v)
    print("通过" if ok else "未通过")
