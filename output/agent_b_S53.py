from agent_b_common import *
p=paper('S53','DD15','不含LiNO3的自配对照',False)
for i,s,c,n in [('DD15','DME/DOL',1.5,0),('SL15','SL',1.5,0),('DDN','DME/DOL',1.0,0.5),('SLN','SL',1.0,0.5),('DD25','DME/DOL',2.5,0),('DD35','DME/DOL',3.5,0),('MIX15','DME-DOL/SL',1.5,0)]:
 cp=[('LiTFSI','盐',c,'M')]+([(s,'溶剂化溶剂',None,'DME:DOL=1:1' if s=='DME/DOL' else 'DME-DOL:SL=2:1' if s=='DME-DOL/SL' else '单溶剂')]);cp+= [('LiNO3','添加剂',n,'M')] if n else [];form(p,i,i,cp,'M0030' if i in ['DD15','SL15','DDN','SLN'] else 'M0096')
grad(p,'溶剂与LiNO3',['DD15','SL15','DDN','SLN'],['DME/DOL','SL','DME/DOL+LiNO3','SL+LiNO3'],'无独立溶剂化强弱排序','M0030')
for temp,vals in [(0,[4.98,169.05,4.20,151.05,25.17,547.10,17.20]),(30,[2.41,51.00,1.93,43.55,8.52,68.80,6.64]),(60,[1.54,19.55,1.33,15.90,4.20,21.10,3.05])]:prop(p,f'{temp}°C黏度/mPa s',dict(zip(['DD15','SL15','DDN','SLN','DD25','DD35','MIX15'],vals)),'SL显著较高；温度升高黏度下降','黏度计','±1°C；1.33标超正常转矩范围','M0055 M0096')
c=dict(sulfur_loading='around 1.5 mg cm-2',ES='未报告（每池15 μL）',rate='0.05 C；1.7–2.9 V',formation='装配后静置12 h')
t=test(p,'室温无LiNO3循环',['SL15','DD15'],'M0049 M0050 M0051 M0052 M0053 M0077',temperature='about 25 °C',LiNO3='无',**c)
result(t,'穿梭','SL15','DD15','200圈后仍不明显','明显',None,'室温循环','M0056 M0057',basis='qualitative',direction='变好')
t1=test(p,'60°C无LiNO3循环',['SL15','DD15'],'M0049 M0050 M0051 M0052 M0053 M0077',temperature='60 °C',LiNO3='无',**c)
result(t1,'寿命','SL15','DD15',35,'从开始不能循环','cycles','失效','M0065 M0066');result(t1,'过充','SL15',None,'about 10',None,'%','5次放充后','M0066')
t2=test(p,'60°C有LiNO3循环',['SLN','DDN'],'M0049 M0050 M0051 M0052 M0053 M0077',temperature='60 °C',LiNO3='0.5 M',**c)
result(t2,'穿梭','SLN','DDN','均得到缓解','均得到缓解',None,'60°C循环','M0090 M0091',basis='qualitative',direction='差异小',reason='作者定性两者均抑制，不能作数值比较')
for temp,forms in [('室温',['SL15','DD15']),('60 °C',['SL15','DD15','SLN','DDN'])]:
 tx=test(p,'LiPS与锂化学反应 '+temp,forms,'M0030 M0032 M0033 M0093',cell='50 mg Li浸泡1.0 mL 0.1 M Li2S6溶液；HPLC',temperature=temp,rate='静置4天')
 result(tx,'LiPS与锂反应性','SL15','DD15','较低','较高',None,'4天','M0059' if temp=='室温' else 'M0073',basis='qualitative',direction='变好')
 if temp=='60 °C':
  for a,b in [('SLN','SL15'),('DDN','DD15')]:result(tx,'LiPS与锂反应性',a,b,'显著降低','较高',None,'4天','M0098',basis='qualitative',direction='变好')
for s,ids,A,B,pr,cats,source,tt in [('SL高黏度可能通过减慢传质减轻穿梭','M0088','SL15','DD15','黏度','多硫化物穿梭','本文推测',[t]),('DME/DOL低黏度可能加快传质，缺少LiNO3时促进穿梭','M0089','DD15','SL15','黏度','多硫化物穿梭','本文推测',[t]),('高温无LiNO3的SL仍有严重穿梭','M0106','SL15',None,'温度/黏度','多硫化物穿梭','本文结论',[t1]),('高温加入LiNO3才有效缓解SL体系穿梭','M0107','SLN','SL15','LiNO3添加','多硫化物穿梭','本文结论',[t2]),('含LiNO3的SL虽然黏度低但穿梭更小，可能源于不同SEI组成','M0101','SLN','SL15','SEI','负极锂 多硫化物穿梭','本文推测',[t2]),('高温DME/DOL中形成的短/中链LiPS可返回正极导致穿梭','M0072','DD15',None,'LiPS反应','多硫化物穿梭','本文结论',[t1])]:mech(p,s,A,B,pr,cats,ids,tt,source=source)
p['design_claims']=[dict(summary='SL仍是折中方案；高温需要LiNO3',evidence_ids=['M0107','M0108'])]
p['gaps']=['本地SI缺失；正文指向SI表S1的HPLC峰面积未取得。无容量循环曲线的可提明确数值；Fig.1为电压曲线不属于v4规定读图两类。E/S、锂厚、1C定义未报告；Li+溶剂化/LiPS溶剂化与溶解度未独立定量。']
save(p)
