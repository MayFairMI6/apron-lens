"""R11 structural experiment: question-aware whole-answer NLI and claim checking.

No lexical learner-topic gate, phrase correction list, or R10 grading rule is
used. All semantic probes are fallible model judgments at the frozen threshold.
The experiment has a separate multi-quotation contract; production is unchanged.
"""
import copy
import itertools
import json
import math
import re
import time
from backend.training_assessment import validate_review, MAX_RESPONSE_CHARS
from modelaccess.nli import MODEL_ID, MODEL_REVISION, LABELS
from .propositions import propositions_for
from .candidate import validate_input, grounding_context, canonical_source, unreported_readiness

VERSION='typed-whole-answer-claim-review-r11-v1'
THRESHOLD=.8
DEADLINE_SECONDS=55.
QUOTE_CONTRACT='r11-multiple-exact-quotes-v1'

# Neutral semantic topics, never a lexical match or an expected truth value.
# The same question lookup used for the authored rubric selects these probes.
TOPICS={
 'surface_conflict':[
  {'flight':['the identity of the held aircraft'],'reason':['the obstruction causing the hold']},
  {'release':['the ground-hold outcome'],'change':['the connection between the hold outcome and the obstruction update']},
  {'unknown':['which takeoff permission remains unconfirmed'],'scope':['the distinction between a ground-hold release and takeoff permission']},
 ],
 'late_arrival':[
  {'flight':['which inbound aircraft is waiting for which stand'],'occupant':['which aircraft occupies the stand']},
  {'availability':['whether the stand is currently confirmed available'],'plan':['what a reposition plan establishes about stand availability']},
  {'availability':['the stand availability update and its intended aircraft'],'release':['the connection between that stand update and the same aircraft ground-hold release']},
 ],
 'late_baggage':[
  {'delay':['the cause of the aircraft baggage delay'],'separation':['the fuel-service status','the relationship between fuel completion and baggage loading']},
  {'estimate':['the latest target off-block estimate'],'scope':['whether the estimate establishes departure permission']},
  {'unknown':['whether overall departure readiness is confirmed'],'scope':['whether service completion and ground release establish takeoff permission','whether all remaining departure prerequisites are established']},
 ],
 'fog_restrictions':[
  {'procedures':['the low-visibility procedure status','the safeguarding status'],'hold':['the aircraft hold or movement status','whether departure permission is confirmed']},
  {'partial_cancellation':['the low-visibility procedure status','the safeguarding status'],'hold':['the aircraft hold or movement status','whether departure permission is confirmed']},
  {'confirmation':['whether safeguarding cancellation is confirmed'],'authority':['whether departure permission is confirmed','the aircraft position or movement status']},
 ],
}


def topics_for(payload,propositions):
    from backend.training_assessment import TYPED_QUESTIONS
    for exercise,questions in TYPED_QUESTIONS.items():
        if payload['question'] in questions:
            rows=TOPICS[exercise][questions.index(payload['question'])]
            if list(rows)!=list(propositions) or any(len(rows[c])!=len(propositions[c]) for c in rows):
                raise ValueError('semantic coverage/rubric mismatch')
            return rows
    raise ValueError('unsupported question')


def label(row):
    if row.get('error') or row.get('truncationRejected'):raise ValueError('unavailable NLI comparison')
    probabilities=row.get('probabilities')
    if not isinstance(probabilities,list) or len(probabilities)!=3 or any(
        not isinstance(p,(int,float)) or isinstance(p,bool) or not math.isfinite(p) or p<0 or p>1 for p in probabilities
    ) or abs(sum(probabilities)-1)>.001:raise ValueError('invalid NLI probabilities')
    index=max(range(3),key=lambda i:probabilities[i])
    return LABELS[index] if probabilities[index]>=THRESHOLD else 'uncertain'


def question_answer(question,answer):
    return 'Question (context only; its presuppositions are not learner assertions): '+question+'\nExact learner answer: '+answer


