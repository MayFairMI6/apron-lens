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

VERSION = 'typed-service-relation-review-v10'
MODEL_ID = 'cross-encoder/nli-deberta-v3-small'
MODEL_REVISION = 'fa2804872c3b4bd748f38c0185cc85775361e735'
THRESHOLD = 0.8
LABELS = ('contradiction', 'entailment', 'neutral')
DEADLINE_SECONDS = 55.


def validate_input(payload):
    def valid_time(value):return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and value>=0
    if not valid_time(payload['cutoff']):raise ValueError('invalid evidence cutoff before inference')
    ids = [r['id'] for r in payload['reports']]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate report')
    for report in payload['reports']:
        if any(not valid_time(report.get(k)) for k in ('eventTime','receiptTime')) or report['eventTime']>report['receiptTime']:
            raise ValueError('invalid report time before inference')
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
                if not isinstance(row[key],(int,float)) or isinstance(row[key],bool) or not math.isfinite(row[key]) or row[key]<0:raise ValueError('invalid typed fact time')
            if row['eventTime']>row['receiptTime']:raise ValueError('typed fact received before event')
            if row['validUntil'] is not None and (not isinstance(row['validUntil'],(int,float)) or isinstance(row['validUntil'],bool) or not math.isfinite(row['validUntil']) or row['validUntil']<=row['validFrom']):raise ValueError('invalid typed fact validity')
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


def unreported_readiness(current,target_aircraft):
    """Source-only closed typed-field search; never asserts actual not-ready."""
    reports=[r for r in current if r.get('aircraftId')==target_aircraft]
    if any(not r.get('facts') for r in reports):return None
    facts=[f for r in reports for f in r.get('_typedFacts',[])]
    actors={f['flightInstance'] for f in facts if f.get('flightInstance')}
    if not facts or len(actors)!=1 or 'overall_readiness' not in FIELDS:return None
    if any(f['property']=='overall_readiness' for f in facts):return None
    # Untyped readiness language may carry a known/denied state; do not infer
    # absence merely because an otherwise eligible message omitted its field.
    if any(re.search(r'\bready\w*\b|\breadiness\b|\bdeparture\s+prerequisites?\b',r['message'],re.I) for r in reports):return None
    actor=next(iter(actors))
    return dict(ruleVersion='unreported-current-readiness-field-v1',flightInstance=actor,
        aircraftId=target_aircraft,property='overall_readiness',searchedFactIds=[f['fact_id'] for f in facts],
        reportIds=[r['id'] for r in reports],
        proposition='Overall departure readiness for '+actor+' is not confirmed by the received reports.',
        scope='complete eligible current target typed-fact set; not a denial of actual readiness')


def unsupported_readiness_assertion(sentence,absence):
    if not absence:return None
    text=sentence['text']
    if text.rstrip().endswith('?') or nonassertive_scope(text) or re.search(r'["“”]|\b(?:not\s+(?:saying|claiming|discussing)|said|says|claims?|according\s+to)\b',text,re.I):return None
    # A surface predicate beneath belief, denial or a condition is not an
    # independently asserted fact. Refuse the rule conservatively rather than
    # trying to recover arbitrary embedded syntax with substring matching.
    if re.search(r'\b(if|unless|whether|assuming|supposing|provided|believe\w*|think\w*|suspect\w*|doubt\w*|false|untrue|inaccurate)\b|\bin\s+case\b',text,re.I):return None
    names={x.upper() for x in re.findall(r'\bTRN\d+\b',text,re.I)}
    if names!={absence['flightInstance'].upper()}:return None
    actor=re.escape(absence['flightInstance'])
    patterns=[r'\b'+actor+r'\s+(?:is|has\s+been)\s+(?:now\s+)?(?:fully\s+)?ready\s+for\s+(?:departure|takeoff)\b',
              r'\b(?:every|all)\s+(?:remaining\s+)?departure\s+prerequisites?\s+(?:is|are|has\s+been|have\s+been)\s+(?:satisfied|complete|completed|met)\b']
    matches=[m for p in patterns for m in re.finditer(p,text,re.I)]
    # Only an affirmative clause opening is eligible. Mentions after arbitrary
    # prose ("there is no evidence that ...", for example) remain model input,
    # never a deterministic unsupported-readiness finding.
    matches=[m for m in matches if re.fullmatch(r'\s*(?:(?:and|but|so|yet)\s+)?',text[:m.start()],re.I)]
    matches=[m for m in matches if not re.search(
        r'\bnot\s+$|\b(?:not|doesn[’\x27]t)\s+(?:mean|imply|prove|establish|confirm|show|guarantee)(?:\s+that)?\s*$',text[:m.start()],re.I)]
    if not matches:return None
    match=min(matches,key=lambda m:m.start())
    return dict(rule='unsupported-positive-readiness-v1',applied=True,reason='positive readiness asserted while current readiness field is unreported',
        exactSentence=text,sourcePreconditions=absence,evidenceIds=absence['reportIds'],
        offendingSpan=dict(start=sentence['start']+match.start(),end=sentence['start']+match.end(),text=match.group()))


