"""Persist root's explicit source-based adjudications, not automatic verdicts."""
import hashlib,json
from step8a_prepare_debug53 import OUT,save

def write(pid,rows,missing,notes='',reference_errors=(),corrections=()):
    p=OUT/'independent_predictions'/f'{pid}.json';d=json.loads(p.read_text(encoding='utf-8'))
    units=[]
    for uid,cat,verdict,reason,evidence in rows:
        if uid.startswith('T'):
            parts=uid.split('/')
            full='T/'+pid+'-'+parts[0]
            if len(parts)>1:full+='/'+pid+'-'+parts[0]+'-'+parts[1]
        else:full='M/'+pid+'-'+uid
        units.append({'id':full,'category':cat,'verdict':verdict,'reason':reason,
                      'evidence_ids':evidence,'reference_ids':[],
                      'new_correct':cat=='机制' or uid in ['T4','T5']})
    out={'paper_id':pid,'reviewer':'root：跨组原文复核','prediction_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
         'all_prediction_units_reviewed':True,'reference_and_source_reviewed':True,
         'coverage_notes':notes,'units':units,
         'missing':[{'id':f'FN{i}','category':c,'description':desc,'reason':why,'evidence_ids':ev,'reference_ids':[]}
                    for i,(c,desc,why,ev) in enumerate(missing,1)],
         'reference_errors':list(reference_errors),'unresolved':[], 'suggested_corrections':list(corrections)}
    save(OUT/'cross_reviews'/f'{pid}.json',out)

def main():
    write('P001',[
      ('T1','测试及条件','TP','0.2 C浓盐Li-S循环的载量、锂厚、60 μL及1C定义与实验部分一致；未报告温度未补默认',['M0038','M0158','M0168','M0172','M0173']),
      ('T2','测试及条件','TP','常规1 M+0.2 M LiNO3另列，公用制片和循环方法可追溯；未把跨图数据合并',['M0050','S0015','M0172','M0173']),
      ('T3','测试及条件','TP','循环EIS为独立测量；条件来自同组Li-S方法，没有把测试次数混入循环条件',['M0111','M0174']),
      ('T4','测试及条件','TP','LiCu含饱和Li2S8组明确，未报道的电流等保持未知',['M0115','S0023']),
      ('T5','测试及条件','TP','SI图S6B确有不含LiPS的LiCu对照，原文未写该组数值，不虚构结果',['S0023']),
      ('T1/R1','方向','SKIP_NONSCORING','71.9%为单组保持率，未提出A/B方向',['M0039']),
      ('T1/R2','方向','SKIP_NONSCORING','33圈为单组寿命，未提出A/B方向',['M0039']),
      ('T1/R3','方向','SKIP_NONSCORING','101%为单组初始CE，未提出方向',['M0040']),
      ('T1/R4','方向','SKIP_NONSCORING','96.6%为单组200圈CE，未提出方向',['M0040']),
      ('T1/R5','方向','SKIP_ABSTENTION','CE稍高但超过100%来自副反应，保留原定性并不判好坏合理',['M0041','M0085','M0086']),
      ('T1/R6','方向','TP','原文明确T3较F3极化更高，记变坏正确',['M0048']),
      ('T2/R1','方向','SKIP_ABSTENTION','对照LiNO3变化且来自另一图，未当同条件数值方向；原作者定性已保留',['M0050','M0052']),
      ('T3/R1','方向','TP','T3循环阻抗下降，F3五圈后增加至失效，保留两组各自趋势支持稳定性方向',['M0112','M0113']),
      ('T4/R1','方向','TP','LiCu中T3稳定而F3效率大幅波动，稳定性定性有原句支持',['M0115','M0116']),
      ('M1','机制','FP','高黏度/低电导导致全电池极化的概括正确，但原句没有将过程归为正极反应，类别多标',['M0049']),
      ('M2','机制','TP','LiTFSI可逆LiSx与LiFSI不可逆LiSOx、后者循环差在连续原文明确；建议补足所引句范围',['M0078','M0079','M0081','M0082','M0083','M0084']),
      ('M3','机制','TP','不可逆LiSOx使充电量低于放电量及CE>100%的因果原文连续明确，属锂侧反应',['M0085','M0086']),
      ('M4','机制','TP','不可逆LiSOx生成更多导致更厚钝化层，原句明确为本文发现',['M0087']),
      ('M5','机制','TP','绝缘LiSOx钝化层快速增厚与阻抗上升对应，原文明确',['M0114']),
      ('M6','机制','FP','盐析出的推测保留正确，但原句未提正极反应，类别多标；下一句所述低CE作用未概括',['M0117','M0118']),
      ('M7','机制','FP','FSI扩散快对应低极化原句成立，但全电池极化未定位正极，类别多标',['M0140']),
      ('M8','机制','TP','大扩散系数可能加速锂表面分解并增加LiSOx，推测语气和负极归属正确',['M0141']),
      ('M9','机制','TP','FSI连续分解使绝缘硫酸盐钝化层快速生长，结论与上下文一致',['M0147'])
    ],[
      ('方向','T3比F3循环更稳定/保持率更高的作者定性方向','预测把同一句拆成两个单组数值并均不判，漏掉原文明说的方向',['M0039','M0048']),
      ('机制','高黏度及低电导使T3全电池极化高于F3；过程大类未定位正极','对应M1类别纠正后的正确单位未被其他预测覆盖',['M0049']),
      ('机制','F3中LiPS溶解度较低，Li2S8增多可能使LiFSI析出并影响CE；不强行归正极','对应M6纠正后单位，保留may并补充落到CE的作者推测',['M0117','M0118']),
      ('机制','FSI扩散较快与F3全电池低极化一致，未定位正极','对应M7类别纠正后的正确单位',['M0140']),
      ('机制','FSI的N-S键较弱，断裂有利于硫酸盐形成及锂界面失稳','原文核心阴离子键强度归因，现有M2只收产物可逆性，缺这条原因',['M0017','M0105','M0108','M0146']),
      ('机制','LiCu中FSI电解液CE大幅波动说明负极/电解液界面不稳定','预测结果有波动，但机制列表缺作者对界面的解释',['M0116'])
    ],notes='逐段读完正文M0001-M0188及全部SI；参考文献不作为本文证据。旧C试提已核。仅对文本冻结预测评分，Fig1a容量待本轮几何读图，图S1无锚点；不把待读图点虚构为FN。',
    reference_errors=[{'reference_id':'C1/E1-E3：循环与CE方向','reason':'旧参考未体现LiNO3改变及跨图；不能当同条件数值方向。作者定性可保留。','evidence_ids':['M0050','M0052']}],
    corrections=[{'unit':'M/P001-M2','action':'补引M0078/M0081/M0082/M0084以覆盖比较双方与循环结果'},
                 {'unit':'M/P001-M3','action':'补引M0086以覆盖CE>100%'}])

if __name__=='__main__':main()
