"""Deterministic, exhaustive ranking under an explicitly heuristic utility model.

No damage formula is inferred. Raw effects remain authoritative; scoring is a
weighted estimate with user-selected activation factors and table-based ceilings.
"""
import json, math, re, heapq, time
from collections import Counter, defaultdict
from .storage import ROOT, load_tables

MODEL='utility-v2'
DIMENSIONS={'attack':'Dano causado','defense':'Redução de dano','survival':'Recuperação de HP','hp':'HP máximo','dodge':'Recarga de esquiva','capture':'Captura de tesouro','speed':'Velocidade de movimento','attack_stat':'Atributo ATK','defense_stat':'Atributo DEF','skill1':'Skill 1','skill2':'Skill 2','critical':'Crítico'}
PRESETS={
 'equilibrada':dict(attack=1,defense=1,survival=1,hp=1,dodge=1,capture=1,speed=1,attack_stat=1,defense_stat=1,skill1=1,skill2=1,critical=0),
 'runner':dict(attack=.3,defense=1,survival=1.2,hp=1.2,dodge=1.2,capture=2,speed=2,attack_stat=.3,defense_stat=1,skill1=.7,skill2=.7,critical=0),
 # Generic attacker does not assume character-specific critical synergy.
 # Critical percentages cannot be interpreted as equivalent damage percentages.
 'attacker':dict(attack=2,defense=.5,survival=.6,hp=.6,dodge=.6,capture=.2,speed=.2,attack_stat=2,defense_stat=.5,skill1=1,skill2=1,critical=0),
 'defender':dict(attack=.4,defense=2,survival=1.5,hp=1.5,dodge=1.5,capture=.3,speed=.3,attack_stat=.4,defense_stat=2,skill1=.7,skill2=.7,critical=0),
 'skill1':dict(skill1=3),'skill2':dict(skill2=3),'skills':dict(skill1=2,skill2=2),
 'dano':dict(attack=3),'reducao':dict(defense=3),'hp':dict(survival=3,hp=3),
 'captura':dict(capture=3),'tesouro':dict(defense=2,survival=1,hp=1,dodge=1,capture=.5),
 'critico':dict(critical=3),'agressiva':dict(attack=2,skill1=1,skill2=1,critical=0),
 'sobrevivencia':dict(defense=2,survival=2,hp=2,dodge=2),'personalizada':dict(attack=1,defense=1,survival=1,hp=1,dodge=1,capture=1,speed=1,attack_stat=1,defense_stat=1,skill1=1,skill2=1,critical=0)}
PRESETS.update(cura=dict(survival=3),esquiva=dict(dodge=3),movimento=dict(speed=3))
# Each mapping is checked against the English description and serialized value.
RULES={
 1:('skill1','Reduce the cooldown time of Skill 1 by',1,'event'),
 2:('skill2','Reduce the cooldown time of Skill 2 by',1,'event'),
 4:('attack','Increase damage dealt by',1,'conditional'),
 5:('defense','Reduce damage received by',-1,'conditional'),
 6:('skill1','Boost the cooldown reduction speed of Skill 1 by',1,'conditional'),
 7:('skill2','Boost the cooldown reduction speed of Skill 2 by',1,'conditional'),
 8:('dodge','Boost the cooldown reduction speed of dodge by',1,'conditional'),
 9:('survival','Recover HP by',1,'event'),
 10:('capture','Boost capture speed by',1,'conditional'),
 200:('hp','Increase HP by',1,'conditional'),
 201:('attack_stat','Increase ATK by',1,'conditional'),
 202:('defense_stat','Increase DEF by',1,'conditional'),
 203:('critical','Increase CRIT by',1,'conditional'),
 204:('speed','Increase SPD by',1,'conditional'),
 679:('attack','Increase Normal Attack damage dealt by',1,'conditional')}

def condition_key(a):
    return json.dumps({k:v for k,v in a.items() if k.startswith('cond') and k!='cond_prob'},sort_keys=True,separators=(',',':'))

