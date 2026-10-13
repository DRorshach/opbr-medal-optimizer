'use strict';
const showCharacterTraits=characterDetail;
let characterRequest=0,characterBuildSlots=3;
characterDetail=async function(id){
 const request=++characterRequest;
 const previous=$('#character-recommendations');
 if(previous)previous.innerHTML='<div class="panel">Carregando sugestões…</div>';
 await showCharacterTraits(id);
 if(request!==characterRequest||page!=='characters')return;
 let section=$('#character-recommendations');
 if(!section){section=document.createElement('section');section.id='character-recommendations';$('.two-col',main).before(section);}
 section.innerHTML='<div class="panel">Carregando sugestões salvas…</div>';
 try{
  const build=await api(`character-builds?id=${id}&slots=${characterBuildSlots}`);
  if(request!==characterRequest||page!=='characters')return;
  const p=build.profile;
  section.innerHTML=`<section class="panel" style="margin-bottom:22px"><div class="eyebrow">TRÊS SUGESTÕES · SALVAS POR PERSONAGEM</div><div class="section-head"><div><h2>${esc(p.name)} · ${esc(p.nickname)}</h2><p class="muted">${esc(p.confidence)}</p></div><label>Nível da build<select id="character-build-level">${option(2,'80 · duas medalhas',characterBuildSlots)+option(3,'100 · três medalhas',characterBuildSlots)}</select></label></div><p>Perfil da classe ajustado por regras reconhecidas nos traits. Não é necessário configurar prioridades para usar estas sugestões.</p><div class="notice">Sugestões calculadas, não builds oficialmente validadas. ${p.traits_matched} de ${p.traits_read} descrições participaram das regras; as demais mecânicas não foram simuladas.</div>${p.stat_advice.map(x=>`<div class="effect"><strong>Traits adicionais</strong><p>${esc(x)}</p></div>`).join('')}<details><summary>Por que este perfil foi escolhido?</summary>${p.reasons.map(r=>`<div class="effect"><p>${esc(r.reason)}</p>${r.evidence.map(e=>`<small>Ability ${e.ability_id}: ${esc(e.text)}</small><br>`).join('')}</div>`).join('')||'<p>Sem regra específica reconhecida. Usa apenas a classe; precisa de revisão.</p>'}<h3>Limitações</h3><ul>${p.limitations.map(x=>`<li>${esc(x)}</li>`).join('')}</ul><details><summary>Traits não utilizados e parâmetros</summary><pre>${esc(JSON.stringify({unmodeled:p.unmodeled,config:p.config,source:p.source},null,2))}</pre></details></details><p class="original-note">${build.generated_at?`Gerado em ${esc(build.generated_at)} · ${fmt(build.evaluated)} combinações por perfil · ${esc(build.version)}`:'Ainda não calculado.'}</p><button id="rebuild-characters">Recalcular todos os personagens</button><div id="character-build-progress"></div></section>${build.status==='stale'?'<div class="notice">Catálogo ou regras alterados. Recalcule as sugestões.</div>':''}<div class="character-build-cards">${build.status==='ready'?build.sets.map((r,i)=>resultCard(r,i)).join(''):'<div class="empty">Sugestões pendentes. Use Recalcular.</div>'}</div>`;
  $('#character-build-level').onchange=()=>{characterBuildSlots=+$('#character-build-level').value;characterDetail(id);};
  const switchCharacter=document.createElement('button');
  switchCharacter.textContent='Trocar personagem';
  switchCharacter.onclick=()=>{$('#char-search').scrollIntoView({block:'center'});$('#char-search').focus();};
  $('.section-head',section).append(switchCharacter);
  $('#rebuild-characters').hidden=true;$('#rebuild-characters').onclick=async()=>{
   try{const task=await api('character-builds/regenerate',{});$('#rebuild-characters').disabled=true;
    const poll=async()=>{try{const j=await api('job?id='+task.id);const status=$('#character-build-progress');if(status)status.textContent=j.status==='running'?`Calculando ${j.slots||2} slots · ${fmt(j.evaluated||0)} conjuntos…`:j.error||'Atualizado.';if(j.status==='running')setTimeout(poll,1500);else if(page==='characters')characterDetail(id);}catch(e){toast(e.message);}};poll();
   }catch(e){toast(e.message);}
  };
  $$('.character-build-cards .result',section).forEach((el,i)=>{
   const r=build.sets[i];
   $('[data-load-set]',el).onclick=()=>{slots=[...r.ids];if(slots.length===2)slots.push(null);traits={};state.settings={...settings(),...r.config,slots:r.ids.length};persist();location.hash='calculator';};
   $('[data-save-set]',el).onclick=async()=>{state.saved_sets.push({name:`${p.name} — ${p.nickname} · sugestão ${i+1}`,ids:r.ids,traits:{},config:r.config,character_id:id});await persist();toast('Conjunto salvo com o perfil do personagem.');};
   $('[data-compare-set]',el).remove();
  });
 }catch(e){if(request===characterRequest)section.innerHTML=`<div class="notice">${esc(e.message)}</div>`;}
};
