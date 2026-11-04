"""Bounded exposed NLI probe matrix; no review statuses or acceptance claims.

Running this script performs actual pinned MPS inference. build_pairs() is pure
fixture-to-pair construction and can be inspected/tested without loading weights.
The builder never opens fresh-v3 or any reserve draft.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.typed_relation_review.candidate import grounding_context
from experiments.typed_relation_review.redesign import question_answer
from modelaccess.nli import PairClassifier,MODEL_ID,MODEL_REVISION,LABELS

VERSION='exposed-lean-nli-probe-matrix-v2'
DEADLINE_SECONDS=55.
FIXTURES=(ROOT/'outputs/compact-review-development-v2/records.jsonl',
          ROOT/'experiments/typed_relation_review/development-v1.json')


def build_pairs():
    old=[json.loads(line)['payload'] for line in FIXTURES[0].read_text().splitlines()]
    dev=[c['payload'] for c in json.loads(FIXTURES[1].read_text())['cases']]
    if len(old)!=6 or len(dev)!=24:raise ValueError('unexpected exposed fixtures')
    pairs=[]
    def add(family,control,premise,hypothesis,variant,meaning,**metadata):
        expected=None
        # Labels are frozen only for unambiguous direct operational controls.
        # Topic/category/meta probes remain exploratory, without an accuracy
        # denominator or an assumption that this classifier understands them.
        if family=='omission-versus-opposite' and variant!='answer_only_mention':
            expected={'procedures-only':'neutral','hold-stated':'entailment','release-stated':'contradiction','unrelated':'neutral'}[control]
        elif family=='identity-presupposition' and variant!='answer_only_coverage':
            expected='entailment' if control=='aircraft-identified' else 'neutral'
        elif family=='correction-content-contrast':
            final_current=control in ('plain-current','correct-to-current')
            asserts_current=metadata['contentContrast'] in ('current-value','current-replaces-prior')
            expected='entailment' if final_current==asserts_current else 'contradiction'
        elif family=='source-clock':
            if control=='assert-pending-now' or control=='history-with-stale-current':expected='contradiction'
            elif control=='assert-confirmed-now':expected='entailment'
            elif control=='explicit-history':expected='entailment' if variant=='labelled_past_then_current' else 'neutral'
        elif family=='short-dialogue-context' and control=='explicit-unconfirmed' and variant!='answer_only_coverage':
            expected='entailment'
        pairs.append(dict(index=len(pairs),family=family,control=control,premise=premise,
            hypothesis=hypothesis,variant=variant,hypothesisMeaning=meaning,expectedLabel=expected,
            expectedInterpretation='Defined direct-content control; question context should preserve the same asserted meaning.' if expected else
                'Exploratory semantic/meta/category probe; no predefined accuracy claim.',**metadata))
    def sources(payload,attributed):
        current,_=grounding_context(payload)
        return '\n'.join(('Flight '+str(r.get('flightInstance'))+'; source '+str(r.get('source'))+': ' if attributed else '')+r['message'] for r in current)
    examples=[(0,'waiting-and-occupancy','Stand B is occupied by TRN102.','stand occupancy','The stand has an occupant, or its occupancy is unknown.'),
              (1,'valid-service-distinction','Fuel service for TRN102 is complete.','fuel service','Fuel service has a reported status.'),
              (2,'omitted-aircraft-hold','TRN101 remains held.','aircraft hold status','An aircraft is held, released, or has an unknown hold status.'),
              (3,'wrong-stand-occupant','Stand B is occupied by TRN102.','stand occupancy','The stand has an occupant, or its occupancy is unknown.'),
              (4,'core-plus-extra','Safeguarding cancellation has been confirmed.','safeguarding cancellation','Safeguarding has a reported cancellation status.'),
              (5,'valid-unknown-authority','Departure clearance for TRN101 remains unconfirmed.','departure clearance','Departure permission is confirmed, denied, or unknown.')]
    for index,name,hypothesis,topic,broad in examples:
        p=old[index];answer=p['learnerResponse'];q=p['question']
        for variant,premise in [('answer_only',answer),('lean_question_answer','Q: '+q+'\nA: '+answer),('r11_instruction_wrapper',question_answer(q,answer))]:
            add('primary-context',name,premise,hypothesis,variant,'Bare criterion content; compare the effects of question context.',fixture='old6',fixtureIndex=index)
        for variant,probe in [('mention',topic.capitalize()+' is mentioned.'),
                              ('about','The answer contains information about '+topic+'.'),('broad_content',broad)]:
            add('answer-only-coverage',name,answer,probe,variant,'Neutral topical coverage hypothesis, not an expected answer.',fixture='old6',fixtureIndex=index)
    q=old[2]['question']
    for name,answer in [('procedures-only','Low-visibility procedures and safeguarding are active.'),
                        ('hold-stated','Low-visibility procedures and safeguarding are active. TRN101 remains held.'),
                        ('release-stated','Low-visibility procedures and safeguarding are active. TRN101 is released.'),
                        ('unrelated','Baggage loading is complete.')]:
        for variant,premise in [('answer_only',answer),('lean_question_answer','Q: '+q+'\nA: '+answer)]:
            add('omission-versus-opposite',name,premise,'TRN101 remains held.',variant,'The aircraft hold claim itself; omission is not a denial.')
        add('omission-versus-opposite',name,answer,'An aircraft hold status is mentioned.','answer_only_mention','Whether the answer itself addresses hold status.')
    q=dev[0]['question']
    for name,answer in [('obstruction-only','A service vehicle is obstructing the ground route.'),
                        ('aircraft-identified','TRN102 is held because a service vehicle obstructs its route.'),
                        ('no-identification','No information is given.')]:
        for variant,premise in [('answer_only',answer),('lean_question_answer','Q: '+q+'\nA: '+answer)]:
            add('identity-presupposition',name,premise,'TRN102 is held.',variant,'Test whether the question supplies missing learner identity.')
        add('identity-presupposition',name,answer,'An aircraft is identified.','answer_only_coverage','Identification must originate in the answer.')
    q=dev[14]['question']
    corrections=[('plain-current','The current target off-block estimate is 10:35.'),
                 ('correct-to-prior','The current target off-block estimate is 10:35; correction: it is 10:20.'),
                 ('correct-to-current','The current target off-block estimate is 10:20; correction: it is 10:35.')]
    hypotheses=[('current-value','The current target off-block estimate is 10:35.'),
                ('prior-value','The current target off-block estimate is 10:20.'),
                ('current-replaces-prior','The target off-block estimate is 10:35, not 10:20.'),
                ('prior-replaces-current','The target off-block estimate is 10:20, not 10:35.')]
    for name,answer in corrections:
        for hname,hypothesis in hypotheses:
            for variant,premise in [('answer_only',answer),('lean_question_answer','Q: '+q+'\nA: '+answer)]:
                add('correction-content-contrast',name,premise,hypothesis,variant,'Ordinary content and value contrast; no ultimate-assertion meta instruction.',contentContrast=hname)
    # Actual exposed DEV clock states. Compare a current report alone with the
    # same report accompanied by the most recent explicitly historical report.
    p=dev[23];current,historical=grounding_context(p)
    latest=max(current,key=lambda r:r['receiptTime']);prior=max(historical,key=lambda r:r['receiptTime'])
    def record(report,status):
        return ('Report '+report['id']+'; flight '+str(report.get('flightInstance'))+'; source '+str(report.get('source'))+
                '; '+status+'; event '+str(report['eventTime'])+'; received '+str(report['receiptTime'])+': '+report['message'])
    clocks=[('current_only',record(latest,'CURRENT')),
            ('labelled_past_then_current',record(prior,'SUPERSEDED HISTORICAL')+'\n'+record(latest,'CURRENT'))]
    clock_claims=[('assert-pending-now','Safeguarding cancellation has not been confirmed.'),
                  ('assert-confirmed-now','Safeguarding cancellation has been confirmed.'),
                  ('explicit-history','Initially safeguarding cancellation was pending, but it has now been confirmed.'),
                  ('history-with-stale-current','Initially safeguarding cancellation was pending, and it is still pending now.')]
    for name,claim in clock_claims:
        for variant,premise in clocks:
            add('source-clock',name,premise,claim,variant,'Current versus explicitly historical source scope.',sourceIds=[latest['id']] if variant=='current_only' else [prior['id'],latest['id']])
        for variant,premise in [('answer_only',claim),('lean_question_answer','Q: '+p['question']+'\nA: '+claim)]:
            add('source-clock-temporal-coverage',name,premise,'An earlier report state is described.',variant,'Whether a current assertion is mistaken for a history description.')
    p=old[4]
    for name,claim in [('unsupported-event','The engine has caught fire.'),
                       ('known-cancellation','Safeguarding cancellation is confirmed.'),
                       ('unknown-permission','The reports do not confirm departure clearance for TRN101.')]:
        for variant,attributed in [('raw_current_reports',False),('attributed_current_reports',True)]:
            add('grounding-content',name,sources(p,attributed),claim,variant,'Direct current source evidence to claim, without unsupported/conflict meta judgments.')
        for variant,hypothesis in [('event','An operational event occurred.'),('reported-state','An operational state is asserted.')]:
            add('answer-only-factuality',name,claim,hypothesis,variant,'Lean factuality/category hypothesis; not a grader instruction.')
    p=dev[9]
    for hname,hypothesis in [('not-available','Stand B is not yet confirmed available.'),('available','Stand B is confirmed free now.')]:
        for variant,premise in [('answer_only',p['learnerResponse']),('lean_question_answer','Q: '+p['question']+'\nA: '+p['learnerResponse'])]:
            add('availability-question-effect',hname,premise,hypothesis,variant,'Actual exposed false-credit input; compare question effect on bare content.',fixture='dev24',fixtureIndex=9)
    q=dev[8]['question']
    for name,answer in [('bare-no','No.'),('explicit-unconfirmed','Stand B is not confirmed available.'),('unsure','I am not sure.')]:
        for variant,premise in [('answer_only',answer),('lean_question_answer','Q: '+q+'\nA: '+answer)]:
            add('short-dialogue-context',name,premise,'Stand B is not yet confirmed available.',variant,'Question-conditioned fragment versus explicit uncertainty; no acceptance label.')
        add('short-dialogue-context',name,answer,'Stand availability is mentioned.','answer_only_coverage','Whether answer-only coverage works for dialogue fragments.')
    if len(pairs)>150:raise ValueError('bounded diagnostic exceeds 150 pairs')
    return pairs


def main():
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
    fixture_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in FIXTURES}
    pairs=build_pairs()
    if any(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=value for path,value in fixture_hashes.items()):raise RuntimeError('fixture changed while constructing matrix')
    paths=[Path(__file__).resolve(),ROOT/'modelaccess/nli.py',ROOT/'experiments/typed_relation_review/candidate.py',
        ROOT/'experiments/typed_relation_review/redesign.py',ROOT/'experiments/typed_relation_review/propositions.py',
        ROOT/'backend/training_assessment.py',ROOT/'backend/evidence.py',ROOT/'docs/course/TYPED_REVIEW_R11_CONTRACT.md']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    snapshot=Path.home()/'.cache/huggingface/hub'/('models--'+MODEL_ID.replace('/','--'))/'snapshots'/MODEL_REVISION
    artifacts={}
    for path in sorted(snapshot.iterdir()):
        if path.is_file() and path.name!='README.md':
            with path.open('rb') as stream:artifacts[path.name]=hashlib.file_digest(stream,'sha256').hexdigest()
    lock=dict(version=VERSION,sourceHashes=hashes,fixtureHashes=fixture_hashes,modelArtifactSHA256=artifacts,
        modelId=MODEL_ID,modelRevision=MODEL_REVISION,device='mps',threshold=.8,deadlineSeconds=DEADLINE_SECONDS,
        pairCount=len(pairs),scoringRule='Canonical argmax label at probability >= 0.8, otherwise uncertain. Expected labels exist only for defined direct controls; null probes have no accuracy denominator.',
        policy='Exposed diagnostic only; no gold review statuses or acceptance scores; retain every actual raw pair.',createdAt=time.time())
    for path in paths:
        dest=out/'source'/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    (out/'lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    (out/'matrix.json').write_text(json.dumps(dict(pairs=pairs),ensure_ascii=False,indent=2)+'\n')
    started=time.monotonic();engine=None;error=None
    try:
        engine=PairClassifier(device='mps')
        (out/'startup.json').write_text(json.dumps(dict(elapsedSeconds=time.monotonic()-started,runtime=engine.runtime),indent=2)+'\n')
        lengths=[len(engine.tokenizer(p['premise'],p['hypothesis'],truncation=False)['input_ids']) for p in pairs]
        (out/'token-preflight.json').write_text(json.dumps(dict(lengths=lengths,maxTokens=max(lengths),overBound=[i for i,n in enumerate(lengths) if n>512]),indent=2)+'\n')
        if any(n>512 for n in lengths):raise ValueError('matrix input exceeds bound; no scoring/truncation')
        score_started=time.monotonic();engine.score(pairs,score_started+DEADLINE_SECONDS)
    except Exception as exc:error=type(exc).__name__+': '+str(exc)
    finally:
        records=[] if engine is None else engine.records
        with (out/'raw-scores.jsonl').open('w') as stream:
            for row in records:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
        summary=dict(planned=len(pairs),scored=len(records),error=error,elapsedSeconds=time.monotonic()-started,
            familyCounts={family:sum(p['family']==family for p in pairs) for family in sorted({p['family'] for p in pairs})})
        observations=[]
        for row in records:
            probabilities=row.get('probabilities');observed='unavailable'
            if probabilities:
                index=max(range(3),key=lambda i:probabilities[i]);observed=LABELS[index] if probabilities[index]>=.8 else 'uncertain'
            observations.append(dict(index=row['index'],observedLabel=observed,expectedLabel=row['expectedLabel']))
        summary['labelObservations']=observations
        (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps(summary),flush=True)
    if any(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=value for path,value in hashes.items()):raise RuntimeError('probe source changed during run')
    if any(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=value for path,value in fixture_hashes.items()):raise RuntimeError('probe fixture changed during run')
    if error:raise RuntimeError(error)


if __name__=='__main__':main()