def explicit_unrepresented_takeoff_scope(current,target_aircraft):
    """Source-only explicit report scope, not missing-schema inference or denial."""
    target=[r for r in current if r.get('aircraftId')==target_aircraft]
    if any(not r.get('facts') for r in target):return None
    actors={r.get('flightInstance') for r in target if r.get('flightInstance')}
    if len(actors)!=1:return None
    actor=next(iter(actors));explicit=[];searched=[]
    no_representation=r'No\s+(?:runway\s+or\s+)?takeoff\s+clearance\s+is\s+represented[.]?'
    permission=r'\b(takeoff|take\s+off|clearance|permission|cleared|grant\w*|deny\w*|deni\w*|authori[sz]\w*|allow\w*|permit\w*|approv\w*)\b'
    for report in current:
        remaining=[];matched=[]
        for sentence in learner_sentences(report['message']):
            if re.fullmatch(no_representation,sentence['text'],re.I):matched.append(sentence)
            else:remaining.append(sentence['text'])
        # An eligible grant, denial, cancellation, uncertain reference or other
        # permission statement prevents this narrow closed-scope rule entirely.
        if re.search(permission,' '.join(remaining),re.I):return None
        if any(re.search(permission,f['value'],re.I) for f in report.get('_typedFacts',[])):return None
        searched.append(report['id'])
        route_facts=[f for f in report.get('_typedFacts',[]) if f['property']=='route' and f['status']=='current']
        if report in target and report.get('flightInstance')==actor and matched and route_facts and all(f.get('flightInstance')==actor for f in route_facts):
            explicit.append(dict(reportId=report['id'],sourceFactIds=[f['fact_id'] for f in route_facts],
                exactSourceStatements=[s['text'] for s in matched],flightInstance=actor,
                aircraftId=target_aircraft))
    if not explicit:return None
    return dict(ruleVersion='explicit-source-unrepresented-takeoff-scope-v1',flightInstance=actor,
        aircraftId=target_aircraft,sourceStatements=explicit,searchedReportIds=searched,
        evidenceIds=[s['reportId'] for s in explicit],
        scope='received route sources explicitly represent no takeoff clearance; not an actual denial of permission')


def unsupported_takeoff_assertion(sentence,scope):
    if not scope:return None
    text=sentence['text'];actor=scope['flightInstance']
    if text.rstrip().endswith('?') or nonassertive_scope(text):return None
    if re.search(r'["“”]|\b(other|another|else|said|says|claims?|according\s+to|if|unless|whether|assuming|supposing|provided|believe\w*|think\w*|suspect\w*|doubt\w*|false|untrue|inaccurate)\b|\bnot\s+(?:saying|claiming|discussing)\b',text,re.I):return None
    # Pending, requested or withdrawn permission is not a positive grant. Keep
    # the entire qualified statement for NLI rather than clipping its qualifier.
    if re.search(r'\b(cancel\w*|withdraw\w*|revok\w*|request\w*|pending|unconfirm\w*|await\w*|expir\w*|laps\w*|deny\w*|deni\w*)\b',text,re.I):return None
    names={x.upper() for x in re.findall(r'\bTRN\d+\b',text,re.I)}
    if names!={actor.upper()}:return None
    pattern=(r'\s*(?:(?:And|But|So|Yet)\s+)?(?P<claim>'+re.escape(actor)+
        r'\s+(?:(?:has|holds|has\s+received|has\s+been\s+given)\s+(?:takeoff\s+clearance|clearance\s+to\s+take\s+off|permission\s+to\s+take\s+off)|is\s+cleared\s+for\s+takeoff))\b')
    match=re.match(pattern,text,re.I)
    if not match:return None
    start,end=match.span('claim')
    return dict(rule='unsupported-positive-takeoff-scope-v1',applied=True,
        reason='positive takeoff permission asserted outside explicit received representation scope',
        sourcePreconditions=scope,evidenceIds=scope['evidenceIds'],exactSentence=text,
        offendingSpan=dict(start=sentence['start']+start,end=sentence['start']+end,text=text[start:end]))


_TAKEOFF=r'take\s*-?\s*off'
_SCOPED_PERMISSION=(r'(?:(?:runway|takeoff|take-off)\s+(?:[\w-]+\s+)?(?:clearance|permission|authori[sz]ation)'
    r'|(?:clearance|permission|authori[sz]ation)\s+(?:to|for)\s+(?:'+_TAKEOFF+r'|takeoff|the\s+runway))')


