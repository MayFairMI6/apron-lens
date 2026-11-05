"""Isolated discriminative NLI development candidate; production never imports it.

NLI confidence is fallible semantic evidence, not a correctness certificate.
Citations are authored comparison context; they do not prove the NLI judgment.
"""
import json
import re
import time
import math
from backend.evidence import classify, FIELDS
from backend.training_assessment import validate_review
from experiments.typed_relation_review.propositions import propositions_for,relevance_for,TOPIC_PATTERNS,occupancy_counter_for,relations_for

VERSION = 'typed-service-relation-review-v3'
MODEL_ID = 'cross-encoder/nli-deberta-v3-small'
MODEL_REVISION = 'fa2804872c3b4bd748f38c0185cc85775361e735'
THRESHOLD = 0.8
LABELS = ('contradiction', 'entailment', 'neutral')
DEADLINE_SECONDS = 55.


def validate_input(payload):
    ids = [r['id'] for r in payload['reports']]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate report')
    for report in payload['reports']:
        if report['episodeId'] != payload['episodeId'] or report['receiptTime'] > payload['cutoff']:
            raise ValueError('unavailable report before inference')
    for criterion in payload['criteria']:
        if not criterion['evidenceIds'] or not set(criterion['evidenceIds']) <= set(ids):
            raise ValueError('unavailable criterion comparison bundle')
    if not payload['learnerResponse'].strip():
        raise ValueError('empty learner response')
    propositions_for(payload)


def learner_sentences(text):
    """Exact sentence spans; preserve conjunctions, negation and semicolons."""
    result = []
    start = 0
    for match in list(re.finditer(r'[.!?](?=\s|$)', text)) + [None]:
        end = match.end() if match else len(text)
        while start < end and text[start].isspace(): start += 1
        while end > start and text[end-1].isspace(): end -= 1
        if end > start:
            result.append(dict(start=start, end=end, text=text[start:end]))
        start = match.end() if match else len(text)
    return result


def grounding_context(payload):
    """Classify literal eligible typed facts with the project's time semantics."""
    facts=[];lookup={}
    for report in payload['reports']:
        for fact in report.get('facts',[]):
            fid=report['id']+':'+fact['property']
            if fid in lookup:raise ValueError('duplicate typed source fact')
            row=dict(fact_id=fid,event_id=report['id'],aircraftId=report.get('aircraftId'),
                flightInstance=report.get('flightInstance'),source=report.get('source','unknown'),
                property=fact['property'],value=fact['value'],eventTime=report['eventTime'],
                receiptTime=report['receiptTime'],validFrom=fact.get('validFrom',report['eventTime']),
                validUntil=fact.get('validUntil'),supersedes=fact.get('supersedes',[]))
            if not isinstance(row['value'],str):raise ValueError('typed fact value must be literal text')
            for key in ('eventTime','receiptTime','validFrom'):
                if not isinstance(row[key],(int,float)) or not math.isfinite(row[key]) or row[key]<0:raise ValueError('invalid typed fact time')
            if row['eventTime']>row['receiptTime']:raise ValueError('typed fact received before event')
            if row['validUntil'] is not None and (not math.isfinite(row['validUntil']) or row['validUntil']<=row['validFrom']):raise ValueError('invalid typed fact validity')
            facts.append(row);lookup[fid]=row
    for fact in facts:
        for old_id in fact['supersedes']:
            old=lookup.get(old_id)
            if old is None:raise ValueError('unavailable supersession source')
            if any(old[k]!=fact[k] for k in ('aircraftId','flightInstance','property')) or old['eventTime']>=fact['eventTime']:
                raise ValueError('invalid typed fact supersession')
    states=classify(facts,payload['cutoff']);current=[];historical=[]
    for report in payload['reports']:
        typed=[f for f in states if f['event_id']==report['id']]
        if any(f['status']=='conflicting' for f in typed):raise ValueError('conflicting current typed sources')
        active=[f for f in typed if f['status']=='current']
        if active and len(active)!=len(typed):raise ValueError('partially superseded report requires clause-level evidence')
        enriched=dict(report,_typedFacts=typed)
        (current if active or not typed else historical).append(enriched)
    return current,historical


def source_text(report):
    lines=[report['message']]
    for fact in report.get('_typedFacts',[]):
        lines.append('Typed source '+fact['fact_id']+'; aircraft '+str(fact['aircraftId'])+' / '+str(fact['flightInstance'])+
            '; '+fact['status']+' '+FIELDS.get(fact['property'],fact['property'])+' = '+json.dumps(fact['value'],ensure_ascii=False)+
            '; event '+str(fact['eventTime'])+'; received '+str(fact['receiptTime'])+'.')
        canonical=canonical_source(fact)
        if canonical:
            lines.append('Canonical typed-source interpretation ('+canonical['ruleVersion']+'): '+' '.join(canonical['propositions']))
    return '\n'.join(lines)


