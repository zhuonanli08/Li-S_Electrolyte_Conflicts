import json
from pathlib import Path
from review_c_extra_finish import finish

R = Path('output/GPT_v4_调试集53篇_2026-10-24/figures')
def save(p, x):
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2), encoding='utf-8')

condition = {
 'S19': ('同一面板内三组均为 1 M LiTFSI、0.4 M LiNO3；各倍率仅同一位置配对，Li2S6 与 CNT/S 测试不混合。', ['S0016','S0029','S0035','S0039']),
 'S20': ('CD40 使用 0.4 M LiNO3，DD 使用 2.0 wt% LiNO3；冻结规程下不能作为相同 LiNO3 条件配对。保留单组读值，取消三项方向比较。', ['S0010','S0011']),
 'S21': ('S14 系列均按未添加 LiNO3 的常规条件；S23 两组均添加 1 wt% LiNO3。分别只在本面板内同条件比较，不跨图配对。', ['S0006','S0007','S0008','S0029','S0032','S0154']),
 'S23': ('BL 与 BL+20% 均为 1 M LiTFSI、0.2 M LiNO3。Fig5a 及 S33 只比较同一面板和倍率；Fig5f 多层软包仅保留 BL+20% 单值，不与其他载量/E/S 的 BL 软包配对。', ['S0015','S0016','S0037','S0042','S0161']),
 'S24': ('只比较同一图、同倍率或同 E/S/孔隙率的 MAN 与对照；不同梯度条件分别保存。方法未报告 LiNO3，保持未知，不补写为零。Fig5g/h 为 MAN 单组，不生成配对。', ['M0116','M0117','M0131','M0135','M0136','M0137','M0154','M0155']),
 'S25': ('DD 与 MtBE 均为 1 M LiTFSI、0.2 M LiNO3；Fig5b 同为 3.5 mg cm−2、E/S 10、21°C。只在相同倍率位置配对。', ['S0010','S0011','S0012','M0192'])
}
for pid,(reason,evidence) in condition.items():
    d=R/pid; p=d/'tasks.json'; tasks=json.loads(p.read_text(encoding='utf-8'))
    records=[]
    for task in tasks:
        has_pairs=bool(task.get('comparison_pairs'))
        if pid=='S20':
            task['excluded_comparison_pairs']=task.get('comparison_pairs') or task.get('excluded_comparison_pairs', [])
            task['comparison_pairs']=[]
            task['allow_comparison']=False
        elif not has_pairs:
            task['allow_comparison']=False
        else:
            # Read and preserve any previous restriction instead of resetting it.
            task.setdefault('allow_comparison', True)
        review={'task_id':task['编号'],'allow_comparison':task['allow_comparison'],
                'same_conditions':False if pid=='S20' else (True if task['allow_comparison'] else None),
                'reason':reason,'evidence_ids':evidence}
        task['condition_review']=review
        if task['编号']=='S24_F5h':
            task['point_conditions']={str(i):('33.5 mA g−1' if i<=2 else '50 mA g−1') for i in range(1,11)}
            task['point_condition_basis']='原始 Fig5h 图内标注；M0115 OCR 不完整，未据 OCR 补猜。'
        if task['编号']=='S25_F5b':
            task.get('point_conditions',{}).pop('52',None)
        records.append(review)
    save(p,tasks)
    save(d/'condition_review.json',{'paper_id':pid,'reviewer':'extract_c','date':'2026-10-27','tasks':records})

finish('S24',[
 '11 个任务逐一核对了原始图和叠图；轴、曲线身份、点的位置及单位一致，均通过同测试数字锚点。',
 'Fig3d 使用对数倍率坐标，Fig5b 使用 E/S 类别位置；没有把不等数值间距当作线性连续坐标。Fig5d 孔隙率按降序轴读值。',
 'Fig5b/d 每个 E/S 或孔隙率独立任务，只比较同档 MAN 与 DD；没有跨条件配对。重叠无法稳定拆出的 Fig3d 对照点留空。',
 'Fig5g 只有 MAN；Fig5h 纵轴为 Ah，保留三位小数，未换算为 mAh g−1。Fig5h 第 1–2 圈为 33.5 mA g−1，第 3–10 圈为 50 mA g−1，依据图内标注。',
 condition['S24'][0]
])

for pid in condition:
    d=R/pid; p=d/'visual_review.json'; vr=json.loads(p.read_text(encoding='utf-8'))
    if condition[pid][0] not in vr.get('notes',[]): vr.setdefault('notes',[]).append(condition[pid][0])
    vr['condition_review_file']='condition_review.json'; save(p,vr)
    for task in json.loads((d/'tasks.json').read_text(encoding='utf-8')):
        p=d/f"{task['编号']}_results.json"; res=json.loads(p.read_text(encoding='utf-8'))
        res['allow_comparison']=task['allow_comparison']
        res['condition_review']=task['condition_review']
        if pid=='S24': res['reader']='review_c_s24_fig.py'
        elif task['编号']=='S21_FS14b': res['reader']='review_c_s21_fig.py'
        save(p,res)

summary={}
for pid in condition:
    d=R/pid; tasks=json.loads((d/'tasks.json').read_text(encoding='utf-8'))
    vr=json.loads((d/'visual_review.json').read_text(encoding='utf-8'))
    rr=json.loads((d/'request_review.json').read_text(encoding='utf-8'))
    assert len(rr)==len(tasks)
    summary[pid]={'requests':len(rr),'plots':len(tasks),'accepted_points':sum(len(v) for x in vr['overlay_details'] for v in x['accepted_points'].values()),'comparison_allowed_tasks':sum(x['allow_comparison'] for x in tasks)}
save(R/'C_extra_group_summary.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
