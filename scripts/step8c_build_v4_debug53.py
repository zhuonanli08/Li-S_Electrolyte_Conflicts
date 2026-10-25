"""Migrate the 53 development records to v4; validate source provenance.

This is reuse + source supplementation, NOT an independent extraction run.
Consequently reference overlap is not an accuracy score. No human cells change.
"""
from pathlib import Path
import json, re, unicodedata, hashlib, collections
from step8a_prepare_debug53 import ROOT, OUT, CACHE, save, norm

V4=ROOT/'output/论断式提取表样_v4_2026-10-24/json'
MISSING='未报告'
CAT={'正极反应':r'cathod|sulfur (?:redox|conversion|utilization)|Li2S (?:deposition|nucleation)|polarization|kinetic',
 '多硫化物穿梭':r'shuttl|self.discharge', '负极锂':r'anod|Li.metal|lithium.metal|dendrit|dead li|\bSEI\b',
 '电解液消耗':r'electrolyte (?:consum|deplet|exhaust|decompos)|consum.{0,20}electrolyte|LiNO3.{0,20}(?:consum|deplet)'}

def compact(s):
    s=unicodedata.normalize('NFKC',str(s)).lower()
    return re.sub(r'[^a-z0-9\u4e00-\u9fff]+','',s)

class Locate:
    def __init__(self,pid):
        self.segs=json.loads((OUT/'sources'/f'{pid}.json').read_text(encoding='utf-8'))
        self.norms=[compact(s['text']) for s in self.segs]
        self.joined={}
        for part in ['main','si']:
            offsets=[];txt=''
            for s,n in zip(self.segs,self.norms):
                if s['part']==part:
                    offsets.append((len(txt),len(txt)+len(n),s));txt+=n
            self.joined[part]=(txt,offsets)
    def quote(self,q):
        if isinstance(q,dict):q=q.get('原句','')
        if not q:return {'状态':'缺原句','原句':'','定位':[]}
        bits=[compact(x) for x in re.split(r'…|\.\.\.|‖',str(q)) if len(compact(x))>15]
        hit=[];missing=[]
        for b in bits:
            found=next((s for s,n in zip(self.segs,self.norms) if b in n),None)
            if found:hit.append(found)
            else:
                # PDF line/page boundaries may split a sentence.
                found=next(({'id':self.segs[i]['id']+'–'+self.segs[i+1]['id'],'part':self.segs[i]['part'],
                             'page':self.segs[i]['page'],'text':self.segs[i]['text']+' '+self.segs[i+1]['text']}
                            for i in range(len(self.segs)-1) if self.segs[i]['part']==self.segs[i+1]['part'] and b in self.norms[i]+self.norms[i+1]),None)
                if found:hit.append(found)
                else:
                    located=False
                    for txt,spans in self.joined.values():
                        at=txt.find(b)
                        if at>=0:
                            hit.extend(z for start,end,z in spans if start<at+len(b) and end>at)
                            located=True;break
                    if not located:missing.append(b)
        uniq={s['id']:s for s in hit}
        return {'状态':'原句定位通过' if bits and not missing else '原句未完整定位','原句':q,
                '定位':[{'证据编号':s['id'],'部分':s['part'],'页':s['page'],'完整句':s['text']} for s in uniq.values()]}

def rawstr(v):return MISSING if v is None or v=='' else str(v)

def components(raw):
    # Names can be parsed; unspecified amounts/chemical roles remain unknown.
    names=re.findall(r'LiTFSI|LiFSI|LiNO[₃3]|LiTfO|LiTDI|LiClO4|LiPF6|LiBF4|LiBr|LiI|DOL|DME|DMSO|THF|TTE|HFE|TFTFE|ETFE|DEE|DMC|DIPS|DIPE|TEGDME|DEGDME|ACN|EC|PC|FEC|BTFE|TTFE|F4DEE',raw)
    result=[]
    for name in dict.fromkeys(names):
        role='添加剂' if name in ['LiNO3','LiNO₃','LiBr','LiI'] else '盐' if name.startswith('Li') else '角色待原文确认'
        match=re.search(r'(\d+(?:\.\d+)?)\s*(M|m|wt%|vol%|mol/L)\s*'+re.escape(name),raw)
        result.append({'名称':name,'角色':role,'用量':match[1] if match else None,'单位':match[2] if match else '',
                       '备注':'其余用量和比例见配方原文；未自动分配混合比例'})
    return result

def metric_name(s,unit='',point=''):
    if s=='循环保持率或寿命':
        return '容量保持率' if '%' in unit else '寿命' if '圈' in unit else '循环保持率或寿命'
    if s=='指定圈数放电容量':return '指定圈数容量'
    if '库仑效率' in s:return '库仑效率'
    if s=='过电位或动力学':return '过电位或动力学'
    return s

