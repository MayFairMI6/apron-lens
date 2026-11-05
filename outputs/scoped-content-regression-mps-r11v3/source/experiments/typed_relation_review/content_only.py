"""R11v2 diagnostic baseline: uniform bare-content NLI, not an accepted grader.

No question text, instruction/meta probes, lexical relation gate, correction
list or per-case format selection enters any comparison. Neutral is uncertain.
The classifier may still misread identity, correction and attribution; exposed
measurements and all fixed gates remain necessary.
"""
import time
from backend.training_assessment import MAX_RESPONSE_CHARS
from modelaccess.nli import MODEL_ID,MODEL_REVISION,LABELS
from .candidate import validate_input,grounding_context
from .propositions import propositions_for
from .redesign import (Plan,label,token_length,bounded_spans,exact_sentences,
                       choose_quotes,validate_redesign_review,QUOTE_CONTRACT)

VERSION='typed-uniform-bare-content-r11v2'
THRESHOLD=.8
DEADLINE_SECONDS=55.


def raw_sources(current):
    """Literal current reports and fields, with source and temporal provenance."""
    units=[]
    for report in current:
        header=('Report '+report['id']+'; flight '+str(report.get('flightInstance'))+
            '; aircraft '+str(report.get('aircraftId'))+'; source '+str(report.get('source','unknown'))+
            '; CURRENT; event '+str(report['eventTime'])+'; received '+str(report['receiptTime'])+'. ')
        facts=report.get('_typedFacts',[])
        text=header+report['message']
        if facts:text+='\n'+'\n'.join(f['property']+'='+repr(f['value'])+' ['+f['status']+']' for f in facts)
        units.append(dict(text=text,provenance=header,reportIds=[report['id']],sourceFacts=facts))
    return units


def add_raw_answer(plan,kind,text,hypothesis,**metadata):
    maximum=min(512,getattr(plan.scorer,'max_length',512))
    spans=bounded_spans(text,lambda value:token_length(plan.scorer,value,hypothesis)<=maximum)
    indices=[plan.add(kind,span['text'],hypothesis,learnerChunk=span,
        wholeAnswerAvailable=len(spans)==1,**metadata) for span in spans]
    return indices,len(spans)==1


def add_sources(plan,kind,units,hypothesis,**metadata):
    """No question prefix. Partial records repeat provenance but cannot certify."""
    maximum=min(512,getattr(plan.scorer,'max_length',512));pieces=[]
    for unit in units:
        partial=token_length(plan.scorer,unit['text'],hypothesis)>maximum
        prefix=unit['provenance'] if partial else ''
        spans=bounded_spans(unit['text'],lambda value:token_length(plan.scorer,prefix+value,hypothesis)<=maximum)
        pieces.extend(dict(text=prefix+span['text'],reportIds=unit['reportIds'],sourceChunk=span,
            repeatedProvenance=prefix,partialRecord=len(spans)>1,sourceFacts=unit['sourceFacts']) for span in spans)
    groups=[];group=[]
    for piece in pieces:
        if group and token_length(plan.scorer,'\n'.join(c['text'] for c in group+[piece]),hypothesis)>maximum:
            groups.append(group);group=[]
        group.append(piece)
    if group:groups.append(group)
    if not groups:raise ValueError('no current source evidence')
    return [plan.add(kind,'\n'.join(c['text'] for c in group),hypothesis,
        reportIds=list(dict.fromkeys(rid for c in group for rid in c['reportIds'])),sourceChunks=group,
        sourceCoverageComplete=all(not c['partialRecord'] for c in group),sourceSetChunkCount=len(groups),
        temporalMode='current_only',**metadata) for group in groups]


def source_status(plan,indices):
    """A partial/unscoped split cannot independently establish a contradiction."""
    complete=[i for i in indices if plan.pairs[i]['sourceCoverageComplete']]
    values=[plan.get(i) for i in complete]
    if 'entailment' in values and 'contradiction' not in values:return 'met'
    if len(indices)==1 and len(complete)==1 and values==['contradiction']:return 'contradicted'
    return 'uncertain'


def quote_candidates(text):
    result=[]
    if len(text)<=160:result.append(dict(start=0,end=len(text),text=text))
    for sentence in exact_sentences(text):
        for part in bounded_spans(sentence['text'],lambda value:len(value)<=160):
            start=sentence['start']+part['start'];end=sentence['start']+part['end']
            while start<end and text[start].isspace():start+=1
            while end>start and text[end-1].isspace():end-=1
            if start<end:result.append(dict(start=start,end=end,text=text[start:end]))
    sentences=exact_sentences(text)
    for first,second in zip(sentences,sentences[1:]):
        if second['end']-first['start']<=160:result.append(dict(start=first['start'],end=second['end'],text=text[first['start']:second['end']]))
    unique={(s['start'],s['end']):s for s in result}
    return [unique[key] for key in sorted(unique)]


