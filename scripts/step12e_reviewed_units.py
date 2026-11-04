from pathlib import Path
import json
VERSION = "2026-11-02_verified_M_and_explicit_1to1_vv"
UNIT_KEYS = {("P062", k) for k in ("R25", "R25L", "R25S", "R50")} | {("P307", "R_ramanLi")}
def apply_review(out, comps, dens, convert, recipe_ratios, counts, solvent_ids):
    for rec in out:
        key=(rec["论文"],rec["配方"])
        if key not in UNIT_KEYS and key != ("P315","R_REF"):
            continue
        changes=[]
        for item in rec["组分"]:
            cid=item["组分"]
            if key in UNIT_KEYS and cid in ("LiTFSI","LiNO3") and item["原文单位"].startswith("m"):
                raw=item["原文用量"]
                value=float(raw)
                item.update({"单位类别":"摩尔浓度","数值":value,"采用单位":"mol/L","单位依据":"原始PDF小型大写M核实；非mol/kg假设","说明":"2026-11-02原始PDF核实为小型大写M，规范化mol/L；保留原提取符号"})
                changes.append({"组分":cid,"类别":"原文单位核实","原文单位":item["原文单位"],"采用单位":"mol/L","采用值":value,"来源": "P062正文第4页Electrolyte Preparation" if key[0]=="P062" else "P307正文第3页拉曼段PDF字形；SI第3页另有基础液1M"})
            if key == ("P315","R_REF") and cid in ("DME","DOL"):
                assert item["原文用量"] == "1", item
                item.update({"单位类别":"体积份","数值":1.0,"采用单位":"体积份","比例基准为假设":True,"说明":"2026-11-02用户批准：原文1:1仅缺基准，按体积比；原文写法保留"})
                changes.append({"组分":cid,"类别":"比例基准假设","原文用量":item["原文用量"],"原文单位":item["原文单位"],"采用单位":"体积份","采用值":1.0})
        assert changes, key
        # Same merging and conversion as step12d; remove stale derived fields before recalculating.
        merged={}
        for item in rec["组分"]:
            cid=item["组分"]
            if cid in merged and item["单位类别"]==merged[cid]["单位类别"] and item["数值"] is not None and merged[cid]["数值"] is not None:
                merged[cid]["数值"]+=item["数值"]
            else:
                merged.setdefault(cid,dict(item))
        for field in ("体积分数","每升溶剂物质的量_mol","摩尔分数","缺","前提","状态","元素比例"):
            rec.pop(field,None)
        rec.update(convert(list(merged.values()),dens,solvent_ids))
        rec["核实与假设"]={"版本":VERSION,"改动":changes,"含比例假设":key==("P315","R_REF")}
        rec["前提"].append("原提取m经PDF字形核实为M，按mol/L" if key in UNIT_KEYS else "DME:DOL原文1:1，体积基准为用户批准假设")
        rec["元素比例"]=recipe_ratios(rec,comps,counts)
        if key == ("P307","R_ramanLi"):
            rec["核实与假设"]["剩余问题"]="DOL/DME溶剂身份冲突与比例缺失，未补1:1"

def add_review_sheet(file, out):
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Font
    wb=load_workbook(file)
    if "11-02核实与假设" in wb:
        del wb["11-02核实与假设"]
    ws=wb.create_sheet("11-02核实与假设")
    ws.append(["论文","配方","组分","处理类别","原文用量","原文单位","采用值","采用单位","依据","元素比例状态","仍缺什么"])
    for rec in out:
        for change in rec.get("核实与假设",{}).get("改动",[]):
            item=next(i for i in rec["组分"] if i["组分"]==change["组分"])
            ws.append([rec["论文"],rec["配方"],item["组分"],change["类别"],item["原文用量"],item["原文单位"],item["数值"],item["采用单位"],item["说明"],rec["元素比例"]["状态"],rec["元素比例"]["原因"]])
    for cell in ws[1]: cell.font=Font(bold=True)
    for row in ws:
        for cell in row: cell.alignment=Alignment(wrap_text=True,vertical="top")
    for col in "ABCDEFGHIJK":ws.column_dimensions[col].width=20 if col not in "IJK" else 45
    ws.freeze_panes="C2"
    wb["说明"].append(["2026-11-02限定修订：P062四配方、P307拉曼液原文小型大写M核实为mol/L；P315 R_REF原文1:1按用户批准假设为v/v。原文用量/单位保留，详见11-02核实与假设页。其他真正不明的m、完全未报告的溶剂比例不补。"])
    wb.save(file)
