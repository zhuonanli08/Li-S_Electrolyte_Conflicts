"""§5.7 读图：核心层随机 30 篇（种子 20261023）正文/SI 图页是位图还是矢量、位图原始 dpi。只读，需本机 PDF 库 + papertrail 环境。"""
import csv, os, random, collections, glob
import pymupdf

库 = r'D:\Desktop\锂电催化\机器学习\skills\Open-Papertrail\Open-Papertrail\corpus\library'
筛 = r'D:\Desktop\课题二锂硫电解液矛盾归因\output\第二阶段_资格筛选.csv'
idx = {r['doi'].lower(): r for r in csv.DictReader(open(os.path.join(库, 'library_index.csv'), encoding='utf-8-sig'))}
池 = [r for r in csv.DictReader(open(筛, encoding='utf-8-sig'))
      if r['Ⅰ类'] == 'Y' and r['主层'] == 'True' and r['代码建议层别'] == '核心']
random.seed(20261023)
样 = random.sample(池, min(30, len(池)))

def 找(fn):
    if not fn: return None
    for p in glob.glob(os.path.join(库, '*LiS_electrolyte*')) + [库]:
        q = os.path.join(p, fn)
        if os.path.exists('\\\\?\\' + os.path.abspath(q)): return '\\\\?\\' + os.path.abspath(q)
    return None

页计 = collections.Counter(); 篇计 = collections.defaultdict(collections.Counter); dpi = []
for r in 样:
    m = idx.get(r['doi'].lower())
    if not m: 页计['索引里没有'] += 1; continue
    pub = m['publisher'] or '?'
    for 类, fn in (('正文', m['pdf_file']), ('SI', m['si_file'])):
        p = 找(fn)
        if not p or not p.lower().endswith('.pdf'):
            if fn: 页计[f'{类}非PDF或找不到'] += 1
            continue
        d = pymupdf.open(stream=open(p, 'rb').read(), filetype='pdf')
        for pg in d:
            t = pg.get_text()
            if 'Fig' not in t and 'FIG' not in t: continue
            A = pg.rect.width * pg.rect.height
            大图 = [i for i in pg.get_image_info() if (i['bbox'][2]-i['bbox'][0])*(i['bbox'][3]-i['bbox'][1]) > 0.12*A]
            n画 = len(pg.get_drawings())
            if 大图:
                k = '位图'
                for i in 大图:
                    bw = i['bbox'][2]-i['bbox'][0]
                    if bw > 0: dpi.append(i['width']/bw*72)
            elif n画 >= 300: k = '矢量'
            else: continue          # 纯文字页（只是引用了 Fig）
            页计[f'{类}-{k}'] += 1; 篇计[pub][k] += 1
        d.close()
print('抽样', len(样), '篇（核心层主层 Ⅰ类 共', len(池), '篇）')
print('图页：', dict(页计))
for k, v in 篇计.items(): print(' ', k, dict(v))
dpi.sort(); n = len(dpi)
if n: print('位图原始 dpi：n=%d 25%% %.0f 中位 %.0f 75%% %.0f；<150 dpi 的 %d 张' % (n, dpi[n//4], dpi[n//2], dpi[3*n//4], sum(x < 150 for x in dpi)))
