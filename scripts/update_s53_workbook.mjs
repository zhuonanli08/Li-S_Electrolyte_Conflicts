import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
process.on('uncaughtException',e=>{console.error(e.message);process.exit(1)});
const file='output/第一阶段_证据表.xlsx';
const dir='output/第一阶段_证据表';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(file));
console.log((await wb.inspect({kind:'sheet',include:'id,name',maxChars:1500})).ndjson);
const preview=async(name,range,suffix)=>{
  const p=await wb.render({sheetName:name,range,scale:1,format:'png'});
  await fs.writeFile(`${dir}/s53_${suffix}.png`,new Uint8Array(await p.arrayBuffer()));
};
await preview('主表','A309:D313','before');
const data=JSON.parse(await fs.readFile(`${dir}/s53_workbook_update.json`,'utf8'));
for(const [name,matrix] of Object.entries(data)){
  const sh=wb.worksheets.getItem(name);
  const old=sh.getUsedRange().values;
  if(name==='主表'){
    for(let r=1;r<old.length;r++) for(let c=0;c<old[r].length;c++){
      if(String(matrix[0][c]).includes('复核 ✍')){matrix[r][c]=old[r][c];continue;}
      if((old[r][c]??'')!==(matrix[r][c]??''))throw Error(`Unexpected existing row change ${r+1},${c+1}`);
    }
    for(let r=old.length;r<matrix.length;r++)sh.getRangeByIndexes(r,0,1,matrix[0].length).copyFrom(sh.getRangeByIndexes(old.length-1,0,1,matrix[0].length),'all');
  }
  // Preserve existing human review cells on derived tables whose stable keys remain aligned.
  for(let c=0;c<matrix[0].length;c++) if(String(matrix[0][c]).includes('复核')){
    for(let r=1;r<Math.min(old.length,matrix.length);r++)if(old[r][0]===matrix[r][0]&&old[r][c])matrix[r][c]=old[r][c];
  }
  sh.getUsedRange().clear({applyTo:'contents'});
  sh.getRangeByIndexes(0,0,matrix.length,matrix[0].length).values=matrix;
  if(name==='主表'){
    const col=matrix[0].indexOf('F2 核验标记');
    sh.getRangeByIndexes(old.length,col,matrix.length-old.length,1).format.fill='#FFF2CC';
  }
  console.log(name,matrix.length-1,'rows');
}
wb.recalculate();
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1500})).ndjson);
await preview('主表','A314:D318','after');
await preview('汇总','A1:D12','summary');
await preview('优势一致性','A190:D193','consistency');
await preview('新旧对照','A720:C724','diff');
await (await SpreadsheetFile.exportXlsx(wb)).save(file);
console.log('Saved',file);
