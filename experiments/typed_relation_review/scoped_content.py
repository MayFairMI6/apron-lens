"""R11v3 diagnostic: uniform bare learner content, scoped normalized sources.

No question text, instruction/meta probes, lexical relation gate, correction
list or per-case format selection enters any comparison. Neutral is uncertain.
Source-only canonical statements retain their exact current preconditions in
the audit. Classifier and quotation confidence do not prove semantic correctness.
Identity, omission and correction limitations remain; all fixed gates still apply.
"""
import time
import re
import itertools
from backend.training_assessment import MAX_RESPONSE_CHARS
from modelaccess.nli import MODEL_ID,MODEL_REVISION,LABELS
from .candidate import (validate_input,grounding_context,canonical_source,unreported_readiness,explicit_unrepresented_takeoff_scope)
from .propositions import propositions_for
from .redesign import (Plan,label,token_length,bounded_spans,exact_sentences,
                       choose_quotes,validate_redesign_review,QUOTE_CONTRACT)

VERSION='typed-scoped-source-content-r11v3.3'
THRESHOLD=.8
DEADLINE_SECONDS=55.


def availability_clause(text,typed=False):
    """Recognize explicit source resource knowledge, never learner wording."""
    reference=re.search(r'\bStand\s+([A-Z]\d*)\b',text,re.I)
    if not reference or not re.search(r'\b(?:un)?availab\w*\b',text,re.I):return None
    resource=reference.group(1).upper()
    pattern=(r'Stand\s+([A-Z]\d*)\s+'+(r'(?:(?:is|remains)\s+)?' if typed else r'(?:is|remains)\s+')+
        r'(?P<state>not\s+(?:yet\s+)?confirmed\s+available|(?:now\s+)?confirmed\s+available|available)'
        r'(?:\s+for\s+[A-Z]+\d+)?[.]?')
    match=re.fullmatch(pattern,text.strip(),re.I)
    if not match and (re.match(r'\s*(?:If|Unless)\b',text,re.I) or
            re.match(r'\s*Stand\s+[A-Z]\d*\s+(?:will|is\s+(?:planned|scheduled))\b',text,re.I)):
        return dict(resourceId=resource,value=None,nonoperative=True)
    value=None
    if match:value='unconfirmed' if match['state'].lower().startswith('not') else 'confirmed_available'
    return dict(resourceId=resource,value=value,nonoperative=False)


def typed_parts(value):
    result=[]
    for match in re.finditer(r'[^;]+',value):
        start,end=match.span()
        while start<end and value[start].isspace():start+=1
        while end>start and value[end-1].isspace():end-=1
        if start<end:result.append(dict(start=start,end=end,text=value[start:end]))
    return result


