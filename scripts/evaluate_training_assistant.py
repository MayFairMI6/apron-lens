"""Bounded development comparison of the live training selector, not frozen research.
Run: python -m scripts.evaluate_training_assistant --output outputs/assistant-comparison/run.json
Stop the local training server first to avoid a second model allocation.
"""
import argparse
from collections import Counter
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import uuid

from backend.conversation.state import SessionState
from backend.conversation.context import snapshot
from backend.lessons import build_lesson
from backend.training_adapter_v5 import TrainingAdapter, TRAINING_PROMPT_VERSION
from backend.training_turn import run_turn
from modelaccess.contract import Settings

VERSION = 'training-comparison-v1'
CONDITIONS = ('lexical_history', 'selector_no_history', 'selector_history')

def suite():
    # Authored expectations are scoring-only; never included in inference prompts.
    def case(t, q, flight, required=(), unknowns=()):
        return dict(cutoff=t, question=q, flight=flight, required=dict(required), unknowns=list(unknowns))
    return {
        'surface_conflict': [
            case(40, 'Why is TRN102 holding?', 'TRN102', [('movement_condition','hold: vehicle obstructing ground route')]),
            case(80, 'Is its ground route still reported obstructed?', 'TRN102', [('movement_condition','hold: vehicle obstructing ground route')]),
            case(103.999, 'Has its ground hold been released?', 'TRN102', [('movement_condition','hold: vehicle obstructing ground route')]),
            case(104, 'Has its ground hold been released now?', 'TRN102', [('movement_condition','exercise ground hold released')]),
            case(105, 'Does that establish its overall departure readiness?', 'TRN102', unknowns=['overall_readiness']),
            case(106, 'I mean TRN101 instead. Is its fuel service complete?', 'TRN101', unknowns=['fuel_status']),
        ],
        'late_arrival': [
            case(40, 'Why is TRN103 waiting for Stand B?', 'TRN103', [('movement_condition','hold: Stand B occupied by TRN102')]),
            case(120, 'Is that stand confirmed available for it yet?', 'TRN103', [('movement_condition','hold: Stand B occupied by TRN102')]),
            case(133.999, 'Has its stand been confirmed available now?', 'TRN103', [('movement_condition','hold: Stand B occupied by TRN102')]),
            case(134, 'Has its stand been confirmed available now?', 'TRN103', [('movement_condition','Stand B available; exercise ground hold released')]),
            case(136, 'Does that establish its overall departure readiness?', 'TRN103', unknowns=['overall_readiness']),
            case(137, 'I mean TRN101 instead. Is its fuel service complete?', 'TRN101', unknowns=['fuel_status']),
        ],
        'late_baggage': [
            case(60, 'What is the reported baggage status for TRN102?', 'TRN102', [('baggage_status','delayed')]),
            case(81.999, 'What is its latest target off-block estimate?', 'TRN102', [('tobt','10:20')]),
            case(82, 'What is its latest target off-block estimate now?', 'TRN102', [('tobt','10:35')]),
            case(134, 'Has its baggage loading finished now?', 'TRN102', [('baggage_status','complete')]),
            case(159, 'Do these updates establish its overall departure readiness?', 'TRN102', unknowns=['overall_readiness']),
            case(160, 'I mean TRN101 instead. Is its fuel service complete?', 'TRN101', unknowns=['fuel_status']),
        ]}

def tokens(text):
    return re.findall(r'[a-z0-9]+', text.lower().replace('_',' '))

def lexical_prompt(prompt, limit=6):
    """Transparent TF-IDF overlap baseline, stable receipt/id tie-breaks.

    Same eligible pool and intent history; only top-k facts reach the selector.
    It is deliberately not called BM25 or a reproduction of published GraphRAG.
    """
    prefix, tail = prompt.split('Candidate flights and received facts: ', 1)
    candidates, end = json.JSONDecoder().raw_decode(tail)
    question = tail[end:].removeprefix('\nUser: ')
    memory, _ = json.JSONDecoder().raw_decode(prefix.split('Memory: ',1)[1])
    query = set(tokens(question))
    ref = memory.get('currentReferent')
    if ref: query.update(tokens(ref['flightInstance']))
    docs = [(c, f, set(tokens(c['flightInstance']+' '+f['property']+' '+f['value'])))
            for c in candidates for f in c['facts']]
    df = Counter(w for _,_,words in docs for w in words)
    def rank(row):
        _, f, words = row
        score = sum(math.log(1+len(docs)/(1+df[w])) for w in query & words)
        return (-score, -f['receiptTime'], f['fact_id'])
    chosen = {f['fact_id'] for _, f, _ in sorted(docs,key=rank)[:limit]}
    for c in candidates: c['facts'] = [f for f in c['facts'] if f['fact_id'] in chosen]
    return prefix+'Candidate flights and received facts: '+json.dumps(candidates)+tail[end:]

