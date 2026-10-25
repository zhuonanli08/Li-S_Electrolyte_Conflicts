from agent_b_common import *
p=paper('P212','G3','两种高浓度glyme比较',si=False)
for f,sol,c in [('G2','DEGDME',1.5),('G3','TREGDME',2)]:form(p,f,sol+'_HCE',[('LiTFSI','盐',c,'mol kgsolvent-1'),('LiNO3','盐/添加剂',c,'mol kgsolvent-1'),(sol,'溶剂',None,None)],'M0011 M0012 M0014')
grad(p,'链长和饱和盐浓度',['G2','G3'],['n=2，每种盐1.5 m','n=3，每种盐2 m'],'并未直接测Li+溶剂化强度；链长与盐浓度共同改变','M0011 M0012')
prop(p,'电导率（引自前作）',{'G2':'3.3×10^-3','G3':'8.9×10^-4'},'G2较高','前作测量','室温；S cm-1','M0041')
c=dict(sulfur_loading='S:Sn复合物约1.3 mg cm-2（不是纯S载量）',LiNO3='G2 1.5 m；G3 2 m',one_C='1675 mA gS-1',rate='C/5',voltage='1.9–2.8 V',electrolyte_volume='60 μL')
ts=[]
for temp,cap,ret,ids in [(25,['约800','约340'],[92,88],'M0042 M0050'),(35,['约1320','接近890'],[90,77],'M0044 M0049 M0050')]:
 t=test(p,f'LiS C/5 {temp}°C循环',['G2','G3'],'M0018 M0028 M0029 '+ids,temperature=f'{temp} °C',**c);ts.append(t)
 result(t,'稳态/最大放电容量','G2','G3',cap[0],cap[1],'mAh gS-1','稳态/最高值，具体圈数未给',ids,reason='保持原文约数；不同峰值圈号未知')
 result(t,'相对最大容量保持率','G2','G3',ret[0],ret[1],'%','50圈',ids)
 fig(p,t,'Fig.2b,d','放电容量','G2','G3','50圈',ids)
t3=test(p,'LiS 1C长循环',['G2'],'M0029 M0076 M0077 M0078 M0085',**dict(c,rate='1 C',temperature='35 °C',voltage='1.6–2.8 V',ES=20,ES_unit='μL mgS-1',electrolyte_volume='未报告'))
result(t3,'活化后放电容量','G2',None,'接近750',None,'mAh gS-1','活化后初值','M0078')
result(t3,'容量保持率','G2',None,70,None,'%','140圈','M0078')
result(t3,'库仑效率','G2',None,'约100',None,'%','循环','M0077')
t4=test(p,'LiS CV及EIS',['G2','G3'],'M0020 M0024 M0035 M0040',**dict(c,rate='0.1 mV s-1',temperature='未报告',voltage='1.8–2.8 V'))
for pt,a,b in [('OCV',['103±2','129±3','232±4'],['73.3±0.4','27±3','101±3']),('1圈',['9.9±0.1','3.4±0.2','13.3±0.2'],['13.1±0.3','9.0±1.5','22.1±1.5']),('5圈',['10.1±0.1','0.8±0.1','10.9±0.1'],['5.3±0.1','7.2±0.3','12.5±0.3']),('10圈',['9.8±0.5','1.5±0.5','11.3±0.7'],['5.4±0.1','6.8±0.3','12.2±0.3'])]:
 for n,va,vb in zip(['R1','R2','R1+R2'],a,b):result(t4,n,'G2','G3',va,vb,'Ω',pt,'M0035')
result(t4,'CV极化','G2','G3','更平滑且较小','较大',None,'稳定CV','M0040',basis='qualitative',direction='变好')
# 非LiS对照化学体系单独记录，禁止混入LiS判断
for name,ret,ids,formation in [('LFP常规窗口',[63,94],'M0061 M0062 M0063','无额外还原'),('LFP首圈低压活化',[71,97],'M0069 M0070 M0071 M0073','首圈1.2–3.9 V，后2.7–3.9 V')]:
 tt=test(p,name,['G2','G3'],'M0018 M0030 '+ids,cell='Li||LiFePO4（研究范围外）',sulfur_loading='不适用；LFP4.5 mg cm-2',temperature='25 °C',rate='C/5',one_C='170 mA gLFP-1',formation=formation,LiNO3=c['LiNO3'])
 result(tt,'容量保持率','G2','G3',ret[0],ret[1],'%','50圈',ids,reason='非LiS测试，仅文献完整性保留')
 result(tt,'初始容量','G2','G3','接近160','接近160','mAh gLFP-1','初期',ids,reason='非LiS测试')
t7=test(p,'LFP长循环',['G3'],'M0076 M0077 M0078 M0086',cell='Li||LiFePO4（研究范围外）',temperature='25 °C',rate='C/3',one_C='170 mA gLFP-1',formation='首圈1.2–3.9 V，后2.7–3.9 V')
result(t7,'容量','G3',None,152,None,'mAh gLFP-1','初期','M0078',reason='非LiS测试')
result(t7,'容量保持率','G3',None,85,None,'%','100圈','M0078',reason='非LiS测试')
for sm,pr,ids,src in [('G2较低黏度及较高导电率可能改善LiS电化学过程。','黏度/导电率','M0041','本文推测'),('浓电解液高黏度阻碍绝缘硫动力学，G3更长链及更高盐浓度使影响更强。','高黏度','M0043','本文推测'),('升温降低黏度并提高Li离子导电率，降低极化和提高容量。','温度/输运','M0044','本文结论（与他文一致）'),('G2优于G3的LiS表现归因其更快电荷转移动力学。','电荷转移','M0082','本文结论')]:mech(p,sm,'G2','G3',pr,'正极反应',ids,ts,source=src)
p['gaps']=['SI本地缺失，无SI索引。','正文0.94/0.98 g mL-1被称作黏度，但单位为密度；不作为可靠黏度数值。','电导率与电化学稳定窗口来自前作，不属于本文新测。','没有独立LiCu/Li对称测试；LFP数据不作为LiS或纯锂半电池归因。','载量1.3 mg cm-2指复合活性物，故60 μL不直接换算E/S。','两配方链长、LiTFSI浓度和LiNO3浓度均不同。']
save(p)
