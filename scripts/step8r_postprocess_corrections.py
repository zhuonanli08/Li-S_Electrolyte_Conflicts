"""Separate debug fixes from the frozen first-pass scoring pipeline."""
import json,re,hashlib
from step8a_prepare_debug53 import OUT,save
from step8f_validate_independent import numeric_direction

def corrected(r):
    metric=r.get('metric','');copy=dict(r);reason=None
    if re.search(r'容量损失|容量衰减|损失容量',metric):
        copy['metric']='衰减率';reason='容量损失/衰减是越低越好；初轮被泛化容量关键词覆盖'
    elif re.search(r'极化.*突增.*时间|突增.*极化.*时间',metric):
        copy['metric']='寿命';reason='不良极化突增前的持续时间越长越好，不是极化幅值'
    elif re.search(r'容量比|[Ii]\s*/.*容量|衍射.*容量',metric):
        copy['metric']='比值（未定义单调优劣）';reason='复合比值不能因为名称含容量就按容量判优劣'
    elif re.search(r'库仑效率|coulomb|(?<![A-Za-z])CE(?![A-Za-z])',metric,re.I):
        copy['metric']='库仑效率';reason='中文邻接CE也识别为库仑效率；仅百分点差'
    return numeric_direction(copy),reason

def main():
    changes=[]
    for p in sorted((OUT/'independent_predictions').glob('*.json')):
        d=json.loads(p.read_text(encoding='utf-8'))
        for t in d.get('tests',[]):
            for r in t.get('results',[]):
                old=numeric_direction(r);new,why=corrected(r)
                if new!=old:
                    changes.append({'paper_id':d['paper_id'],'unit':'T/'+t['id']+'/'+r['id'],
                                    'metric':r.get('metric'),'original_calculation':old,
                                    'corrected_calculation':new,'reason':why,
                                    'evidence_ids':r.get('evidence_ids',[]),
                                    'prediction_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    save(OUT/'revisions'/'program_direction_corrections.json',{'version':'debug-fix-2026-10-27','scoring_use':'仅用于修正展示；初轮评分不回改、不称独立重测','changes':changes})
    print('程序更正另存：',len(changes),'条；冻结预测和初轮评分未更改')

if __name__=='__main__':
    # Regression cases include the collision between 比容量 and 容量比.
    def case(metric,a,b):return corrected(dict(metric=metric,value_A=a,value_B=b,unit='%',basis='numeric',same_conditions=True))[0]
    assert case('容量损失',4.5,51.8)['direction']=='变好'
    assert case('容量衰减',29.86,50.65)['direction']=='变好'
    assert case('剥离极化突增时间',180,163)['direction']=='变好'
    assert case('I/低平台总容量',2,1)['direction']=='不判'
    assert case('低/高平台容量比',2.21,2.06)['direction']=='不判'
    assert case('比容量',1200,800)['direction']=='变好'
    assert case('平均CE值',99.5,99)['delta']==.5
    main()