def unsupported_takeoff_clause(sentence,scope):
    """v9 clause-level positive takeoff/runway permission in explicit scope.

    Same source precondition as v1: received target route sources explicitly
    represent no runway or takeoff clearance. The learner clause must
    affirmatively assert that permission for the single named target flight.
    Negation, modality, conditions, attribution, qualifiers or another flight
    leave the clause to ordinary NLI. Departure clearance alone is outside the
    source's explicit runway/takeoff wording and is not covered.
    """
    if not scope:return None
    text=sentence['text'];actor=re.escape(scope['flightInstance'])
    if text.rstrip().endswith('?') or nonassertive_scope(text):return None
    if re.search(r'["“”]|\b(other|another|else|said|says|claims?|according\s+to|if|unless|whether|assuming|supposing|provided|believe\w*|think\w*|suspect\w*|doubt\w*|false|untrue|inaccurate)\b|\bnot\s+(?:saying|claiming|discussing)\b',text,re.I):return None
    if re.search(r'\b(cancel\w*|withdraw\w*|revok\w*|expir\w*|laps\w*)\b',text,re.I):return None
    names={x.upper() for x in re.findall(r'\bTRN\d+\b',text,re.I)}
    if names!={scope['flightInstance'].upper()}:return None
    claims=[actor+r'\s+(?:also\s+)?(?:has|holds|now\s+has|has\s+(?:now\s+)?(?:received|obtained|been\s+(?:given|granted|issued))|was\s+(?:given|granted|issued)|received)\s+(?:a\s+|the\s+|its\s+)?'+_SCOPED_PERMISSION,
            actor+r'\s+(?:is|has\s+been|was)\s+(?:now\s+)?(?:cleared|authori[sz]ed|permitted|allowed|approved)\s+(?:for\s+(?:takeoff|'+_TAKEOFF+r')|to\s+'+_TAKEOFF+r')',
            r'(?:the\s+)?(?:tower|controller|atc|runway\s+controller)\s+(?:has\s+)?(?:now\s+)?(?:authori[sz]ed|cleared|permitted|allowed|approved)\s+'+actor+r'\s+(?:to\s+'+_TAKEOFF+r'|for\s+(?:takeoff|'+_TAKEOFF+r'))']
    opening=(r'[\s,;:]*(?:(?:and|but|so|yet|while|then|also|now)\s+)*'
             r'(?:(?:[\w\x27’-]+\s+){0,6}(?:confirms?|shows?|proves?|means?|establish(?:es)?|demonstrates?|indicates?)\s+that\s+)?')
    for clause in learner_clauses(sentence):
        body=clause['text']
        if re.search(r'\b(not|no|never|neither|nor|without|cannot|can|must|nothing|none|little|hardly|scarcely|barely|few|seldom|rarely|minimal|nobody|no-one|lack\w*|absen\w*|unclear|unknown|unverified|unestablished|fail\w*|refus\w*|assum\w*|suppos\w*|imagin\w*|hypothetical\w*|pending|request\w*|unconfirm\w*|await\w*|deny\w*|deni\w*|will|would|could|should|need\w*|requir\w*|once|until|when|before|after|expected|plan\w*|soon|yet)\b|n[’\x27]t\b',body,re.I):continue
        for claim in claims:
            # v10: the claim must end its clause; a trailing limiter or
            # restriction leaves the whole clause to ordinary NLI.
            match=re.match(opening+r'(?P<claim>'+claim+r')(?:\s+(?:now|already|too|also|as\s+well))?[\s.,;:!]*$',body,re.I)
            if not match:continue
            start=clause['start']-sentence['start']+match.start('claim');end=clause['start']-sentence['start']+match.end('claim')
            return dict(rule='unsupported-positive-takeoff-clause-v2',applied=True,
                reason='positive runway/takeoff permission asserted outside explicit received representation scope',
                sourcePreconditions=scope,evidenceIds=scope['evidenceIds'],exactSentence=text,exactClause=body,
                offendingSpan=dict(start=sentence['start']+start,end=sentence['start']+end,text=text[start:end]))
    return None


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
    learner={x.upper() for x in re.findall(r'\bTRN\d+\b',sentence,re.I)}
    source={x.upper() for x in re.findall(r'\bTRN\d+\b',report['message'],re.I)}
    # v9: a message without a flight name still belongs to its typed flight;
    # another flight's identical scope wording is not same-flight evidence.
    typed=(report.get('flightInstance') or '').upper()
    if learner and not source and typed and typed not in learner:return False
    return not learner or not source or bool(learner&source)


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
    # v9: a self-correction marker cannot switch identity when the learner
    # names exactly one flight; it stays ambiguous with competing identities.
    ambiguous=bool(re.search(r'\b(other|another|instead|said|says|quote)\b|[\"“”]',context_text,re.I)
        or (re.search(r'\b(correction|actually)\b',context_text,re.I) and len(names)!=1))
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
        # A colon starts a new explanatory clause: an earlier predicate cannot
        # license splitting a bare coordinated noun list after that colon.
        left_predicate_scope=left.rsplit(':',1)[-1]
        if ';' in match.group() or (re.search(predicate,left_predicate_scope,re.I) and re.search(predicate,right,re.I)):
            if at>boundaries[-1]:boundaries.append(at)
    boundaries.append(len(text));result=[]
    for start,end in zip(boundaries,boundaries[1:]):
        while start<end and text[start].isspace():start+=1
        while end>start and text[end-1].isspace():end-=1
        if end>start:result.append(dict(start=sentence['start']+start,end=sentence['start']+end,text=text[start:end],originalSentence=sentence['text']))
    return result


def nonassertive_scope(text):
    return bool(re.search(r'^\s*(?:if|unless|suppose|imagine|perhaps|maybe)\b|\b(?:not\s+(?:true|the\s+case)|(?:deny|denies|denying)\s+that)\b|\b(might|may|would|possibly)\b',text,re.I))


# Neutral epistemic/contrastive relation wording. It licenses a comparison;
# the classifier still decides direction, and nothing here asserts a value.
_EPISTEMIC_RELATION=(r'\b(?:tell\w*|evidence|indicat\w*|show\w*|guarantee\w*|demonstrat\w*|infer\w*|follow\w*|'
    r'confirmation|proof|neither|rather\s+than|instead\s+of|merely)\b|\bonly\s+(?:an?\s+)?estimate\b|'
    r'\b(?:not|no)\s+(?:a\s+|an\s+|the\s+|any\s+)?(?:[\w-]+\s+){0,2}(?:clearance|permission|authori[sz]ation)\b')