def exact_sentences(text):
    """Punctuation/newline spans only. Never split coordinated nouns or clauses."""
    spans=[];start=0
    for match in list(re.finditer(r'[.!?](?=\s|$)|\n+',text))+[None]:
        end=match.end() if match else len(text)
        while start<end and text[start].isspace():start+=1
        while end>start and text[end-1].isspace():end-=1
        if start<end:spans.append(dict(start=start,end=end,text=text[start:end]))
        start=match.end() if match else len(text)
    return spans


def token_length(scorer,premise,hypothesis):
    # Real calls always use the pinned tokenizer. The fallback is for injected
    # contract-test scorers only, and is explicitly marked in the pair audit.
    tokenizer=getattr(scorer,'tokenizer',None)
    if tokenizer:return len(tokenizer(premise,hypothesis,truncation=False)['input_ids'])
    return len(premise.split())+len(hypothesis.split())+3


def bounded_spans(text,fits):
    """Lossless exact non-overlapping chunks. No character is silently removed."""
    result=[];start=0
    while start<len(text):
        lo=start+1;hi=len(text);end=None
        while lo<=hi:
            mid=(lo+hi)//2
            if fits(text[start:mid]):end=mid;lo=mid+1
            else:hi=mid-1
        if end is None:raise ValueError('comparison context alone exceeds token bound')
        if end<len(text):
            boundary=text.rfind(' ',start,end)
            if boundary>start:end=boundary+1
        result.append(dict(start=start,end=end,text=text[start:end]))
        start=end
    return result


class Plan:
    def __init__(self,scorer,deadline):
        self.scorer=scorer;self.deadline=deadline;self.pairs=[];self.rows=[];self.chunks=[]
    def add(self,kind,premise,hypothesis,**metadata):
        count=token_length(self.scorer,premise,hypothesis)
        if count>min(512,getattr(self.scorer,'max_length',512)):raise ValueError('unpartitioned comparison exceeds token bound')
        index=len(self.pairs)
        self.pairs.append(dict(kind=kind,premise=premise,hypothesis=hypothesis,inputTokensPlanned=count,
            tokenizerVerified=hasattr(self.scorer,'tokenizer'),**metadata))
        return index
    def learner(self,kind,question,text,hypothesis,**metadata):
        prefix=lambda value:question_answer(question,value)
        spans=bounded_spans(text,lambda value:token_length(self.scorer,prefix(value),hypothesis)<=min(512,getattr(self.scorer,'max_length',512)))
        indices=[self.add(kind,prefix(s['text']),hypothesis,learnerChunk=s,wholeAnswerAvailable=len(spans)==1,**metadata) for s in spans]
        self.chunks.extend(dict(role=kind,**s) for s in spans)
        return indices,len(spans)==1
    def run(self):
        if time.monotonic()>=self.deadline:raise TimeoutError('redesign shared deadline')
        pending=self.pairs[len(self.rows):]
        if pending:
            try:rows=self.scorer.score(pending,self.deadline)
            finally:self.scorer.planned_pairs=list(self.pairs)
            if len(rows)!=len(pending):raise ValueError('incomplete NLI stage')
            self.rows.extend(rows)
        self.scorer.planned_pairs=list(self.pairs)
        if time.monotonic()>=self.deadline:raise TimeoutError('redesign shared deadline')
    def get(self,index):return label(self.rows[index])
    def one(self,indices,complete=True):
        if not complete:return 'uncertain'
        if len(indices)!=1:raise ValueError('whole-answer comparison accounting')
        return self.get(indices[0])