def resource_availability_view(reports,cutoff):
    """Actor-independent current resource knowledge over ALL eligible reports.

    Exact source assertions are retained. A later actor-field replacement does
    not retract a resource assertion; only this resource's operative clock does.
    Unknown availability is never converted to factual unavailability.
    """
    rows=[]
    for report in reports:
        if report['receiptTime']>cutoff:continue
        for origin,parts,property_name,fact in [('message',exact_sentences(report['message']),None,None)]+[
            ('typed_fact',typed_parts(f['value']),f['property'],f) for f in report.get('facts',[])]:
            for part in parts:
                parsed=availability_clause(part['text'],typed=origin=='typed_fact')
                if parsed is None:continue
                row=dict(ruleVersion='stand-resource-availability-clock-v1',reportId=report['id'],
                    episodeId=report.get('episodeId'),source=report.get('source'),actorProvenance=report.get('flightInstance'),
                    resourceType='stand',resourceId=parsed['resourceId'],property='availability_confirmation',
                    value=parsed['value'],nonoperative=parsed['nonoperative'],origin=origin,fieldProperty=property_name,
                    exactSpan=part,eventTime=report['eventTime'],receiptTime=report['receiptTime'],
                    operativeFrom=fact.get('validFrom',report['eventTime']) if fact else report['eventTime'],
                    validUntil=fact.get('validUntil') if fact else None)
                row['assertionId']=report['id']+':'+origin+':'+str(property_name)+':'+str(part['start'])
                rows.append(row)
    # Matching typed availability explicitly supplies its validity interval to
    # the same report's message statement; unrelated movement validity does not.
    for row in rows:
        if row['origin']!='message' or row['nonoperative'] or row['value'] is None:continue
        intervals={(f['operativeFrom'],f['validUntil']) for f in rows if f['origin']=='typed_fact' and
            f['reportId']==row['reportId'] and f['resourceId']==row['resourceId'] and f['value']==row['value']}
        if len(intervals)==1:row['operativeFrom'],row['validUntil']=next(iter(intervals))
        elif len(intervals)>1:row['value']=None;row['unresolvedValidity']=True
    keys={(r['episodeId'],r['resourceType'],r['resourceId'],r['property']) for r in rows}
    for key in keys:
        group=[r for r in rows if (r['episodeId'],r['resourceType'],r['resourceId'],r['property'])==key]
        operative=[r for r in group if not r['nonoperative'] and r['operativeFrom']<=cutoff]
        latest=max((r['operativeFrom'] for r in operative),default=None)
        heads=[r for r in operative if r['operativeFrom']==latest]
        conflict=bool(heads) and (any(r['value'] is None for r in heads) or len({r['value'] for r in heads})>1)
        for row in group:
            if row['nonoperative']:status='nonoperative_plan_or_condition'
            elif row['operativeFrom']>cutoff:status='scheduled'
            elif row['operativeFrom']!=latest:status='historical_resource'
            elif conflict:status='ambiguous_resource'
            elif row['validUntil'] is not None and cutoff>=row['validUntil']:status='expired_resource'
            else:status='current_resource'
            row['resourceStatus']=status
            row['newerResourceAssertionIds']=[r['assertionId'] for r in heads] if status=='historical_resource' else []
    return rows


def current_report_projection(report,resource_rows):
    """A derived current input view; never alters the original message/facts."""
    related=[r for r in resource_rows if r['reportId']==report['id']]
    complete=not any(r['resourceStatus']=='ambiguous_resource' or
        (r['value'] is None and not r['nonoperative']) for r in related)
    messages=[];message_audit=[]
    for part in exact_sentences(report['message']):
        row=next((r for r in related if r['origin']=='message' and r['exactSpan']['start']==part['start']),None)
        keep=row is None or row['value'] is None or row['resourceStatus'] in ('current_resource','nonoperative_plan_or_condition','ambiguous_resource')
        if keep:messages.append(part['text'])
        message_audit.append(dict(exactSpan=part,inCurrentInput=keep,
            resourceStatus=row['resourceStatus'] if row else 'actor_message_component'))
    fields=[];field_audit=[]
    for fact in report.get('_typedFacts',[]):
        retained=[];parts_audit=[]
        for part in typed_parts(fact['value']):
            row=next((r for r in related if r['origin']=='typed_fact' and r['fieldProperty']==fact['property'] and r['exactSpan']['start']==part['start']),None)
            keep=row is None or row['value'] is None or row['resourceStatus'] in ('current_resource','nonoperative_plan_or_condition','ambiguous_resource')
            if keep:retained.append(part['text'])
            parts_audit.append(dict(exactSpan=part,inCurrentInput=keep,resourceStatus=row['resourceStatus'] if row else 'actor_field_component'))
        if retained:fields.append(fact['property']+'='+repr('; '.join(retained)))
        field_audit.append(dict(factId=fact['fact_id'],originalValue=fact['value'],parts=parts_audit))
    return ' '.join(messages),fields,dict(rule='actor-message-resource-clock-projection-v1',
        originalMessage=report['message'],messageParts=message_audit,fieldParts=field_audit,
        resourceAssertions=related,complete=complete)