# An anaphoric opening (within the first three tokens) depends on an earlier
# learner statement. Detection never resolves meaning by itself.
_ANAPHOR_OPENING=(r'^\W*(?:(?:and|but|so|yet|while|whereas|even|together|still|also|then|now|however|thus|hence)\W+){0,3}'
    r'(?:it|its|they|them|their|that|this|these|those|the\s+former|the\s+latter|which|such)\b')


def anaphoric_opening(text):
    return bool(re.match(_ANAPHOR_OPENING,text,re.I))


def anaphoric_antecedents(unit,text):
    """Exact earlier learner sentences a sentence-initial anaphor can refer to.

    Walks back over at most two assertive sentences, stopping at the first one
    that is not itself anaphoric. Returns sentence spans; adds no fact.
    """
    sentences=learner_sentences(text)
    own=next((s for s in sentences if s['start']<=unit['start']<s['end']),None)
    if own is None or not anaphoric_opening(own['text']):return []
    previous=[s for s in sentences if s['end']<=own['start']];chain=[]
    while previous and len(chain)<2:
        candidate=previous.pop()
        if nonassertive_scope(candidate['text']) or candidate['text'].rstrip().endswith('?'):break
        chain.insert(0,candidate)
        if not anaphoric_opening(candidate['text']):break
    return chain if _antecedent_identity_safe(own['text'],[c['text'] for c in chain]) else []


def _antecedent_identity_safe(own,antecedents):
    """An antecedent may supply a flight only when that flight is unique.

    If the anaphoric sentence names its own flight, the antecedent supplies
    non-flight referents only (a stand, an update). Otherwise the antecedent
    text must name at most one flight, with no quotation or identity switch.
    """
    joined=' '.join(antecedents)
    if re.search(r'\b(other|another|instead|said|says|told|according\s+to|quote)\b|["“”]',joined+' '+own,re.I):return False
    if re.search(r'\bTRN\d+\b',own,re.I):return True
    return len({x.upper() for x in re.findall(r'\bTRN\d+\b',joined,re.I)})<=1


def relation_present(text,mode):
    has=lambda pattern:bool(re.search(pattern,text,re.I))
    topics=_topics(text)
    permission='permission' in topics
    relation=has(r'\b(mean\w*|impl\w*|prov\w*|establish\w*|grant\w*|giv\w*|give|confer\w*|permit\w*|authori[sz]\w*|confirm\w*|distinct|different|same|equivalent|because|so|following|after|despite)\b') or has(_EPISTEMIC_RELATION)
    if mode=='occupancy':
        # Waiting FOR a resource alone is not an occupancy assertion. It must
        # not hide a separate explicit predicate (including a relative clause)
        # that actually says which aircraft occupies that resource.
        return has(r'\boccup\w*\b') or (has(r'\b(?:at|in)\s+(?:stand\s+)?[A-Z]\d*\b') and not has(r'\bwait\w*\s+for\b'))
    if mode=='waiting_position':return has(r'\b(wait\w*|occup\w*|staging|inbound|already\s+at)\b') and ('stand' in topics or has(r'\bfor\s+[A-Z]\d*\b'))
    if mode=='baggage_delay':return 'baggage' in topics and has(r'\b(delay\w*|late\s+(?:baggage|bags?|batch)|waiting\s+(?:on|for)|holding\s+up|holds?\s+up|held\s+up|holding\s+(?:\w+\s+)?back)\b') and not has(r'\b(proves?|means?|impl\w*)\b')
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
    # v10: a takeoff-clearance scope facet needs clearance/permission wording;
    # readiness or bare "departure" wording alone is a different claim.
    if mode=='clearance_authority':return has(r'\b(clearance|permission|authori[sz]\w*|cleared|takeoff|take.off)\b') and relation
    if mode=='readiness_status':return has(r'\b(readiness|ready)\b') and has(r'\b(is|are|remains?|unconfirmed|confirm\w*|unknown|leave|leaves|establish\w*|show\w*|prov\w*)\b')
    if mode=='estimate':return 'time' in topics and has(r'\b\d{1,2}:\d{2}\b')
    if mode=='availability_status':return has(r'\b(available|availability|free)\b') and not has(r'\b(?:not|doesn[’\x27]t)\s+(?:establish|prove|confirm|mean|show)\b')
    if mode=='fuel_state':return 'fuel' in topics and has(r'\b(complete\w*|finished|done|pending|delayed|progress)\b')
    if mode=='service_relation':return {'fuel','baggage'}<=topics and (relation or has(r'\b(pending|delayed|outstanding|incomplete)\b'))
    if mode=='lvp_status':return 'lvp' in topics
    if mode=='safeguarding_status':
        # v10: only a prepositional source-of-inference mention ("infer ...
        # from that cancellation") refers back without asserting a status. Any
        # clause predicating a status of "that cancellation" stays a unit.
        given=re.sub(r'\bfrom\s+(?:the|that|this|the\s+same)\s+(?:cancellation|cancelled|canceled)\b',' ',text,flags=re.I)
        return bool(re.search(r'\bsafeguard\w*\b',given,re.I) or ('safeguarding' in _topics(given) and 'lvp' not in _topics(given)))
    if mode=='hold_status':return has(r'\bhold\b') and has(r'\b(releas\w*|lift\w*|held|remain\w*)\b')
    if mode=='movement_status':return 'movement' in topics and not (permission and not has(r'\b(hold|held|park\w*|mov\w*)\b'))
    raise ValueError('unsupported neutral relation')