def canonical_source(fact):
    """Source-only domain interpretation; accepts no learner or rubric input."""
    if fact.get('status')!='current' or fact.get('property')!='movement_condition':return None
    actor=fact.get('flightInstance');aircraft=fact.get('aircraftId')
    if not isinstance(actor,str) or not re.fullmatch(r'TRN\d+',actor) or not aircraft:return None
    match=re.fullmatch(r'hold: Stand ([A-Z]\d*) occupied by (TRN\d+)',fact['value'])
    if not match:return None
    stand,occupant=match.groups()
    if occupant==actor:return None
    return dict(ruleVersion='typed-stand-wait-condition-v1',sourceFactId=fact['fact_id'],
        exactValue=fact['value'],preconditions=dict(status='current',property='movement_condition',
            aircraftId=aircraft,flightInstance=actor,stand=stand,occupant=occupant,
            eventTime=fact['eventTime'],receiptTime=fact['receiptTime']),
        propositions=[actor+' is waiting for Stand '+stand+' because Stand '+stand+' is occupied by '+occupant+'.'])


def confident_label(row):
    if row.get('error') or row.get('truncationRejected'):
        raise ValueError('NLI pair unavailable: '+str(row.get('error')))
    probs = row['probabilities']
    if len(probs) != 3 or any(not isinstance(p, (float,int)) or not 0 <= p <= 1 for p in probs) or abs(sum(probs)-1) > .001:
        raise ValueError('invalid NLI probabilities')
    index = max(range(3), key=lambda i: probs[i])
    return LABELS[index] if probs[index] >= THRESHOLD else 'uncertain'


def _topics(text):
    return {name for name,pattern in TOPIC_PATTERNS.items() if re.search(pattern,text,re.I)}


def _same_flight_context(sentence, report):
    learner=set(re.findall(r'\bTRN\d+\b',sentence,re.I))
    source=set(re.findall(r'\bTRN\d+\b',report['message'],re.I))
    return not learner or not source or bool({x.upper() for x in learner}&{x.upper() for x in source})


def _counter_eligible(sentence, counter):
    if not counter:return False
    if nonassertive_scope(sentence):return False
    if re.search(r'\b(will|plan\w*|intend\w*|future|would|waiting|waits)\b|\bgoing\s+to\b',sentence,re.I):return False
    return bool(re.search(r'(?<!\w)'+re.escape(counter['flight'])+r'(?!\w)',sentence,re.I)
                and re.search(r'\bstand\s+'+re.escape(counter['stand'])+r'(?!\w)',sentence,re.I)
                and re.search(r'\b(occup\w*|at)\b',sentence,re.I))


def _check_current_conflicts(reports):
    values={}
    for report in reports:
        for fact in report.get('facts',[]):
            key=(report.get('aircraftId'),report.get('flightInstance'),fact['property'])
            value=json.dumps(fact['value'],sort_keys=True)
            values.setdefault(key,set()).add(value)
    if any(len(v)>1 for v in values.values()):
        raise ValueError('incompatible current report facts require clarification')


def _sentence_context(sentence, text, payload):
    # A clause's own original sentence supplies a nearer unambiguous subject
    # than an independently discussed aircraft in another sentence.
    context_text=sentence.get('originalSentence',text)
    if not re.search(r'\bTRN\d+\b',context_text,re.I):context_text=text
    names={x.upper() for x in re.findall(r'\bTRN\d+\b',context_text,re.I)}
    local=set(re.findall(r'\bTRN\d+\b',sentence['text'],re.I))
    if local:return sentence['text'],None,False
    needs=bool(_topics(sentence['text']) & {'fuel','baggage','movement','permission','stand','time','vehicle'})
    if not needs:return sentence['text'],None,False
    ambiguous=bool(re.search(r'\b(other|another|instead|correction|actually|said|says|quote)\b|[\"“”]',context_text,re.I))
    scope={r.get('flightInstance').upper() for r in payload['reports'] if r['id'] in {rid for c in payload['criteria'] if c['id']!='grounding' for rid in c['evidenceIds']} and r.get('flightInstance')}
    identity_denial=bool(re.search(r'\bnot\s+(?:(?:discussing|referring\s+to|talking\s+about|about)\s+)?TRN\d+|\bdo\s+not\s+mean\s+TRN\d+|\baccording\s+to\b|\b(claimed|speaker|told)\b',context_text,re.I))
    affirmative_anchor=any(re.search(r'\bTRN\d+\b',s['text'],re.I) and bool(_topics(s['text'])) for s in learner_sentences(context_text))
    if len(names)==1 and not ambiguous and not identity_denial and affirmative_anchor and (not scope or next(iter(names)) in scope):
        context={'learnerExplicitFlight':next(iter(names)),'origin':'unique explicit learner flight; no operational fact added'}
        return 'Flight explicitly named elsewhere by the learner: '+next(iter(names))+'.\nExact learner sentence: '+sentence['text'],context,False
    return sentence['text'],None,bool(names or re.search(r'\b(it|its|they|their)\b',sentence['text'],re.I))


