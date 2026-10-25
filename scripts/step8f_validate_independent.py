"""Validate frozen source-only predictions; never edit them or score semantics.

Evidence pointers are resolved to the indexed original text. Mechanical flags
are review inputs, not precision/recall. First observed SHA256 is preserved.
"""
import argparse
import collections
import hashlib
import json
import math
import re
import unicodedata
from step8a_prepare_debug53 import OUT, save

CONDITIONS = ['sulfur_loading', 'ES', 'ES_unit', 'Li_thickness', 'rate',
              'formation', 'temperature', 'LiNO3', 'one_C']
NUM = re.compile(r'(?<![\w.])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?')

def clean(s):
    return unicodedata.normalize('NFKC', str(s)).replace('−', '-').replace(',', '')

def scalar(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v) if math.isfinite(v) else None
    s = clean(v).strip()
    if re.fullmatch(r'[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?', s):
        return float(s)
    return None

def metric_kind(metric):
    if re.search(r'库仑效率|coulomb|\bCE\b', metric, re.I):
        return 'ce'
    if re.search(r'衰减率|衰减速度|过电位|极化|阻抗|自放电率|穿梭电流|decay rate|overpotential|polariz|impedance|shuttle current', metric, re.I):
        return 'lower'
    if re.search(r'容量|能量密度|寿命|保持率|循环圈|capacity|energy density|lifespan|retention|cycle life', metric, re.I):
        return 'higher'
    return None

def numeric_direction(r):
    if r.get('same_conditions') is not True:
        return {'direction': '不判', 'reason': '未确认条件相同'}
    if r.get('basis') != 'numeric':
        return {'direction': None, 'reason': '作者定性/仅图项另列，不当成数值判向'}
    a, b = scalar(r.get('value_A')), scalar(r.get('value_B'))
    if a is None or b is None:
        return {'direction': '不判', 'reason': '非精确标量；近似/界限/区间待按原文复核'}
    kind = metric_kind(r.get('metric', ''))
    if kind is None:
        return {'direction': '不判', 'reason': '该指标未定义单调优劣'}
    if kind == 'ce':
        return {'direction': None, 'delta': a-b,
                'delta_unit': '百分点' if '%' in r.get('unit', '') else r.get('unit', ''),
                'reason': '库仑效率仅记差，不用5%阈值；作者判断另列'}
    if a < 0 or b < 0:
        return {'direction': '不判', 'reason': '负值需先核对指标及符号'}
    diff = abs(a-b)/max(a,b) if max(a,b) else 0
    dr = '差异小' if diff < .05 else ('变好' if ((a>b) == (kind=='higher')) else '变坏')
    return {'direction':dr, 'relative_difference':diff,
            'reason':'abs(A-B)/max(A,B)，阈值严格小于5%'}

