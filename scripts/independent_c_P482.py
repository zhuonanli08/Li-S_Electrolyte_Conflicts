from independent_c_helpers import *
p=init('P482');p['control_id']='conventional';p['control_type']='常规醚基准（DOL/DME + LiTFSI + LiNO3）'
for id,a,b in [('conventional','1','0'),('LiFPB','0.8','0.2')]:
 cs=[['LiTFSI','盐',a,'M'],['LiNO3','添加剂','1','wt%'],['DOL','溶剂化溶剂','1','体积份'],['DME','溶剂化溶剂','1','体积份']]
 if b!='0':cs.append(['LiFPB','盐',b,'M'])
 form(p,id,a+' M LiTFSI +'+b+' M LiFPB +1 wt% LiNO3 DOL/DME1:1',cs,'M0041 S0003 S0010')
grad(p,'LiFPB浓度',['conventional','LiFPB','其他图示档未获得'],['0','0.2 M','未报告'],'正文仅给最优0.2M，其他档仅图S22','M0137 S0128 S0129')
grad(p,'硼盐种类',['LiFPB','其他两种硼盐未获名称'],['LiFPB','未报告'],'Figure S23种类梯度，非溶剂化强弱','S0130 S0131')
prop(p,'Li+溶剂化',{'LiFPB':'Raman DME/DOL/LiTFSI位移无显著变化'},'与conventional近似；主文认为SEI改善非溶剂化变化','Raman','电解液','M0114 M0115 S0114')
prop(p,'LiPS化学稳定性',{'LiFPB':'Li2S6混合60h峰位/颜色无变','conventional':'LiTFSI与Li2S6反应出现副产物'},'LiFPB较稳定，不等于溶解度低','19F NMR/颜色','盐与Li2S6混合；DMSO-d6用于NMR','M0043 M0044 M0046 M0047 S0052 S0053 S0054')
fs=['LiFPB','conventional'];base={'LiNO3':'1 wt%'}
t=test(p,'T1','Li对称循环','Li||Li',{**base,'rate':'0.5 mA cm−2,1 mAh cm−2'},fs,'M0067')
result(t,'稳定循环','LiFPB','conventional','>500','380后极化上升','h','恒流循环','numeric','不判','M0058 M0059')
t=test(p,'T2','Li||Cu CE循环','Li||Cu CR2032',{**base,'rate':'0.5 mA cm−2,1 mAh cm−2；剥至1V'},fs,'S0029 M0060')
result(t,'CE','LiFPB','conventional','>98.5','<65','%','100圈','numeric','不判','M0060 M0061')
result(t,'不可逆Li消耗','LiFPB','conventional','1.01','14.89','mAh cm−2','累计100圈','numeric','不判','M0062')
t=test(p,'T3','Aurbach CE','Li||Cu',{**base,'rate':'0.5 mA cm−2；5 mAh cm−2库存，1 mAh cm−2循环10次','formation':'先沉积5 mAh cm−2再剥至1V'},fs,'S0030')
result(t,'CE','LiFPB','conventional','99.59','97.73','%','Aurbach','numeric','不判','M0062')
t=test(p,'T4','界面动力学','Li||Li',{**base,'rate':'Tafel CV0.2 mV s−1,0–0.1V'},fs,'S0035 M0103')
result(t,'交换电流密度','LiFPB','conventional','1.001','0.689','mA cm−2','Tafel','numeric','不判','M0103')
result(t,'界面阻抗','LiFPB','conventional','较低','较高',None,'极化前后/变温','qualitative','变好','M0116 M0117')
for tid,r,e in [('T5','0.2 C','M0134 M0138 M0141 M0142'),('T6','0.5 C','M0143 M0144 S0133')]:
 t=test(p,tid,'低载量循环','S/SuperP||Li',{**base,'sulfur_loading':'1.2 mg cm−2','rate':r,'formation':'0.1 C 3圈','voltage':'1.7–2.8 V'},fs,e+' S0031')
 if tid=='T5':
  for m,a,b,u,pt in [('初始容量','1001.8','935.9','mAh g−1','保持率分母，是否化成后未明确'),('容量','758.5','478.5','mAh g−1','200圈'),('保持率','75.7','50.9','%','200圈/初始'),('平均CE','99.01','97.62','%','循环')]:result(t,m,'LiFPB','conventional',a,b,u,pt,'numeric','不判',e)
 else:
  result(t,'保持率','LiFPB','conventional','73.6','56.41','%','末圈，圈数正文未明','numeric','不判',e)
  result(t,'平均CE','LiFPB','conventional','98.77','97.88','%','循环','numeric','不判',e)