def normalize(a, aid, source, limits, channel='affect'):
    typ=a.get(channel+'_type',0);text=a.get('detail','');param=a.get(channel+'_param1')
    e={'ability_id':aid,'type':typ,'description':text,'source':source,'condition':condition_key(a),'probability':a.get('cond_prob',100)/100,'raw':a,'channel':channel,'supported':False,'dimension':None,'value':None,'cap':None,'unit':'unknown','key':str(typ),'kind':'unknown'}
    if not 0<=e['probability']<=1:e['probability']=0
    if typ in RULES:
        dim,phrase,sign,kind=RULES[typ]
        match=re.search(re.escape(phrase)+r'\s*([\d.]+)%',text,re.I)
        if match and isinstance(param,(float,int)):
            val=float(match[1]);raw=(param-1)*100*sign
            if math.isclose(val,raw,abs_tol=.02) and val>=0:
                e.update(supported=True,dimension=dim,value=val,unit='percent',kind=kind)
                lim=limits.get(typ,{}).get('affect_limit')
                if isinstance(lim,(int,float)) and lim!=0:e['cap']=abs(lim)
    elif typ==601:
        match=re.search(r'(CRIT|SPD|ATK|DEF): Boosted by ([\d.]+)% for ([\d.]+) second',text)
        if match and 'Cannot Stack' in text:
            dim={'CRIT':'critical','SPD':'speed','ATK':'attack_stat','DEF':'defense_stat'}[match[1]]
            e.update(supported=True,dimension=dim,value=float(match[2]),cap=float(match[2]),unit='percent',kind='temporary',duration=float(match[3]),key=f'601:{param}')
    if e['supported'] and e['kind']=='conditional' and a.get('cond_type',0)==0:
        # Absence alone is insufficient: only recognized affirmative descriptions.
        if text.startswith(RULES[typ][1]):e['kind']='permanent'
    return e

class Catalog:
    def __init__(self,path=None):
        self.tables,self.imports=load_tables() if path is None else load_tables(path)
        self.medals=self.tables['medal'];self.tags=self.tables['medal_tag'];self.abilities=self.tables['ability'];self.limits=self.tables['medal_ability_affect_limit']
        self.effects={aid:[normalize(a,aid,'ability',self.limits,ch) for a in row.get('affects',[]) for ch in ('affect','affect2') if a.get(ch+'_type')] for aid,row in self.abilities.items()}
        self.images=json.loads((ROOT/'data/image_sources.json').read_text()) if (ROOT/'data/image_sources.json').exists() else {}
        self.unique={mid:self.effects.get(m['ability_id'],[]) for mid,m in self.medals.items()}
        self.tag_effects={(tid,n):self.effects.get(t.get(f'set{n}_ability_id'),[]) for tid,t in self.tags.items() for n in (2,3)}
        # User preference: one logical medal, prefer the colored RANKING variant.
        # Equivalence is established by original_id + identical unique ability/tags.
        families=defaultdict(list)
        for m in self.medals.values():
            families[(m.get('original_id',m['medal_id']),m['ability_id'],tuple(sorted(m['tag_ids'])))].append(m)
        self.aliases={};self.variants={};self.visible_medals={}
        for members in families.values():
            preferred=min(members,key=lambda m:(0 if m.get('medal_type')==2 else 1 if 'original_id' not in m else 2,m['medal_id']))
            mid=preferred['medal_id'];self.visible_medals[mid]=preferred
            self.variants[mid]=[m['medal_id'] for m in members]
            for m in members:self.aliases[m['medal_id']]=mid

    def canonical_ids(self,ids):
        return list(dict.fromkeys(self.aliases.get(i,i) for i in ids))

    def kind(self,m):
        base=self.medals.get(m.get('original_id'),m)
        return {0:'normal',1:'evento',2:'ranking',3:'recompensa'}.get(base.get('medal_type',0),'desconhecido')

    def public_medal(self,m,details=False):
        icon=m.get('icon_name','');effects=self.unique[m['medal_id']]
        out={'id':m['medal_id'],'family':m.get('original_id',m['medal_id']),'name':m['name'],'type':self.kind(m),'appearance':'colorida' if m.get('medal_type')==2 else 'original de evento','raw_type':m.get('medal_type',0),'equivalent_ids':self.variants.get(m['medal_id'],[m['medal_id']]),'is_event':m.get('is_event',False),'tags':[{'id':t,'name':self.tags[t]['name']} for t in m['tag_ids'] if t in self.tags],'image':'/images/'+icon+'.png' if icon in self.images else None,'effects':effects,'source':m['_source'],'availability':'Não verificada','verification':'Extraído do cache local; versão não confirmada','supported':sum(e['supported'] for e in effects),'total_effects':len(effects)}
        if details:
            out['raw']=m;out['image_source']=self.images.get(icon);out['traits']={}
            for field in ('ability2_group_id','ability3_group_id','ability4_group_id'):
                group=self.tables['abilityTable'].get(m.get(field),{})
                out['traits'][field]=[{'id':x['ability_id'],'weight_raw':x.get('per'),'effects':self.effects.get(x['ability_id'],[])} for x in group.get('table_datas',[])]
        return out

    def filter(self,filters,owned=()):
        result=[];owned=set(self.canonical_ids(owned))
        for mid,m in self.visible_medals.items():
            kind=self.kind(m)
            if filters.get('type') and filters['type']!='all' and kind!=filters['type']:continue
            if filters.get('owned')=='yes' and mid not in owned:continue
            if filters.get('owned')=='no' and mid in owned:continue
            if filters.get('available'):continue # No time-bound availability evidence in this snapshot.
            if filters.get('tag') and int(filters['tag']) not in m['tag_ids']:continue
            q=filters.get('query','').casefold()
            if q and q not in m['name'].casefold() and q not in str(mid):continue
            if filters.get('effect') and not any(e['dimension']==filters['effect'] for e in self.unique[mid]):continue
            result.append(m)
        return sorted(result,key=lambda m:m['medal_id'])