class ComparisonAdapter(TrainingAdapter):
    condition = 'selector_history'
    def _generate(self, request, effective):
        if self.condition == 'lexical_history':
            request = replace(request, messages=(('user',lexical_prompt(request.messages[0][1])),))
        return super()._generate(request,effective)

def score(result, world, case):
    try: p = json.loads(result.get('rawModelOutput',''))
    except (ValueError,TypeError): p = {}
    if not isinstance(p,dict): p = {}
    claims = p.get('claims',[]) if isinstance(p.get('claims'),list) else []
    ref = p.get('referent') or {}
    expected = dict(aircraftId='A'+case['flight'][-1],flightInstance=case['flight'])
    facts = {f['fact_id']: f for f in snapshot(world,expected['aircraftId'],case['flight'],case['cutoff'])['facts']}
    identity = ref == expected
    citations = bool(claims) and all(isinstance(c,dict) and c.get('fact_id') in facts and
        c.get('evidence_ids') == [facts[c['fact_id']]['event_id']] for c in claims)
    supported = all(isinstance(c,dict) and c.get('fact_id') in facts and
        c.get('value') == facts[c['fact_id']]['value'] and c.get('status') == facts[c['fact_id']]['status']
        for c in claims)
    selected = {facts[c['fact_id']]['property']:c.get('value') for c in claims
                if isinstance(c,dict) and c.get('fact_id') in facts and c.get('status')=='current'}
    complete = all(selected.get(k)==v for k,v in case['required'].items())
    unknowns = p.get('unknowns',[])
    uncertainty = isinstance(unknowns,list) and set(unknowns)==set(case['unknowns'])
    stale = any(isinstance(c,dict) and c.get('status')!='current' for c in claims)
    accepted = bool(result.get('accepted'))
    passed = accepted and identity and supported and complete and uncertainty and not stale and (not claims or citations)
    return dict(passed=passed, accepted=accepted, identityCorrect=identity, claimsSupported=supported,
                complete=complete, unknownsCorrect=uncertainty, citationValid=citations if claims else None,
                staleClaims=stale, emptyAnswer=not claims and not unknowns,
                errors=result.get('errors',[]))

def validate_cases():
    for exercise,cases in suite().items():
        world,_,_=build_lesson(17,exercise)
        for c in cases:
            facts=snapshot(world,'A'+c['flight'][-1],c['flight'],c['cutoff'])['facts']
            current={f['property']:f['value'] for f in facts if f['status']=='current'}
            assert all(current.get(k)==v for k,v in c['required'].items()), (exercise,c)
            assert not set(c['unknowns']) & current.keys()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--validate-only',action='store_true')
    args=parser.parse_args();validate_cases()
    if args.validate_only: print('18 scoring cases match report cutoffs');return
    if args.output.exists():raise SystemExit('Refusing to overwrite a run')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    adapter=ComparisonAdapter('qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=args.output.with_suffix('.prompts.jsonl'))
    adapter.load();settings=Settings(adapter.served_model,768,image_max_side=672)
    report=dict(version=VERSION,promptVersion=TRAINING_PROMPT_VERSION,seed=17,textOnly=True,
        studyType='authored development comparison; not held-out or learning-gain evaluation',
        sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        suiteSha256=hashlib.sha256(json.dumps(suite(),sort_keys=True).encode()).hexdigest(),
        runtime=adapter.run_metadata(),records=[],completed=False,
        stopReasonLimitation='Local adapter infers stop/length from output count; actual engine stop reason unavailable.')
    for condition in CONDITIONS:
        adapter.condition=condition
        for exercise,cases in suite().items():
            world,_,_=build_lesson(17,exercise)
            session=SessionState(uuid.uuid4().hex)
            for index,case in enumerate(cases):
                if condition=='selector_no_history': session=SessionState(uuid.uuid4().hex)
                turn=dict(requestId=uuid.uuid4().hex,turnId=str(index),expectedRevision=session.revision,
                          aircraftId=None,flightInstance=None,cutoff=case['cutoff'],question=case['question'])
                result=run_turn(session,world,turn,adapter,settings)
                record=dict(condition=condition,exercise=exercise,turn=index,case=case,result=result,score=score(result,world,case))
                report['records'].append(record)
                args.output.write_text(json.dumps(report,indent=2)+'\n')
                print(json.dumps(dict(condition=condition,exercise=exercise,turn=index,score=record['score'],latency=result['latencySeconds'])),flush=True)
    report['completed']=True
    report['summary']={condition:dict(passed=sum(r['score']['passed'] for r in report['records'] if r['condition']==condition),total=18)
                       for condition in CONDITIONS}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary']),flush=True)

if __name__=='__main__': main()
