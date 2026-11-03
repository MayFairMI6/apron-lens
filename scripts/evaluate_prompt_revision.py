"""Versioned v5/v6 readiness revision: observed regression first, fresh locked probes second."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import uuid
from backend.training_adapter_v6 import TrainingAdapter as V6
from backend.training_adapter_v5 import TrainingAdapter as V5
from backend.lessons import build_lesson
from backend.training_turn import run_turn
from backend.conversation.state import SessionState
from backend.conversation.context import snapshot
from modelaccess.contract import Settings
from scripts.evaluate_training_assistant import suite, score

VERSION='readiness-prompt-revision-v1'

def fresh_suite():
    def c(t,q,flight='TRN102',required=(),unknowns=()):
        return dict(cutoff=t,question=q,flight=flight,required=dict(required),unknowns=list(unknowns))
    return {
      'surface_conflict': [
        c(50,'What restriction currently applies to TRN102?',required=[('movement_condition','hold: vehicle obstructing ground route')]),
        c(104,'Has its reported ground restriction ended?',required=[('movement_condition','exercise ground hold released')]),
        c(105,'With that restriction lifted, is its overall readiness now confirmed?',unknowns=['overall_readiness']),
        c(106,'For this same flight, do we have a fuel-completion report?',unknowns=['fuel_status']),
        c(107,'Switch to TRN103. Is overall readiness reported for that flight?',flight='TRN103',unknowns=['overall_readiness']),
        c(108,'What ground route is reported for it?',flight='TRN103',required=[('route','apron ground circuit')]),
      ],
      'late_arrival': [
        c(90,'Can TRN103 use its intended stand according to the latest received condition?',flight='TRN103',required=[('movement_condition','hold: Stand B occupied by TRN102')]),
        c(133.5,'Is the availability of its intended stand confirmed at this point?',flight='TRN103',required=[('movement_condition','hold: Stand B occupied by TRN102')]),
        c(134.5,'What does the received update say about availability for that inbound?',flight='TRN103',required=[('movement_condition','Stand B available; exercise ground hold released')]),
        c(136,'Which stand has it now been assigned?',flight='TRN103',required=[('stand','B')]),
        c(137,'Does having that stand establish that it is ready for departure?',flight='TRN103',unknowns=['overall_readiness']),
        c(138,'Correction: TRN101. Is its baggage loading reported complete?',flight='TRN101',unknowns=['baggage_status']),
      ],
      'late_baggage': [
        c(60,'For TRN102, has refuelling finished?',required=[('fuel_status','complete')]),
        c(70,'Does that completion establish that the flight is ready to depart?',unknowns=['overall_readiness']),
        c(83,'What off-block time is now estimated for the same flight?',required=[('tobt','10:35')]),
        c(133.5,'Has its baggage loading been reported finished yet?',required=[('baggage_status','delayed')]),
        c(134.5,'What is its reported loading status now?',required=[('baggage_status','complete')]),
        c(159,'After loading and the hold release, what is still unconfirmed about its overall readiness?',unknowns=['overall_readiness']),
      ],
      'explicit_readiness': [
        c(199.999,'Is there a current report establishing overall readiness for TRN102?',unknowns=['overall_readiness']),
        c(200,'What does the latest received report say about its overall readiness?',required=[('overall_readiness','ready')]),
        c(219.999,'Is overall readiness still reported for that flight?',required=[('overall_readiness','ready')]),
        c(220,'Has the latest update changed its reported readiness?',required=[('overall_readiness','not ready: additional inspection required')]),
        c(221,'Is its fuel service complete, regardless of the readiness restriction?',required=[('fuel_status','complete')]),
        c(222,'Now TRN101: is overall readiness established for it?',flight='TRN101',unknowns=['overall_readiness']),
      ]}

def make_world(exercise,seed):
    world,_,_=build_lesson(seed,'late_baggage' if exercise=='explicit_readiness' else exercise)
    if exercise=='explicit_readiness':
        # Evaluation-only authored reports. Never injected into the real app/lesson.
        world['scenarioId']='READINESS-EVAL-'+str(seed)
        world['events'] += [dict(id='EVAL_READY',aircraftId='A2',flightInstance='TRN102',source='exercise-coordinator',
            eventTime=190.,receiptTime=200.,facts=[dict(property='overall_readiness',value='ready')],message='Overall readiness reported ready.'),
          dict(id='EVAL_NOT_READY',aircraftId='A2',flightInstance='TRN102',source='exercise-coordinator',
            eventTime=210.,receiptTime=220.,facts=[dict(property='overall_readiness',value='not ready: additional inspection required',
            supersedes=['EVAL_READY:overall_readiness'])],message='Overall readiness withdrawn: additional inspection required.')]
        world['events'].sort(key=lambda e:(e['receiptTime'],e['id']))
    return world

def validate_keys(cases,seed):
    for exercise,turns in cases.items():
        w=make_world(exercise,seed)
        for c in turns:
            current={f['property']:f['value'] for f in snapshot(w,'A'+c['flight'][-1],c['flight'],c['cutoff'])['facts'] if f['status']=='current'}
            assert all(current.get(k)==v for k,v in c['required'].items()),(exercise,c)
            assert not set(c['unknowns']) & current.keys()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--validate-only',action='store_true')
    a=p.parse_args();validate_keys(suite(),17);validate_keys(fresh_suite(),29)
    if a.validate_only:print('18 observed regression + 24 fresh question keys match received reports');return
    if a.output.exists() or a.output.with_suffix('.lock.json').exists():raise SystemExit('Refusing overwrite')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    files=['backend/training_adapter_v6.py','backend/training_adapter_v5.py','scripts/evaluate_prompt_revision.py','scripts/evaluate_training_assistant.py']
    lock=dict(version=VERSION,regression=suite(),fresh=fresh_suite(),sourceHashes={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files},
        sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        adoptionGate='v6 passes all18 observed regression cases; on24 fresh questions improves total over v5, with no v5-pass/v6-fail pair; all explicit ready/not-ready cases pass. No prompt revision after opening fresh results.',
        limits='Authored same-scenario fresh questions, not independent unseen-airport generalization. Offline, text-only; actual engine stop reason unavailable.')
    a.output.with_suffix('.lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    v6=V6('qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=a.output.with_suffix('.v6.prompts.jsonl'));v6.load()
    v5=V5('qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=a.output.with_suffix('.v5.prompts.jsonl'));v5._engine=v6._engine
    settings=Settings(v6.served_model,768,image_max_side=672)
    report=dict(version=VERSION,lockSha256=hashlib.sha256(a.output.with_suffix('.lock.json').read_bytes()).hexdigest(),runtime=v6.run_metadata(),records=[],completed=False)
    def run(phase,version,cases,seed,adapter):
        for exercise,turns in cases.items():
            world=make_world(exercise,seed);session=SessionState(uuid.uuid4().hex)
            for i,c in enumerate(turns):
                result=run_turn(session,world,dict(requestId=uuid.uuid4().hex,turnId=str(i),expectedRevision=session.revision,
                    aircraftId=None,flightInstance=None,cutoff=c['cutoff'],question=c['question']),adapter,settings)
                row=dict(phase=phase,version=version,exercise=exercise,turn=i,case=c,result=result,score=score(result,world,c))
                report['records'].append(row);a.output.write_text(json.dumps(report,indent=2)+'\n')
                print(json.dumps(dict(phase=phase,version=version,exercise=exercise,turn=i,passed=row['score']['passed'],latency=result['latencySeconds'])),flush=True)
    run('observed_regression','v6',suite(),17,v6)
    if not all(r['score']['passed'] for r in report['records']):
        report['stopped']='Regression gate failed; fresh questions not run.';a.output.write_text(json.dumps(report,indent=2)+'\n');return
    run('fresh','v5',fresh_suite(),29,v5)
    run('fresh','v6',fresh_suite(),29,v6)
    old=[r for r in report['records'] if r['phase']=='fresh' and r['version']=='v5']
    new=[r for r in report['records'] if r['phase']=='fresh' and r['version']=='v6']
    report['summary']={v:dict(passed=sum(r['score']['passed'] for r in rows),total=len(rows)) for v,rows in [('v5',old),('v6',new)]}
    report['regressions']=[dict(exercise=a['exercise'],turn=a['turn']) for a,b in zip(old,new) if a['score']['passed'] and not b['score']['passed']]
    report['adopt']=sum(r['score']['passed'] for r in new)>sum(r['score']['passed'] for r in old) and not report['regressions'] and all(r['score']['passed'] for r in new if r['exercise']=='explicit_readiness')
    report['completed']=True;a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(summary=report['summary'],adopt=report['adopt'],regressions=report['regressions'])),flush=True)

if __name__=='__main__':main()