def source_units(payload,current,historical):
    """Only eligible source data, not expected answers or learner statements."""
    result=[]
    for report in current+historical:
        facts=report.get('_typedFacts',[])
        status='current' if report in current else 'non-current (use only as history)'
        header='Report '+report['id']+'; flight '+str(report.get('flightInstance'))+'; aircraft '+str(report.get('aircraftId'))+'; source '+json.dumps(report.get('source','unknown'))+'; '+status+'; event '+str(report['eventTime'])+'; received '+str(report['receiptTime'])+'. '
        body=header+'Message: '+report['message']
        body+='\n'+'\n'.join(f['status']+' '+f['property']+'='+json.dumps(f['value']) for f in facts)
        canonical=[canonical_source(f) for f in facts if canonical_source(f)]
        if canonical:body+='\n'+' '.join(p for c in canonical for p in c['propositions'])
        result.append(dict(text=body,provenance=header,reportIds=[report['id']],status=status,sourceFacts=facts,canonicalSources=canonical))
    absence=unreported_readiness(current,payload.get('aircraftId'))
    if absence:result.append(dict(text='Closed current typed-field search: '+absence['proposition'],reportIds=absence['reportIds'],status='current',closedScope=absence))
    # A source-only counterexample to service equivalence. This never examines
    # learner language and never invents a reported service state.
    facts=[f for r in current for f in r.get('_typedFacts',[])]
    for actor in {(f['aircraftId'],f['flightInstance']) for f in facts}:
        scoped=[f for f in facts if (f['aircraftId'],f['flightInstance'])==actor]
        for first,second in [('fuel_status','baggage_status'),('baggage_status','fuel_status')]:
            a=[f for f in scoped if f['property']==first and f['value']=='complete']
            b=[f for f in scoped if f['property']==second and f['value'] in ('delayed','pending','in progress','incomplete')]
            if a and b:
                names={'fuel_status':'fuel service','baggage_status':'baggage loading'}
                result.append(dict(text=str(actor[1])+': '+names[first]+' is complete while '+names[second]+' remains '+b[0]['value']+'. Completion of '+names[first]+' does not establish completion of '+names[second]+'.',
                    reportIds=list(dict.fromkeys(f['event_id'] for f in a+b)),status='current',rule='separately-reported-service-counterexample-v1',sourceFacts=a+b))
    return result


def source_pairs(plan,kind,question,units,hypothesis,**metadata):
    """Token-bounded greedy packing; every source record/chunk stays audited."""
    prefix='Question for interpreting the answer: '+question+'\nReceived source evidence (current and historical states are explicitly labelled):\n'
    max_tokens=min(512,getattr(plan.scorer,'max_length',512));chunks=[]
    for unit in units:
        split=token_length(plan.scorer,prefix+unit['text'],hypothesis)>max_tokens
        provenance=unit.get('provenance','Source reports '+','.join(unit['reportIds'])+'; '+unit['status']+'. ') if split else ''
        spans=bounded_spans(unit['text'],lambda value:token_length(plan.scorer,prefix+provenance+value,hypothesis)<=max_tokens)
        for span in spans:
            chunks.append(dict(text=provenance+span['text'],reportIds=unit['reportIds'],sourceChunk=span,
                repeatedProvenance=provenance,partialRecord=len(spans)>1,sourceStatus=unit['status'],sourceRecord=unit))
    groups=[];group=[]
    for chunk in chunks:
        if group and token_length(plan.scorer,prefix+'\n'.join(c['text'] for c in group+[chunk]),hypothesis)>max_tokens:
            groups.append(group);group=[]
        group.append(chunk)
    if group:groups.append(group)
    if not groups:raise ValueError('no eligible source context')
    indices=[]
    for group in groups:
        indices.append(plan.add(kind,prefix+'\n'.join(c['text'] for c in group),hypothesis,
            reportIds=list(dict.fromkeys(rid for c in group for rid in c['reportIds'])),sourceChunks=group,
            sourceCoverageComplete=all(not c['partialRecord'] for c in group),sourceSearchComplete=True,
            sourceSetChunkCount=len(groups),**metadata))
    return indices


def choose_quotes(text,facets,maximum=3):
    """Minimal exact non-overlapping witness cover for every required facet."""
    choices=[]
    candidates=sorted({(s['start'],s['end']) for options in facets for s in options})
    for size in range(1,min(maximum,len(candidates))+1):
        for selected in itertools.combinations(candidates,size):
            if any(a[1]>b[0] for a,b in zip(selected,selected[1:])):continue
            if len({text[a:b] for a,b in selected})!=len(selected):continue
            if not all(any((s['start'],s['end']) in selected for s in options) for options in facets):continue
            choices.append((sum(b-a for a,b in selected),selected))
        if choices:break
    if not choices:raise ValueError('no relevant nonoverlapping quotation cover')
    selected=min(choices,key=lambda item:(item[0],item[1]))[1]
    return [text[a:b] for a,b in selected]


