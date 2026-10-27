from _a_tasks import *
from PIL import Image
sc=lambda box,k:[round(v*k) for v in box]
k=2007/1902
curves=[]
for id,y in [('2.5-SL',414),('2.0-SL',483),('1.5-SL',552),('1.0-SL',620),('0.5-SL',969),('standard-SL',1038)]:
 curves.append(series(id,id,sc([1175,y-8,1193,y+8],k),[val(2,278,'M0078')] if id=='0.5-SL' else []))
put('P296',[task('P296','F4','T1',1,'main/p4_xref74.png',[0,0,2007,1384],[0,10,20,30,40,50],[0,500,1000,1500,2000],[2,5,50],curves,[sc(b,k) for b in [[0,0,1902,350],[1110,360,1610,670],[1100,920,1650,1100]]],['M0078'],'第1圈高容量与CE点相邻，仅读第2圈及共同存在的圈；末圈已失效配方不外推。',axis_threshold=200)])
p=BASE/'P354/si/p15_xref159.png';im=Image.open(p).convert('RGBA');bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im);bg.convert('RGB').save(p.with_name('p15_xref159_white.png'))
t4=task('P354','F4b','T4',1,'main/p5_xref220.png',[0,540,800,1148],[0,10,20,30,40,50],[0,500,1000,1500,2000],[2,25,50],[series('3M','pink 3 M',[371,169,382,180]),series('3.6M','orange 3.6 M',[374,198,390,214],[val(2,1578.8,'M0156'),val(50,82.3,'M0156')]),series('4M','green 4 M',[371,234,384,246],[val(2,1475.4,'M0156'),val(50,161.6,'M0156')])],[[0,0,800,141],[340,148,675,254]],['M0156'],axis_threshold=180,opening_size=2)
t6=task('P354','F5b','T6',3,'main/p6_xref245.png',[0,527,800,1126],[0,10,20,30,40,50],[0,500,1000,1500,2000],[1,2,25,50],[series('3M','pink 3 M',[323,168,336,181],[val(2,1462.9,'M0178'),val(50,732.3,'M0178')]),series('HFE','purple 3 M in DME/HFE',[324,203,337,216],[val(2,1347.7,'M0178'),val(50,830.4,'M0178')])],[[0,0,800,126],[315,145,677,231]],['M0178'],axis_threshold=180,opening_size=2)
t7=task('P354','F5c_2C','T7',4,'main/p6_xref245.png',[800,527,1584,1126],[0,5,10,15,20,25,30],[0,400,800,1200,1600],[23],[series('3M','pink 3 M',[180,461,193,474]),series('HFE','purple 3 M in DME/HFE',[180,495,193,508],[val(23,943,'M0005')])],[[0,0,784,90],[170,440,680,515]],['M0005'],'仅2C档内同点比较，不把2C锚借给其他倍率档。',axis_threshold=180,opening_size=2)
t8=task('P354','FS10c','T8',5,'si/p15_xref159_white.png',[350,700,1330,1433],[0,10,20,30,40,50,60,70,80],[0,500,1000,1500,2000],[1,2,50],[series('3M','pink 3 M',[411,133,427,149]),series('HFE','purple 3 M in DME/HFE',[412,174,427,190],[val(2,1203.7,'S0079'),val(50,787.3,'S0079')])],[[350,90,835,230],[230,250,835,305]],['S0079'],'保留原图Alpha透明背景，仅合成白底以重现PDF显示。对照若无相同后续圈不外推。',axis_threshold=180,opening_size=2)
put('P354',[t4,t6,t7,t8],[{'request_index':2,'status':'no_anchor','reason':'Figure4c低倍率测试无同测试可核数字。','evidence_ids':[]}])
p389s=task('P389','FS10a','T3',1,'si/p15_xref136.png',[0,0,840,642],[0,50,100,150,200,250,300],[0,400,800,1200,1600],[1,100,280],[series('DOL/DME','blue diamond',[204,456,218,471]),series('HME-EPSE','pink square',[205,482,218,495],[val(1,856,'M0100')])],[[0,0,840,290],[190,440,390,500]],['M0100'],'280圈时对照已终止，不给对照推值。',opening_size=2)
k=2350/1356
p389m=task('P389','F3c','T4',2,'main/p4_xref48.png',sc([90,670,1356,1325],k),[0,20,40,60,80,100],[0,400,800,1200,1600,2000],[10,60,69,113],[series('DOL/DME','blue diamond',sc([221,384,237,400],k),[val(69,652,'M0106')]),series('HME-EPSE','pink square',sc([221,416,237,432],k),[val(69,860,'M0107')])],[sc(b,k) for b in [[0,0,1266,250],[210,370,650,522]]],['M0106','M0107'],'69圈DOL/DME存在突变及充放电标记，程序核锚点；不跨FigureS12平行样。',opening_size=3)
put('P389',[p389s,p389m])
k=1659/1568
p525=task('P525','F5c','T9',1,'main/p6_xref63.png',sc([0,530,1568,1060],k),[0,100,200,300,400,500],[0,200,400,600,800,1000,1200],[1,100,500],[series('STE','red STE',sc([1151,153,1168,168],k),[val(1,944,'S0108')]),series('CE','blue CE',sc([1151,196,1168,211],k))],[sc(b,k) for b in [[0,0,1568,112],[1110,140,1400,220]]],['S0108'],'S4的本工作5C944容量与图5c初始点核对；倍率图5b之5C平台明显不同，不跨批。',opening_size=3)
put('P525',[p525],[{'request_index':2,'status':'no_anchor','reason':'100圈只是测试时长，正文未给该-30°C测试的可核容量、保持率或失效寿命。','evidence_ids':['M0184']}])
k=2531/1376
p352=task('P352','F5d','T11',1,'main/p9_render300.png',sc([100,420,1270,735],k),[0,10,20,30,40,50,60,70,80,90,100,110,120,130],[0,200,400,600,800,1000],[1,50,100,130],[series('TE5','blue TE-5%',sc([563,183,603,198],k),[val(1,140,'M0175')]),series('TE10','orange TE-10%',sc([563,204,610,219],k),[val(130,406,'M0183')]),series('TE15','purple TE-15%',sc([563,224,610,239],k),[val(1,270,'M0175')])],[sc(b,k) for b in [[0,0,1170,85],[552,177,660,246]]],['M0175','M0183'],'逐档载量1.7/2.1/1.9mgcm-2，记录梯度数值不作同条件数值判向；不反算浓度。',axis_threshold=210,opening_size=2)
put('P352',[p352])
# P337 remaining main request appended without touching the attempted S13 task.
k=1778/1545
p337=task('P337','F5c','T6',2,'main/p7_xref126.png',sc([95,415,1085,795],k),[0,50,100,150,200,250],[0,400,800,1200,1600],[1,25,75,250],[series('R-SEI','gray R-SEI',anchors=[val(1,1250,'M0173')],kind='gray',gray_range=[70,180]),series('FN-SEI','cyan FN-SEI',sc([758,101,778,113],k),[val(1,1250,'M0173')])],[sc(b,k) for b in [[0,0,990,115],[400,267,900,308]]],['M0173'],'1250为约数；25圈衰退起点不误作曲线终止，失效后不外推。',opening_size=2)
p=BASE/'P337/tasks.json';tt=json.loads(p.read_text(encoding='utf8'));tt.append(p337);save(p,tt)
