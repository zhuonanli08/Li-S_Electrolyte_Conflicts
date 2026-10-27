import json,pathlib
from PIL import Image
B=pathlib.Path('output/GPT_v4_调试集53篇_2026-10-24')
def task(pid,num,test,req,path,display,crop,xt,yt,cycles,exclude,series,notes='',**kw):
 path=B/'figures'/pid/path;w,h=Image.open(path).size;sx=w/display[0];sy=h/display[1]
 sc=lambda box:[round(box[0]*sx),round(box[1]*sy),round(box[2]*sx),round(box[3]*sy)]
 cp=sc(crop)
 def local(box):
  x=sc(box);return [x[0]-cp[0],x[1]-cp[1],x[2]-cp[0],x[3]-cp[1]]
 ss=[]
 for z in series:
  z=z.copy()
  if '图例框' in z:z['图例框']=local(z['图例框'])
  if '排除' in z:z['排除']=[local(x) for x in z['排除']]
  ss.append(z)
 return dict(编号=pid+'_'+num,test_id=pid+'-'+test,request_index=req,图=str(path.resolve()),子图=cp,x刻度=xt,y刻度=yt,标记宽=round(7*sx),取圈=cycles,排除=[local(x) for x in exclude],曲线=ss,shared_test_anchor=True,notes=notes,**kw)
def color(name,box,anchors=[],exclude=[]):return dict(配方编号=name,图例原文=name+'实心容量点',类型='color',图例框=box,anchors=anchors,排除=exclude)
def gray(name,lo,hi,anchors=[],exclude=[]):return dict(配方编号=name,图例原文=name+'灰色实心容量点',类型='gray',gray_range=[lo,hi],anchors=anchors,排除=exclude)
def black(name,anchors=[]):return dict(配方编号=name,图例原文=name+'黑色实心容量点',类型='black',anchors=anchors)
def val(c,v,e):return dict(cycle=c,value=v,evidence_id=e)
def life(v,e):return dict(type='lifetime',value=v,evidence_id=e)
def save(pid,tasks,reviews=[]):
 d=B/'figures'/pid;d.mkdir(parents=True,exist_ok=True)
 for name,x in [('tasks.json',tasks),('request_review.json',reviews)]: (d/name).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':
 p='S16';ts=[]
 ts.append(task(p,'F5a','T5',1,'main/p8_xref75.png',(1612,1536),(0,0,850,510),[0,20,40,60,80,100],[0,300,600,900,1200],[1,50,99],[(160,40,725,80),(170,310,400,415),(490,330,720,420)],[gray('DD',60,160),color('DD_DMSO',(184,357,204,376)),color('DD_HMPA',(184,389,204,409),[val(1,1094,'M0165')])],'100圈靠右轴，保留99圈实际读取；容量实心与CE空心分离。',shared_test_anchor_evidence=['M0165']))
 ts.append(task(p,'F5c','T6',2,'main/p8_xref75.png',(1612,1536),(0,515,850,1020),[0,10,20,30,40,50,60,70],[0,400,800,1200,1600],[1,40,69],[(170,550,730,610),(180,850,405,925),(475,850,730,925)],[color('DD_DMSO',(194,865,214,887)),color('DD_HMPA',(194,898,214,920),[val(1,1213,'M0172')])],'图例实际是DD_DMSO和DD_HMPA，无DD；更正请求B对应，不制造DD数据。69圈为靠右轴的70圈之前实际点。',shared_test_anchor_evidence=['M0172']))
 ts.append(task(p,'F5e','T7',3,'main/p8_xref75.png',(1612,1536),(0,1035,850,1536),[0,10,20,30,40,50,60],[0,300,600,900,1200],[1,30,55,64],[(170,1070,730,1120),(180,1370,400,1450),(500,1370,730,1450)],[gray('DD',80,160),color('DD_HMPA',(193,1420,215,1440),[val(1,864,'M0191')])],'灰色DD后期CE空心散点可能干扰，需叠图检查；原文85.4%可辅助，第一容量锚为864。',shared_test_anchor_evidence=['M0191']))
 ts.append(task(p,'F6d','T13',5,'main/p9_xref78.png',(1984,1272),(910,625,1984,1272),[0,5,10,15,20],[0,.9,1.8,2.7,3.6],[1,10,19],[(1110,1050,1465,1150),(1630,1100,1750,1155)],[black('DD'),color('DD_HMPA',(1135,1105,1160,1132),[val(1,2.71,'M0185')])],'使用左轴Ah；右轴仅HMPA比容量不能套给DD。20圈点贴右轴，读取实际19圈。',shared_test_anchor_evidence=['M0185']))
 save(p,ts,[dict(request_index=4,status='no_anchor',reason='S19a独立循环无同测试数值锚；其他倍率容量不得混用。',evidence_ids=['S0224']),dict(request_index=2,status='corrected_comparator',reason='Fig5c图例为DD_DMSO/ DD_HMPA，无DD，按真实图例读取。')])
