"""Live report-answer regression; run with python -m scripts.verify_training_answers.

Uses the preselected local model, no mock responses or answer repair. Expected
facts are used only after inference to score the result, never in the prompt.
These text-only probes complement the actual image-bearing simulator demo.
Stop the training service first to avoid loading two copies of the model.
"""
import argparse
import json
from pathlib import Path
import uuid

from backend.conversation.state import IntentRecord
from backend.conversation.turns import build_prompt
from backend.conversation.validate import validate_proposal
from backend.lessons import build_lesson
from backend.training_adapter import TrainingAdapter, TRAINING_PROMPT_VERSION
from modelaccess.contract import Request, Settings


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise SystemExit('Refusing to overwrite verification evidence')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    adapter=TrainingAdapter('qwen3.5-9b',profile='apronlens-v2-mps',
        prompt_audit_path=args.output.with_suffix('.prompts.jsonl'))
    adapter.load()
    settings=Settings(adapter.served_model,768,image_max_side=672)
    cases=[
        ('original-question',17,120,'Is Stand B confirmed available for TRN103?','hold'),
        ('paraphrase-other-seed',7,120,'Can TRN103 use Stand B yet, according to the reports?','hold'),
        ('before-release-received',17,133.999,'Is Stand B confirmed available for TRN103?','hold'),
        ('at-release-received',17,134,'Is Stand B confirmed available for TRN103?','released'),
        ('after-release',17,180,'Is Stand B confirmed available for TRN103?','released'),
        ('missing-service',17,120,'Is fuel service complete for TRN103?','unknown'),
    ]
    records=[]
    for name,seed,cutoff,question,expectation in cases:
        world,_,_=build_lesson(seed,'late_arrival')
        intents=[IntentRecord('earlier','reference','A3','TRN103','Why is TRN103 waiting?',60)]
        prompt=build_prompt(world,cutoff,('A3','TRN103'),('A3','TRN103'),intents,{},question)
        result=adapter.generate(Request(uuid.uuid4().hex,(('user',prompt),),settings))
        proposal=None;checked=None;errors=[]
        try:
            proposal=json.loads(result.text)
            checked=validate_proposal(proposal,world,cutoff)
        except (ValueError,TypeError,KeyError):errors.append('invalid_proposal')
        if result.error:errors.append(result.error)
        if not checked or not checked['accepted']:errors.extend(checked['errors'] if checked else [])
        if checked and checked['accepted']:
            current=[c for c in proposal['claims'] if c['status']=='current']
            if proposal['referent']!={'aircraftId':'A3','flightInstance':'TRN103'}:errors.append('wrong_flight')
            if expectation=='unknown':
                if proposal['unknowns']!=['fuel_status'] or current:errors.append('missing_service_not_preserved')
            else:
                expected_value=('hold: Stand B occupied by TRN102' if expectation=='hold'
                                else 'Stand B available; exercise ground hold released')
                if not any(c['value']==expected_value for c in current):errors.append('required_report_not_selected')
                if proposal['unknowns']:errors.append('irrelevant_or_contradictory_unknowns')
                if any(c['status']!='current' for c in proposal['claims']):errors.append('superseded_report_selected')
        record=dict(case=name,seed=seed,cutoff=cutoff,question=question,requestId=result.request_id,
            expectedOutcome=expectation,passed=not errors,errors=errors,proposal=proposal,
            latencySeconds=result.latency_seconds,model=result.returned_model,finishReason=result.finish_reason.value)
        records.append(record)
        completed=len(records)==len(cases)
        args.output.write_text(json.dumps(dict(promptVersion=TRAINING_PROMPT_VERSION,
            runtimeProfile='apronlens-v2-mps',textOnly=True,cases=records,completed=completed,
            passed=completed and all(r['passed'] for r in records)),indent=2)+'\n')
        print(json.dumps({k:record[k] for k in ('case','passed','errors','latencySeconds')}),flush=True)
    if not all(r['passed'] for r in records):raise SystemExit('A real-model report-answer regression failed')


if __name__=='__main__':main()
