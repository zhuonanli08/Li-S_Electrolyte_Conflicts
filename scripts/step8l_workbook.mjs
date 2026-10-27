import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
process.on('uncaughtException',err=>{console.error(err.message);process.exitCode=1;});

const root=path.resolve(import.meta.dirname,'..');
const base=path.join(root,'output/GPT_v4_调试集53篇_2026-10-24');
const output=path.join(root,'outputs/01a16d15-0bb5-7b62-b8ff-6f148a512cfd');
const data=JSON.parse(await fs.readFile(path.join(base,'delivery_tables.json'),'utf8'));
const wb=Workbook.create();
if(process.argv.includes('--probe')){
 const p=wb.worksheets.add('试验');p.getRange('A1:B3').values=[['文献','值'],['S05',12],['P001',3]];
 wb.recalculate();await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(base,'export_probe.xlsx'));
 console.log('minimal export passed');process.exit(0);
}
if(process.argv.includes('--export-help')){console.log(wb.help('SpreadsheetFile.exportXlsx',{include:'index,notes,examples',maxChars:4000}).ndjson);process.exit(0);}
if(process.argv.includes('--probe-data')){
 const only=process.argv.find(a=>a.startsWith('--only='))?.slice(7);
 for(const [key,rows] of Object.entries(data.tables)){
  if(only&&key!==only)continue;
  const p=wb.worksheets.add(key);const h=data.headers[key];
  const matrix=[h,...rows].map(row=>row.map(v=>typeof v==='object'&&v!==null?JSON.stringify(v):v));
  p.getRangeByIndexes(0,0,matrix.length,h.length).values=matrix;
 }
 wb.recalculate();await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(base,'export_probe_'+(only||'data')+'.xlsx'));console.log('data export passed '+only);process.exit(0);
}
wb.worksheets.add('评分');
const defs=[
 ['①一句话结论','conclusions',[10,65,65,180,115,27,40]],
 ['②要你看','questions',[10,15,34,18,70,75,32,100,35]],
 ['③测试','tests',[10,20,36,26,27,26,23,27,35,40,24,35,25,45,50,22,32,100]],
 ['④表现','results',[10,20,27,27,24,24,25,25,22,33,18,14,25,40,55,22,32,100,65]],
 ['⑤机制','mechanisms',[10,23,85,24,24,33,36,33,45,22,22,32,110]],
 ['⑥配方','formulations',[10,25,38,70,38,34,30,25,35,32,100]],
 ['⑦性质梯度','properties',[10,14,40,85,75,45,50,32,100]],
 ['⑧读图补充','figure_values',[10,18,22,25,25,15,25,25,18,18,22,20,95,65]],
 ['图读取记录','figures',[10,22,25,15,45,25,25,40,65,35,75,110]],
 ['评分明细','scores',[10,18,36,22,90,80,32,100]],
 ['程序核对记录','checks',[10,40,34,130]]
];
for (const [name] of defs)wb.worksheets.add(name);
wb.worksheets.add('说明');
const col=n=>{let s='';while(n){n--;s=String.fromCharCode(65+n%26)+s;n=Math.floor(n/26);}return s;};
function clean(v){
 if(v==null)return null;if(typeof v==='object')v=JSON.stringify(v);
 if(typeof v==='string'){
  // PDF text caches contain NUL/backspace artifacts which corrupt XLSX XML.
  v=v.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g,ch=>'[U+'+ch.charCodeAt(0).toString(16).toUpperCase().padStart(4,'0')+']');
  if(v.startsWith('='))v="'"+v;
 }
 return v;
}
function lines(value,width){return String(value??'').split('\n').reduce((n,s)=>n+Math.max(1,Math.ceil([...s].reduce((m,c)=>m+(c.charCodeAt(0)>255?2:1),0)/(width*.9))),0);}
function splitCell(value,width,maxLines=25){
 if(typeof value!=='string'||lines(value,width)<=maxLines)return [value];
 const units=[];for(const line of value.split('\n')){
  let part='',w=0;for(const ch of line){let cw=ch.charCodeAt(0)>255?2:1;if(w+cw>width*.9){units.push(part);part='';w=0;}part+=ch;w+=cw;}units.push(part);
 }
 const out=[];for(let i=0;i<units.length;i+=maxLines)out.push(units.slice(i,i+maxLines).join('\n'));return out;
}
const layouts=[];
for(const [name,key,widths] of defs){
 const sh=wb.worksheets.getItem(name),header=data.headers[key];
 const start=5;
 let raw=data.tables[key],expanded=[];
 for(const row of raw){
  const parts=row.map((v,c)=>splitCell(clean(v),widths[c]));const n=Math.max(...parts.map(x=>x.length));
  // Continuations preserve every character while avoiding Excel's row-height limit.
  for(let i=0;i<n;i++)expanded.push(parts.map((p,c)=>p[i]??(c===0?row[0]+'（续）':null)));
 }
 if(!expanded.length)expanded=[[key==='questions'?'本轮尚无已确认条目':'暂无记录',...Array(header.length-1).fill(null)]];
 const end=start+expanded.length;
 sh.showGridLines=false;
 const used=sh.getRange(`A1:${col(header.length)}${end}`);
 used.format.font={name:'Arial',size:10,color:'#243247'};used.format.verticalAlignment='top';used.format.wrapText=true;
 sh.getRange('A2').values=[[key==='conclusions'?'GPT 调试集提取与评分':name.replace(/^.[①②③④⑤⑥⑦]/,'')]];
 sh.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:'#20364D'};
 // Title is an overflowing plain cell, deliberately unmerged.
 sh.getRange('A2').format.wrapText=false;
 sh.getRange('A3').values=[[key==='conclusions'?`独立提取 ${data.counts.papers}/53 篇；AI交叉核对 ${data.metrics.reviewed_papers}/53 篇。文本评分已完成；读图补充另列。`:'首次预测保留；AI辅助复核，用户尚未逐项人工确认。过长原句使用续行，仍属同一单位。']];
 sh.getRange('A3').format.wrapText=false;sh.getRange('A3').format.font.color='#785723';
 sh.getRange(`A${start}:${col(header.length)}${start}`).values=[header];
 sh.getRange(`A${start+1}:${col(header.length)}${end}`).values=expanded;
 for(let c=0;c<widths.length;c++)sh.getRange(`${col(c+1)}1:${col(c+1)}${end}`).format.columnWidth=widths[c];
 const hr=sh.getRange(`A${start}:${col(header.length)}${start}`);hr.format={fill:'#294B68',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,horizontalAlignment:'center',verticalAlignment:'center',rowHeight:32};
 for(let i=0;i<expanded.length;i++){
  const height=Math.min(390,Math.max(26,Math.max(...expanded[i].map((v,c)=>lines(v,widths[c])))*14+8));
  sh.getRange(`A${start+i+1}:${col(header.length)}${start+i+1}`).format.rowHeight=height;
 }
 if(!process.argv.includes('--simple'))sh.tables.add(`A${start}:${col(header.length)}${end}`,true,'Data_'+key);
 sh.freezePanes.freezeRows(start);sh.freezePanes.freezeColumns(1);
 if(key==='conclusions')sh.tabColor='#20364D';
 if(key==='questions')sh.tabColor='#B58337';
 const statusCol={questions:4,tests:16,results:16,mechanisms:11,scores:4}[key];
 if(statusCol&&!process.argv.includes('--simple')){const r=sh.getRange(`${col(statusCol)}${start+1}:${col(statusCol)}${end}`);r.conditionalFormats.add('containsText',{text:'FP',format:{fill:'#FBE5E5',font:{color:'#A12626',bold:true}}});r.conditionalFormats.add('containsText',{text:'FN',format:{fill:'#FFF0CC',font:{color:'#885C12',bold:true}}});}
 if(key==='questions')sh.getRange(`I${start+1}:I${end}`).format.fill='#FFF5CD';
 layouts.push({name,key,start,end,rows:raw.length,render:`A1:${col(Math.min(header.length,5))}${Math.min(end,start+2)}`});
}
// This input ledger supplies each numerator/denominator; it is not a mechanical audit sheet.
const score=wb.worksheets.getItem('评分');const last=layouts.find(x=>x.key==='scores').end;
score.showGridLines=false;score.tabColor='#20364D';
score.getRange('A1:G13').format={font:{name:'Arial',size:10,color:'#243247'},verticalAlignment:'center',rowHeight:30};
[22,12,12,12,16,16,36].forEach((w,i)=>score.getRange(`${col(i+1)}1:${col(i+1)}13`).format.columnWidth=w);
score.getRange('A2').values=[[data.metrics.all_53_text_reviews_complete?'GPT 53篇调试集文本评分':'GPT 调试集阶段评分']];score.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:'#20364D'};
score.getRange('A3').values=[[`独立提取 ${data.counts.papers}/53 篇；交叉核对 ${data.metrics.reviewed_papers}/53 篇；图请求已处理 ${data.figure_summary?.completed??0}/${data.figure_summary?.requested??0}。`]];
score.getRange('A5:G5').values=[['范围/类别','TP','FP','FN','精确率','召回率','说明']];
score.getRange('A5:G5').format={fill:'#E8EDF2',font:{name:'Arial',size:10,bold:true,color:'#20364D'},rowHeight:27};
const cats=['测试及条件','方向','机制'];
for(let i=0;i<3;i++){
 const row=i+6;score.getRange(`A${row}`).values=[[cats[i]]];
 for(let j=0;j<3;j++)score.getRange(`${col(j+2)}${row}`).formulas=[[`=COUNTIFS('评分明细'!$B$6:$B$${last},$A${row},'评分明细'!$D$6:$D$${last},${col(j+2)}$5)`]];
 score.getRange(`E${row}:F${row}`).formulas=[[`=IF(B${row}+C${row}=0,"不可计算",B${row}/(B${row}+C${row}))`,`=IF(B${row}+D${row}=0,"不可计算",B${row}/(B${row}+D${row}))`]];
 score.getRange(`G${row}`).values=[['仅已复核 '+data.metrics.reviewed_papers+' 篇']];
}
score.getRange('A9').values=[['微平均']];
score.getRange('B9:D9').formulas=[['=SUM(B6:B8)','=SUM(C6:C8)','=SUM(D6:D8)']];
score.getRange('E9:F9').formulas=[['=IF(B9+C9=0,"不可计算",B9/(B9+C9))','=IF(B9+D9=0,"不可计算",B9/(B9+D9))']];
score.getRange('E6:F9').setNumberFormat('0.00%');
score.getRange('A11').values=[['精确率=TP/(TP+FP)；召回率=TP/(TP+FN)。参考由AI复核，未经人工gold验收；未复核篇不进入上表。']];score.getRange('A11').format.wrapText=false;
score.getRange('A12').values=[['冻结预测保留；①采用程序修正并注明读图补充，初轮评分不变；错漏见②。同条件/同圈才比较。']];score.getRange('A12').format.wrapText=false;
const info=wb.worksheets.getItem('说明');info.showGridLines=false;
info.getRange('A1:B10').values=[
 ['项目','口径'],['版本','v4；机制按2026-10-25新增因果说法口径'],['提取方式','当前对话GPT及用户授权子代理。无外部付费API；不是固定API模型快照。'],
 ['预测冻结','首次独立预测保存后按SHA256冻结；未用旧参考生成首次预测。修正建议另存。'],
 ['评分范围',`${data.metrics.reviewed_papers}/53 篇交叉复核；首次文本预测+初轮数值程序，暂定调试指标，非独立测试集准确率。程序修正见④末列，读图另列，不回改初轮分。`],
 ['机制单位','按因果说法去重；同义句、引用位置与数量不扣分；仅标签问题记修正。'],
 ['方向','同一测试条件才判；精确值差异小于5%记差异小；CE记百分点差不套阈值。近似/界限未被当前解析器支持时保留不判。'],
 ['图','图读取状态单列；只有代码读值、坐标校准和同测试文字锚点核对通过才使用。未完成的图不虚构数值。'],
 ['缺SI','S53、P212、P296、P432本地无SI。P014/P039后判不合格但保留调试。'],
 ['使用','②黄列供人工填写，本次保持空白。原始人工gold与其他模型结果未覆盖。PDF缓存里的非法控制字符在Excel展示为[U+编码]，原始索引与冻结预测保留。']
];info.getRange('A1:B10').format={font:{name:'Arial',size:10,color:'#243247'},wrapText:true,verticalAlignment:'top',rowHeight:44};info.getRange('A1:A10').format.columnWidth=22;info.getRange('B1:B10').format.columnWidth=135;info.getRange('A1:B1').format={fill:'#294B68',font:{bold:true,color:'#FFFFFF'},rowHeight:28};
await fs.mkdir(output,{recursive:true});await fs.mkdir(path.join(base,'previews'),{recursive:true});
wb.recalculate();
const target=path.join(output,'GPT_调试集53篇_提取与评分.xlsx');
await (await SpreadsheetFile.exportXlsx(wb)).save(target);
console.log((await wb.inspect({kind:'table',range:'评分!A5:G9',include:'values,formulas',tableMaxRows:6,tableMaxCols:7,maxChars:2600})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},maxChars:1500})).ndjson);
await fs.writeFile(path.join(base,'workbook_manifest.json'),JSON.stringify({path:target,layouts,extracted:data.counts.papers,reviewed:data.metrics.reviewed_papers,complete:data.metrics.all_53_text_reviews_complete},null,2));
console.log(JSON.stringify({saved:target,sheets:defs.length+2,extracted:data.counts.papers,reviewed:data.metrics.reviewed_papers}));
// Render bounded copies of the saved view values and the identical authored sizing.
// The full multi-thousand-row workbook renderer failed in this runtime's WASM engine.
for(const layout of [{name:'评分',render:'A1:G13'},...layouts,{name:'说明',render:'A1:B10'}]){
 const renderOnly=process.argv.find(a=>a.startsWith('--render-only='))?.slice(14).split(',');
 if(renderOnly&&!renderOnly.includes(layout.name))continue;
 const pwb=Workbook.create();const ps=pwb.worksheets.add(layout.name);const source=wb.worksheets.getItem(layout.name);
 const cells=source.getRange(layout.render).values;const nr=cells.length,nc=cells[0].length;
 ps.getRange(layout.render).values=cells;
 ps.showGridLines=false;ps.getRange(layout.render).format={font:{name:'Arial',size:10,color:'#243247'},wrapText:true,verticalAlignment:'top'};
 const widths=layout.name==='评分'?[22,12,12,12,16,16,36]:layout.name==='说明'?[22,135]:defs.find(x=>x[0]===layout.name)[2];
 for(let c=0;c<nc;c++)ps.getRange(`${col(c+1)}1:${col(c+1)}${nr}`).format.columnWidth=widths[c];
 for(let r=0;r<nr;r++){
  const h=source.getRange(`A${r+1}`).format.rowHeight;
  ps.getRange(`A${r+1}:${col(nc)}${r+1}`).format.rowHeight=typeof h==='number'&&Number.isFinite(h)?h:20;
 }
 const hr=layout.name==='说明'?1:5;ps.getRange(`A${hr}:${col(nc)}${hr}`).format={fill:'#294B68',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true};
 if(layout.name==='评分'){ps.getRange('E6:F9').setNumberFormat('0.00%');ps.getRange('A2:A3').format.wrapText=false;ps.getRange('A11:A12').format.wrapText=false;}
 else if(layout.name!=='说明'){ps.getRange('A2:A3').format.wrapText=false;}
 ps.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:'#20364D'};
 pwb.recalculate();
 try {const blob=await pwb.render({sheetName:layout.name,range:layout.render,scale:1,format:'png'});await fs.writeFile(path.join(base,'previews',layout.name+'.png'),new Uint8Array(await blob.arrayBuffer()));console.log('rendered '+layout.name);}
 catch(err){console.log('render_failed '+layout.name+': '+String(err));break;}
}
