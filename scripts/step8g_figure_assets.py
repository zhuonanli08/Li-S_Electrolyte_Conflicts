"""Locate article PDFs and extract native figure images, with page/dpi provenance."""
import argparse,json,re
from pathlib import Path
import fitz
from PIL import Image
from step8a_prepare_debug53 import OUT,save

LIB=Path(r'D:\Desktop\锂电催化\机器学习\skills\Open-Papertrail\Open-Papertrail\corpus\library')

def pdfpath(pid,part):
    mf={m['id']:m for m in json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))}
    papers=json.loads((LIB/'library.json').read_text(encoding='utf-8'))['papers']
    rec=papers.get(mf[pid]['doi'],{})
    name=rec.get('pdf_file' if part=='main' else 'si_file')
    if not name:raise ValueError(f'{pid} {part}: no file recorded')
    candidates=list(LIB.rglob(name))
    if len(candidates)!=1:raise ValueError(f'{pid}: expected one PDF, found {candidates}')
    p=candidates[0]
    if p.suffix.lower()!='.pdf':raise ValueError(f'SI requires document conversion: {p}')
    return p

def main():
    ap=argparse.ArgumentParser();ap.add_argument('pid');ap.add_argument('--part',default='main')
    ap.add_argument('--page',type=int);ap.add_argument('--find');ap.add_argument('--render-page',action='store_true');a=ap.parse_args()
    p=pdfpath(a.pid,a.part);doc=fitz.open(p)
    if a.find:
        for i,page in enumerate(doc):
            tx=page.get_text()
            for m in re.finditer(a.find,tx,re.I):
                print(json.dumps({'page':i+1,'context':tx[max(0,m.start()-70):m.end()+300]},ensure_ascii=False))
        return
    if not a.page:raise ValueError('--page or --find required')
    page=doc[a.page-1];out=OUT/'figures'/a.pid/a.part;out.mkdir(parents=True,exist_ok=True)
    records=[];seen=set()
    if a.render_page:
        # Vector figures have no native bitmap DPI. Rasterize the source page;
        # never interpret PDF drawing paths as measured values.
        target=out/f'p{a.page}_render300.png'
        pix=page.get_pixmap(dpi=300,colorspace=fitz.csRGB,alpha=False);pix.save(target)
        records.append({'pid':a.pid,'part':a.part,'page':a.page,'path':str(target),
                        'width':pix.width,'height':pix.height,'render_dpi':300,
                        'native_bitmap_dpi':None,'source_kind':'PDF页面栅格化；非原生位图',
                        'source_pdf':str(p)})
        save(out/f'p{a.page}_render_assets.json',records)
        print(json.dumps(records,ensure_ascii=False));return
    for im in page.get_images(full=True):
        xref=im[0]
        if xref in seen:continue
        seen.add(xref);pix=fitz.Pixmap(doc,xref)
        if pix.width<250 or pix.height<150:continue
        if pix.colorspace is None:continue
        if pix.colorspace.name not in ('DeviceGray','DeviceRGB'):pix=fitz.Pixmap(fitz.csRGB,pix)
        target=out/f'p{a.page}_xref{xref}.png'
        pix.save(target)
        with Image.open(target) as img:
            if 'A' in img.getbands():
                white=Image.new('RGB',img.size,'white');white.paste(img,mask=img.getchannel('A'));white.save(target)
        rects=page.get_image_rects(xref)
        dpi=[round(pix.width/(r.width/72),1) for r in rects if r.width]
        records.append({'pid':a.pid,'part':a.part,'page':a.page,'xref':xref,'path':str(target),
                        'width':pix.width,'height':pix.height,'dpi':dpi,'source_pdf':str(p)})
    save(out/f'p{a.page}_assets.json',records)
    print(json.dumps(records,ensure_ascii=False))

if __name__=='__main__':main()
