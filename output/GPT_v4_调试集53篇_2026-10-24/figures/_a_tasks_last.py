from _a_tasks import *
sc=lambda box,k:[round(v*k) for v in box]
k=2050/1792
c=[]
for id,label,y in [('1M','cyan square 1M',46),('0.2','green circle 0.2',77),('Se','orange triangle 0.2Se',107),('Te','salmon down-triangle 0.2Te',138),('Mix','red diamond Se0.15Te0.05',169)]:
 c.append(series(id,label,sc([177,y-4,185,y+4],k),[val(1,1103,'M0258'),val(100,985,'M0259')] if id=='Mix' else []))
t=task('P591','F5a','T6',1,'main/p11_xref34.png',sc([0,0,1180,470],k),[0,20,40,60,80,100],[600,800,1000,1200,1400,1600],[1,50,80,100],c,[sc([0,0,1180,190],k)],['M0258','M0259'],'0.2Te末圈仅到约80圈，100圈不外推。',opening_size=2,axis_threshold=180)
put('P591',[t],[{'request_index':2,'status':'conditions_differ','reason':'Mix/LowMix的LiNO3分别3 wt%/2 wt%；不能作同条件容量数值方向比较，作者定性仍保留在文本。','evidence_ids':['M0302']}])
put('P455',[],[{'request_index':1,'status':'conditions_differ','reason':'原图S14的黑色对照为1 M LiTFSI+0.25 M LiNO3；红色LiTF组为0.05 M LiTFSI+0.025 M LiNO3+0.015 M LiTF。非同LiNO3用量，不能把黑组错配为预测L组并作同条件判向。九圈稳定、十圈失效的作者文字保留。','evidence_ids':['M0272','S0027'],'inspected_image':'si/p13_xref143.png'}])
put('P432',[],[{'request_index':i,'status':'no_anchor','reason':'M0212给20–25圈失效，但原图BmPyr容量曲线实际仍绘至100圈，失效起点没有数值容量或保持率判据；不能把20–25当曲线终点，现程序无法独立校验该语义寿命锚。仅图未读。','evidence_ids':['M0212'],'inspected_image':'main/p7_xref203.png'} for i in [1,2]])
put('P413',[],[{'request_index':i,'status':'no_anchor','reason':'完整正文/SI核对没有此测试可核容量、保持率或失效寿命数字；50/100为绘图时长不构成锚点。','evidence_ids':[]} for i in range(1,5)])
put('P527',[],[{'request_index':1,'status':'out_of_scope','reason':'请求为离子电导率与Li迁移数纯物性梯度，非本轮允许的循环性能缺失容量侧。','evidence_ids':['M0067']}])
p=BASE/'P337/request_review.json';rr=json.loads(p.read_text(encoding='utf8'));rr.append({'request_index':3,'status':'duplicate','reason':'SI原图标题误写Figure20，已定位image20.png。单组软包的首圈1.67Ah和20圈1.55Ah均已由M0200/M0201给出，无待补缺失容量侧。','evidence_ids':['M0200','M0201'],'inspected_image':'si/image20.png'});save(p,rr)
for p in ['P394','P548']:
 put(p,[])