def relation_units(sentence,mode):
    clauses=learner_clauses(sentence)
    relational={'clearance_authority','hold_change_link','authority_distinction','plan_availability_relation','stand_hold_link','service_relation','estimate_authority','readiness_authority'}
    candidates=list(clauses)
    if mode in {'readiness_authority','clearance_authority','authority_distinction','plan_availability_relation','service_relation','estimate_authority'}:
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
    if mode=='stand_hold_link':
        # The stand's intended aircraft and the released aircraft must match;
        # two correct but unrelated aircraft updates do not form this relation.
        for clause in learner_clauses(unit):
            if not re.search(r'\bhold\b',clause['text'],re.I) or not re.search(r'\b(releas\w*|lift\w*)\b',clause['text'],re.I):continue
            attached={x.upper() for x in re.findall(r'\bTRN\d+\b',clause['text'],re.I)}
            if len(attached)==1 and attached!=expected:return True
    names={x.upper() for x in re.findall(r'\bTRN\d+\b',unit['text'],re.I)}
    # In an obstruction clause, "its route" has the single named aircraft in
    # the same original causal sentence as antecedent. Do not attach globally.
    if not names and mode=='vehicle_obstruction' and re.search(r'\bits\s+(?:ground\s+)?route\b',unit['text'],re.I):
        names={x.upper() for x in re.findall(r'\bTRN\d+\b',unit.get('originalSentence',''),re.I)}
    if len(names)!=1 or names==expected:return False
    if re.search(r'\b(other|another|instead|correction|actually|said|says|not\s+TRN)\b|["“”]',unit.get('originalSentence',unit['text']),re.I):return False
    return True


def hold_reference_binding(unit,payload,current,evidence_ids):
    """Bind only an entity, never a hold state, from a unique local context."""
    original=unit.get('originalSentence',unit['text'])
    if nonassertive_scope(original) or re.search(r'["“”]|\b(other|another|else|someone|said|says|claims?|correction|actually)\b',original,re.I):return None
    match=re.search(r'\bthe\s+(?:(?:exercise|ground)\s+)?hold\b',unit['text'],re.I)
    if not match:return None
    names={x.upper() for x in re.findall(r'\bTRN\d+\b',original,re.I)}
    if len(names)!=1:return None
    actor=next(iter(names));question_names={x.upper() for x in re.findall(r'\bTRN\d+\b',payload['question'],re.I)}
    if question_names and actor not in question_names:return None
    reports=[r for r in current if r['id'] in evidence_ids and any(
        f['property'] in ('movement_status','movement_condition') and re.search(r'\bhold\b|\bheld\b',f['value'],re.I)
        for f in r.get('_typedFacts',[]))]
    if any(not r.get('flightInstance') for r in reports):return None
    holders={r.get('flightInstance','').upper() for r in reports if r.get('flightInstance')}
    if holders!={actor}:return None
    binding=dict(ruleVersion='unqualified-local-hold-entity-v1',flightInstance=actor,
        exactReference=match.group(),start=unit['start']+match.start(),end=unit['start']+match.end(),
        sourceReportIds=[r['id'] for r in reports],
        scope='entity reference only; supplies no hold state or authority')
    # The exercise label does not itself identify the hold kind. Resolve that
    # kind only from an explicit current movement-condition field for this actor.
    kind_sources=[f for r in reports for f in r.get('_typedFacts',[])
        if f['property']=='movement_condition' and f['status']=='current'
        and (f.get('flightInstance') or '').upper()==actor and re.search(r'\bground\s+hold\b',f['value'],re.I)]
    if re.search(r'\bexercise\s+hold\b',match.group(),re.I) and kind_sources:
        binding['holdKindAlias']=dict(ruleVersion='source-explicit-ground-hold-kind-v1',
            originalKind='exercise hold',canonicalKind='ground hold',
            sourceFactIds=[f['fact_id'] for f in kind_sources],exactSourceValues=[f['value'] for f in kind_sources],
            scope='hold kind only; supplies no released, held or permission status')
    return binding


def comparison_context(unit,text,payload,current,evidence_ids=()):
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
    if unit['text']!=original and (re.search(r'\bits\s+(?:ground\s+)?(?:route|hold)|\bthat\s+aircraft\b',unit['text'],re.I) or anaphoric_opening(unit['text'])):
        names={x.upper() for x in re.findall(r'\bTRN\d+\b',original,re.I)}
        if len(names)<=1 and not nonassertive_scope(original):antecedents.append(original)
    # v9: a sentence-initial anaphor ("It", "That", "Even together, those
    # updates") keeps its exact earlier learner antecedent sentence(s).
    cross=[s['text'] for s in anaphoric_antecedents(unit,text) if s['end']<=unit['start']]
    if not cross and re.match(r'\s*(?:Those|These|That|This)\s+(?:reports?|updates?|services?)\b',unit['text'],re.I):
        previous=[s for s in learner_sentences(text) if s['end']<=unit['start']]
        if previous and not nonassertive_scope(previous[-1]['text']):cross=[previous[-1]['text']]
    antecedents=cross+antecedents
    if antecedents:premise='Exact learner antecedent context: '+'\n'.join(antecedents)+'\nCompared exact learner clause (resource aliases disclosed separately): '+premise
    binding=hold_reference_binding(unit,payload,current,evidence_ids)
    if binding:
        kind=binding.get('holdKindAlias',{}).get('canonicalKind') or re.sub(r'^the\s+','',binding['exactReference'],flags=re.I)
        bound_reference=binding['flightInstance']+"'s "+kind
        premise=premise.replace(binding['exactReference'],bound_reference,1)
        binding['normalizedReference']=bound_reference
        entity=dict(entity or {},learnerExplicitFlight=binding['flightInstance'],holdReferenceBinding=binding)
    return premise,entity,ambiguous,aliases,antecedents


