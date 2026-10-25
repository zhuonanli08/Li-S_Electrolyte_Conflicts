"""Prepare source-only packets for in-chat GPT extraction. No API calls.

Existing extractions remain separate evaluation references. Scientific content
from those references is not used to generate source packets.
"""
from pathlib import Path
import csv
import hashlib
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'GPT_v4_调试集53篇_2026-10-24'
CACHE = ROOT / 'output' / 'text_cache'

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def norm(s):
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'([A-Za-z])-\s*\n\s*([a-z])', r'\1\2', s)
    return re.sub(r'\s+', ' ', s).strip()

def segments(raw, part):
    out = []
    pages = re.split(r'<<PAGE\s+(\d+)>>', raw)
    if len(pages) == 1:
        pages = ['', '0', raw]
    for i in range(1, len(pages), 2):
        page, body = int(pages[i]), pages[i+1]
        txt = norm(body)
        ss = re.split(r'(?<=[.!?])\s+(?=[A-Z(\[])', txt)
        for s in ss:
            ss2 = re.split(r'(?<=;)\s+', s) if len(s)>4000 else [s]
            for q in ss2:
                if len(q)>=18:
                    out.append({'id':f'{part[0].upper()}{len(out)+1:04}', 'part':part,'page':page,'text':q})
    return out

def main():
    trial={r['编号']:r for r in csv.DictReader((ROOT/'output/第二阶段_C步试提/抽样名单.csv').open(encoding='utf-8-sig'))}
    pool={r['池编号']:r for r in csv.DictReader((ROOT/'output/第一阶段_初筛池.csv').open(encoding='utf-8-sig'))}
    manifest=[]
    for folder in ['第一阶段_证据表','第二阶段_C步试提']:
        for p in sorted((ROOT/'output'/folder/'json').glob('*.json')):
            old=json.loads(p.read_text(encoding='utf-8')); pid=p.stem
            meta=pool.get(pid,trial.get(pid,{}))
            doi=old.get('paper',{}).get('doi') or meta.get('doi')
            if not doi: raise ValueError(f'Missing DOI {pid}')
            stem=re.sub(r'[^\w.-]+','_',doi)
            rec={'id':pid,'doi':doi,'title':meta.get('题名',''),'reference':str(p.relative_to(ROOT)),'stem':stem}
            sources=[]
            for part in ['main','si']:
                f=CACHE/f'{stem}.{part}.txt'; raw=f.read_text(encoding='utf-8') if f.exists() else ''
                rec[f'{part}_chars']=len(raw)
                rec[f'{part}_sha256']=hashlib.sha256(raw.encode()).hexdigest()
                sources+=segments(raw,part)
            if not rec['main_chars']: raise ValueError(f'Missing main text {pid}')
            save(OUT/'sources'/f'{pid}.json',sources); manifest.append(rec)
    assert len(manifest)==53 and len({r['doi'].lower() for r in manifest})==53
    assert not {'S34','S35','S38','S52','S55','S56'} & {r['id'] for r in manifest}
    save(OUT/'manifest.json',manifest)
    save(OUT/'run_config.json',{'date':'2026-10-24','mode':'当前对话 GPT 提取；不调用外部 API',
       'model':'Codex 当前对话 GPT；API 模型快照未固定','scheme':'现行方案 §5.7 v4','scope':53,
       'reference_status':'旧 Claude 开发材料，非完整人工 gold',
       'evaluation_status':'待提取与逐项匹配；不得把参考缺项自动判为错提',
       'metrics_units':['测试及条件','比较内一个指标的方向','机制说法'],
       'warnings':['调试集不代表独立测试准确率','当前对话提取不等价于可复现的 API 批量测评']})
    print(json.dumps({'papers':len(manifest),'main_chars':sum(x['main_chars'] for x in manifest),
       'si_chars':sum(x['si_chars'] for x in manifest),'missing_si':[x['id'] for x in manifest if not x['si_chars']]},ensure_ascii=False))

if __name__=='__main__': main()
