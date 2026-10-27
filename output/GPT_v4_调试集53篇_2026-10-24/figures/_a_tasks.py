import json, pathlib
BASE=pathlib.Path(__file__).resolve().parent
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def series(id,label,box=None,anchors=None,kind='color',**kw):
 d={'配方编号':id,'图例原文':label,'类型':kind,'anchors':anchors or []};d.update(kw)
 if box:d['图例框']=box
 return d
def task(pid,tag,test,req,img,crop,x,y,points,curves,exclude,ev,notes='',**kw):
 d={'编号':pid+'_'+tag,'test_id':test,'request_index':req,'图':str(BASE/pid/img),'子图':crop,'x刻度':x,'y刻度':y,'标记宽':9,'取圈':points,'曲线':curves,'排除':exclude,'shared_test_anchor':True,'shared_test_anchor_evidence':ev,'notes':notes};d.update(kw);return d
def val(c,v,e):return {'cycle':c,'value':v,'evidence_id':e}
def retention(c,r,e,initial=1):return {'type':'retention','cycle':c,'initial_cycle':initial,'ratio':r,'evidence_id':e}
def put(pid,tasks,reviews=[]):
 p=BASE/pid/'tasks.json';assert not p.exists(),p;save(p,tasks);save(BASE/pid/'request_review.json',reviews)
if __name__=='__main__':
 # Source-pixel coordinates scaled from the displayed original; numerical values are program-read only.
 sc=lambda box,k:[round(v*k) for v in box]
 k=2009/1766
 p482a=task('P482','FS25a','T6',3,'si/image25.png',sc([0,0,1766,742],k),[0,50,100,150,200],[0,400,800,1200],[1,100,200],[series('conventional','blue LiTFSI',sc([289,448,303,462],k),[retention(200,.5641,'M0143')]),series('LiFPB','red LiTFSI + LiFPB',sc([289,535,303,548],k),[retention(200,.736,'M0143')])],[sc([0,0,1766,210],k),sc([210,425,1300,574],k),sc([1345,324,1592,451],k)],['M0143'])
 k=2051/1567
 p482g=task('P482','F5g','T7',4,'main/p8_xref167.png',sc([0,895,1108,1285],k),[0,20,40,60,80,100],[0,200,400,600,800,1000],[1,50,100],[series('orange_curve','orange (panel legend LiTFSI;正文LiFPB)',sc([136,1122-895,147,1133-895],k),[val(1,824.6,'M0152'),val(100,688.1,'M0153')]),series('blue_curve','blue (panel legend LiTFSI + LiFPB;正文conventional)',sc([136,1162-895,147,1174-895],k),[val(100,530.6,'M0157')])],[sc([0,0,1108,90],k),sc([110,205,780,322],k),sc([866,138,1016,215],k)],['M0152','M0153','M0157'],'Figure 5g图例与正文/同文其他图反向；仅按颜色读数，不作确定配方映射或方向。',opening_size=2)
 put('P482',[p482a,p482g],[{'request_index':1,'status':'no_anchor','reason':'梯度S22无同测试文字数字锚点。','evidence_ids':[]},{'request_index':2,'status':'no_anchor','reason':'梯度S23无同测试文字数字锚点。','evidence_ids':[]}])
 p564d=task('P564','F5d','T12',1,'main/p8_xref329.png',[0,435,900,850],[0,50,100,150,200],[0,500,1000,1500],[2,5,100],[series('E1.0','teal 1.0 M LiTFSI',[348,53,364,69]),series('EB','orange 0.8 M LiTFSI/0.2 M LiBr',[510,53,526,69],[val(100,883,'M0252')])],[[0,0,900,130],[400,260,730,333]],['M0252'],'原请求写Fig.5c，但M0252明确Figure5d循环图；对照100圈已终止，不外推。',opening_size=3)
 p564e=task('P564','F5e','T13',2,'main/p8_xref329.png',[910,440,1750,850],[0,10,20,30,40,50,60,70],[0,300,600,900,1200,1500],[2,20,38],[series('E1.0','teal 1.0 M LiTFSI',[319,60,335,76]),series('EB','orange 0.8 M LiTFSI/0.2 M LiBr',[473,60,489,76],[val(2,1129,'M0255')])],[[0,0,840,120],[510,260,740,338]],['M0255'],'0.05C形成圈位于最先点；0.1C初始对应图示2圈。仅读共同存在循环点。',opening_size=3)
 put('P564',[p564d,p564e])
 p337b=task('P337','FS13b','T5',1,'si/image13.png',[900,0,1660,501],[0,20,40,60,80,100],[0,400,800,1200,1600],[1,50,100],[series('R-SEI','gray R-SEI',anchors=[retention(100,.613,'M0165')],kind='gray',gray_range=[80,185]),series('FN-SEI','cyan FN-SEI',[521,112,538,128],[retention(100,.806,'M0165')])],[[0,0,760,172],[0,290,760,393]],['M0165'],'等量LiNO3对比；容量与CE条件混杂保持文本判定。')
 put('P337',[p337b])