_SERVICE_SUBJECT = r'(?:fuel(?:\s+service)?|refuelling|refueling|baggage(?:\s+loading)?|bag(?:gage)?\s+service|bags|loading)(?:\s+for\s+TRN\d+)?'
_COMPLETE = r'(?:(?:is|are|has\s+been|have\s+been|has|have)\s+)?(?:complete|completed|finished|done)'
_UNRESOLVED = r'(?:(?:is|are|remains?|is\s+still|are\s+still)\s+)?(?:pending|outstanding|delayed|incomplete|not\s+(?:yet\s+)?complete|still\s+(?:pending|outstanding|delayed|incomplete))'
_NEGATED_IMPLICATION = r'(?:(?:that(?:\s+(?:(?:completed|finished)\s+)?service)?|this(?:\s+(?:(?:completed|finished)\s+)?service)?|it|fuel\s+completion|baggage\s+completion)\s+)?(?:does\s+not|doesn[’\x27]t|cannot|can[’\x27]t)\s+(?:mean|imply|prove|establish|confirm|guarantee|show)(?:\s+that)?'
_CONNECTOR = r'\s*[,;]?\s*(?:but|and|yet|;|,)\s*'


def _service_property(subject):
    return 'fuel_status' if re.search(r'\bfuel\b|\brefuelling\b|\brefueling\b',subject,re.I) else 'baggage_status'


def service_relation(sentence, payload, current):
    """Parse one complete bounded service statement, without rewriting its text.

    Success verifies an explicitly stated completed first service and either a
    denied implication to the other service, or that other's explicit unresolved
    status. Every token must belong to this grammar. Unsupported leftovers,
    cross-flight assertions and positive implications get no rule support.
    """
    text=sentence['text'];audit=dict(rule='reported-service-independence-v1',
        sentenceStart=sentence['start'],sentenceEnd=sentence['end'],exactSentence=text,
        applied=False,reason='outside bounded service grammar',spans=[],evidenceIds=[])
    if text.rstrip().endswith('?'):
        audit['reason']='interrogative service statement is not an assertion';return audit
    body=text.rstrip('.!?').strip()
    first=r'(?P<first_subject>'+_SERVICE_SUBJECT+r')\s+(?P<first_status>'+_COMPLETE+r')'
    second=[r'(?P<second_subject>'+_SERVICE_SUBJECT+r')\s+(?P<second_status>'+_COMPLETE+r')',
            r'(?P<second_status>completed|finished)\s+(?P<second_subject>'+_SERVICE_SUBJECT+r')']
    parallel=r'(?P<second_subject>'+_SERVICE_SUBJECT+r')\s+(?P<second_status>'+_UNRESOLVED+r')'
    independent=first+_CONNECTOR+parallel
    match=None
    for form in second:
        denied=first+_CONNECTOR+r'(?P<relation>'+_NEGATED_IMPLICATION+r')\s+'+form
        match=re.fullmatch(denied,body,re.I)
        if match:break
    kind='denied_implication'
    if not match:
        match=re.fullmatch(independent,body,re.I);kind='parallel_reported_statuses'
    if not match:return audit
    one=_service_property(match['first_subject']);two=_service_property(match['second_subject'])
    if one==two:
        audit['reason']='services are not distinct';return audit
    # Flight identity must originate in this learner response, agree with the
    # cutoff's authored target, and have no competing or attributed identity.
    names={x.upper() for x in re.findall(r'\bTRN\d+\b',payload['learnerResponse'],re.I)}
    if len(names)!=1 or re.search(r'\b(other|another|instead|actually|correction|said|says|told|according\s+to)\b|[\"“”]|\bnot\s+(?:discussing|referring\s+to|talking\s+about|about)\s+TRN\d+|\bdo\s+not\s+mean\s+TRN\d+',payload['learnerResponse'],re.I):
        audit['reason']='service subject flight is ambiguous';return audit
    if not re.search(r'\bTRN\d+\b',text,re.I):
        _,context,ambiguous=_sentence_context(sentence,payload['learnerResponse'],payload)
        if ambiguous or not context:
            audit['reason']='service sentence has no safe affirmative learner flight context';return audit
        audit['entityContext']=context
    flight=next(iter(names));sources=[]
    for report in current:
        if report.get('flightInstance','').upper()!=flight:continue
        if report.get('aircraftId')!=payload.get('aircraftId'):continue
        for fact in report.get('facts',[]):
            if fact['property'] in (one,two):sources.append((report,fact))
    completed=[r for r,f in sources if f['property']==one and str(f['value']).lower() in ('complete','completed')]
    unresolved=[r for r,f in sources if f['property']==two and str(f['value']).lower() in ('delayed','in progress','incomplete','pending','not complete','not completed','outstanding')]
    if not completed or not unresolved:
        audit['reason']='both independent current service states are not established';return audit
    # In parallel syntax the second clause asserts an unresolved status. The
    # exact state must match its typed report, not merely a broad incomplete set.
    if kind=='parallel_reported_statuses':
        stated=match['second_status'].lower()
        family='delayed' if 'delayed' in stated else 'pending' if 'pending' in stated else 'outstanding' if 'outstanding' in stated else 'incomplete'
        permitted={'delayed':{'delayed'},'pending':{'pending','in progress'},'outstanding':{'delayed','pending','in progress','incomplete','outstanding'},'incomplete':{'delayed','pending','in progress','incomplete','not complete','not completed','outstanding'}}[family]
        unresolved=[r for r,f in sources if f['property']==two and str(f['value']).lower() in permitted]
        if not unresolved:audit['reason']='asserted second service state is not reported';return audit
    for name in ('first_subject','first_status','relation','second_subject','second_status'):
        if name not in match.re.groupindex:continue
        start,end=match.span(name)
        audit['spans'].append(dict(role=name,start=sentence['start']+start,end=sentence['start']+end,text=body[start:end]))
    audit.update(applied=True,reason='reported distinct service states verify the fully parsed learner relation',
        relationKind=kind,firstProperty=one,secondProperty=two,flight=flight,
        evidenceIds=list(dict.fromkeys(r['id'] for r in completed+unresolved)),
        supportedFacetIds=['separation.1','separation.2'] if one=='fuel_status' and two=='baggage_status' else [])
    return audit


