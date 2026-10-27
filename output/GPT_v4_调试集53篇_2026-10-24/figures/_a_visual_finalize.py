from _a_tasks import *
def rev(pid,summary,overlays=[],details=None):
 save(BASE/pid/'visual_review.json',{'paper_id':pid,'reviewer':'extract_a','date':'2026-10-27','reviewed_overlays':overlays,'result':summary,'details':details or [],'scoring_use':'只作为读图补充；不回写冻结独立预测或首轮文本评分。'})
def filter_points(pid,tag,fid,excluded,reason):
 p=BASE/pid/(pid+'_'+tag+'_results.json');r=json.loads(p.read_text(encoding='utf8'));s=r['series'][fid]
 s['program_points_before_visual_filter']=s['points'].copy();s['program_repeat_points_before_visual_filter']=s['repeat_points'].copy();s['visual_excluded_points']={k:reason for k in excluded}
 for k in excluded:s['points'].pop(k,None);s['repeat_points'].pop(k,None);s['points_repeat_consistent'].pop(k,None)
 save(p,r)
p=BASE/'P296/P296_F4_results.json';r=json.loads(p.read_text(encoding='utf8'))
for fid in ['1.5-SL','2.0-SL']:
 r['series'][fid]['usable']=False;r['series'][fid]['reason']='视觉否决：青色两曲线紧邻且取色掩膜交叠，不能独立映射。'
r['visual_validation']='部分曲线通过；1.5-SL与2.0-SL排除';save(p,r)
p=BASE/'P296/tasks.json';t=json.loads(p.read_text(encoding='utf8'));t[0]['comparison_pairs']=[[a,'standard-SL'] for a in ['0.5-SL','1.0-SL','2.5-SL']];save(p,t)
rev('P296','Figure4坐标标定和0.5-SL第二圈278锚通过。容量为实心点，CE空心点已排除。1.5/2.0-SL相近青色掩膜交叠，results已明确usable=false；其余四条保留。50圈已结束的组不补。',['核对_P296_F4.png'])
rev('P337','S13b刻度无法满足三点标定，终态仅图未读。Figure5c一次边界窗口修正后，FN初始约1250锚通过，但灰色R初始点遮挡不能核锚；按整图规则不采用。软包Figure20原图已定位，首圈与20圈均有正文值，重复请求不补。',['核对_P337_F5c.png'])
rev('P352','Figure5d容量圆点与CE菱形分离、各色映射和数字锚点通过。已看到各组载量1.7/2.1/1.9mgcm-2；只保留逐组容量，不作同条件数值方向。',['核对_P352_F5d.png'])
rev('P354','四个适用面板各进行一次浅灰刻度几何阈值修正，仍不满足刻度数或2像素残差上限，全部仅图未读。S10c保持原尺寸白底显示，未虚增分辨率；4c缺同测试锚点。')
filter_points('P389','FS10a','HME-EPSE',['1'],'粉色初始点被蓝色覆盖，窄窗可能只捕获可见边缘；不把局部边缘中位值当完整初始容量。')
rev('P389','S10a初圈附近同色箭头已一次排除；280圈锚以正文856×60%=513.6校验，读值513.7通过。HME初始点被蓝色遮挡，已从供汇总points移除并保存程序原值审计；100圈两组有效。Figure3c核对69圈652/860通过；113圈对照已无点，10圈HME不稳定值不采用。',['核对_P389_FS10a.png','核对_P389_F3c.png'])
rev('P394','冻结预测无figure_requests，无待读图。')
rev('P413','四项均缺同测试可核容量、保持率或失效寿命数字；按规则全部不读。')
rev('P432','已检查Figure5原图。BmPyr曲线仍画至100圈；作者20–25圈失效不等于曲线终点，也未给容量阈值，无法用当前程序核验该锚。两个请求均仅图未读。')
rev('P455','已检查SI FigureS14原图，黑对照0.25 M LiNO3、红LiTF组0.025 M LiNO3，不能错映射为相同硝酸锂条件。保留作者9圈稳定/10圈失效文字，图方向不采用。')
rev('P482','S25a缩小文字排除框后，通过两组200圈保持率锚和重复窗口，容量实心圆/CE空心圆区分正确。5g正文将高容量曲线归LiFPB，而图例把橙色写LiTFSI，存在反向映射；仅保留颜色程序读值，全部usable=false，不强配A/B。蓝色末圈受文字排除区域影响且已达一次修正限，不再追试。',['核对_P482_FS25a.png','核对_P482_F5g.png'])
rev('P525','Figure5c表S4本工作5C944与起始容量锚匹配；首点靠近轴，一次调整窗口13/15像素后通过半格误差。CE带与容量点已分离，首/100/500圈读值可用。-30°C图5e仅给100圈时长，无可核锚。',['核对_P525_F5c.png'])
rev('P527','物性梯度请求不属于本轮读图补容量范围。')
rev('P548','冻结预测无figure_requests，无待读图。')
filter_points('P564','F5d','EB',['2'],'首次切换倍率的密集大标记重叠，读取窗口同时覆盖不同早期点；不用于同点配对。')
rev('P564','原请求Fig5c为电压曲线，M0252对应Fig5d循环图。Figure5d的100圈883锚通过；对照100圈已终止，不能补值。EB第2圈混叠点已从供汇总points移除，保留程序原值审计；第5圈共同点可用。Figure5e初始锚被早期大标记重叠干扰，锚未通过，整图不采用。',['核对_P564_F5d.png','核对_P564_F5e.png'])
rev('P591','已定位正文p11 Figure5原图。程序不能从浅色图例提取符合阈值的独立颜色，因此不输出数值，终态仅图未读；S15c硝酸锂用量不同，条件不符。')