t=test(p,'T7','高载量循环','S/SuperP||Li',{**base,'sulfur_loading':'3.1 mg cm−2','rate':'0.2 C','formation':'0.1 C3圈'},fs,'M0135 M0151')
for m,a,b,u,pt,e in [('初始容量','824.6',None,'mAh g−1','初始','M0152'),('容量','688.1','530.6','mAh g−1','100圈','M0153 M0157'),('保持率','83.4',None,'%','100圈','M0153'),('平均CE','97.96','96.71','%','循环','M0156 M0157')]:result(t,m,'LiFPB','conventional' if b else None,a,b,u,pt,'numeric','不判',e)
t=test(p,'T8','倍率','S/SuperP||Li',{**base,'rate':'0.1/0.2/0.4/0.8/1.0/回0.1 C','sulfur_loading':'1.2 mg cm−2（通用方法，推定）'},fs,'M0123 M0124 S0012')
for r,v in zip(['0.1','0.2','0.4','0.8','1.0','回0.1'],['914.9','805.8','728.1','638.7','596','837.6']):result(t,'倍率容量','LiFPB',None,v,None,'mAh g−1',r+' C','numeric','不判','M0123 M0124')
result(t,'倍率表现','LiFPB','conventional','较好','基准',None,'倍率测试','qualitative','变好','M0124')
t=test(p,'T9','Ah软包','S||Li pouch',{**base,'rate':'0.1 C'},['LiFPB'],'M0166 M0167')
for m,v,u,pt in [('能量密度','408','Wh kg−1','初始'),('保持率','62.24','%','76圈'),('平均CE','99.02','%','76圈')]:result(t,m,'LiFPB',None,v,None,u,pt,'numeric','不判','M0167')
for tid,f in [('T10','S22'),('T11','S23')]:
 t=test(p,tid,'浓度筛选' if tid=='T10' else '硼盐筛选','S||Li',{**base,'rate':'0.2 C'},['LiFPB','图示其他档'],'S0128 S0130')
 result(t,'循环稳定性','LiFPB','图示其他档','最佳','较低',None,'100圈','qualitative','变好','M0137 S0131')
 fig(p,tid,'Figure '+f,'si','容量/梯度档位','LiFPB','图示其他档','首圈/100圈','','补配方档位及容量；无数值锚点则整图不用')
for su,pr,cats,typ,e,ts in [
('大体积高质荷比阴离子抵抗双电层排斥，增强还原成膜','阴离子界面富集',['负极锂'],'本文结论','M0033 M0034 M0035',['T1','T3']),
('LiFPB对PS低反应性可能来自位阻和B低价态','化学稳定性',['电解液消耗'],'本文推测','M0048',[]),
('致密均匀Li沉积减少SEI开裂微短路和死锂','沉积形貌',['负极锂'],'本文结论','M0077',['T2']),
('B-O位点固定TFSI，减少电解液分解','SEI阴离子固定',['负极锂','电解液消耗'],'本文结论（与他文一致）','M0087 M0088',['T1']),
('LiBxOy为快Li导体促进均匀Li沉积','SEI输运',['负极锂'],'本文结论（与他文一致）','M0094 M0095',['T4']),
('稳固导Li SEI减少电极电解液直接接触和副反应','SEI',['负极锂','电解液消耗'],'本文结论','M0097',['T2','T5']),
('Raman显示SEI修改并非来自体相溶剂化变化','溶剂化不变',['负极锂'],'本文结论','M0115',['T5']),
('SI另称LiFPB入溶剂化壳减少PS与Li接触、抑穿梭，和Raman解释不一致','溶剂化壳',['多硫化物穿梭'],'本文结论','S0064 S0065',[]),
('薄均匀SEI抑穿梭/副反应并稳定Li沉积，改善Li-S循环','SEI',['负极锂','多硫化物穿梭'],'本文结论（与他文一致）','M0165 M0166',['T5','T6','T7']),
('LiF/LiBxOy富集SEI抑枝晶提高软包稳定','SEI',['负极锂'],'本文结论','M0173',['T9'])]:
 mech(p,su,'LiFPB','conventional',pr,cats,typ,e,ts,'其他')
claim(p,'最优0.2 M LiFPB协同成膜，体相溶剂化基本不变','M0137 M0115 M0174 M0175')
fig(p,'T6','Figure S25a','si','容量','LiFPB','conventional','0.5C首圈/末圈','M0143','保持率锚点补容量')
fig(p,'T7','Figure 5g','main','初始容量','LiFPB','conventional','0.2C第1圈','M0152 M0153 M0157','对照初始容量缺')
p['gaps']=['锂厚/E/S/1C/电池温度未报告；不可把室温EIS当全部循环温度','浓度和盐种类梯度具体档位仅图；不能遗漏但无文字可抄','主文溶剂化不变与SI入壳解释冲突均保留','摘要75圈与正文76圈不同，采用正文具体76圈','软包载量/锂厚/E/S均未给；无bulk电导率/黏度实测数']
save(p)