def _relevant(sentence, topic_spec):
    topics=_topics(sentence)
    return set(topic_spec['all'])<=topics if isinstance(topic_spec,dict) else bool(topics.intersection(topic_spec))


def learner_clauses(sentence):
    """Exact bounded clause spans; original sentence remains grounding input.

    A conjunction is split only when its left side and right side have their
    own predicate. Shared-subject/negation fragments stay together. Operators
    stay in the right span; no grammatical text is manufactured.
    """
    text=sentence['text'];boundaries=[0]
    if nonassertive_scope(text):
        return [dict(**sentence,originalSentence=text,ambiguousScope=True)]
    predicate=r'\b(is|are|was|were|has|have|remains?|continues?|confirms?|releases?|released|lifted|held|waits?|waiting|blocks?|obstructs?|delays?|delaying|does|do|means|proves|grants?|leaves?)\b'
    for match in re.finditer(r';\s*|,\s*(?=(?:but|and|so|yet|whereas)\b)|\s+(?=(?:but|and|so|yet|whereas|because|following)\b)',text,re.I):
        at=match.end() if text[match.start():match.end()].lstrip().startswith(';') else match.start()
        left=text[boundaries[-1]:at];right=text[at:]
        if ';' in match.group() or (re.search(predicate,left,re.I) and re.search(predicate,right,re.I)):
            if at>boundaries[-1]:boundaries.append(at)
    boundaries.append(len(text));result=[]
    for start,end in zip(boundaries,boundaries[1:]):
        while start<end and text[start].isspace():start+=1
        while end>start and text[end-1].isspace():end-=1
        if end>start:result.append(dict(start=sentence['start']+start,end=sentence['start']+end,text=text[start:end],originalSentence=sentence['text']))
    return result


def nonassertive_scope(text):
    return bool(re.search(r'^\s*(?:if|unless|suppose|imagine|perhaps|maybe)\b|\b(?:not\s+(?:true|the\s+case)|(?:deny|denies|denying)\s+that)\b|\b(might|may|would|possibly)\b',text,re.I))


