import { mkdir, writeFile } from 'node:fs/promises';
import { performance } from 'node:perf_hooks';
const base = (process.env.API_URL || 'http://localhost:8080').replace(/\/$/,'');
const key = process.env.NUBIXIA_API_KEY || 'nubixia-demo-local-2026';
const concurrency = Number(process.env.TEST_CONCURRENCY || 20);
if (!Number.isInteger(concurrency) || concurrency < 1 || concurrency > 20) throw new Error('TEST_CONCURRENCY debe estar entre 1 y 20');
const headers = {'Content-Type':'application/json','X-API-Key':key};
const report = { fecha: new Date().toISOString(), api: base, entorno: base.includes('localhost') ? 'local' : 'remoto', concurrencia: concurrency, resultados: [], comprobantes: [] };
const check = (nombre, ok, detalle) => { report.resultados.push({nombre, ok, detalle}); if(!ok) console.error('FALLO:', nombre, detalle); };
const sleep = ms => new Promise(r => setTimeout(r,ms));
async function request(path, options={}) {
 const r=await fetch(base+path,{...options,headers:options.headers || headers,signal:AbortSignal.timeout(30000)});
 return r;
}
const startNumber = Math.floor(Math.random()*90000000)+1000000;
const invoice = n => ({rucEmisor:'20123456789',cliente:'Cliente de prueba '+n,fecha:'2026-10-25',serie:'F999',numero:String(startNumber+n),
 items:[{descripcion:'Servicio de demostración',cantidad:2,precioUnitario:50}],subtotal:100,igv:18,total:118});
try {
 const unauth=await request('/comprobantes',{headers:{}});
 check('Acceso sin credencial rechazado',[401,403].includes(unauth.status),unauth.status);
 const invalid=await request('/comprobantes',{method:'POST',body:JSON.stringify({...invoice(90),total:1})});
 check('Total inconsistente rechazado',invalid.status===400,invalid.status);
 const results = new Array(20);
 let next = 0;
 await Promise.all(Array.from({length:concurrency},async()=>{
  while (next < 20) {
  const n = next++;
  const begin=performance.now(); const payload=invoice(n);
  const r=await request('/comprobantes',{method:'POST',body:JSON.stringify(payload)}); const data=await r.json();
  results[n] = {status:r.status,ms:Math.round(performance.now()-begin),data,payload};
  }
 }));
 check(`20 solicitudes recibidas (concurrencia ${concurrency})`,results.every(r=>r.status===202),results.map(r=>r.status));
 check('20 documentId únicos',new Set(results.map(r=>r.data.documentId)).size===20);
 check('Recepción menor a 2 segundos',results.every(r=>r.ms<2000),results.map(r=>r.ms));
 let docs=[];
 for(let attempt=0;attempt<40;attempt++) {
  const r=await request('/comprobantes');
  if(r.status===429) { await sleep(2000); continue; }
  if(!r.ok) throw new Error('Consulta de estados: '+r.status);
  const data=await r.json(); const ids=new Set(results.map(r=>r.data.documentId));
  docs=data.items.filter(d=>ids.has(d.documentId));
  if(docs.length===20 && docs.every(d=>['ACEPTADO','RECHAZADO'].includes(d.estado))) break;
  await sleep(1000);
 }
 check('20 comprobantes aceptados sin pérdida',docs.length===20 && docs.every(d=>d.estado==='ACEPTADO'),docs.map(d=>d.estado));
 check('Procesamiento menor a 15 segundos',docs.length===20 && docs.every(d=>d.estado==='ACEPTADO' && Date.parse(d.actualizadoEn)-Date.parse(d.creadoEn)<15000));
 report.comprobantes=docs.map(d=>({documentId:d.documentId,estado:d.estado,recepcionMs:results.find(r=>r.data.documentId===d.documentId)?.ms,procesoMs:Date.parse(d.actualizadoEn)-Date.parse(d.creadoEn),historial:d.historial}));
 await sleep(1000);
 const duplicate=await request('/comprobantes',{method:'POST',body:JSON.stringify(results[0].payload)});
 const duplicateData=await duplicate.json();
 check('Reenvío idempotente',duplicate.status===200 && duplicateData.duplicado===true && duplicateData.documentId===results[0].data.documentId);
 await sleep(600);
 const conflict=await request('/comprobantes',{method:'POST',body:JSON.stringify({...results[0].payload,cliente:'Otro cliente'})});
 check('Duplicado con datos distintos rechazado',conflict.status===409,conflict.status);
 for(const ext of ['xml','pdf']) {
  await sleep(600);
  let r=await request('/comprobantes/'+results[0].data.documentId+'/archivos/'+ext);
  if(r.headers.get('Content-Type')?.includes('application/json') && r.ok) { const data=await r.json(); r=await fetch(data.url); }
  const bytes=Buffer.from(await r.arrayBuffer());
  check('Descarga '+ext,r.status===200 && (ext==='pdf'?bytes.subarray(0,4).toString()==='%PDF':bytes.toString().includes('ComprobanteAcademico')),bytes.length+' bytes');
 }
} catch(e) { check('Ejecución completa',false,String(e)); }
await mkdir('evidencias',{recursive:true});
await writeFile('evidencias/ultima-prueba.json',JSON.stringify(report,null,2));
console.log(JSON.stringify(report.resultados,null,2));
console.log('Evidencia guardada en evidencias/ultima-prueba.json');
if(report.resultados.some(r=>!r.ok)) process.exitCode=1;
