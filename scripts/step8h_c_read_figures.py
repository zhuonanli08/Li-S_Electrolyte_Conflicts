"""Geometric digitization; model supplies semantic tasks, never numerical points."""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import step6e_figure_read_trial as old
from step8a_prepare_debug53 import save

def process(task,out):
    img=old.load(task['图'],task['子图']);geometry=img
    if task.get('axis_threshold'):
        geometry=img.copy()
        gray=(img.max(-1)-img.min(-1)<20)&(img.max(-1)<task['axis_threshold'])
        geometry[gray]=0  # geometry only; curve colors/readings still use original pixels
    frame=old.v3.找坐标框(geometry)
    def calibration(axis):
        key=axis+'_tick_pixels'
        if key not in task:return old.calib(geometry,frame,axis,task[axis+'刻度'])
        pix=np.array(task[key],float);values=np.array(task[axis+'刻度'],float)
        a,b=np.polyfit(pix,values,1);res=np.abs(pix-(values-b)/a).tolist()
        return a,b,res
    cx=calibration('x');cy=calibration('y')
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
        kind=s.get('类型','color')
        color=old.v3.取图例色(img,s['图例框']) if kind=='color' else None
        excl=task.get('排除',[])+s.get('排除',[])
        if kind=='gray':
            from scipy import ndimage
            lo,hi=s['gray_range'];mask=(img.max(-1)-img.min(-1)<15)&(img.min(-1)>=lo)&(img.max(-1)<=hi)
            left,right,top,bottom=frame
            mask[:,:left+4]=False;mask[bottom-3:,:]=False
            if right:mask[:,right-3:]=False
            if top:mask[:top+4,:]=False
            for x0,y0,x1,y1 in excl:mask[y0:y1,x0:x1]=False
            mask=ndimage.binary_opening(mask,structure=np.ones((5,5)))
        elif task.get('opening_size'):
            from scipy import ndimage
            mask=(img.max(-1)<90) if kind=='black' else old.v3.同色掩膜(img,np.array(color,np.uint8))
            left,right,top,bottom=frame
            mask[:,:left+4]=False;mask[bottom-3:,:]=False
            if right:mask[:,right-3:]=False
            if top:mask[:top+4,:]=False
            for x0,y0,x1,y1 in excl:mask[y0:y1,x0:x1]=False
            w=task['opening_size'];mask=ndimage.binary_opening(mask,structure=np.ones((w,w)))
        else:
            if kind=='color' and 'mask_opening' in task:
                from scipy import ndimage
                mask=old.v3.同色掩膜(img,color)
                left,right,top,bottom=frame
                mask[:,:left+4]=False;mask[bottom-3:,:]=False
                if right:mask[:,right-3:]=False
                if top:mask[:top+4,:]=False
                for x0,y0,x1,y1 in excl:mask[y0:y1,x0:x1]=False
                k=task['mask_opening'];mask=ndimage.binary_opening(mask,structure=np.ones((k,k)))
            elif kind=='color' and 'color_lab_tolerance' in task:
                original_color_mask=old.v3.同色掩膜
                old.v3.同色掩膜=lambda arr,col:original_color_mask(arr,col,lab容差=task['color_lab_tolerance'])
                try:mask=old.series_mask(img,frame,kind,color,excl)
                finally:old.v3.同色掩膜=original_color_mask
            else:mask=old.series_mask(img,frame,kind,color,excl)
        vals=[]
        for w in [task['标记宽'],task['标记宽']+2]:
            vals.append({str(c):old.value_at(mask,cx,cy,c,w) for c in task['取圈']})
        halfgrid=float(min(np.diff(sorted(task['y刻度'])))/2)
        point_usable={k:bool(v is not None and vals[1][k] is not None and abs(v-vals[1][k])<=halfgrid) for k,v in vals[0].items()}
        stable=any(point_usable.values())
        anchors=[]
        for a in s.get('anchors',[]):
            typ=a.get('type','value')
            if typ in ('lifetime','minimum_lifetime'):
                cols=np.nonzero(mask.any(0))[0]
                val=None if not len(cols) else round(cx[0]*(cols.max()-task['标记宽']/2)+cx[1],1)
            elif typ=='maximum_cycle':
                measured=[(c,old.value_at(mask,cx,cy,c,task['标记宽'])) for c in a['cycles']]
                measured=[(c,v) for c,v in measured if v is not None]
                val=max(measured,key=lambda z:z[1])[0] if measured else None
            elif typ=='maximum':
                measured=[old.value_at(mask,cx,cy,c,task['标记宽']) for c in a['cycles']]
                val=max((v for v in measured if v is not None),default=None)
            else:val=old.value_at(mask,cx,cy,a['cycle'],task['标记宽'])
            target=a.get('value')
            if typ=='retention':
                if a.get('initial_type')=='maximum':
                    measured=[old.value_at(mask,cx,cy,c,task['标记宽']) for c in a['initial_cycles']]
                    initial=max((v for v in measured if v is not None),default=None)
                else:initial=old.value_at(mask,cx,cy,a['initial_cycle'],task['标记宽'])
                target=None if initial is None else a['ratio']*initial
            tolerance=float(min(np.diff(sorted(task['x刻度'])))/2) if typ in ('lifetime','minimum_lifetime','maximum_cycle') else halfgrid
            if typ=='value_range':
                target=a['range'];passed=val is not None and target[0]-halfgrid<=val<=target[1]+halfgrid
            elif typ in ('minimum_lifetime','minimum_value'):
                passed=val is not None and target is not None and val>=target-a.get('tolerance',tolerance)
            else:passed=bool(val is not None and target is not None and abs(val-target)<=a.get('tolerance',tolerance))
            anchors.append({**a,'expected_value':target,'read_value':val,'tolerance':tolerance,'pass':bool(passed)})
        valid=bool(anchors) and all(a['pass'] for a in anchors)
        result['series'][s['配方编号']]={'legend':s['图例原文'],'color':None if color is None else color.tolist(),
                'points':vals[0],'repeat_points':vals[1],'points_repeat_consistent':point_usable,'anchors':anchors,
                'usable':valid and stable,'reason':'通过' if valid and stable else '锚点未通过/无锚点/取值遮挡'}
        ys,xs=np.nonzero(mask)
        for x,y in zip(xs[::5],ys[::5]):draw.point((int(x),int(y)),fill='#00B050')
    for box in task.get('排除',[]):draw.rectangle(box,outline='gray')
    im.save(out/f"核对_{task['编号']}.png")
    if task.get('shared_test_anchor'):
        # The protocol requires a number for this test, not one number per arm.
        # An explicit same-test caption may identify both arms with one anchor.
        given=[a for s in result['series'].values() for a in s['anchors']]
        shared_ok=bool(given) and all(a['pass'] for a in given)
        result['shared_test_anchor_evidence']=task.get('shared_test_anchor_evidence',[])
        for s in result['series'].values():
            s['usable']=shared_ok and any(s['points_repeat_consistent'].values())
            s['reason']='同测试共享锚点通过，曲线按图例分别对应' if s['usable'] else '共享锚点或取值核验失败'
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
            result={'id':task['编号'],'test_id':task.get('test_id'),'source_image':task.get('图'),'status':'仅图未读','reason':str(e)}
            save(p.parent/f"{task['编号']}_results.json",result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