def relation_present(text,mode):
    has=lambda pattern:bool(re.search(pattern,text,re.I))
    topics=_topics(text)
    permission='permission' in topics
    relation=has(r'\b(mean\w*|impl\w*|prov\w*|establish\w*|grant\w*|giv\w*|give|confer\w*|permit\w*|authori[sz]\w*|confirm\w*|distinct|different|same|equivalent|because|so|following|after|despite)\b')
    if mode=='occupancy':return has(r'\boccup\w*\b|\b(?:at|in)\s+(?:stand\s+)?[A-Z]\d*\b') and not has(r'\bwait\w*\s+for\b')
    if mode=='waiting_position':return has(r'\b(wait\w*|occup\w*|staging|inbound|already\s+at)\b') and ('stand' in topics or has(r'\bfor\s+[A-Z]\d*\b'))
    if mode=='baggage_delay':return 'baggage' in topics and has(r'\b(delay\w*|late\s+baggage|waiting\s+(?:on|for))\b') and not has(r'\b(proves?|means?|impl\w*)\b')
    if mode=='vehicle_obstruction':return 'vehicle' in topics and has(r'\b(obstruct\w*|block\w*|cause\w*)\b')
    if mode=='hold_change_link':return 'vehicle' in topics and has(r'\bhold\b') and has(r'\b(releas\w*|lift\w*|cancel\w*)\b') and relation
    if mode=='permission_status':
        distinction=has(r'\b(hold|release\w*|service|completion|estimate|cancellation)\b') and has(r'\b(mean\w*|impl\w*|prov\w*|grant\w*|distinct|different|same|equivalent)\b')
        return permission and not distinction and has(r'\b(is|are|has|have|remains?|unknown|unconfirmed|confirmed|confirmation|established|know|known|cleared)\b')
    if mode=='authority_distinction':return permission and has(r'\b(hold|release\w*)\b') and relation
    if mode=='plan_availability_relation':return has(r'\b(plan\w*|reposition\w*|will\s+move)\b') and has(r'\b(available|availability|free)\b') and relation
    if mode=='stand_hold_link':return has(r'\b(available|availability|free)\b') and has(r'\bhold\b') and has(r'\b(releas\w*|lift\w*)\b')
    if mode=='estimate_authority':return permission and relation
    if mode=='readiness_authority':return (permission or has(r'\bprerequisites?\b')) and relation
    if mode=='readiness_status':return has(r'\b(readiness|ready)\b') and has(r'\b(is|are|remains?|unconfirmed|confirmed|unknown|leave|leaves)\b')
    if mode=='estimate':return 'time' in topics and has(r'\b\d{1,2}:\d{2}\b')
    if mode=='availability_status':return has(r'\b(available|availability|free)\b') and not has(r'\b(?:not|doesn[’\x27]t)\s+(?:establish|prove|confirm|mean|show)\b')
    if mode=='fuel_state':return 'fuel' in topics and has(r'\b(complete\w*|finished|done|pending|delayed|progress)\b')
    if mode=='service_relation':return {'fuel','baggage'}<=topics and (relation or has(r'\b(pending|delayed|outstanding|incomplete)\b'))
    if mode=='lvp_status':return 'lvp' in topics
    if mode=='safeguarding_status':return bool(has(r'\bsafeguard\w*\b') or ('safeguarding' in topics and 'lvp' not in topics))
    if mode=='hold_status':return has(r'\bhold\b') and has(r'\b(releas\w*|lift\w*|held|remain\w*)\b')
    if mode=='movement_status':return 'movement' in topics and not (permission and not has(r'\b(hold|held|park\w*|mov\w*)\b'))
    raise ValueError('unsupported neutral relation')


def relation_units(sentence,mode):
    clauses=learner_clauses(sentence)
    relational={'hold_change_link','authority_distinction','plan_availability_relation','stand_hold_link','service_relation','estimate_authority','readiness_authority'}
    candidates=list(clauses)
    if mode in {'readiness_authority','authority_distinction','plan_availability_relation','service_relation'}:
        return [dict(**sentence,originalSentence=sentence['text'])] if relation_present(sentence['text'],mode) else []
    if mode in relational:
        for start in range(len(clauses)):
            for end in range(start+1,len(clauses)):
                a=clauses[start]['start'];b=clauses[end]['end']
                candidates.append(dict(start=a,end=b,text=sentence['text'][a-sentence['start']:b-sentence['start']],originalSentence=sentence['text']))
    matched=[c for c in candidates if relation_present(c['text'],mode)]
    # Prefer the minimum exact window expressing the relation; unrelated suffix
    # claims remain in original grounding but cannot alter its core criterion.
    return [c for c in matched if not any(other['start']>=c['start'] and other['end']<=c['end'] and (other['start'],other['end'])!=(c['start'],c['end']) for other in matched)]


def explicit_identity_mismatch(unit,hypothesis,mode):
    if nonassertive_scope(unit.get('originalSentence',unit['text'])):return False
    expected={x.upper() for x in re.findall(r'\bTRN\d+\b',hypothesis,re.I)}
    if len(expected)!=1:return False
    names={x.upper() for x in re.findall(r'\bTRN\d+\b',unit['text'],re.I)}
    # In an obstruction clause, "its route" has the single named aircraft in
    # the same original causal sentence as antecedent. Do not attach globally.
    if not names and mode=='vehicle_obstruction' and re.search(r'\bits\s+(?:ground\s+)?route\b',unit['text'],re.I):
        names={x.upper() for x in re.findall(r'\bTRN\d+\b',unit.get('originalSentence',''),re.I)}
    if len(names)!=1 or names==expected:return False
    if re.search(r'\b(other|another|instead|correction|actually|said|says|not\s+TRN)\b|["“”]',unit.get('originalSentence',unit['text']),re.I):return False
    return True


