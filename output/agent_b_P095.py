from agent_b_common import *
p=paper('P095','DME','不含LiNO3的自配对照');fs=['DME','DMA','DMSO','MeIm']
for s in fs:form(p,s,'DOL-'+s,[('DOL','溶剂化溶剂',1,'体积份'),(s,'溶剂化溶剂',1,'体积份'),('LiTFSI','盐',1,'m（原文小写，不换算）')],'M0145 M0152')
grad(p,'共溶剂种类',fs,fs,'DME低溶解能力；DMA/DMSO/MeIm高溶解能力；三高DN溶剂不强行单一排序','M0048 M0054')
prop(p,'Li2S6溶解度',{'DME':'1.5 m不能完全溶解','DMA':'1.5 m完全溶解','DMSO':'1.5 m完全溶解','MeIm':'1.5 m完全溶解'},'三高DN溶剂高于DOL-DME','溶解实验','纯DMA/DMSO/MeIm vs DOL-DME；不是测试电解液混合溶剂','M0053 M0054 M0164')
prop(p,'S3自由基与S6物种',{'DMA':'0.25 m时S3相对量为DMSO/MeIm约5倍','DMSO':'高浓度S6占优','MeIm':'高浓度S6占优','DME':'无明显S3峰'},'高低浓度物种不同','短光程UV-vis','0.25 m nominal Li2S6；纯溶剂或DOL-DME','M0061 M0062 M0069 M0070')
ts=[]
for load,es,cut,vals in [(2,20,1.5,[1100,1250,1250,150]),(6,10,1.4,[540,670,570,470])]:
 t=test(p,f'{load}mg载量首次放电',fs,'M0080 M0142 M0143 M0154 M0155 M0156 M0159 M0160 M0161',cell='Li||S-CNT CR2032' if load==2 else 'Li||S-CNF CR2032',sulfur_loading=f'{load} mg cm-2',ES=es,ES_unit='μL mg-1',rate='C/10',formation='0.5–2h静置润湿',LiNO3='无',one_C='1672 mA g-1',voltage=f'放电至{cut}V');ts.append(t)
 for s,v in zip(fs[1:],vals[1:]):result(t,'初始放电容量',s,'DME',v,vals[0],'mAh g-1','第一圈',('M0084 M0090' if load==2 else 'M0085 M0087 M0090'),reason='原文around/average；保留近似含义')
 result(t,'第二平台过电位','MeIm',None,100 if load==2 else 400,None,'mV','首放第二平台','M0091')
tl=test(p,'锂对称电池循环',fs,'M0099 M0157',cell='Li||Li CR2032；40 μL',LiNO3='无')
result(tl,'过电位','DMSO','DME',150,50,'mV','锂剥镀','M0101 M0102');result(tl,'失效','DMA/MeIm','DME','通电迅速失效','稳定低极化',None,'锂剥镀','M0100 M0102',basis='qualitative',direction='变坏')
te=test(p,'锂对称电池EIS',fs,'M0103 M0135 M0162',cell='Li||Li；一圈后或失效后',rate='EIS 10^6–10^-1 Hz，5mV')
for s,v in [('MeIm',380),('DMA',315),('DMSO',70)]:result(te,'界面电阻',s,'DME',v,30,'Ω','一圈后/MeIm和DMA失效后','M0104 M0105',same=False if s in ['MeIm','DMA'] else True,reason='MeIm/DMA在失效后取样，与DME一圈后不完全等状态')
for s,ids,pr,cats,source,side,tt in [('更高LiPS溶解能力与S3自由基提高硫利用率','M0086','LiPS溶解度/物种','正极反应','本文结论','弱侧',ts),('DMSO高浓度S3减少使高载量利用率收益下降','M0088','LiPS物种','正极反应','本文结论','其他',[ts[1]]),('DMA成核过电位后恢复归因于S3促进更多Li2S析出','M0089','LiPS物种','正极反应','本文结论','其他',[ts[1]]),('MeIm低容量可能来自溶剂与电极不可逆副反应','M0090','化学稳定性','负极锂','本文推测','其他',ts),('高DN溶剂与锂不稳定可能掩盖DMA更大利用率潜力','M0093','化学稳定性','负极锂 正极反应','本文推测','其他',ts),('所有高DN溶剂与锂存在不稳定和分解','M0132','溶剂反应性','负极锂 电解液消耗','本文结论','其他',[tl]),('高溶解度可延长溶液介导放电并改善贫液高载量利用率','M0127','LiPS溶解度','正极反应','本文结论','弱侧',ts),('各溶剂与LiPS一个月均较稳定，后续应着重保护锂','M0125','化学稳定性','负极锂','本文结论','其他',[])]:mech(p,s,'DMA','DME',pr,cats,ids,tt,side,source)
p['design_claims']=[dict(summary='高溶解能力策略需配合稳健负极钝化，防溶剂反应及穿梭',evidence_ids=['M0121','M0138','M0140'])]
p['gaps']=['无长期LiS循环/CE/保持率；只首放不能判兼顾寿命。对称电池电流和面容量原文未给；锂厚未给。纯溶剂物种表征不能直接当DOL混合盐电解液数值。原文小写m不换算。']
save(p)