_RETRACTION=(r'\b(?:I\s+(?:had|got)\s+(?:th(?:ose|ese|at|is|em)|it|them|everything)(?:\s+two)?\s+(?:all\s+)?(?:the\s+)?(?:wrong|backwards|mixed\s+up|reversed|confused)'
    r'|(?:the\s+)?wrong\s+way\s+round|scratch\s+that|I\s+take\s+(?:that|it|this)\s+back|ignore\s+(?:that|this|what\s+I\s+(?:said|wrote))'
    r'|disregard\s+(?:that|this|what\s+I\s+(?:said|wrote)|my\s+(?:previous|earlier|last))|I\s+was\s+wrong|I\s+mixed\s+(?:them|those|these|it)\s+up'
    r'|(?:that|this|everything\s+above)\s+(?:was|is)\s+(?:wrong|incorrect|a\s+mistake))\b')


def explicit_retraction(text):
    """v10: an explicit retraction cue that does not restate content.

    Sentence-local review cannot know what was retracted, so earlier requested
    points lose their met/contradicted status and become uncertain. Only a
    sentence whose wording is the retraction itself (no restated content
    topic) qualifies; a correction that restates content is reviewed normally.
    """
    for sentence in learner_sentences(text):
        if sentence['text'].rstrip().endswith('?') or nonassertive_scope(sentence['text']):continue
        match=re.search(_RETRACTION,sentence['text'],re.I)
        if not match:continue
        remainder=re.sub(_RETRACTION,' ',sentence['text'],flags=re.I)
        if _topics(remainder) or re.search(r'\bTRN\d+\b|\d{1,2}:\d{2}',remainder,re.I):continue
        return dict(rule='explicit-retraction-uncertainty-v1',applied=True,start=sentence['start'],end=sentence['end'],
            exactSentence=sentence['text'],reason='explicit retraction without restated content; earlier requested points are not reliably asserted',
            affectedCriteria=[])
    return None


def anaphoric_windows(sentences,text,mode):
    """Exact two-sentence windows joining an anaphoric sentence to its
    immediately preceding assertive antecedent, when the window as a whole
    expresses the neutral relation. Literal substrings; nothing is rewritten."""
    windows=[]
    for previous,current in zip(sentences,sentences[1:]):
        if not anaphoric_opening(current['text']):continue
        if nonassertive_scope(previous['text']) or previous['text'].rstrip().endswith('?'):continue
        if not _antecedent_identity_safe(current['text'],[previous['text']]):continue
        window=dict(start=previous['start'],end=current['end'],text=text[previous['start']:current['end']],anaphoricWindow=True)
        window['originalSentence']=window['text']
        if relation_present(window['text'],mode):windows.append(window)
    return windows