def config(raw):
    out={'weights':{k:float(raw.get('weights',PRESETS.get(raw.get('preset','equilibrada'),PRESETS['equilibrada'])).get(k,0)) for k in DIMENSIONS},'activation':float(raw.get('activation',.5)),'event':float(raw.get('event',.25)),'conditions':{str(k):float(v) for k,v in raw.get('conditions',{}).items()}}
    if any(not math.isfinite(x) or not 0<=x<=10 for x in out['weights'].values()):raise ValueError('Pesos devem estar entre 0 e 10')
    if any(not math.isfinite(x) or not 0<=x<=1 for x in [out['activation'],out['event'],*out['conditions'].values()]):raise ValueError('Fatores de ativação devem estar entre 0 e 1')
    return out

def factor(e,cfg):
    if e['kind']=='permanent':return e['probability']
    default=cfg['event'] if e['kind']=='event' else cfg['activation']
    # Character/status synergies require an explicit scenario, not generic uptime.
    text=e['description'].lower()
    if 'when critical occurs' in text:default=0
    if 'when an enemy is inflicted with' in text:default=0
    return cfg['conditions'].get(e['condition'],default)*e['probability']

def effects_for_set(cat,ids,traits=None):
    if len(ids) not in (2,3) or len(set(ids))!=len(ids):raise ValueError('Escolha 2 ou 3 medalhas distintas')
    if any(i not in cat.medals for i in ids):raise ValueError('Medalha não encontrada')
    families=[cat.medals[i].get('original_id',i) for i in ids]
    if len(set(families))!=len(ids):raise ValueError('Este modo compara medalhas de famílias distintas; variantes da mesma medalha são alternativas.')
    effects=[];counts=Counter();active=[]
    for mid in ids:
        m=cat.medals[mid];counts.update(set(m['tag_ids']))
        effects.extend(dict(e,source='unique',medal_id=mid,label=m['name']) for e in cat.unique[mid])
        for field,aid in (traits or {}).get(str(mid),{}).items():
            if field not in ('ability2_group_id','ability3_group_id','ability4_group_id'):raise ValueError('Slot de trait inválido')
            options=cat.tables['abilityTable'].get(m.get(field),{}).get('table_datas',[])
            if aid and aid not in {x['ability_id'] for x in options}:raise ValueError('Trait não pertence ao grupo desta medalha')
            if aid:effects.extend(dict(e,source='trait',medal_id=mid,label=m['name']) for e in cat.effects.get(aid,[]))
    for tid,n in sorted(counts.items()):
        if n<2:continue
        if tid not in cat.tags:continue
        tag=cat.tags[tid];level=min(n,3);tes=cat.tag_effects[tid,level]
        active.append({'id':tid,'name':tag['name'],'count':n,'tier':level,'effects':tes})
        effects.extend(dict(e,source='tag',label=tag['name']) for e in tes)
    return effects,active

def score_effects(effects,cfg):
    groups=defaultdict(float);caps={};dims={};details=[]
    for e in effects:
        if not e['supported']:continue
        v=e['value']*factor(e,cfg);key=e['key']
        # Non-stackable timed buffs of the same ID: count only strongest estimate.
        groups[key]=max(groups[key],v) if e['kind']=='temporary' else groups[key]+v
        if e['cap'] is not None:caps[key]=e['cap']
        dims[key]=e['dimension']
    scores=dict.fromkeys(DIMENSIONS,0.)
    for k,v in groups.items():
        used=min(v,caps.get(k,math.inf));scores[dims[k]]+=used
        details.append({'key':k,'dimension':dims[k],'estimated':round(v,6),'used':round(used,6),'cap':caps.get(k),'redundancy':round(v-used,6)})
    total=sum(v*cfg['weights'][k] for k,v in scores.items())
    return total,scores,details

