"""Isolated discriminative NLI development candidate; production never imports it.

NLI confidence is fallible semantic evidence, not a correctness certificate.
Citations are authored comparison context; they do not prove the NLI judgment.
"""
import json
import re
import time
from backend.training_assessment import validate_review
from experiments.typed_nli_review.propositions import propositions_for,relevance_for,TOPIC_PATTERNS,occupancy_counter_for

VERSION = 'discriminative-nli-review-v2'
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
    """Remove only wholly superseded messages; partial messages must withhold."""
    reports = payload['reports']
    replaced = set()
    for report in reports:
        for fact in report.get('facts', []):
            replaced.update(fact.get('supersedes', []))
    current = []; historical = []
    for report in reports:
        facts = report.get('facts', [])
        old = [report['id']+':'+f['property'] in replaced for f in facts]
        if any(old) and not all(old):
            raise ValueError('partially superseded report requires clause-level evidence')
        if old and all(old):
            historical.append(report)
        else:
            current.append(report)
    return current, historical


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
    names={x.upper() for x in re.findall(r'\bTRN\d+\b',text,re.I)}
    local=set(re.findall(r'\bTRN\d+\b',sentence['text'],re.I))
    if local:return sentence['text'],None,False
    needs=bool(_topics(sentence['text']) & {'fuel','baggage','movement','permission','stand','time'})
    if not needs:return sentence['text'],None,False
    ambiguous=bool(re.search(r'\b(other|another|instead|correction|actually|said|says|quote)\b|[\"“”]',text,re.I))
    scope={r.get('flightInstance').upper() for r in payload['reports'] if r['id'] in {rid for c in payload['criteria'] if c['id']!='grounding' for rid in c['evidenceIds']} and r.get('flightInstance')}
    identity_denial=bool(re.search(r'\bnot\s+(?:discussing|referring\s+to|talking\s+about|about)\s+TRN\d+|\bdo\s+not\s+mean\s+TRN\d+|\baccording\s+to\b|\b(claimed|speaker|told)\b',text,re.I))
    affirmative_anchor=any(re.search(r'\bTRN\d+\b',s['text'],re.I) and bool(_topics(s['text'])) for s in learner_sentences(text))
    if len(names)==1 and not ambiguous and not identity_denial and affirmative_anchor and (not scope or next(iter(names)) in scope):
        context={'learnerExplicitFlight':next(iter(names)),'origin':'unique explicit learner flight; no operational fact added'}
        return 'Flight explicitly named elsewhere by the learner: '+next(iter(names))+'.\nExact learner sentence: '+sentence['text'],context,False
    return sentence['text'],None,bool(names or re.search(r'\b(it|its|they|their)\b',sentence['text'],re.I))


def evaluate(payload, scorer, deadline):
    """V2: exact sentence-local NLI, neutral relevance, conflict-safe aggregation."""
    validate_input(payload)
    current,historical=grounding_context(payload)
    _check_current_conflicts(current)
    propositions=propositions_for(payload);relevance=relevance_for(payload)
    text=payload['learnerResponse'];sentences=learner_sentences(text)
    pairs=[];facets={};grounding=[]
    for cid,hypotheses in propositions.items():
        for number,hypothesis in enumerate(hypotheses):
            key=(cid,number);facets[key]=[]
            for sentence in sentences:
                if not _topics(sentence['text']).intersection(relevance[cid][number]):continue
                premise,context,ambiguous=_sentence_context(sentence,text,payload)
                index=len(pairs)
                pairs.append(dict(kind='criterion',criterionId=cid,facet=number+1,premise=premise,hypothesis=hypothesis,
                                  exactLearnerSentence=sentence['text'],entityContext=context,ambiguousEntityContext=ambiguous))
                entry=dict(index=index,sentence=sentence,counter=None,ambiguous=ambiguous)
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
            premise='\n'.join(r['message'] for r in reports)
            used=list(ids)
            if is_history:
                premise+='\n'+'\n'.join('Earlier superseded report (event '+str(r['eventTime'])+'; received '+str(r['receiptTime'])+'): '+r['message'] for r in historical)
                used.extend(r['id'] for r in historical)
            entries.append(dict(index=len(pairs),reportIds=used,
                # Only the combined relevant source group is a semantic conflict
                # veto. An unrelated individual report cannot override support.
                conflictVeto=bool(relevant) and ids==tuple(r['id'] for r in relevant)))
            pairs.append(dict(kind='grounding',premise=premise,hypothesis=sentence['text'],reportIds=used,
                              conservativeHistoricalUncertainty=is_history))
        grounding.append(dict(sentence=sentence,entries=entries,history=is_history))
    if time.monotonic()>=deadline:raise TimeoutError('shared NLI review deadline')
    rows=scorer.score(pairs,deadline)
    if len(rows)!=len(pairs):raise ValueError('NLI pair coverage')
    labels=[confident_label(row) for row in rows]
    if time.monotonic()>=deadline:raise TimeoutError('shared NLI review deadline')
    facet_results={}
    for key,entries in facets.items():
        results=[]
        for entry in entries:
            label='uncertain' if entry['ambiguous'] else labels[entry['index']]
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
        if support and veto:status='uncertain';chosen=veto
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