def validate_redesign_review(result,payload):
    """Frozen experiment contract plus an unchanged strict legacy projection."""
    legacy=copy.deepcopy(result)
    for point in legacy.get('points',[]):point.pop('learnerQuotes',None)
    validate_review(json.dumps(legacy),payload)
    text=payload['learnerResponse']
    for point in result['points']:
        quotes=point.get('learnerQuotes')
        if not isinstance(quotes,list) or len(quotes)>3 or any(not isinstance(q,str) for q in quotes) or len(set(quotes))!=len(quotes):raise ValueError('multi-quote schema')
        end=0
        for quote in quotes:
            if not isinstance(quote,str) or not quote.strip() or len(quote)>160:raise ValueError('multi-quote length')
            start=text.find(quote,end)
            if start<0:raise ValueError('multi-quote order or overlap')
            end=start+len(quote)
        if point['learnerQuote']!=(quotes[0] if quotes else ''):raise ValueError('legacy quote projection mismatch')
        if point['status'] in ('met','contradicted') and not quotes:raise ValueError('quoted witness required')
        if point['status']=='missing' and quotes:raise ValueError('missing point quoted')
    return result


def evaluate(payload,scorer,deadline):
    validate_input(payload)
    text=payload['learnerResponse']
    if len(text)>MAX_RESPONSE_CHARS:raise ValueError('learner response exceeds allowed input bound')
    current,historical=grounding_context(payload)
    propositions=propositions_for(payload);topics=topics_for(payload,propositions)
    scorer.semantic_rule_audit=[];scorer.typed_state_audit=[f for r in current+historical for f in r.get('_typedFacts',[])]
    plan=Plan(scorer,deadline);question=payload['question'];facets={}
    correction,correction_complete=plan.learner('correction_scope',question,text,'The learner corrects or retracts an earlier operational claim.')
    for cid,hypotheses in propositions.items():
        for number,hypothesis in enumerate(hypotheses):
            info={};key=(cid,number)
            for name,probe in [('meaning',hypothesis),('coverage','The learner answer, not just the question, supplies information about '+topics[cid][number]+'.'),
                ('omission','The learner answer provides no information about '+topics[cid][number]+'.'),
                ('final','The learner ultimately asserts, after any corrections, that '+hypothesis)]:
                info[name],info[name+'_complete']=plan.learner('criterion_'+name,question,text,probe,criterionId=cid,facet=number+1)
            facets[key]=info
    sources=source_units(payload,current,historical)
    units=exact_sentences(text)
    if not any(s['text']==text for s in units):units.append(dict(start=0,end=len(text),text=text))
    ground=[]
    for unit in units:
        # Very long passages are losslessly chunked and each chunk is checked;
        # loss of whole-answer scope is explicit and prevents positive credit.
        spans=bounded_spans(unit['text'],lambda value:token_length(scorer,question_answer(question,''),value)<min(400,getattr(scorer,'max_length',512)-80))
        for chunk in spans:
            span=dict(start=unit['start']+chunk['start'],end=unit['start']+chunk['end'],text=chunk['text'])
            info=dict(span=span,wholeScopeAvailable=len(spans)==1)
            info['history'],info['history_complete']=plan.learner('grounding_temporal_scope',question,span['text'],
                'The learner describes earlier or superseded report states as history, rather than asserting them as current.',learnerSpan=span)
            info['factual'],info['factual_complete']=plan.learner('grounding_factuality',question,span['text'],
                'The learner makes an affirmative factual assertion about an operational event or state.',learnerSpan=span)
            info['nonfactual'],info['nonfactual_complete']=plan.learner('grounding_nonfactual',question,span['text'],
                'The answer only names requested information or describes what the reports do not confirm, without asserting an additional operational fact.',learnerSpan=span)
            info['committed'],info['committed_complete']=plan.learner('grounding_commitment',question,text,
                'The learner ultimately commits to the following as an unwithdrawn statement: '+span['text'],learnerSpan=span)
            ground.append(info)
    plan.run()
    has_correction=plan.one(correction,correction_complete)=='entailment'
    facet_results={}
    for key,info in facets.items():
        meaning=plan.one(info['meaning'],info['meaning_complete'])
        coverage=plan.one(info['coverage'],info['coverage_complete'])
        omitted=plan.one(info['omission'],info['omission_complete'])
        final=plan.one(info['final'],info['final_complete'])
        if has_correction:meaning=final
        # Question presuppositions cannot supply learner coverage or earn credit.
        if omitted=='entailment' and coverage=='entailment':status='uncertain'
        elif omitted=='entailment' and coverage!='entailment':status='missing'
        elif coverage!='entailment':status='uncertain'
        elif meaning=='entailment':status='met'
        elif meaning=='contradiction':status='contradicted'
        else:status='uncertain'
        facet_results[key]=status
    for info in ground:
        history=plan.one(info['history'],info['history_complete'])=='entailment'
        applicable=sources if history else [s for s in sources if s['status']=='current']
        info['support']=source_pairs(plan,'grounding_support',question,applicable,info['span']['text'],
            learnerSpan=info['span'],temporalMode='labelled_history_and_current' if history else 'current_only')
        info['unsupported']=source_pairs(plan,'grounding_unsupported_probe',question,applicable,
            'The following answer makes an asserted factual claim unsupported by these reports: '+info['span']['text'],
            learnerSpan=info['span'],temporalMode='labelled_history_and_current' if history else 'current_only')
        info['conflict']=source_pairs(plan,'grounding_scoped_conflict_probe',question,applicable,
            'These current source records explicitly conflict with the factual claim in this answer, rather than discussing a different aircraft, subject or time: '+info['span']['text'],
            learnerSpan=info['span'],temporalMode='labelled_history_and_current' if history else 'current_only')
    # Quote witnesses are generated after whole-answer judgments, never used to
    # override a missing/uncertain/corrected whole-answer interpretation.
    witness_candidates=[]
    for sentence in exact_sentences(text):
        for span in bounded_spans(sentence['text'],lambda value:len(value)<=160):
            start=sentence['start']+span['start'];end=sentence['start']+span['end']
            while start<end and text[start].isspace():start+=1
            while end>start and text[end-1].isspace():end-=1
            if start<end:witness_candidates.append(dict(start=start,end=end,text=text[start:end]))
    for first,second in zip(exact_sentences(text),exact_sentences(text)[1:]):
        if second['end']-first['start']<=160:witness_candidates.append(dict(start=first['start'],end=second['end'],text=text[first['start']:second['end']]))
    witnesses={}
    for key,status in facet_results.items():
        if status not in ('met','contradicted'):continue
        cid,number=key;witnesses[key]=[]
        for span in witness_candidates:
            index=plan.add('quotation_witness',question_answer(question,span['text']),propositions[cid][number],
                criterionId=cid,facet=number+1,learnerSpan=span)
            witnesses[key].append((index,span))
    plan.run()
    points=[]
    for criterion in payload['criteria']:
        cid=criterion['id']
        if cid=='grounding':continue
        keys=[(cid,i) for i in range(len(propositions[cid]))];statuses=[facet_results[k] for k in keys]
        status='contradicted' if 'contradicted' in statuses else 'missing' if 'missing' in statuses else 'uncertain' if 'uncertain' in statuses else 'met'
        quotes=[]
        if status in ('met','contradicted'):
            needed=keys if status=='met' else [next(k for k in keys if facet_results[k]=='contradicted')]
            options=[]
            for key in needed:
                target='entailment' if status=='met' else 'contradiction'
                options.append([span for index,span in witnesses.get(key,[]) if plan.get(index)==target])
            quotes=choose_quotes(text,options)
        points.append(dict(criterionId=cid,status=status,comment={'met':'Your answer states this point.','missing':'The requested point is absent.','contradicted':'Your answer conflicts with this point.','uncertain':'This point needs clarification.'}[status],
            evidenceIds=list(dict.fromkeys(criterion['evidenceIds'])),learnerQuotes=quotes,learnerQuote=quotes[0] if quotes else ''))
    ground_results=[]
    for info in ground:
        support=[plan.get(i) for i in info['support'] if plan.pairs[i]['sourceCoverageComplete']]
        unsupported=[plan.get(i) for i in info['unsupported']]
        scoped_conflict=any(plan.get(i)=='entailment' and plan.pairs[i]['sourceCoverageComplete'] and
            plan.pairs[i]['temporalMode']=='current_only' for i in info['conflict'])
        factual=plan.one(info['factual'],info['factual_complete']);nonfactual=plan.one(info['nonfactual'],info['nonfactual_complete'])
        committed=plan.one(info['committed'],info['committed_complete'])
        if has_correction and committed=='contradiction':
            status='withdrawn'
        elif has_correction and committed!='entailment':status='uncertain'
        elif not info['wholeScopeAvailable']:status='uncertain'
        elif 'entailment' in support and not scoped_conflict:status='met'
        elif 'entailment' in support and scoped_conflict:status='uncertain'
        elif factual=='entailment' and (all(v=='entailment' for v in unsupported) or scoped_conflict):status='contradicted'
        elif nonfactual=='entailment' and factual!='entailment' and 'entailment' not in unsupported:status='met'
        else:status='uncertain'
        ground_results.append((status,info))
    active=[item for item in ground_results if item[0]!='withdrawn']
    if not active:active=[('uncertain',ground[0])]
    selected=next((item for item in active if item[0]=='contradicted'),None) or next((item for item in active if item[0]=='uncertain'),None) or active[0]
    status,info=selected
    if status in ('met','contradicted'):
        spans=bounded_spans(info['span']['text'],lambda value:len(value)<=160)
        # Grounding quotes state the actual passage the judgment relies on;
        # chunks are exact, ordered, and retain qualifiers across up to 3 quotes.
        if len(spans)>3:raise ValueError('grounding quotation exceeds experiment contract')
        quotes=[s['text'] for s in spans if s['text'].strip()]
    else:quotes=[]
    used=active if status=='met' else [selected]
    ids=list(dict.fromkeys(rid for _,item in used for i in item['support'] for rid in plan.pairs[i]['reportIds']))
    grounding_criterion=next(c for c in payload['criteria'] if c['id']=='grounding')
    ids=[rid for rid in ids if rid in grounding_criterion['evidenceIds']]
    if not ids:raise ValueError('no eligible grounding comparison reference')
    points.append(dict(criterionId='grounding',status=status,comment='Your stated claims agree with the sources.' if status=='met' else 'The sources do not establish an asserted claim.' if status=='contradicted' else 'The asserted meaning or its support needs clarification.',
        evidenceIds=ids,learnerQuotes=quotes,learnerQuote=quotes[0] if quotes else ''))
    count=sum(p['status']=='met' for p in points)
    verdict='needs_review' if any(p['status']=='contradicted' for p in points) else 'supported' if count==len(points) else 'partly_supported' if count else 'needs_review'
    result=dict(episodeId=payload['episodeId'],checkpointId=payload['checkpointId'],verdict=verdict,explanation='Compare your answer with the received reports and each requested point.',points=points)
    scorer.semantic_rule_audit.extend([dict(rule='r11-semantic-probe-decisions-v1',hasCorrection=has_correction,
        facets={str(k):v for k,v in facet_results.items()},grounding=[dict(status=s,span=i['span']) for s,i in ground_results]),
        dict(rule='r11-lossless-token-chunks-v1',chunks=plan.chunks,quoteContract=QUOTE_CONTRACT)])
    scorer.planned_pairs=list(plan.pairs)
    if time.monotonic()>=deadline:raise TimeoutError('redesign shared deadline')
    return validate_redesign_review(result,payload)
