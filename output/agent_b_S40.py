from agent_b_common import *
p=paper('S40','SL_LiTFSI','其他（五种1 M盐/单溶剂并列，无常规醚基准）')
fs=['SL_LiTFSI','SL_LiTF','SL_LiClO4','G3_LiTFSI','G3_LiTF']
for f in fs:
 s,salt=f.split('_');form(p,f,f,[(s,'溶剂化溶剂',None,'单溶剂'),(salt,'盐',1,'M')],'M0151')
grad(p,'盐/溶剂种类',fs,fs,'没有实测统一溶剂化排序','M0151')
c=dict(sulfur_loading='1.1–1.3 mg cm-2（图标1.2）',ES_unit='mL g-1',Li_thickness='170 μm',rate='0.1 C；1.5–2.8 V',formation='OCV静置16 h；无单独化成协议',temperature='室温（数值未报告）',LiNO3='配方未添加')
ts=[]
for es,letter in [(23,'a'),(16,'b'),(9,'c'),(6,'d')]:
 t=test(p,f'E/S={es}循环',fs,'M0072 M0148 M0152 M0153 M0154 M0155 M0156',ES=es,**c);ts.append(t)
 for a,b in [('SL_LiTFSI','SL_LiTF'),('G3_LiTFSI','SL_LiClO4')]:result(t,'循环表现',a,b,'较好','较差',None,'循环总体（作者定性）','M0057',basis='qualitative',direction='变好',reason='作者称几乎所有E/S，单测试精确曲线仍待核')
 result(t,'CE','SL_LiTFSI','G3_LiTFSI','around 90','较低且波动','%','循环','M0062',basis='qualitative',direction='变好')
 if es!=16:result(t,'放电容量','SL_LiClO4','SL_LiTFSI','最低','较高',None,'循环','M0063',basis='qualitative',direction='变坏')
 fig(p,t,f'Fig.1{letter}','五档首圈及同圈容量/保持率','全梯度','SL_LiTFSI','首圈及相同终点',[])
t=ts[-1]
result(t,'容量/保持率','G3_LiTF','SL_LiTFSI','最高','较低',None,'E/S=6循环','M0065 M0168',basis='qualitative',direction='变好')
result(t,'循环表现','SL_LiTFSI','G3_LiTFSI','较好','较差',None,'E/S=6循环','M0061',basis='qualitative',direction='变好')
result(t,'硫利用率','SL_LiTFSI','全梯度','最高','较低',None,'循环各圈','M0127',basis='qualitative',direction='变好')
result(t,'低压/高压容量比','G3_LiTFSI','SL_LiTFSI','较高','较低',None,'循环','M0129',basis='qualitative',direction='不判',reason='只是分段容量比，不等同总容量好坏')
te=test(p,'E/S=6 EIS随循环',fs,'M0086 M0158 M0159 M0160 S0029',ES=6,**c)
src=json.loads((BASE/'sources/S40.json').read_text(encoding='utf8'));txt=next(s['text'] for s in src if s['id']=='S0029')
import re
rows={}
for orig,nextorig in zip(['SL-LiTFSI','SL-LiTF','SL-LiClO4','G3-LiTFSI','G3-LiTF'],['SL-LiTF','SL-LiClO4','G3-LiTFSI','G3-LiTF',None]):
 sec=txt.split(orig+' ',1)[1];sec=sec.split(nextorig+' ',1)[0] if nextorig else sec;nums=re.findall(r'\d+(?:\.\d+)?',sec);rows[orig.replace('-','_')]=[nums[z:z+5] for z in range(0,len(nums),5)]
for f in fs[1:]:
 for r,b in zip(rows[f],rows[fs[0]]):
  for k,m in enumerate(['R1','R2','R3','RTotal'],1):result(te,m,f,fs[0],r[k],b[k],'Ω',f'第{r[0]}圈','S0029 M0086')
for es in [9,6]:
 tc=test(p,f'E/S={es} CV',fs,'M0108 M0162',ES=es,**dict(c,rate='0.1 mV s-1，1.5–3.0 V'))
 result(tc,'反应动力学','SL_LiTFSI','G3_LiTFSI','较有利','较差',None,'CV','M0114' if es==9 else 'M0120',basis='qualitative',direction='变好')
tl=test(p,'含长链LiPS对称锂循环',['SL_LiTF','G3_LiTF'],'S0024 S0025 S0026 S0027',cell='Li||Li；饱和长链LiPS（S:Li2S=7:1）；20 μL cm-2',rate='0.2 mA cm-2，1.0 mAh cm-2',temperature='30 °C',LiNO3='未添加')
result(tl,'界面稳定性','SL_LiTF','G3_LiTF','较稳定','较差',None,'循环','M0147',basis='qualitative',direction='变好')
te2=test(p,'含长链LiPS对称锂储存EIS',['SL_LiTF','G3_LiTF'],'S0020 S0021 S0022 S0023',cell='Li||Li；饱和长链LiPS（S:Li2S=7:1）；20 μL cm-2',rate='储存EIS 1 MHz–10 mHz，0.5 mA',temperature='30 °C')
for summary,ids,A,B,pr,cats,source in [('低E/S的SL-LiTFSI比G3-LiTFSI循环好，作者推测来自SL的电化学稳定性等','M0061','SL_LiTFSI','G3_LiTFSI','溶剂特性','正极反应','本文推测'),('LiTF体系较高电阻可能使G3-LiTF前几圈容量低','M0096','G3_LiTF','SL_LiTFSI','电阻','正极反应','本文推测'),('SL-LiClO4虽总电阻最低但循环最差，电阻不能充分解释循环','M0106','SL_LiClO4','SL_LiTFSI','电阻','正极反应','本文结论'),('较多电解液提高多硫化物转化及氧化还原动力学','M0112','E/S=9','E/S=6','电解液量','正极反应','本文结论'),('随循环硫利用率下降可能因穿梭、钝化或副反应','M0124','全梯度',None,'循环变化','正极反应 多硫化物穿梭','本文推测'),('G3中锂表面硫积累更明显，说明多硫化物到达并与锂反应','M0141','G3_LiTFSI','SL_LiTFSI','LiPS迁移','多硫化物穿梭 负极锂','本文结论'),('SEM及EDS显示SL较G3具有更稳定锂界面','M0145','SL_LiTFSI','G3_LiTFSI','界面稳定性','负极锂','本文结论'),('对称电池储存与循环支持SL形成更稳定SEI的假设','M0147','SL_LiTF','G3_LiTF','SEI','负极锂','本文推测')]:mech(p,summary,A,B,pr,cats,ids,[t] if ids not in ['M0147'] else [tl,te2],source=source)
p['design_claims']=[dict(summary='贫液条件优先考虑SL-LiTFSI，但G3-LiTF在E/S=6容量和保持率最高且CE低，需保留权衡',evidence_ids=['M0168','M0174'])]
p['gaps']=['未给1C定义；Li+溶剂化/LiPS溶剂化/溶解度未独立实测定量。跨E/S趋势为条件改变，不作同条件方向合并。循环图无明确同图数值锚点。']
save(p)
