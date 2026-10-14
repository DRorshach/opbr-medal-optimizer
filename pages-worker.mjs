// Same Python scoring engine, isolated from the UI in a Web Worker.
import {loadPyodide} from 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs';
let runtime;
async function initialize(){
 const py=await loadPyodide();
 py.FS.mkdirTree('/app/opbr');py.FS.mkdirTree('/app/data');
 for(const [url,path] of [['engine.py','/app/opbr/engine.py'],['storage-browser.py','/app/opbr/storage.py'],['data/tables.json','/app/data/tables.json'],['data/image_sources.json','/app/data/image_sources.json']]){
  const r=await fetch(new URL(url,import.meta.url),{cache:'no-cache'});if(!r.ok)throw Error('Falha ao carregar '+url);
  py.FS.writeFile(path,new Uint8Array(await r.arrayBuffer()));
 }
 py.FS.writeFile('/app/opbr/__init__.py','');
 py.runPython("import sys; sys.path.insert(0, '/app')\nimport json\nfrom opbr.engine import Catalog, evaluate, optimize\ncat=Catalog()");
 return py;
}
let queue=Promise.resolve();
self.onmessage=({data:m})=>{queue=queue.then(async()=>{
 try{
  const py=await (runtime??=initialize());
  py.globals.set('request_json',JSON.stringify(m.payload));
  py.globals.set('report_progress',p=>self.postMessage({id:m.id,progress:JSON.parse(p)}));
  let code;
  if(m.action==='evaluate')code="r=json.loads(request_json)\njson.dumps(evaluate(cat,r['ids'],r.get('config',{}),r.get('traits')))";
  else if(m.action==='optimize'){
   await py.loadPackage('numpy');
   code="r=json.loads(request_json)\njson.dumps(optimize(cat,r['config'],r['owned'],lambda p:report_progress(json.dumps(p))))";
  }else throw Error('Operação desconhecida');
  self.postMessage({id:m.id,result:JSON.parse(py.runPython(code))});
 }catch(e){self.postMessage({id:m.id,error:String(e.message||e)});}
 });};