def numeric(v):
    if isinstance(v,(int,float)):return float(v)
    m=re.fullmatch(r'≈?\s*(-?\d+(?:\.\d+)?)',str(v))
    return float(m[1]) if m else None

def direction(a,b,metric,point,comparable,old,qstatus):
    if not comparable:return '不判','取值点或测试条件不同'
    if qstatus!='原句定位通过':return '不判','原句尚未完整定位'
    av,bv=numeric(a),numeric(b)
    if av is not None and bv is not None:
        if '库仑效率' in metric and (av>100 or bv>100):return '不判','CE 超过 100%，不能按越高越好'
        if metric in ['其他','多硫化物溶解或穿梭','过电位或动力学','循环保持率或寿命']:return '不判','旧指标混合含义，须拆分后判断'
        smaller=any(k in metric for k in ['过电位','阻抗','衰减率','自放电','穿梭电流'])
        if not '库仑效率' in metric and max(abs(av),abs(bv)) and abs(av-bv)/max(abs(av),abs(bv))<.05:return '差异小','程序按 <5%'
        if av==bv:return '差异小','相等'
        return ('变好' if (av<bv if smaller else av>bv) else '变坏'),'程序比较同项数值'
    # Preserve, but do not endorse a qualitative direction inherited from old data.
    return {'A更好':'变好','A更差':'变坏','差异小':'差异小'}.get(old,'不判'),'沿用旧定性判断，语义待核' if old in ['A更好','A更差','差异小'] else '没有可比较的数值或明确方向'

def source_tag(text):
    if re.search(r'\b(speculat|may\b|might\b|suggest|expect|anticipat|believe|perhaps)',text,re.I):return '本文推测（待语义复核）'
    if re.search(r'previous|reported|literature|well.known|it is known',text,re.I):return '转述风险，来源待语义复核'
    return '来源待语义复核'