def evaluate(cat,ids,raw,traits=None):
    ids=[cat.aliases.get(i,i) for i in ids]
    if traits:traits={str(cat.aliases.get(int(mid),int(mid))):v for mid,v in traits.items()}
    cfg=config(raw);effects,tags=effects_for_set(cat,ids,traits);total,scores,groups=score_effects(effects,cfg)
    supported=[e for e in effects if e['supported']]
    weighted=sorted(((e['value']*factor(e,cfg)*cfg['weights'][e['dimension']],e) for e in supported),key=lambda x:-x[0])
    strengths=[f"{e['label']}: {e['description']} (contribuição individual estimada {v:.2f}, antes de limites compartilhados)" for v,e in weighted[:4] if v>0]
    unsupported=[e for e in effects if not e['supported']]
    weak=[]
    if unsupported:weak.append(f'{len(unsupported)} efeito(s) preservado(s), mas sem pontuação: sem interpretação numérica validada.')
    conditional=[e for e in supported if e['kind']!='permanent']
    if conditional:weak.append(f'{len(conditional)} efeito(s) dependem dos fatores de ativação configurados. Situações mutuamente exclusivas não são bônus simultâneos.')
    descriptions=' '.join(e['description'] for e in conditional).lower()
    if 'your team has less treasure secured' in descriptions and 'your team has more treasure secured' in descriptions:
        weak.append('Conflito de cenário: há efeitos para ter menos tesouros e para ter mais tesouros. Eles não ficam ativos ao mesmo tempo; ajuste os fatores de cada condição.')
    hp_high=[float(x) for x in re.findall(r'your hp is ([\d.]+)% or more',descriptions)]
    hp_low=[float(x) for x in re.findall(r'your hp is ([\d.]+)% or less',descriptions)]
    if hp_high and hp_low and max(hp_high)>min(hp_low):weak.append('Conflito de HP: parte dos efeitos requer HP alto e outra parte HP baixo. A pontuação é utilidade de cenários, não bônus simultâneo.')
    if any(g['redundancy']>0 for g in groups):weak.append('Há contribuição excedente aos limites utilizados no modelo; consulte a decomposição.')
    if not traits:weak.append('Traits adicionais não foram selecionados e não contribuem para esta avaliação.')
    if any(e['supported'] and factor(e,cfg)==0 and e['kind']!='permanent' for e in effects):weak.append('Há condições sem peso neste cenário. Gatilhos de crítico e aplicação de status exigem contexto; podem ser ajustados em Condições e hipóteses.')
    tag_score=score_effects([e for e in effects if e['source']=='tag'],cfg)[0]
    consistency=sum(factor(e,cfg) for e in supported)/len(supported) if supported else 0
    return {'ids':ids,'medals':[cat.public_medal(cat.medals[i]) for i in ids],'score':round(total,6),'scores':{k:round(v,6) for k,v in scores.items()},'tag_score':round(tag_score,6),'consistency':round(consistency,4),'tags':tags,'effects':effects,'groups':groups,'strengths':strengths,'weaknesses':weak,'coverage':{'supported':len(supported),'total':len(effects)},'explanation':f"{len(tags)} tags ativadas; {len(supported)}/{len(effects)} efeitos interpretados. A ordem usa os pesos escolhidos e fatores de ativação, com limites por tipo. Não representa dano, recarga final nem taxa de vitória.",'model':MODEL,'config':cfg}