def raw_sources(current,target_aircraft=None,eligible_reports=None,cutoff=None):
    """Compact source-only normalization. No learner, question or rubric input."""
    units=[]
    reports=eligible_reports if eligible_reports is not None else current
    cutoff=cutoff if cutoff is not None else max((r['receiptTime'] for r in reports),default=0)
    resource_rows=resource_availability_view(reports,cutoff)
    for report in current:
        facts=report.get('_typedFacts',[])
        actor=report.get('flightInstance')
        header='['+report['id']+'] '+str(actor)+'; source='+str(report.get('source','unknown'))+'; CURRENT. '
        message,fields,projection=current_report_projection(report,resource_rows)
        text=header+message
        if fields:text+=' Fields: '+'; '.join(fields)+'.'
        interpretations=[canonical_source(f) for f in facts if canonical_source(f)]
        if interpretations:text+=' '+' '.join(p for c in interpretations for p in c['propositions'])
        units.append(dict(text=text,provenance=header,reportIds=[report['id']],semanticReportIds=[report['id']],
            proofDependencies=[report['id']],sourceFacts=facts,
            actorIds=[actor] if actor else [],properties=sorted({f['property'] for f in facts}),
            resources=sorted({f['value'] for f in facts if f['property']=='stand'}|set(re.findall(r'\bStand\s+([A-Z]\d*)\b',text))),
            canonicalRules=interpretations+[projection],complete=projection['complete'],
            clock=dict(eventTime=report['eventTime'],receiptTime=report['receiptTime'])))
    current_ids={r['id'] for r in current}
    for row in resource_rows:
        if row['resourceStatus']!='current_resource' or row['reportId'] in current_ids:continue
        # Prefer message provenance when the same operative assertion is also
        # present as a typed literal; keep every original row in the audit.
        if row['origin']=='typed_fact' and any(r['reportId']==row['reportId'] and r['origin']=='message' and
                r['resourceStatus']=='current_resource' and r['resourceId']==row['resourceId'] and r['value']==row['value'] for r in resource_rows):continue
        units.append(dict(text='['+row['reportId']+'] source='+str(row['source'])+'; CURRENT resource assertion: '+row['exactSpan']['text'],
            provenance='Current stand resource '+row['resourceId']+'; source '+row['reportId']+'. ',
            reportIds=[row['reportId']],semanticReportIds=[],proofDependencies=[row['reportId']],sourceFacts=[],
            actorIds=[],properties=['stand.availability_confirmation'],resources=[row['resourceId']],
            canonicalRules=[row],complete=True))
    # Resource ambiguity survives independently of both actors' current fields.
    # Its marker never republishes an actor's historical movement as current.
    ambiguous_keys={(r['episodeId'],r['resourceId'],r['property']) for r in resource_rows
        if r['resourceStatus']=='ambiguous_resource'}
    for key in sorted(ambiguous_keys):
        heads=[r for r in resource_rows if (r['episodeId'],r['resourceId'],r['property'])==key
            and r['resourceStatus']=='ambiguous_resource']
        ids=list(dict.fromkeys(r['reportId'] for r in heads));clauses=[]
        for row in heads:
            item='['+row['reportId']+'] '+row['exactSpan']['text']
            if item not in clauses:clauses.append(item)
        units.append(dict(text='Unresolved current stand '+key[1]+' availability source scope: '+' '.join(clauses),
            provenance='Unresolved current resource scope, stand '+key[1]+'. ',
            reportIds=ids,semanticReportIds=[],proofDependencies=ids,sourceFacts=[],actorIds=[],
            properties=['stand.availability_confirmation'],resources=[key[1]],complete=False,
            canonicalRules=[dict(rule='independent-resource-ambiguity-marker-v1',resourceKey=key,
                exactSourceAssertions=heads,scope='prevents certification; no asserted available/unavailable state')]))
    def derived(text,ids,actor,rule,proof,proof_ids=None):
        units.append(dict(text=text,provenance='Derived current source scope for '+str(actor)+'. ',
            reportIds=list(dict.fromkeys(ids)),semanticReportIds=[],
            proofDependencies=list(dict.fromkeys(proof_ids if proof_ids is not None else ids)),searchAudit=proof,
            sourceFacts=[],actorIds=[actor] if actor else [],resources=[],
            properties=[],canonicalRules=[dict(rule=rule,preconditions=proof)],complete=True))
    absent=unreported_readiness(current,target_aircraft)
    if absent:derived(absent['proposition'],absent['reportIds'],absent['flightInstance'],'current-readiness-unreported-source-v1',absent)
    authority=explicit_unrepresented_takeoff_scope(current,target_aircraft)
    if authority:
        derived('The received reports do not establish takeoff clearance for '+authority['flightInstance']+'. This is not a denial of permission.',
            authority['evidenceIds'],authority['flightInstance'],'explicit-unrepresented-takeoff-source-v1',authority,
            proof_ids=authority['searchedReportIds'])
    facts=[f for r in current for f in r.get('_typedFacts',[])]
    for actor in {(f['aircraftId'],f['flightInstance']) for f in facts}:
        scoped=[f for f in facts if (f['aircraftId'],f['flightInstance'])==actor]
        for first,second in [('fuel_status','baggage_status'),('baggage_status','fuel_status')]:
            a=[f for f in scoped if f['property']==first and f['value']=='complete']
            b=[f for f in scoped if f['property']==second and f['value'] in ('delayed','pending','in progress','incomplete')]
            if a and b:
                names={'fuel_status':'fuel service','baggage_status':'baggage loading'}
                text=(str(actor[1])+': '+names[first]+' is complete, while '+names[second]+' is '+b[0]['value']+'. '
                    'Completion of '+names[first]+' does not establish completion of '+names[second]+'.')
                derived(text,[f['event_id'] for f in a+b],actor[1],'current-separate-service-counterexample-v1',a+b)
    if units:
        units[0]['canonicalRules'].append(dict(rule='complete-resource-availability-source-audit-v1',
            cutoff=cutoff,assertions=resource_rows,sourceReportIds=[r['id'] for r in reports]))
    return units