def validate(d, src):
    pid=d['paper_id']; issues=[]; evidence=[]; directions=[]
    def flag(unit, code, detail):
        issues.append({'paper_id':pid,'unit':unit,'code':code,'detail':detail})
    def refs(obj, unit, required=True, extra_ids=()):
        ids=obj.get('evidence_ids', [])
        if not isinstance(ids, list):
            flag(unit,'证据字段格式','evidence_ids必须为列表');ids=[]
        if required and not ids:flag(unit,'缺原句','没有evidence_ids')
        for sid in ids:
            if sid not in src:flag(unit,'未知证据',str(sid))
            else:evidence.append({'paper_id':pid,'unit':unit,**src[sid]})
        return ' '.join(src[s]['text'] for s in list(ids)+list(extra_ids) if s in src)
    def numbers(v, q, unit, field):
        if v is None or isinstance(v,(dict,list)):return
        vals=[float(s) for s in NUM.findall(clean(v))]
        if not vals:return
        source_vals={float(s) for s in NUM.findall(clean(q))}
        absent=[x for x in vals if x not in source_vals]
        if absent:flag(unit,'数字待核',{'field':field,'value':v,'not_found':absent,
                                    'note':'可能为英文数字词、公式或排版；必须再看原文，不自动判错'})
    fs=d.get('formulations',[]); ts=d.get('tests',[])
    fids=[f.get('id') for f in fs];tids=[t.get('id') for t in ts]
    for name, ids in [('配方',fids),('测试',tids)]:
        if len(ids)!=len(set(ids)):flag(pid,'重复编号',name)
    if d.get('control_id') and d['control_id'] not in fids:flag(pid,'对照编号不存在',d['control_id'])
    all_condition_evidence=[s for t in ts for s in t.get('evidence_ids',[]) if s in src]
    for f in fs:
        unit='F/'+str(f.get('id'));q=refs(f,unit)
        for c in f.get('components',[]):numbers(c.get('amount'),q,unit,c.get('name'))
    for label in ['gradients','properties','design_claims']:
        for i,x in enumerate(d.get(label,[]),1):refs(x,label+'/'+str(i))
    for t in ts:
        tu='T/'+str(t.get('id'));q=refs(t,tu)
        cq=q+' '+' '.join(src[s]['text'] for s in all_condition_evidence)
        for k in CONDITIONS:
            if k not in t.get('conditions',{}):flag(tu,'条件字段缺失',k)
            else:numbers(t['conditions'][k],cq,tu,k)
        for f in t.get('formulations',[]):
            if f not in fids:flag(tu,'测试引用未知配方',f)
        rids=[]
        for i,r in enumerate(t.get('results',[]),1):
            rid=r.get('id',f'R{i}');rids.append(rid);ru=tu+'/'+str(rid)
            rq=refs(r,ru,required=r.get('basis')!='figure_only')
            for k in ['A','B']:
                if r.get(k) and r[k] not in fids:flag(ru,'结果引用未知配方',{k:r[k]})
            for k in ['value_A','value_B']:numbers(r.get(k),rq,ru,k)
            dr=numeric_direction(r)
            directions.append({'paper_id':pid,'unit':ru,'metric':r.get('metric'),
                               'author_direction':r.get('direction_text'),**dr})
            if dr['direction'] and dr['direction']!=r.get('direction_text'):
                flag(ru,'方向待核',{'GPT':r.get('direction_text'),'code':dr})
        if len(rids)!=len(set(rids)):flag(tu,'重复结果编号',rids)
    mids=[]
    for m in d.get('mechanisms',[]):
        mid=m.get('id');mids.append(mid);mu='M/'+str(mid);refs(m,mu)
        for t in m.get('test_ids',[]):
            if t not in tids:flag(mu,'机制引用未知测试',t)
        for c in m.get('categories',[]):
            if c not in ['正极反应','多硫化物穿梭','负极锂','电解液消耗']:flag(mu,'过程类别非法',c)
        if m.get('source_type') not in ['本文结论','本文结论（与他文一致）','本文推测','转述他文或通用说法']:
            flag(mu,'来源分类非法',m.get('source_type'))
    if len(mids)!=len(set(mids)):flag(pid,'重复机制编号',mids)
    return issues,evidence,directions

def main():
    mf=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    lockpath=OUT/'prediction_freeze.json'
    locks=json.loads(lockpath.read_text(encoding='utf-8')) if lockpath.exists() else {}
    issues=[];evidence=[];directions=[];counts={}
    for p in sorted((OUT/'independent_predictions').glob('*.json')):
        raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        d=json.loads(raw);pid=d['paper_id']
        if pid in locks and locks[pid]['sha256']!=digest:
            raise ValueError(f'冻结预测被修改：{pid}；修订必须另存revisions')
        locks.setdefault(pid,{'sha256':digest,'path':str(p.relative_to(OUT))})
        src={s['id']:s for s in json.loads((OUT/'sources'/f'{pid}.json').read_text(encoding='utf-8'))}
        ii,ee,dd=validate(d,src);issues+=ii;evidence+=ee;directions+=dd
        counts[pid]={'formulations':len(d.get('formulations',[])), 'tests':len(d.get('tests',[])),
                     'results':sum(len(t.get('results',[])) for t in d.get('tests',[])),
                     'mechanisms':len(d.get('mechanisms',[])),
                     'figure_requests':len(d.get('figure_requests',[]))}
    save(lockpath,locks)
    dest=OUT/'validation'
    save(dest/'issues.json',issues);save(dest/'evidence.json',evidence)
    save(dest/'numeric_directions.json',directions)
    stats={'completed_papers':len(counts),'expected_papers':len(mf),
           'missing_papers':[m['id'] for m in mf if m['id'] not in counts],
           'counts':counts,'issue_types':dict(collections.Counter(i['code'] for i in issues)),
           'precision':None,'recall':None,'note':'机械检查，不能替代语义核对或召回率'}
    save(dest/'status.json',stats)
    print(json.dumps({k:v for k,v in stats.items() if k!='counts'},ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
    if a.self_test:
        r={'basis':'numeric','same_conditions':True,'metric':'首圈容量','value_A':100,'value_B':95}
        assert numeric_direction(r)['direction']=='变好'
        r['value_B']=96;assert numeric_direction(r)['direction']=='差异小'
        r['metric']='过电位';r['value_B']=120;assert numeric_direction(r)['direction']=='变好'
        r['same_conditions']=False;assert numeric_direction(r)['direction']=='不判'
        r.update(same_conditions=True,metric='库仑效率',value_A=99.9,value_B=99.8,unit='%')
        assert numeric_direction(r)['direction'] is None
        assert abs(numeric_direction(r)['delta']-.1)<1e-8
        r.update(metric='首圈容量',value_A='≈100');assert numeric_direction(r)['direction']=='不判'
        print('方向边界、条件不同、CE与近似数拦截通过')
    else:main()