def optimize(cat,raw,owned=(),progress=None,cancel=None):
    """Enumerate every eligible distinct-family pair/triple in bounded NumPy chunks.

    Exact only relative to utility-v2. No preselection by popularity or individual score.
    Equivalent variants within the same family collapse when tags and unique effects
    are identical (additional traits are not part of automatic ranking).
    """
    import numpy as np
    start=time.monotonic();cfg=config(raw);slots=int(raw.get('slots',3));top=int(raw.get('top',10))
    if slots not in (2,3) or not 1<=top<=50:raise ValueError('Quantidade de slots ou resultados inválida')
    candidates=cat.filter(raw.get('filters',{}),owned)
    groups={}
    for m in candidates:
        family=m.get('original_id',m['medal_id']);key=(family,m['ability_id'],tuple(sorted(m['tag_ids'])))
        groups.setdefault(key,[]).append(m)
    medals=[v[0] for v in groups.values()];n=len(medals)
    if n<slots:return {'results':[],'evaluated':0,'eligible':len(candidates),'representatives':n,'seconds':0,'complete':True}
    all_effects=[e for m in medals for e in cat.unique[m['medal_id']]]+[e for es in cat.tag_effects.values() for e in es]
    channels=sorted({e['key'] for e in all_effects if e['supported']});idx={k:i for i,k in enumerate(channels)};width=len(idx)
    weights=np.zeros(width);caps=np.full(width,np.inf);temporary=np.zeros(width,dtype=bool)
    for e in all_effects:
        if not e['supported']:continue
        j=idx[e['key']];weights[j]=cfg['weights'][e['dimension']]
        if e['cap'] is not None:caps[j]=e['cap']
        temporary[j]=e['kind']=='temporary'
    full_temporary=temporary.copy()
    def vector(es):
        v=np.zeros(width)
        for e in es:
            if not e['supported']:continue
            j=idx[e['key']];val=e['value']*factor(e,cfg)
            v[j]=max(v[j],val) if full_temporary[j] else v[j]+val
        return v
    matrix=np.array([vector(cat.unique[m['medal_id']]) for m in medals])
    # Columns with zero objective weight need not participate in rank evaluation.
    relevant=np.flatnonzero(weights)
    matrix=matrix[:,relevant];weights=weights[relevant];caps=caps[relevant];temporary=temporary[relevant]
    tids=sorted({t for m in medals for t in m['tag_ids'] if t in cat.tags})
    tagindex={t:j for j,t in enumerate(tids)}
    membership=np.zeros((n,len(tids)),dtype=np.int8)
    for i,m in enumerate(medals):
        for t in set(m['tag_ids']):
            if t in tagindex:membership[i,tagindex[t]]=1
    t2=np.array([vector(cat.tag_effects[t,2])[relevant] for t in tids]);t3=np.array([vector(cat.tag_effects[t,3])[relevant] for t in tids])
    families=np.array([m.get('original_id',m['medal_id']) for m in medals]);ids=np.array([m['medal_id'] for m in medals]);heap=[];evaluated=0
    def accept(combos):
        nonlocal evaluated
        valid=np.ones(len(combos),dtype=bool)
        for x in range(slots):
            for y in range(x):valid &= families[combos[:,x]]!=families[combos[:,y]]
        combos=combos[valid]
        if not len(combos):return
        counts=membership[combos].sum(axis=1)
        vals=matrix[combos].sum(axis=1)
        if temporary.any():vals[:,temporary]=matrix[combos][:,:,temporary].max(axis=1)
        # Tags have one active tier, never tier 2 + tier 3 together.
        tagvals=(counts==2)@t2 + (counts>=3)@t3
        vals[:,~temporary] += tagvals[:,~temporary]
        # Non-stackable channels must also use max across tags and unique effects.
        for col in np.flatnonzero(temporary & ((t2!=0).any(axis=0) | (t3!=0).any(axis=0))):
            tv=np.where(counts==2,t2[:,col],np.where(counts>=3,t3[:,col],0)).max(axis=1) if len(tids) else 0
            vals[:,col]=np.maximum(vals[:,col],tv)
        score=np.minimum(vals,caps)@weights
        evaluated+=len(combos)
        # Stable ties: smaller IDs win. Do not truncate ties via argpartition.
        threshold=heap[0][0] if len(heap)>=top else -math.inf
        for q in np.flatnonzero(score>=threshold-1e-9):
            chosen=tuple(int(x) for x in ids[combos[q]])
            entry=(round(float(score[q]),8),tuple(-x for x in chosen),chosen)
            if len(heap)<top:heapq.heappush(heap,entry)
            elif entry>heap[0]:heapq.heapreplace(heap,entry)
    # Small bounded chunks avoid constructing all C(n,3) rows in memory.
    for i in range(n-slots+1):
        if cancel and cancel():return {'cancelled':True,'complete':False,'evaluated':evaluated,'results':[]}
        if slots==2:
            js=np.arange(i+1,n);accept(np.column_stack((np.full(len(js),i),js)))
        else:
            for j in range(i+1,n-1):
                ks=np.arange(j+1,n);accept(np.column_stack((np.full(len(ks),i),np.full(len(ks),j),ks)))
        if progress:progress({'evaluated':evaluated,'progress':round(100*(1-((n-i-1)/n)**slots),2),'seconds':round(time.monotonic()-start,1)})
    results=[evaluate(cat,list(entry[2]),raw) for entry in sorted(heap,reverse=True)]
    for r in results:
        r['alternatives']={str(mid):cat.variants.get(mid,[mid]) for mid in r['ids']}
    return {'results':results,'evaluated':evaluated,'eligible':len(candidates),'representatives':n,'seconds':round(time.monotonic()-start,2),'complete':True,'scope':'Famílias distintas; variantes equivalentes agrupadas; traits adicionais fora do ranking automático.','model':MODEL}