def comparison_context(unit,text,payload,current):
    """Audited aliases and exact antecedents; quotation text never changes."""
    premise,entity,ambiguous=_sentence_context(unit,text,payload)
    aliases=[];comparison=unit['text']
    resource_context=bool(_topics(comparison)&{'stand','movement'}) or bool(re.search(r'\b(?:for|to|at)\s+[A-Z]\d*\b',comparison))
    if resource_context:
        sources={}
        for report in current:
            for fact in report.get('_typedFacts',[]):
                values=[]
                if fact['property']=='stand' and re.fullmatch(r'[A-Z]\d*',fact['value']):values.append(fact['value'])
                values.extend(re.findall(r'\bStand\s+([A-Z]\d*)\b',fact['value']))
                for value in values:sources.setdefault(value,[]).append(fact['fact_id'])
        for value,fact_ids in sources.items():
            def replace(match):
                if re.search(r'\bstand\s+$',comparison[:match.start()],re.I):return match.group()
                left=comparison[:match.start()];right=comparison[match.end():]
                resource_role=bool(re.search(r'\b(?:for|to|at|from|of|that)\s+$',left,re.I)
                    or (not left.strip() and re.match(r'\s+(?:is|was|has|remains|confirmed|available|free)\b',right,re.I)))
                if not resource_role:return match.group()
                aliases.append(dict(original=value,canonical='Stand '+value,sourceFactIds=list(dict.fromkeys(fact_ids))))
                return 'Stand '+value
            comparison=re.sub(r'(?<!\w)'+re.escape(value)+r'(?!\w)',replace,comparison)
        if aliases:premise=premise.replace(unit['text'],comparison)
    antecedents=[];original=unit.get('originalSentence',unit['text'])
    if unit['text']!=original and re.search(r'\bits\s+(?:ground\s+)?(?:route|hold)|\bthat\s+aircraft\b',unit['text'],re.I):
        names={x.upper() for x in re.findall(r'\bTRN\d+\b',original,re.I)}
        if len(names)==1 and not nonassertive_scope(original):antecedents.append(original)
    if re.match(r'\s*(?:Those|These|That|This)\s+(?:reports?|updates?|services?)\b',unit['text'],re.I):
        previous=[s for s in learner_sentences(text) if s['end']<=unit['start']]
        if previous and not nonassertive_scope(previous[-1]['text']):antecedents.append(previous[-1]['text'])
    if antecedents:premise='Exact learner antecedent context: '+'\n'.join(antecedents)+'\nCompared exact learner clause (resource aliases disclosed separately): '+premise
    return premise,entity,ambiguous,aliases,antecedents