def source_scope(units,passage):
    """Literal entity/resource retrieval, with reference closure and full audit.

    All properties for selected actors remain. Unknown or unbound references
    use the global current source set. No learner assertion is manufactured.
    """
    actors={actor for u in units for actor in u['actorIds']}
    named={actor for actor in actors if re.search(r'(?<!\w)'+re.escape(actor)+r'(?!\w)',passage,re.I)}
    resources=set(re.findall(r'\bStand\s+([A-Z]\d*)\b',passage))
    all_ids={rid for u in units for rid in u['reportIds']}
    if not named and not resources:
        return units,dict(entityScope='global_unbound',actorIds=sorted(actors),resourceIds=[],
            includedReportIds=sorted(all_ids),allCurrentReportIds=sorted(all_ids),complete=all(u['complete'] for u in units),
            propertyScope=sorted({p for u in units for p in u['properties']}),resourceClockComplete=all(u['complete'] for u in units))
    selected=[];ids=set();changed=True
    while changed:
        changed=False
        for unit in units:
            referenced={actor for actor in actors if re.search(r'(?<!\w)'+re.escape(actor)+r'(?!\w)',unit['text'],re.I)}
            semantic_ids=set(unit.get('semanticReportIds',unit['reportIds']))
            if set(unit['actorIds'])&named or referenced&named or set(unit['resources'])&resources or semantic_ids&ids:
                if unit not in selected:selected.append(unit);changed=True
                before=(len(named),len(resources),len(ids))
                named.update(unit['actorIds']);named.update(referenced);resources.update(unit['resources']);ids.update(semantic_ids)
                if before!=(len(named),len(resources),len(ids)):changed=True
    if not selected:return source_scope(units,'')
    return selected,dict(entityScope='literal_reference_closure',actorIds=sorted(named),resourceIds=sorted(resources),
        includedReportIds=sorted({rid for u in selected for rid in u['reportIds']}),
        semanticRawReportIds=sorted(ids),proofDependencyReportIds=sorted({rid for u in selected for rid in u.get('proofDependencies',u['reportIds'])}),
        allCurrentReportIds=sorted(all_ids),complete=all(u['complete'] for u in selected),
        propertyScope=sorted({p for u in selected for p in u['properties']}),
        rule='all current properties and source-reference closure; no categorical claim about learner wording')


def add_raw_answer(plan,kind,text,hypothesis,**metadata):
    maximum=min(512,getattr(plan.scorer,'max_length',512))
    spans=bounded_spans(text,lambda value:token_length(plan.scorer,value,hypothesis)<=maximum)
    indices=[plan.add(kind,span['text'],hypothesis,learnerChunk=span,
        wholeAnswerAvailable=len(spans)==1,**metadata) for span in spans]
    return indices,len(spans)==1


