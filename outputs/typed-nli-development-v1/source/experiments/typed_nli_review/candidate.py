"""Isolated discriminative NLI development candidate; production never imports it.

NLI confidence is fallible semantic evidence, not a correctness certificate.
Citations are authored comparison context; they do not prove the NLI judgment.
"""
import json
import re
import time
from backend.training_assessment import validate_review
from experiments.typed_nli_review.propositions import propositions_for

VERSION = 'discriminative-nli-review-v1'
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


def evaluate(payload, scorer, deadline):
    """scorer.score(pairs, deadline) returns auditable probability rows in order."""
    validate_input(payload)  # Must run before any tokenization/model operation.
    current, historical = grounding_context(payload)
    propositions = propositions_for(payload)
    text = payload['learnerResponse']; sentences = learner_sentences(text)
    # A complete short response is also an exact quotation witness when pronouns
    # or conjunctions require cross-sentence context.
    witnesses = list(sentences)
    if len(text) <= 160 and not any(s['text'] == text for s in witnesses):
        witnesses.append(dict(start=0, end=len(text), text=text))
    pairs = []; facet_pairs = {}; witness_pairs = {}; grounding_pairs = []
    for cid, hypotheses in propositions.items():
        for number, hypothesis in enumerate(hypotheses):
            key = (cid, number)
            facet_pairs[key] = len(pairs)
            pairs.append(dict(kind='criterion', criterionId=cid, facet=number+1, premise=text, hypothesis=hypothesis))
            witness_pairs[key] = []
            for witness in witnesses:
                witness_pairs[key].append((len(pairs), witness))
                pairs.append(dict(kind='quotation_witness', criterionId=cid, facet=number+1,
                                  premise=witness['text'], hypothesis=hypothesis))
    for sentence in sentences:
        is_history = bool(re.search(r'\b(earlier|previously|previous|prior|formerly|before|used to)\b', sentence['text'], re.I))
        premise = '\n'.join(r['message'] for r in current)
        if is_history:
            premise += '\n'+'\n'.join('Earlier superseded report (event '+str(r['eventTime'])+'; received '+str(r['receiptTime'])+'): '+r['message'] for r in historical)
        grounding_pairs.append((len(pairs), sentence, is_history))
        pairs.append(dict(kind='grounding', premise=premise, hypothesis=sentence['text'],
                          reportIds=[r['id'] for r in current]+([r['id'] for r in historical] if is_history else []),
                          conservativeHistoricalUncertainty=is_history))
    if time.monotonic() >= deadline: raise TimeoutError('shared NLI review deadline')
    rows = scorer.score(pairs, deadline)
    if len(rows) != len(pairs): raise ValueError('NLI pair coverage')
    labels = [confident_label(row) for row in rows]
    if time.monotonic() >= deadline: raise TimeoutError('shared NLI review deadline')
    points = []
    for criterion in payload['criteria']:
        cid = criterion['id']
        if cid == 'grounding': continue
        keys = [(cid, i) for i in range(len(propositions[cid]))]
        values = [labels[facet_pairs[k]] for k in keys]
        status = ('contradicted' if 'contradiction' in values else 'met' if all(v=='entailment' for v in values)
                  else 'missing' if 'neutral' in values else 'uncertain')
        quote = ''
        if status in ('met','contradicted'):
            needed = keys if status == 'met' else [next(k for k in keys if labels[facet_pairs[k]]=='contradiction')]
            spans = []
            for key in needed:
                label = 'entailment' if status == 'met' else 'contradiction'
                eligible = [(index,w) for index,w in witness_pairs[key] if labels[index] == label and len(w['text']) <= 160]
                if not eligible: raise ValueError('no bounded NLI quotation witness')
                _, chosen = min(eligible, key=lambda x: (len(x[1]['text']),x[1]['start']))
                spans.append(chosen)
            quote = text[min(s['start'] for s in spans):max(s['end'] for s in spans)]
            if len(quote)>160: raise ValueError('NLI quotation witness span too wide')
        comment = {'met':'Your stated meaning supports this point.', 'missing':'At least one required point is not expressed.',
                   'contradicted':'Your stated meaning conflicts with this point.', 'uncertain':'The meaning needs clarification.'}[status]
        points.append(dict(criterionId=cid,status=status,comment=comment,evidenceIds=list(dict.fromkeys(criterion['evidenceIds'])),learnerQuote=quote))
    unsafe = next(((i,s) for i,s,h in grounding_pairs if labels[i] in ('neutral','contradiction')), None)
    unclear = next(((i,s) for i,s,h in grounding_pairs if labels[i]=='uncertain' or h), None)
    chosen = unsafe or unclear or (grounding_pairs[0][0],grounding_pairs[0][1])
    status = 'contradicted' if unsafe else 'uncertain' if unclear else 'met'
    quote = chosen[1]['text']
    if len(quote)>160: raise ValueError('grounding quotation witness too wide')
    criterion = next(c for c in payload['criteria'] if c['id']=='grounding')
    grounding_ids = [rid for rid in pairs[chosen[0]]['reportIds'] if rid in criterion['evidenceIds']]
    if not grounding_ids: raise ValueError('no eligible grounding comparison source')
    points.append(dict(criterionId='grounding',status=status,
        comment='Not established by the received reports.' if unsafe else 'This passage needs clarification.' if unclear else 'Your claims agree with the received reports.',
        evidenceIds=list(dict.fromkeys(grounding_ids)),learnerQuote=quote))
    met=sum(p['status']=='met' for p in points)
    verdict='needs_review' if any(p['status']=='contradicted' for p in points) else 'supported' if met==len(points) else 'partly_supported' if met else 'needs_review'
    result=dict(episodeId=payload['episodeId'],checkpointId=payload['checkpointId'],verdict=verdict,
                explanation='Compare your stated meanings with the received reports.',points=points)
    accepted=validate_review(json.dumps(result),payload)
    if time.monotonic()>=deadline: raise TimeoutError('shared NLI review deadline')
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