def evaluate(payload, scorer, deadline):
    """V2: exact sentence-local NLI, neutral relevance, conflict-safe aggregation."""
    validate_input(payload)
    current,historical=grounding_context(payload)
    scorer.typed_state_audit=[f for r in current+historical for f in r.get('_typedFacts',[])]
    _check_current_conflicts(current)
    propositions=propositions_for(payload);relevance=relevance_for(payload);relations=relations_for(payload)
    text=payload['learnerResponse'];sentences=learner_sentences(text)
    rule_audit=[service_relation(sentence,payload,current) for sentence in sentences]
    scorer.semantic_rule_audit=rule_audit
    rules={r['sentenceStart']:r for r in rule_audit if r['applied']}
    pairs=[];facets={};grounding=[]
    for cid,hypotheses in propositions.items():
        for number,hypothesis in enumerate(hypotheses):
            key=(cid,number);facets[key]=[]
            mode=relations[cid][number]
            units=[unit for original in sentences for unit in relation_units(original,mode)]
            expected_names={x.upper() for x in re.findall(r'\bTRN\d+\b',hypothesis,re.I)}
            target_present=any(expected_names and expected_names<={x.upper() for x in re.findall(r'\bTRN\d+\b',unit['text'],re.I)} for unit in units)
            for sentence in units:
                unit_names={x.upper() for x in re.findall(r'\bTRN\d+\b',sentence['text'],re.I)}
                if target_present and len(unit_names)==1 and unit_names.isdisjoint(expected_names):
                    # An independently described other aircraft is extra content,
                    # not a replacement answer when the target is also stated.
                    continue
                premise,context,ambiguous,aliases,antecedents=comparison_context(sentence,text,payload,current)
                ambiguous=ambiguous or nonassertive_scope(sentence.get('originalSentence',sentence['text']))
                index=len(pairs)
                pairs.append(dict(kind='criterion',criterionId=cid,facet=number+1,premise=premise,hypothesis=hypothesis,
                                  exactLearnerSentence=sentence['text'],entityContext=context,ambiguousEntityContext=ambiguous,
                                  resourceAliases=aliases,exactLearnerAntecedents=antecedents))
                rule=rules.get(sentence['start'])
                rule_support=bool(rule and cid+'.'+str(number+1) in rule['supportedFacetIds'])
                identity_mismatch=explicit_identity_mismatch(sentence,hypothesis,mode)
                entry=dict(index=index,sentence=sentence,counter=None,ambiguous=ambiguous,ruleSupport=rule_support,identityMismatch=identity_mismatch)
                pairs[-1].update(neutralRelation=mode,explicitIdentityMismatch=identity_mismatch)
                pairs[-1]['semanticRuleSupport']=rule if rule_support else None
                counter=occupancy_counter_for(payload,cid,number)
                if _counter_eligible(sentence['text'],counter):
                    entry['counter']=len(pairs)
                    pairs.append(dict(kind='exclusive_counter',criterionId=cid,facet=number+1,
                                      premise=sentence['text'],hypothesis=counter['hypothesis']))
                facets[key].append(entry)
    bundle_ids=set(rid for c in payload['criteria'] if c['id']!='grounding' for rid in c['evidenceIds'])
    active_bundle=[r for r in current if r['id'] in bundle_ids]
    for sentence in sentences:
        is_history=bool(re.search(r'\b(earlier|previously|previous|prior|formerly|before|used to)\b',sentence['text'],re.I))
        topics=_topics(sentence['text'])
        relevant=[r for r in current if topics.intersection(_topics(r['message'])) and _same_flight_context(sentence['text'],r)]
        groups=[]
        if active_bundle:groups.append(active_bundle)
        if relevant:groups.append(relevant)
        groups.extend([r] for r in relevant)
        if not groups:groups=[current]
        seen=set();entries=[]
        for reports in groups:
            ids=tuple(r['id'] for r in reports)
            if ids in seen:continue
            seen.add(ids)
            premise=('Evidence policy: only information established by received reports is confirmed; '
                     'unreported information remains unconfirmed, not denied. Source excerpts for this comparison:\n'
                     +'\n'.join(source_text(r) for r in reports))
            used=list(ids)
            if is_history:
                premise+='\n'+'\n'.join('Non-current historical source (event '+str(r['eventTime'])+'; received '+str(r['receiptTime'])+'): '+source_text(r) for r in historical)
                used.extend(r['id'] for r in historical)
            entries.append(dict(index=len(pairs),reportIds=used,
                # Only the combined relevant source group is a semantic conflict
                # veto. An unrelated individual report cannot override support.
                conflictVeto=bool(relevant) and ids==tuple(r['id'] for r in relevant)))
            pairs.append(dict(kind='grounding',premise=premise,hypothesis=sentence['text'],reportIds=used,
                              conservativeHistoricalUncertainty=is_history,sourceFactIds=[f['fact_id'] for r in reports for f in r.get('_typedFacts',[])],
                              canonicalSources=[canonical_source(f) for r in reports for f in r.get('_typedFacts',[]) if canonical_source(f)]))
        grounding.append(dict(sentence=sentence,entries=entries,history=is_history,rule=rules.get(sentence['start'])))
    if time.monotonic()>=deadline:raise TimeoutError('shared NLI review deadline')
    rows=scorer.score(pairs,deadline)
    if len(rows)!=len(pairs):raise ValueError('NLI pair coverage')
    labels=[confident_label(row) for row in rows]
    if time.monotonic()>=deadline:raise TimeoutError('shared NLI review deadline')
    facet_results={}
    for key,entries in facets.items():
        results=[]
        for entry in entries:
            label='contradiction' if entry['identityMismatch'] else 'entailment' if entry['ruleSupport'] else 'uncertain' if entry['ambiguous'] else labels[entry['index']]
            counter=labels[entry['counter']] if entry['counter'] is not None else None
            if counter=='entailment':label='uncertain' if label=='entailment' else 'contradiction'
            results.append((label,entry))
        values={label for label,_ in results}
        if 'entailment' in values and 'contradiction' in values:label='uncertain'
        elif 'contradiction' in values:label='contradiction'
        elif 'entailment' in values:label='entailment'
        elif 'uncertain' in values:label='uncertain'
        else:label='uncertain' if entries else 'neutral'
        witnesses=[entry['sentence'] for value,entry in results if value==label and len(entry['sentence']['text'])<=160]
        facet_results[key]=(label,min(witnesses,key=lambda s:(len(s['text']),s['start'])) if witnesses else None)
    points=[]
    for criterion in payload['criteria']:
        cid=criterion['id']
        if cid=='grounding':continue
        results=[facet_results[(cid,i)] for i in range(len(propositions[cid]))]
        values=[label for label,_ in results]
        status='contradicted' if 'contradiction' in values else 'uncertain' if 'uncertain' in values else 'met' if all(v=='entailment' for v in values) else 'missing'
        quote=''
        if status in ('met','contradicted'):
            needed=results if status=='met' else [next(r for r in results if r[0]=='contradiction')]
            if any(w is None for _,w in needed):raise ValueError('no bounded NLI quotation witness')
            quote=text[min(w['start'] for _,w in needed):max(w['end'] for _,w in needed)]
            if len(quote)>160:raise ValueError('NLI quotation witness span too wide')
        comment={'met':'Your stated meaning supports this point.','missing':'At least one required point is not expressed.',
                 'contradicted':'Your stated meaning conflicts with this point.','uncertain':'The meaning needs clarification.'}[status]
        points.append(dict(criterionId=cid,status=status,comment=comment,evidenceIds=list(dict.fromkeys(criterion['evidenceIds'])),learnerQuote=quote))
    checks=[]
    for item in grounding:
        entries=item['entries'];support=[e for e in entries if labels[e['index']]=='entailment']
        veto=next((e for e in entries if e['conflictVeto'] and labels[e['index']]=='contradiction'),None)
        if item['rule']:
            # This audited rule checks the COMPLETE original sentence against
            # typed current service states; raw NLI comparisons remain saved.
            status='met';chosen=dict(index=None,reportIds=item['rule']['evidenceIds'],semanticRule=item['rule'])
        elif support and veto:status='uncertain';chosen=veto
        elif support:status='uncertain' if item['history'] else 'met';chosen=min(support,key=lambda e:len(pairs[e['index']]['premise']))
        elif veto:status='contradicted';chosen=veto
        elif all(labels[e['index']] in ('neutral','contradiction') for e in entries):status='contradicted';chosen=entries[0]
        else:status='uncertain';chosen=entries[0]
        checks.append(dict(status=status,sentence=item['sentence'],pair=chosen))
    chosen=next((c for c in checks if c['status']=='contradicted'),None) or next((c for c in checks if c['status']=='uncertain'),None) or checks[0]
    status=chosen['status'];quote=chosen['sentence']['text']
    if len(quote)>160:raise ValueError('grounding quotation witness too wide')
    criterion=next(c for c in payload['criteria'] if c['id']=='grounding')
    used_checks=checks if status=='met' else [chosen]
    ids=[rid for check in used_checks for rid in check['pair']['reportIds'] if rid in criterion['evidenceIds']]
    if not ids:raise ValueError('no eligible grounding comparison source')
    points.append(dict(criterionId='grounding',status=status,
        comment='Not established by the received reports.' if status=='contradicted' else 'This passage needs clarification.' if status=='uncertain' else 'Your claims agree with the received reports.',
        evidenceIds=list(dict.fromkeys(ids)),learnerQuote=quote))
    met=sum(p['status']=='met' for p in points)
    verdict='needs_review' if any(p['status']=='contradicted' for p in points) else 'supported' if met==len(points) else 'partly_supported' if met else 'needs_review'
    result=dict(episodeId=payload['episodeId'],checkpointId=payload['checkpointId'],verdict=verdict,
                explanation='Compare your stated meanings with the received reports.',points=points)
    accepted=validate_review(json.dumps(result),payload)
    if time.monotonic()>=deadline:raise TimeoutError('shared NLI review deadline')
    return accepted


