"""Prepare candidate native images for pending figures; no semantic decisions."""
import collections,json,re,zipfile,xml.etree.ElementTree as ET,io,posixpath
from pathlib import Path
import pymupdf as fitz
from PIL import Image
from step8a_prepare_debug53 import OUT,save
from step8g_figure_assets import sourcepath

def docx_assets(source,pid,part,reqs):
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
        'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}
    dest=OUT/'figures'/pid/part;dest.mkdir(parents=True,exist_ok=True);rows=[]
    with zipfile.ZipFile(source) as z:
        doc=ET.fromstring(z.read('word/document.xml'))
        rel={x.attrib['Id']:posixpath.normpath('word/'+x.attrib['Target']) for x in ET.fromstring(z.read('word/_rels/document.xml.rels'))}
        paragraphs=[]
        for p in doc.findall('.//w:p',ns):
            text=''.join(t.text or '' for t in p.findall('.//w:t',ns))
            pictures=[]
            for drawing in p.findall('.//w:drawing',ns):
                extent=drawing.find('.//wp:extent',ns)
                for b in drawing.findall('.//a:blip',ns):
                    rid=b.get('{'+ns['r']+'}embed')
                    if rid in rel:pictures.append((rel[rid],int(extent.get('cx')) if extent is not None else None))
            paragraphs.append((text,pictures))
        for r in reqs:
            labels=list(dict.fromkeys(re.findall(r'(?<![A-Za-z0-9])S?\d+',r.get('figure',''))));hits=[];assets=[]
            for label in labels:
                pat=re.compile(r'^\s*(?:Figure|Fig\.?)\s*'+re.escape(label)+r'(?=\s|\.|\(|[a-z]|$)',re.I)
                for i,(text,pics) in enumerate(paragraphs):
                    if not pat.search(text):continue
                    hits.append({'label':label,'paragraph':i+1,'caption_context':text[:450]})
                    candidates=pics
                    if not candidates:
                        for distance in range(1,5):
                            for j in [i-distance,i+distance]:
                                if 0<=j<len(paragraphs) and paragraphs[j][1]:candidates=paragraphs[j][1];break
                            if candidates:break
                    for name,cx in candidates:
                        target=dest/(Path(name).stem+'.png')
                        try:
                            with Image.open(io.BytesIO(z.read(name))) as im:
                                width,height=im.size
                                if not target.exists():
                                    rgba=im.convert('RGBA');white=Image.new('RGB',im.size,'white');white.paste(rgba,mask=rgba.getchannel('A'));white.save(target)
                            assets.append({'pid':pid,'part':part,'paragraph':i+1,'path':str(target),'width':width,'height':height,
                                           'dpi':[round(width/(cx/914400),1)] if cx else [],'source_kind':'DOCX内嵌原图，透明底转白','source_document':str(source),'media_part':name})
                        except Exception as ex:assets.append({'media_part':name,'error':str(ex)})
            rows.append({'paper_id':pid,'request_index':r['request_index'],'figure':r.get('figure'),'part':part,'caption_candidates':hits,'candidate_assets':assets,'status':'候选已准备' if any('path' in a for a in assets) else '未定位图像，需文档渲染'})
    save(dest/'docx_assets.json',rows);return rows

def extract(doc,page_index,pid,part,source):
    page=doc[page_index];dest=OUT/'figures'/pid/part;dest.mkdir(parents=True,exist_ok=True)
    meta=dest/f'p{page_index+1}_assets.json'
    if meta.exists():
        old=json.loads(meta.read_text(encoding='utf-8'))
        if old and all(Path(x['path']).exists() for x in old):return old
    records=[];seen=set()
    for im in page.get_images(full=True):
        xr=im[0]
        if xr in seen:continue
        seen.add(xr);pix=fitz.Pixmap(doc,xr)
        if pix.width<250 or pix.height<150 or pix.colorspace is None:continue
        if pix.colorspace.name not in ('DeviceGray','DeviceRGB'):pix=fitz.Pixmap(fitz.csRGB,pix)
        target=dest/f'p{page_index+1}_xref{xr}.png'
        if not target.exists():
            pix.save(target)
            with Image.open(target) as img:
                if 'A' in img.getbands():
                    white=Image.new('RGB',img.size,'white');white.paste(img,mask=img.getchannel('A'));white.save(target)
        rects=page.get_image_rects(xr)
        records.append({'pid':pid,'part':part,'page':page_index+1,'xref':xr,'path':str(target),
                        'width':pix.width,'height':pix.height,'dpi':[round(pix.width/(r.width/72),1) for r in rects if r.width],
                        'source_pdf':str(source)})
    if not records:
        target=dest/f'p{page_index+1}_render300.png'
        if not target.exists():page.get_pixmap(dpi=300,colorspace=fitz.csRGB,alpha=False).save(target)
        records=[{'pid':pid,'part':part,'page':page_index+1,'path':str(target),'render_dpi':300,'native_bitmap_dpi':None,'source_kind':'PDF栅格化，非原生位图','source_pdf':str(source)}]
    save(meta,records);return records

def main():
    state=json.loads((OUT/'figure_status.json').read_text(encoding='utf-8'))
    groups=collections.defaultdict(list)
    for r in state['requests']:
        if not r['complete']:groups[(r['paper_id'],r.get('part','main'))].append(r)
    rows=[]
    for (pid,part),reqs in groups.items():
        try:
            source=sourcepath(pid,part)
            if source.suffix.lower()=='.docx':rows.extend(docx_assets(source,pid,part,reqs));continue
            if source.suffix.lower()!='.pdf':raise ValueError('暂不支持文档格式 '+source.suffix)
            doc=fitz.open(source);texts=[p.get_text() for p in doc]
            for r in reqs:
                labels=list(dict.fromkeys(re.findall(r'(?<![A-Za-z0-9])S?\d+',r.get('figure',''))))
                hits=[]
                for label in labels:
                    pat=re.compile(r'(?m)^\s*(?:Figure|Fig\.?)\s*'+re.escape(label)+r'(?=\s|\.|\(|[a-z]|$)',re.I)
                    for i,tx in enumerate(texts):
                        m=pat.search(tx)
                        if m:hits.append({'label':label,'page':i+1,'caption_context':tx[m.start():m.start()+400]})
                assets=[]
                for i in sorted({x['page']-1 for x in hits}):assets+=extract(doc,i,pid,part,source)
                rows.append({'paper_id':pid,'request_index':r['request_index'],'figure':r.get('figure'),'part':part,'caption_candidates':hits,'candidate_assets':assets,'status':'候选已准备' if hits else '未定位图注，需人工定位'})
            doc.close()
        except Exception as ex:
            rows.extend({'paper_id':pid,'request_index':r['request_index'],'figure':r.get('figure'),'part':part,'status':'未准备','reason':str(ex)} for r in reqs)
    save(OUT/'figure_asset_queue.json',rows)
    print(json.dumps({'requests':len(rows),'status_counts':dict(collections.Counter(x['status'] for x in rows)),
                      'unique_images':len({x['path'] for r in rows for x in r.get('candidate_assets',[]) if 'path' in x})},ensure_ascii=False))
if __name__=='__main__':main()
