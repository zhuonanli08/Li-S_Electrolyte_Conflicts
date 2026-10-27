"""Semantic task coordinates for S09; numerical outputs are produced by the reader."""
import json
from step8a_prepare_debug53 import OUT,save
from step8h_read_figures import process
fd=OUT/'figures'/'S09'
def task(name,ix,tid,page,crop,scale,x,y,points,curves,exclude,**kw):
    def box(b):return [round(z*scale) for z in b]
    for s in curves:
        if '图例框' in s:s['图例框']=box(s['图例框'])
        s['排除']=[box(b) for b in s.get('排除',[])]
    return {'编号':name,'request_index':ix,'test_id':tid,'图':str(fd/'main'/f'p{page}_top.png'),
      '子图':box(crop),'x刻度':x,'y刻度':y,'取圈':points,'标记宽':8,'曲线':curves,'排除':[box(b) for b in exclude],
      'shared_test_anchor':True,**kw}
def color(fid,xy,anchors=[]):return {'配方编号':fid,'图例原文':fid,'图例框':xy,'anchors':anchors}
def gray(fid,ran,anchors=[]):return {'配方编号':fid,'图例原文':fid+'灰实圆','类型':'gray','gray_range':ran,'anchors':anchors}
def pairs(ids,base):return [(x,base) for x in ids if x!=base]+list(zip(ids[1:],ids[:-1]))
mean=lambda value,ev:{'type':'mean','cycles':list(range(1,51)),'value':value,'evidence_id':ev,'note':'图注明确前50圈均值，必须50个点全部可读；化成点只用于锚点，不输出。'}
tasks=[task('S09_F3B',1,'S09-T2',5,[620,0,1200,470],2150/1792,[0,10,20,30,40,50],[0,400,800,1200,1600],[6,25,49],
 [gray('DD',[180,215]),gray('DEE',[105,155]),color('F3DEE',[300,108,315,122]),color('F4DEE',[425,108,440,122],[mean(651,'M0112')]),color('F4DMB',[300,134,315,148]),color('F5DEE',[425,134,440,148])],
 [[270,65,560,165]],shared_test_anchor_evidence=['M0112','Fig3C caption'],comparison_pairs=pairs(['DD','DEE','F3DEE','F4DEE','F4DMB','F5DEE'],'DD')),
 task('S09_F3G',2,'S09-T4',5,[0,920,600,1400],2150/1792,[0,10,20,30,40,50],[0,400,800,1200,1600,2000],[6,25,49],
 [gray('DDN',[180,215]),color('F3DEE',[439,78,454,94]),color('F4DEE',[316,105,332,119]),color('F4DMB',[439,105,454,119],[mean(1050,'M0131')]),color('F5DEE',[316,132,332,146],[mean(679,'M0133')]),color('F6DEE',[439,132,454,146])],
 [[280,65,560,155]],shared_test_anchor_evidence=['M0131','M0133','Fig3H caption'],comparison_pairs=pairs(['DDN','F3DEE','F4DEE','F4DMB','F5DEE','F6DEE'],'DDN')),
 task('S09_F5A',3,'S09-T9',7,[0,0,660,500],2150/2048,[0,10,20,30,40,50],[200,400,600,800,1000,1200,1400],[6,25,49],
 [gray('DDN',[105,155]),color('F4DMB',[497,123,512,140],[{'cycle':6,'value':936.5,'evidence_id':'M0187'}])],
 [[470,75,650,150]],shared_test_anchor_evidence=['M0187']),
 task('S09_F5E',4,'S09-T10',7,[660,500,2048,1038],2150/2048,[0,20,40,60,80,100,120,140],[0,500,1000,1500,2000],[6,20,29],
 [gray('DDN',[105,155]),color('F4DMB',[777,192,792,207],[{'cycle':6,'value':1054,'evidence_id':'M0191'}])],
 [[0,0,1388,140],[420,140,1388,240]],shared_test_anchor_evidence=['M0191'],opening_size=3)]
save(fd/'tasks.json',tasks)
for t in tasks:
    try:r=process(t,fd)
    except Exception as e:r={'id':t['编号'],'test_id':t['test_id'],'status':'仅图未读','reason':str(e)};save(fd/(t['编号']+'_results.json'),r)
    print(json.dumps({'id':r['id'],'status':r['status'],'reason':r.get('reason'),'series':r.get('series')},ensure_ascii=False))