class NLIEngine:
    """Pinned local safetensors, CPU only. Deadline checks occur between batches.

    A running CPU kernel is not forcibly killed. Over-budget results are rejected.
    """
    def __init__(self, model_dir, batch_size=8):
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        torch.set_num_threads(min(4,torch.get_num_threads()))
        self.torch=torch; self.batch_size=batch_size; self.records=[]; self.planned_pairs=[]
        self.tokenizer=AutoTokenizer.from_pretrained(model_dir,revision=MODEL_REVISION,local_files_only=True,trust_remote_code=False)
        self.model=AutoModelForSequenceClassification.from_pretrained(model_dir,revision=MODEL_REVISION,local_files_only=True,
            trust_remote_code=False,use_safetensors=True).to('cpu').eval()
        if self.model.config.num_labels != 3: raise ValueError('unexpected NLI label count')
        for i,name in self.model.config.id2label.items():
            if str(name).lower() not in ('label_'+str(i),LABELS[int(i)]):
                raise ValueError('unexpected NLI label order')
        self.max_length=min(512,getattr(self.model.config,'max_position_embeddings',512),self.tokenizer.model_max_length)

    def score(self, pairs, deadline):
        self.planned_pairs=list(pairs)
        rows=[]
        for offset in range(0,len(pairs),self.batch_size):
            if time.monotonic()>=deadline: raise TimeoutError('NLI deadline between batches')
            batch=pairs[offset:offset+self.batch_size];started=time.monotonic()
            encoded=[self.tokenizer(p['premise'],p['hypothesis'],truncation=False) for p in batch]
            lengths=[len(x['input_ids']) for x in encoded]
            if any(n>self.max_length for n in lengths):
                for pair,n in zip(batch,lengths):
                    self.records.append(dict(**pair,modelId=MODEL_ID,modelRevision=MODEL_REVISION,inputTokens=n,
                        truncationRejected=n>self.max_length,probabilities=None,error='input_too_long' if n>self.max_length else 'batch_withheld',elapsedSeconds=time.monotonic()-started))
                raise ValueError('NLI input exceeds token bound; no truncation')
            inputs=self.tokenizer.pad(encoded,padding=True,return_tensors='pt')
            with self.torch.inference_mode():
                probabilities=self.torch.softmax(self.model(**inputs).logits,dim=-1).cpu().tolist()
            elapsed=time.monotonic()-started
            for pair,n,prob in zip(batch,lengths,probabilities):
                row=dict(**pair,modelId=MODEL_ID,modelRevision=MODEL_REVISION,inputTokens=n,
                    truncationRejected=False,probabilities=prob,error=None,elapsedSeconds=elapsed)
                self.records.append(row);rows.append(row)
            if time.monotonic()>=deadline: raise TimeoutError('NLI deadline after CPU batch')
        return rows
