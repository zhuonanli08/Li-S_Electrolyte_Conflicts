"""Geometric digitization; model supplies semantic tasks, never numerical points."""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import step6e_figure_read_trial as old
from step8a_prepare_debug53 import save

def process(task,out):
    img=old.load(task['图'],task['子图']);frame=old.v3.找坐标框(img)
    cx=old.calib(img,frame,'x',task['x刻度']);cy=old.calib(img,frame,'y',task['y刻度'])
    if min(len(task['x刻度']),len(task['y刻度']))<3 or max(cx[2]+cy[2])>2:
        raise ValueError('刻度不足3或标定残差超过2像素')
    result={'id':task['编号'],'test_id':task['test_id'],'source_image':task['图'],
            'frame':[int(x) if x is not None else None for x in frame],
            'calibration':{'x':cx,'y':cy},'series':{},'status':'待核锚点'}
    im=Image.fromarray(img);draw=ImageDraw.Draw(im)
    for v in task['x刻度']:
        x=(v-cx[1])/cx[0];draw.line([(x,frame[2] or 0),(x,frame[3])],fill='orange')
    for v in task['y刻度']:
        y=(v-cy[1])/cy[0];draw.line([(frame[0],y),(frame[1] or img.shape[1]-1,y)],fill='orange')
    for s in task['曲线']:
        color=old.v3.取图例色(img,s['图例框']) if s.get('类型','color')=='color' else None
        excl=task.get('排除',[])+s.get('排除',[])
        mask=old.series_mask(img,frame,s.get('类型','color'),color,excl)
        vals=[]
        for w in [task['标记宽'],task['标记宽']+2]:
            vals.append({str(c):old.value_at(mask,cx,cy,c,w) for c in task['取圈']})
        halfgrid=float(min(np.diff(sorted(task['y刻度'])))/2)
        point_usable={k:bool(v is not None and vals[1][k] is not None and abs(v-vals[1][k])<=halfgrid) for k,v in vals[0].items()}
        stable=any(point_usable.values())
        anchors=[]
        for a in s.get('anchors',[]):
            val=old.value_at(mask,cx,cy,a['cycle'],task['标记宽'])
            target=a.get('value')
            if a.get('type')=='retention':
                initial=old.value_at(mask,cx,cy,a['initial_cycle'],task['标记宽'])
                target=None if initial is None else a['ratio']*initial
            anchors.append({**a,'expected_value':target,'read_value':val,'pass':bool(val is not None and target is not None and abs(val-target)<=a.get('tolerance',halfgrid))})
        valid=bool(anchors) and all(a['pass'] for a in anchors)
        result['series'][s['配方编号']]={'legend':s['图例原文'],'color':None if color is None else color.tolist(),
                'points':vals[0],'repeat_points':vals[1],'points_repeat_consistent':point_usable,'anchors':anchors,
                'usable':valid and stable,'reason':'通过' if valid and stable else '锚点未通过/无锚点/取值遮挡'}
        ys,xs=np.nonzero(mask)
        for x,y in zip(xs[::5],ys[::5]):draw.point((int(x),int(y)),fill='#00B050')
    for box in task.get('排除',[]):draw.rectangle(box,outline='gray')
    im.save(out/f"核对_{task['编号']}.png")
    if any(not s['usable'] for s in result['series'].values()):
        result['status']='仅图未读：至少一条曲线无可核锚点或锚点不通过'
        for s in result['series'].values():s['usable']=False
    else:result['status']='锚点通过；仅使用points_repeat_consistent为true的点'
    save(out/f"{task['编号']}_results.json",result)
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tasks');a=ap.parse_args();p=Path(a.tasks)
    for task in json.loads(p.read_text(encoding='utf-8')):
        try:print(json.dumps(process(task,p.parent),ensure_ascii=False))
        except Exception as e:
            result={'id':task['编号'],'status':'仅图未读','reason':str(e)}
            save(p.parent/f"{task['编号']}_results.json",result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
