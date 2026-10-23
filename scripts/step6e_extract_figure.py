# 把图注所在页上的大位图按原始分辨率导出
import sys, pymupdf
pdf, key, out = sys.argv[1], sys.argv[2], sys.argv[3]
doc = pymupdf.open(pdf)
for i, p in enumerate(doc):
    if key in p.get_text():
        for im in p.get_images(full=True):
            pix = pymupdf.Pixmap(doc, im[0])
            if pix.width > 800:
                if pix.n - pix.alpha >= 4:
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                k = out.replace(".png", f"_{im[0]}.png"); pix.save(k); print(k, pix.width, pix.height, "页", i + 1)
        break
