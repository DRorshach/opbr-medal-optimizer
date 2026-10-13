'use strict';
// Visitor state never leaves this browser. Public catalog files are read-only.
window.pagesAPI=(()=>{
 const base=new URL('.',document.currentScript.src),key='opbr-medal-optimizer-v1';
 let worker=null,seq=0;const pending=new Map(),jobs=new Map();
 const empty=()=>({owned:[],favorites:[],saved_sets:[],settings:{}});
 function read(){try{return {...empty(),...JSON.parse(localStorage.getItem(key)||'{}')};}catch{return empty();}}
 async function json(path){const r=await fetch(new URL(path,base),{cache:'no-cache'});if(!r.ok)throw Error('Não foi possível carregar o catálogo. Recarregue a página.');return r.json();}
 function paths(x){if(Array.isArray(x))return x.map(paths);if(x&&typeof x==='object'){for(const k in x)x[k]=paths(x[k]);return x;}return typeof x==='string'&&x.startsWith('/images/')?new URL(x.slice(1),base).href:x;}
 function reset(){worker?.terminate();worker=null;for(const p of pending.values())p.reject(Error('Cálculo cancelado.'));pending.clear();}
 function calculate(action,payload,progress){
  if(!worker){worker=new Worker(new URL('pages-worker.mjs',base),{type:'module'});
   worker.onmessage=({data:m})=>{const p=pending.get(m.id);if(!p)return;if(m.progress){p.progress?.(m.progress);return;}pending.delete(m.id);if(m.error)p.reject(Error(m.error));else p.resolve(paths(m.result));};
   worker.onerror=()=>reset();
  }
  return new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject,progress});worker.postMessage({id,action,payload});});
 }
 return async function(path,payload){
  const [route,query]=path.split('?'),q=new URLSearchParams(query);
  if(route==='bootstrap'){const d=paths(await json('data/bootstrap.json'));d.state=read();return d;}
  if(route==='state'){localStorage.setItem(key,JSON.stringify(payload));return {ok:true};}
  if(route==='export')return {schema:1,state:read()};
  if(route==='medal'||route==='character')return paths(await json(`data/${route}/${Number(q.get('id'))}.json`));
  if(route==='character-builds')return paths(await json(`data/${q.get('pool')==='normal'?'builds-normal':'builds'}/${Number(q.get('id'))}-${Number(q.get('slots')||3)}.json`));
  if(route==='changes')return [];
  if(route==='evaluate')return calculate('evaluate',payload);
  if(route==='optimize'){
   if([...jobs.values()].some(j=>j.status==='running'))throw Error('Aguarde ou cancele a busca atual.');
   const id=String(++seq),j={status:'running',progress:0,evaluated:0};jobs.set(id,j);
   calculate('optimize',{config:payload,owned:read().owned},p=>Object.assign(j,p)).then(r=>Object.assign(j,{status:'done',result:r})).catch(e=>{if(j.status!=='cancelled')Object.assign(j,{status:'error',error:e.message});});
   return {id};
  }
  if(route==='job'){const j=jobs.get(q.get('id'));if(!j)throw Error('Busca não encontrada.');return {...j};}
  if(route==='cancel'){const j=jobs.get(payload.id);if(j?.status==='running'){j.status='cancelled';reset();}return {ok:true};}
  throw Error('O catálogo público é atualizado pelo responsável do projeto.');
 };
})();