def evaluate(payload,scorer,deadline):
    validate_input(payload);text=payload['learnerResponse']
    if len(text)>MAX_RESPONSE_CHARS:raise ValueError('learner response exceeds input bound')
    current,historical=grounding_context(payload)
    scorer.semantic_rule_audit=[]
    scorer.typed_state_audit=[f for r in current+historical for f in r.get('_typedFacts',[])]
    plan=Plan(scorer,deadline);props=propositions_for(payload);facets={}
    for cid,hypotheses in props.items():
        for number,hypothesis in enumerate(hypotheses):
            indices,complete=add_raw_answer(plan,'bare_criterion',text,hypothesis,criterionId=cid,facet=number+1)
            facets[(cid,number)]=dict(indices=indices,complete=complete,hypothesis=hypothesis)
    sources=raw_sources(current);ground=[]
    passages=exact_sentences(text)
    if not any(s['text']==text for s in passages):passages.append(dict(start=0,end=len(text),text=text))
    # Whole answer and every original sentence are mandatory, including scope,
    # correction, modality and extra facts. No clause splitter alters the text.
    for passage in passages:
        maximum=min(400,getattr(scorer,'max_length',512)-100)
        chunks=bounded_spans(passage['text'],lambda value:token_length(scorer,'',value)<=maximum)
        for chunk in chunks:
            span=dict(start=passage['start']+chunk['start'],end=passage['start']+chunk['end'],text=chunk['text'])
            ground.append(dict(span=span,wholeScopeAvailable=len(chunks)==1,
                indices=add_sources(plan,'bare_grounding',sources,span['text'],learnerSpan=span)))
    plan.run()
    statuses={}
    for key,info in facets.items():
        value=plan.one(info['indices'],info['complete'])
        statuses[key]='met' if value=='entailment' else 'contradicted' if value=='contradiction' else 'uncertain'
    ground_statuses=[(source_status(plan,info['indices']) if info['wholeScopeAvailable'] else 'uncertain',info) for info in ground]
    selected=next((x for x in ground_statuses if x[0]=='contradicted'),None) or next((x for x in ground_statuses if x[0]=='uncertain'),None) or ground_statuses[0]
    candidates=quote_candidates(text);witnesses={}
    for key,status in statuses.items():
        if status not in ('met','contradicted'):continue
        witnesses[key]=[(plan.add('bare_quote_witness',span['text'],facets[key]['hypothesis'],
            criterionId=key[0],facet=key[1]+1,learnerSpan=span),span) for span in candidates]
    ground_witnesses=[]
    if selected[0] in ('met','contradicted'):
        for span in candidates:
            ground_witnesses.append((add_sources(plan,'bare_grounding_quote',sources,span['text'],learnerSpan=span),span))
    plan.run()
    points=[]
    for criterion in payload['criteria']:
        cid=criterion['id']
        if cid=='grounding':continue
        keys=[(cid,i) for i in range(len(props[cid]))];values=[statuses[k] for k in keys]
        status='contradicted' if 'contradicted' in values else 'uncertain' if 'uncertain' in values else 'met'
        quotes=[]
        if status in ('met','contradicted'):
            needed=keys if status=='met' else [next(k for k in keys if statuses[k]=='contradicted')]
            required='entailment' if status=='met' else 'contradiction'
            options=[[span for index,span in witnesses[key] if plan.get(index)==required] for key in needed]
            quotes=choose_quotes(text,options)
        points.append(dict(criterionId=cid,status=status,comment='Your stated meaning supports this point.' if status=='met' else 'Your stated meaning conflicts with this point.' if status=='contradicted' else 'The meaning cannot be confirmed confidently.',
            evidenceIds=list(dict.fromkeys(criterion['evidenceIds'])),learnerQuotes=quotes,learnerQuote=quotes[0] if quotes else ''))
    status,info=selected;quotes=[]
    if status in ('met','contradicted'):
        options=[span for indices,span in ground_witnesses if source_status(plan,indices)==status]
        quotes=choose_quotes(text,[options])
    evidence=list(dict.fromkeys(rid for _,item in (ground_statuses if status=='met' else [selected])
        for index in item['indices'] for rid in plan.pairs[index]['reportIds']))
    allowed=next(c['evidenceIds'] for c in payload['criteria'] if c['id']=='grounding')
    evidence=[rid for rid in evidence if rid in allowed]
    if not evidence:raise ValueError('no eligible current grounding comparison')
    points.append(dict(criterionId='grounding',status=status,comment='Your claims agree with the current sources.' if status=='met' else 'A claim conflicts with the current sources.' if status=='contradicted' else 'The sources do not confirm the asserted meaning confidently.',
        evidenceIds=evidence,learnerQuotes=quotes,learnerQuote=quotes[0] if quotes else ''))
    met=sum(p['status']=='met' for p in points)
    verdict='needs_review' if any(p['status']=='contradicted' for p in points) else 'supported' if met==len(points) else 'partly_supported' if met else 'needs_review'
    scorer.semantic_rule_audit=[dict(rule='uniform-content-only-diagnostic-v1',
        questionIncludedInAnyPair=False,missingVsUncertainNotResolved=True,correctionScopeNotGuaranteed=True,
        facetStatuses={str(k):v for k,v in statuses.items()},
        grounding=[dict(status=s,span=i['span']) for s,i in ground_statuses])]
    scorer.planned_pairs=list(plan.pairs)
    if time.monotonic()>=deadline:raise TimeoutError('content-only shared deadline')
    return validate_redesign_review(dict(episodeId=payload['episodeId'],checkpointId=payload['checkpointId'],
        verdict=verdict,explanation='Compare the whole answer with each point and the current received sources.',points=points),payload)