def add_sources(plan,kind,units,hypothesis,**metadata):
    """No question prefix. Partial records repeat provenance but cannot certify."""
    units,scope=source_scope(units,hypothesis)
    maximum=min(512,getattr(plan.scorer,'max_length',512));pieces=[]
    for unit in units:
        partial=token_length(plan.scorer,unit['text'],hypothesis)>maximum
        prefix=unit['provenance'] if partial else ''
        spans=bounded_spans(unit['text'],lambda value:token_length(plan.scorer,prefix+value,hypothesis)<=maximum)
        pieces.extend(dict(text=prefix+span['text'],reportIds=unit['reportIds'],sourceChunk=span,
            repeatedProvenance=prefix,partialRecord=len(spans)>1,sourceFacts=unit['sourceFacts'],
            semanticReportIds=unit.get('semanticReportIds',unit['reportIds']),
            proofDependencies=unit.get('proofDependencies',unit['reportIds']),
            searchAudit=unit.get('searchAudit')) for span in spans)
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
        temporalMode='current_only',sourceScope=scope,sourceNormalizations=[rule for u in units for rule in u['canonicalRules']],**metadata) for group in groups]


def source_status(plan,indices):
    """Only a complete scoped source set can certify either semantic direction."""
    if len(indices)!=1:return 'uncertain'
    complete=[i for i in indices if plan.pairs[i]['sourceCoverageComplete']]
    if not complete or not plan.pairs[complete[0]]['sourceScope']['complete']:return 'uncertain'
    values=[plan.get(i) for i in complete]
    if 'entailment' in values and 'contradiction' not in values:return 'met'
    if len(indices)==1 and len(complete)==1 and values==['contradiction']:return 'contradicted'
    return 'uncertain'


def leading_context_reference(text):
    """Closed-class discourse reference, used for quotes, never grading gates."""
    if re.match(r'\s*It\s+(?:is|was)\s+(?:not\s+)?(?:true|false|the\s+case)\b',text,re.I):return False
    return bool(re.match(r'\s*(?:(?:And|But|So|Yet|However)[,]?\s+)?(?:It|Its|They|Them|Their|This|That|These|Those|Such|The\s+former|The\s+latter)\b',text,re.I))


def explicit_learner_actors(text):
    """Recognize literal flight-like identifiers; never invent an antecedent."""
    return {m.group().upper() for m in re.finditer(r'(?<!\w)[A-Z]{2,}\d+[A-Z]?(?!\w)',text,re.I)}


def implicit_actor_context(previous,target):
    return len(explicit_learner_actors(previous))==1 and not explicit_learner_actors(target)


def quote_candidates(text):
    """Scored original targets plus only necessary adjacent discourse context.

    Independent sentences are never combined for a confidence boost. A long
    sentence is represented collectively, preserving every qualifier, rather
    than certifying an isolated 160-character prefix or tail.
    """
    sentences=exact_sentences(text);result=[]
    for target_index,target in enumerate(sentences):
        first=target_index
        context_kind=None
        ambiguous_previous=target_index and len(explicit_learner_actors(sentences[target_index-1]['text']))>1 and not explicit_learner_actors(target['text'])
        if target_index and not ambiguous_previous and (leading_context_reference(target['text']) or
                implicit_actor_context(sentences[target_index-1]['text'],target['text'])):
            context_kind='leading_reference' if leading_context_reference(target['text']) else 'implicit_actor_argument'
            first=target_index-1
            while first and leading_context_reference(sentences[first]['text']):first-=1
        selected=sentences[first:target_index+1]
        if target['end']-selected[0]['start']>480:continue
        quote_spans=[]
        for number,sentence in enumerate(selected):
            for part in bounded_spans(sentence['text'],lambda value:len(value)<=160):
                a=sentence['start']+part['start'];b=sentence['start']+part['end']
                while a<b and text[a].isspace():a+=1
                while b>a and text[b-1].isspace():b-=1
                if a<b:quote_spans.append(dict(start=a,end=b,text=text[a:b],
                    role='target' if number==len(selected)-1 else 'necessary_antecedent',
                    originalSentenceStart=sentence['start'],originalSentenceEnd=sentence['end'],
                    collectiveSentenceWitness=True))
        if len(quote_spans)>3 or len({p['text'] for p in quote_spans})!=len(quote_spans):continue
        start=selected[0]['start'];end=target['end']
        result.append(dict(start=start,end=end,text=text[start:end],quoteSpans=quote_spans,
            targetSentence=target,antecedentSentences=selected[:-1],
            contextKind=context_kind,
            contextRule='generic discourse reference or unique literal learner actor; exact preceding learner context only'))
    return result