def point_quote_span(facet_witnesses):
    """Choose one literal display quote for a point from per-facet witnesses.

    Every facet keeps its own verified witness in the audit. The display quote
    covers as many facet witnesses as fit the unchanged 160-character field,
    then prefers the shortest span; it never widens or rewrites a witness.
    """
    import itertools
    best=None
    for choice in itertools.product(*facet_witnesses):
        start=min(w['start'] for w in choice);end=max(w['end'] for w in choice)
        if end-start<=160:
            key=(-len(choice),end-start,start)
            if best is None or key<best[0]:best=(key,(start,end),len(choice))
    if best:return best[1],None
    # No single span covers every facet: quote the most facets that fit.
    for size in range(len(facet_witnesses)-1,0,-1):
        for subset in itertools.combinations(facet_witnesses,size):
            for choice in itertools.product(*subset):
                start=min(w['start'] for w in choice);end=max(w['end'] for w in choice)
                if end-start<=160:
                    key=(-size,end-start,start)
                    if best is None or key<best[0]:best=(key,(start,end),size)
        if best:break
    if not best:return (facet_witnesses[0][0]['start'],facet_witnesses[0][0]['end']),None
    return best[1],dict(rule='per-facet-quote-witness-v1',applied=True,
        reason='combined facet witnesses exceed the display quote field; each facet keeps its own exact witness',
        facetWitnesses=[dict(start=w[0]['start'],end=w[0]['end'],text=w[0]['text']) for w in facet_witnesses],
        quotedFacetCount=best[2],facetCount=len(facet_witnesses))


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
            units.extend(w for w in anaphoric_windows(sentences,text,mode) if not any((u['start'],u['end'])==(w['start'],w['end']) for u in units))
            expected_names={x.upper() for x in re.findall(r'\bTRN\d+\b',hypothesis,re.I)}
            target_present=any(expected_names and expected_names<={x.upper() for x in re.findall(r'\bTRN\d+\b',unit['text'],re.I)} for unit in units)
            for sentence in units:
                unit_names={x.upper() for x in re.findall(r'\bTRN\d+\b',sentence['text'],re.I)}
                if target_present and len(unit_names)==1 and unit_names.isdisjoint(expected_names):
                    # An independently described other aircraft is extra content,
                    # not a replacement answer when the target is also stated.
                    continue
                premise,context,ambiguous,aliases,antecedents=comparison_context(sentence,text,payload,current,next(c['evidenceIds'] for c in payload['criteria'] if c['id']==cid))
                ambiguous=ambiguous or nonassertive_scope(sentence.get('originalSentence',sentence['text']))
                index=len(pairs)
                pairs.append(dict(kind='criterion',criterionId=cid,facet=number+1,premise=premise,hypothesis=hypothesis,
                                  exactLearnerSentence=sentence['text'],entityContext=context,ambiguousEntityContext=ambiguous,
                                  resourceAliases=aliases,exactLearnerAntecedents=antecedents))
                rule=None if sentence.get('anaphoricWindow') else rules.get(sentence['start'])
                rule_support=bool(rule and cid+'.'+str(number+1) in rule['supportedFacetIds'])
                identity_mismatch=explicit_identity_mismatch(sentence,hypothesis,mode)
                entry=dict(index=index,sentence=sentence,counter=None,ambiguous=ambiguous,ruleSupport=rule_support,identityMismatch=identity_mismatch)
                pairs[-1].update(neutralRelation=mode,explicitIdentityMismatch=identity_mismatch,anaphoricWindow=bool(sentence.get('anaphoricWindow')))
                pairs[-1]['semanticRuleSupport']=rule if rule_support else None
                counter=occupancy_counter_for(payload,cid,number)
                if _counter_eligible(sentence['text'],counter):
                    entry['counter']=len(pairs)
                    pairs.append(dict(kind='exclusive_counter',criterionId=cid,facet=number+1,
                                      premise=sentence['text'],hypothesis=counter['hypothesis']))
                facets[key].append(entry)
    bundle_ids=set(rid for c in payload['criteria'] if c['id']!='grounding' for rid in c['evidenceIds'])
    active_bundle=[r for r in current if r['id'] in bundle_ids]
    absence=unreported_readiness(current,payload.get('aircraftId'))
    takeoff_scope=explicit_unrepresented_takeoff_scope(current,payload.get('aircraftId'))
    readiness_rules={}
    for original in sentences:
        rule=unsupported_readiness_assertion(original,absence) or unsupported_takeoff_assertion(original,takeoff_scope) or unsupported_takeoff_clause(original,takeoff_scope)
        if rule:readiness_rules[original['start']]=rule;scorer.semantic_rule_audit.append(rule)
    plans=[]
    for original in sentences:
        clauses=learner_clauses(original)
        full_rule=rules.get(original['start']);ready_rule=readiness_rules.get(original['start'])
        full_decision=True
        plans.append((original,full_decision,full_rule,ready_rule,'full_sentence'))
        if len(clauses)>1:
            for k,clause in enumerate(clauses):
                if k and anaphoric_opening(clause['text']):
                    # v9: an anaphoric clause is checked with its exact
                    # antecedent clause; the full sentence is always checked.
                    start=clauses[k-1]['start'];end=clause['end']
                    if (start,end)==(original['start'],original['end']):continue
                    clause=dict(start=start,end=end,text=text[start:end],originalSentence=original['text'])
                    plans.append((clause,True,full_rule,None,'anaphoric_clause_window'))
                else:plans.append((clause,True,full_rule,None,'independent_clause'))
    for sentence,decision,full_rule,ready_rule,coverage in plans:
        is_history=bool(re.search(r'\b(earlier|previously|previous|prior|formerly|before|used to)\b',sentence['text'],re.I))
        topics=_topics(sentence['text'])
        relevant=[r for r in current if topics.intersection(_topics(r['message'])) and _same_flight_context(sentence['text'],r)]
        groups=[]
        if active_bundle:groups.append(('raw',active_bundle))
        if relevant:groups.append(('raw',relevant))
        groups.extend(('raw',[r]) for r in relevant)
        if active_bundle:groups.append(('normalized',active_bundle))
        if relevant:groups.append(('normalized',relevant))
        if not groups:groups=[('raw',current),('normalized',current)]
        seen=set();entries=[]
        for variant,reports in groups:
            ids=tuple(r['id'] for r in reports)
            if (variant,ids) in seen:continue
            seen.add((variant,ids))
            if variant=='raw':premise='\n'.join(r['message'] for r in reports)
            else:
                premise=('Evidence policy: only information established by received reports is confirmed; '
                         'unreported information remains unconfirmed, not denied. Source excerpts for this comparison:\n'
                         +'\n'.join(source_text(r) for r in reports))
            used=list(ids)
            closed_scope=absence if variant=='normalized' else None
            if closed_scope:
                premise+='\nClosed current typed-field search: '+closed_scope['proposition']
                used.extend(closed_scope['reportIds'])
            if is_history:
                premise+='\n'+'\n'.join('Non-current historical source (event '+str(r['eventTime'])+'; received '+str(r['receiptTime'])+'): '+source_text(r) for r in historical)
                used.extend(r['id'] for r in historical)
            entries.append(dict(index=len(pairs),reportIds=list(dict.fromkeys(used)),resolvedSupportOnly=False,
                conflictVeto=variant=='raw' and bool(relevant) and ids==tuple(r['id'] for r in relevant)))
            pairs.append(dict(kind='grounding',premise=premise,hypothesis=sentence['text'],reportIds=list(dict.fromkeys(used)),
                sourceVariant=variant,groundingCoverage=coverage,contributesToDecision=decision,
                conservativeHistoricalUncertainty=is_history,
                sourceFactIds=[f['fact_id'] for r in reports for f in r.get('_typedFacts',[])] if variant=='normalized' else [],
                canonicalSources=[canonical_source(f) for r in reports for f in r.get('_typedFacts',[]) if canonical_source(f)] if variant=='normalized' else [],
                closedReadinessScope=closed_scope))
        chain=anaphoric_antecedents(sentence,text) if coverage=='full_sentence' else []
        if chain and active_bundle:
            # v9: support-only comparison of the exact learner window from the
            # antecedent through this anaphoric sentence. It cannot veto or
            # turn a neutral check into a contradiction; ordinary checks stay.
            window=text[chain[0]['start']:sentence['end']]
            for variant in ('raw','normalized'):
                premise='\n'.join(r['message'] for r in active_bundle) if variant=='raw' else (
                    'Evidence policy: only information established by received reports is confirmed; '
                    'unreported information remains unconfirmed, not denied. Source excerpts for this comparison:\n'
                    +'\n'.join(source_text(r) for r in active_bundle))
                used=[r['id'] for r in active_bundle]
                if variant=='normalized' and absence:
                    premise+='\nClosed current typed-field search: '+absence['proposition'];used.extend(absence['reportIds'])
                entries.append(dict(index=len(pairs),reportIds=list(dict.fromkeys(used)),conflictVeto=False,resolvedSupportOnly=True))
                pairs.append(dict(kind='grounding',premise=premise,hypothesis=window,reportIds=list(dict.fromkeys(used)),
                    sourceVariant=variant,groundingCoverage='anaphoric_antecedent_window',contributesToDecision=True,
                    supportOnly=True,focusSentence=sentence['text'],conservativeHistoricalUncertainty=is_history,
                    sourceFactIds=[f['fact_id'] for r in active_bundle for f in r.get('_typedFacts',[])] if variant=='normalized' else [],
                    canonicalSources=[],closedReadinessScope=absence if variant=='normalized' else None))
        grounding.append(dict(sentence=sentence,entries=entries,history=is_history,rule=full_rule,
                              readinessRule=ready_rule,decision=decision))
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
        facet_results[key]=(label,sorted(witnesses,key=lambda s:(len(s['text']),s['start'])))
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
            if any(not w for _,w in needed):raise ValueError('no bounded NLI quotation witness')
            span,audit=point_quote_span([w for _,w in needed])
            quote=text[span[0]:span[1]]
            if len(quote)>160:raise ValueError('NLI quotation witness span too wide')
            if audit:audit.update(criterionId=cid,status=status);scorer.semantic_rule_audit.append(audit)
        comment={'met':'Your stated meaning supports this point.','missing':'At least one required point is not expressed.',
                 'contradicted':'Your stated meaning conflicts with this point.','uncertain':'The meaning needs clarification.'}[status]
        points.append(dict(criterionId=cid,status=status,comment=comment,evidenceIds=list(dict.fromkeys(criterion['evidenceIds'])),learnerQuote=quote))
    checks=[]
    for item in grounding:
        if not item['decision']:continue
        entries=item['entries'];support=[e for e in entries if labels[e['index']]=='entailment']
        veto=next((e for e in entries if e['conflictVeto'] and labels[e['index']]=='contradiction'),None)
        if item['readinessRule']:
            status='contradicted';chosen=dict(index=None,reportIds=item['readinessRule']['evidenceIds'],semanticRule=item['readinessRule'])
        elif item['rule']:
            # This audited rule checks the COMPLETE original sentence against
            # typed current service states; raw NLI comparisons remain saved.
            status='met';chosen=dict(index=None,reportIds=item['rule']['evidenceIds'],semanticRule=item['rule'])
        elif support and veto:status='uncertain';chosen=veto
        elif support:status='uncertain' if item['history'] else 'met';chosen=min(support,key=lambda e:len(pairs[e['index']]['premise']))
        elif veto:status='contradicted';chosen=veto
        elif all(labels[e['index']] in ('neutral','contradiction') for e in entries if not e['resolvedSupportOnly']):status='contradicted';chosen=entries[0]
        else:status='uncertain';chosen=entries[0]
        selected_span=item['readinessRule']['offendingSpan'] if item['readinessRule'] else item['sentence']
        checks.append(dict(status=status,sentence=selected_span,pair=chosen))
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
    retraction=explicit_retraction(text)
    if retraction:
        scorer.semantic_rule_audit.append(retraction)
        for point in points:
            if point['criterionId']=='grounding' or point['status'] not in ('met','contradicted'):continue
            start=text.find(point['learnerQuote'])
            if start>=0 and start+len(point['learnerQuote'])<=retraction['start']:
                retraction['affectedCriteria'].append(dict(criterionId=point['criterionId'],originalStatus=point['status']))
                point.update(status='uncertain',comment='The meaning needs clarification.',learnerQuote='')
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