def old_to_v4(m,old,loc):
    pid=m['id'];s=pid.startswith('S')
    doc={'文献编号':pid,'DOI':m['doi'],'文献':m['title'],'全文缓存':m['stem'],'格式':'v4迁移与补提',
         '提取来源':'既有 Claude 开发材料迁移；GPT 原文核对和补提；非独立提取',
         '对照':None,'对照类型':'待确认','配方':[],'梯度':[],'性质':[],'测试':[],'机制':[],'设计主张':[],
         '缺口':[],'原始参考文件':m['reference']}
    es=old['electrolytes'] if s else old['电解液']
    for eid,e in es.items():
        raw='；'.join(f'{k}:{e.get(k,"")}' for k in ['solvent','salt','diluent','lino3','additive']) if s else e.get('配方','')
        doc['配方'].append({'代号':eid,'作者原名':e.get('name',e.get('名称',eid)),'组分':components(raw),
         '配方原文记载':raw,'原句':e.get('quote',''),'证据核对':loc.quote(e.get('quote','')),
         '状态':'沿用已有配方；组分角色及比例未完整核实'})
    cs=old['conditions'] if s else old['条件']
    for cid,c in cs.items():
        t={'编号':cid,'名称':c.get('desc',cid),'电池':rawstr(c.get('cell',c.get('电池'))),
          '硫载量':rawstr(c.get('S_loading',c.get('硫载量'))),'E/S':rawstr(c.get('ES_reported',c.get('E/S'))),
          'E/S单位':c.get('ES_unit','原文单位'),'锂厚':rawstr(c.get('Li_um',c.get('锂厚'))),
          '倍率':rawstr(c.get('rate_author',c.get('倍率'))),'倍率备注':c.get('rate_note',''),
          '1C定义':rawstr(c.get('rate_1C_def',c.get('1C定义'))),'化成':'未独立核对',
          '温度':rawstr(c.get('temp_C',c.get('温度'))),'LiNO₃':'见各配方，测试覆盖关系待核',
          '条件原句':c.get('quote',c.get('原句','')),'配方':[],'结果':[],
          '状态':'旧条件组；按 v4 测试定义拆分尚待复核'}
        t['证据核对']=loc.quote(t['条件原句']);doc['测试'].append(t)
    tests={t['编号']:t for t in doc['测试']}
    comps=old['comparisons'] if s else [dict(z,**{'比较A':x['A'],'比较B':x['B'],'条件':x['条件'],'B角色':x.get('B角色',''),'溶剂化依据':x.get('溶剂化依据','')}) for x in old['比较'] for z in x['指标']]
    for i,c in enumerate(comps,1):
        cid=c.get('cond',c.get('条件'));t=tests[cid]
        a=c['A'] if s else c['比较A'];b=c['B'] if s else c['比较B']
        for e in [a,b]:
            if e not in t['配方']:t['配方'].append(e)
        va=c.get('val_A') if s else c.get('A');vb=c.get('val_B') if s else c.get('B')
        metric=metric_name(c.get('metric',c.get('指标','')),c.get('unit',c.get('单位','')))
        q=c.get('quote',c.get('原句',''));qcheck=loc.quote(q)
        olddir=c.get('obs_dir',c.get('方向',''))
        d,why=direction(va,vb,metric,c.get('point',c.get('取值点','')),c.get('comparable_point',True),olddir,qcheck['状态'])
        r={'编号':f'R{i:03}','指标':metric,'取值点':c.get('point',c.get('取值点','')),'比较A':a,'比较B':b,'数值':{a:va,b:vb},
          '单位':c.get('unit',c.get('单位','')),'原句':q,'证据核对':qcheck,'方向':d,'判定依据':why,
          '旧方向':olddir,'位置':c.get('evidence_loc',c.get('来源','')),'备注':c.get('note',c.get('备注','')),
          '记录来源':'沿用既有提取，非本轮盲提'}
        t['结果'].append(r)
        rq=c.get('reason_quote','')
        if rq:
            check=loc.quote(rq)
            full=' '.join(x['完整句'] for x in check['定位'])
            doc['机制'].append({'编号':f'M{len(doc["机制"])+1:03}','A':a,'B':b,'概括':c.get('author_judgement',''),
              '原句':full or rq,'原始摘句':rq,'证据核对':check,'来源':source_tag(full or rq),
              '过程大类':[k for k,v in CAT.items() if re.search(v,full or rq,re.I)],
              '落到':[{'测试':cid,'表现':metric}],'记录来源':'旧归因回到原文扩成整句；待语义复核'})
    if s:
        for d in old['descriptors']:
            doc['性质'].append({'性质':d.get('object',''),'测法':d.get('scale',''),'测量体系':d.get('mapping_note',''),
              '数值':{} if re.search('DFT|结合能|binding energy',str(d),re.I) else d.get('values',{}),
              '方向依据':d.get('stronger_if',''),'原句':d.get('quote',''),'证据核对':loc.quote(d.get('quote','')),
              '备注':'DFT/MD 计算值不作跨篇尺子；原论文解释保留' if re.search('DFT|结合能|binding energy',str(d),re.I) else ''})
    else:
        for c in old['比较']:
            doc['性质'].append({'性质':'旧记录溶剂化依据','比较':f"{c['A']} vs {c['B']}",'原记载':c.get('溶剂化依据',''),
                               '状态':'未分开 Li+ 溶剂化/多硫化物溶剂化/溶解度，待补提'})
    doc['缺口']=['配方组分与梯度档位尚需按全文完整补提','旧条件组未完全按 v4 拆成同条件测试','机制与来源标签尚需语义复核','未进行本轮独立读图']
    return doc

def main():
    mf=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'));allrows=[];counts=collections.Counter()
    for m in mf:
        pid=m['id'];loc=Locate(pid);old=json.loads((ROOT/m['reference']).read_text(encoding='utf-8'))
        p=V4/f'{pid}.json'
        if p.exists():
            d=json.loads(p.read_text(encoding='utf-8'));d['提取来源']='沿用既有 v4 表样，非本轮独立提取';d['缺口']=['本轮未进行独立盲提或独立读图']
        else:d=old_to_v4(m,old,loc)
        d['SI文本状态']='存在' if m['si_chars'] else '缓存缺失，不能宣称已审阅 SI'
        if not m['si_chars']:d['缺口'].append('SI 文本缺失')
        save(OUT/'v4_records'/f'{pid}.json',d)
        for t in d.get('测试',[]):
            counts['tests']+=1
            for r in t.get('结果',[]):
                counts['results']+=1
                qc=r.get('证据核对') or loc.quote(r.get('原句',''))
                if r.get('来源')=='读图':
                    qc={'状态':'沿用读图：锚点通过' if str(r.get('锚点','')).startswith('通过') else '沿用读图：无锚点，不判',
                        '原句':r.get('锚点',''),'定位':[]}
                counts[qc['状态']]+=1
                allrows.append({'文献':pid,'测试':t['编号'],'结果':r.get('编号',''),'指标':r['指标'],
                  '核对状态':qc['状态'],'原句':qc['原句'],'定位':qc['定位'],
                  '注意':'定位通过仅证明文字存在，未证明数值归属、语义和测试划分正确'})
    save(OUT/'程序核对记录.json',allrows);save(OUT/'迁移统计.json',dict(counts))
    print(json.dumps(dict(counts),ensure_ascii=False))

if __name__=='__main__':main()