def select_quote_bundles(text,options):
    """Rank valid contextual covers by confidence; do not optimize thresholds."""
    choices=[]
    for combination in itertools.product(*options):
        spans={(s['start'],s['end']):s for _,bundle in combination for s in bundle['quoteSpans']}
        ordered=[spans[k] for k in sorted(spans)]
        if len(ordered)>3 or any(a['end']>b['start'] for a,b in zip(ordered,ordered[1:])):continue
        if len({s['text'] for s in ordered})!=len(ordered):continue
        key=(-min(score for score,_ in combination),len(ordered),sum(len(s['text']) for s in ordered),tuple(spans))
        choices.append((key,ordered))
    if not choices:raise ValueError('no contextual nonoverlapping quotation cover')
    return [s['text'] for s in min(choices,key=lambda c:c[0])[1]]


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
    sources=raw_sources(current,payload.get('aircraftId'),payload['reports'],payload['cutoff']);ground=[]
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
            criterionId=key[0],facet=key[1]+1,learnerSpan=span,quoteSpans=span['quoteSpans']),span) for span in candidates]
    ground_witnesses=[]
    if selected[0] in ('met','contradicted'):
        for span in candidates:
            ground_witnesses.append((add_sources(plan,'bare_grounding_quote',sources,span['text'],learnerSpan=span,quoteSpans=span['quoteSpans']),span))
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
            label_index=1 if required=='entailment' else 0
            options=[[(plan.rows[index]['probabilities'][label_index],span) for index,span in witnesses[key] if plan.get(index)==required] for key in needed]
            quotes=select_quote_bundles(text,options)
        points.append(dict(criterionId=cid,status=status,comment='Your stated meaning supports this point.' if status=='met' else 'Your stated meaning conflicts with this point.' if status=='contradicted' else 'The meaning cannot be confirmed confidently.',
            evidenceIds=list(dict.fromkeys(criterion['evidenceIds'])),learnerQuotes=quotes,learnerQuote=quotes[0] if quotes else ''))
    status,info=selected;quotes=[]
    if status in ('met','contradicted'):
        label_index=1 if status=='met' else 0
        options=[(max(plan.rows[i]['probabilities'][label_index] for i in indices if plan.pairs[i]['sourceCoverageComplete']),span)
            for indices,span in ground_witnesses if source_status(plan,indices)==status]
        quotes=select_quote_bundles(text,[options])
    evidence=list(dict.fromkeys(rid for _,item in (ground_statuses if status=='met' else [selected])
        for index in item['indices'] for rid in plan.pairs[index]['reportIds']))
    allowed=next(c['evidenceIds'] for c in payload['criteria'] if c['id']=='grounding')
    evidence=[rid for rid in evidence if rid in allowed]
    if not evidence:raise ValueError('no eligible current grounding comparison')
    points.append(dict(criterionId='grounding',status=status,comment='Your claims agree with the current sources.' if status=='met' else 'A claim conflicts with the current sources.' if status=='contradicted' else 'The sources do not confirm the asserted meaning confidently.',
        evidenceIds=evidence,learnerQuotes=quotes,learnerQuote=quotes[0] if quotes else ''))
    met=sum(p['status']=='met' for p in points)
    verdict='needs_review' if any(p['status']=='contradicted' for p in points) else 'supported' if met==len(points) else 'partly_supported' if met else 'needs_review'
    scorer.semantic_rule_audit=[dict(rule='scoped-source-content-diagnostic-v3',
        questionIncludedInAnyPair=False,missingVsUncertainNotResolved=True,correctionScopeNotGuaranteed=True,sourceOnlyNormalizations=[u['canonicalRules'] for u in sources],
        quotationPolicy='whole original sentence/context bundles; confidence rank never certifies relevance',
        facetStatuses={str(k):v for k,v in statuses.items()},
        grounding=[dict(status=s,span=i['span']) for s,i in ground_statuses])]
    scorer.planned_pairs=list(plan.pairs)
    if time.monotonic()>=deadline:raise TimeoutError('content-only shared deadline')
    return validate_redesign_review(dict(episodeId=payload['episodeId'],checkpointId=payload['checkpointId'],
        verdict=verdict,explanation='Compare the whole answer with each point and the current received sources.',points=points),payload)
