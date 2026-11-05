"""Authored synthetic pilot. Split assigned before episode substitution; no model labels."""
import hashlib
import json
from pathlib import Path
from backend.training_assessment import review_prompt, validate_review
ROOT = Path(__file__).parent
# Each family has two separately judged clauses. Wording is family-specific;
# substitutions are correlated replicates, never claimed independent samples.
FAMILIES = {
 'stand_occupancy': (
  '{f} waits for stand {s}; {o} currently occupies {s}.',
  'Who is waiting for which stand, and who occupies it?',
  ['Identify the inbound flight and the stand awaited; awaiting is not occupying.', 'Identify the occupying aircraft.'],
  ['{f} is waiting for stand {s}.', '{o} occupies that stand.'],
  ['The inbound awaiting {s} is {f}.', 'Its current occupant is {o}.'],
  ['{f} already occupies stand {s}.', '{f} occupies that stand.'],
  '{f} has takeoff clearance.'),
 'service_dependency': (
  'Fuel service for {f} is complete. Baggage loading for {f} is incomplete.',
  'What is complete and what remains unfinished?',
  ['Recognise fuel completion for the selected aircraft.', 'Recognise baggage loading remains incomplete.'],
  ['Fuel for {f} is complete.', 'Baggage loading is unfinished.'],
  ['{f} has finished refuelling.', 'Its baggage loading remains incomplete.'],
  ['Fuel for {f} is incomplete.', 'Baggage loading is complete.'],
  'All departure prerequisites are complete.'),
 'ground_hold': (
  'The exercise ground hold for {f} is released after the vehicle cleared its route. No takeoff clearance is reported.',
  'What hold changed, and what permission remains unconfirmed?',
  ['State the ground hold was released.', 'State takeoff clearance remains unconfirmed.'],
  ['The ground hold for {f} is released.', 'Takeoff clearance is unconfirmed.'],
  ['{f} is no longer under the reported ground hold.', 'The reports do not establish permission to take off.'],
  ['The ground hold for {f} is still active.', 'Takeoff clearance is confirmed.'],
  'The runway has been inspected and reopened.'),
 'departure_estimate': (
  '{f}: target off-block estimate revised from 10:20 to 10:35. This is an estimate, not clearance.',
  'Give the latest estimate and explain its authority.',
  ['Identify 10:35 as the current estimate.', 'Distinguish an estimate from clearance.'],
  ['The latest estimate for {f} is 10:35.', 'It is not clearance.'],
  ['{f} now has a target off-block time of 10:35.', 'That target does not grant permission to depart.'],
  ['The latest estimate for {f} is 10:20.', 'The estimate is departure clearance.'],
  'The delay was caused by an engine defect.'),
 'position_destination': (
  '{f} is stationary at holding point {s}. Its intended destination is stand {d}. Movement approval has not been received.',
  'Where is the aircraft now and what is its intended destination?',
  ['Identify the present holding point.', 'Identify the intended stand without claiming it has been reached.'],
  ['{f} is at holding point {s}.', 'Its intended destination is stand {d}.'],
  ['The present position of {f} is {s}.', 'It is awaiting movement to stand {d}.'],
  ['{f} is already at stand {d}.', 'Its intended destination is stand {s}.'],
  'Movement approval has been received.'),
 'visibility_safeguarding': (
  'Low-visibility procedures are cancelled. Safeguarding remains in force. {f} remains held.',
  'Which procedure ended and which protection remains?',
  ['Identify cancellation of low-visibility procedures.', 'Identify continued safeguarding.'],
  ['Low-visibility procedures are cancelled.', 'Safeguarding remains active.'],
  ['The low-visibility procedures have ended.', 'The safeguarding measures still apply.'],
  ['Low-visibility procedures remain active.', 'Safeguarding is cancelled.'],
  '{f} is cleared to depart.'),
 'inspection_release': (
  'Inspection of route {s} is finished, but reopening requires a separate release. That release has not been received. {f} is waiting.',
  'Separate the completed work from the outstanding authority.',
  ['Inspection completion is confirmed.', 'Route reopening is not confirmed without the separate release.'],
  ['Inspection of {s} has finished.', 'The separate route release is outstanding.'],
  ['The inspection work on {s} is done.', 'Reopening still lacks the required confirmation.'],
  ['Inspection of {s} has not finished.', 'Route {s} is confirmed reopened.'],
  '{f} has been instructed to enter the route.'),
 'service_withdrawal': (
  'Earlier: {f} baggage complete. Correction: that completion was entered in error; baggage completion is now unconfirmed. Fuel completion remains confirmed.',
  'After the correction, what can be said about baggage and fuel?',
  ['Use the correction: baggage completion is unconfirmed.', 'Retain the unaffected fuel completion.'],
  ['Baggage completion for {f} is now unconfirmed.', 'Fuel completion remains confirmed.'],
  ['The earlier baggage completion for {f} was withdrawn.', 'The fuel service is still recorded complete.'],
  ['Baggage completion for {f} is confirmed.', 'Fuel completion was withdrawn.'],
  'The aircraft is fully ready for departure.'),
 'route_authority': (
  'Route {s} is blocked. An alternative via {d} is proposed for {f}; approval of the alternative remains pending.',
  'What is the status of the original route and the proposed alternative?',
  ['Identify the original route as blocked.', 'Describe the alternative as proposed, not approved.'],
  ['The original route {s} is blocked.', 'The alternative via {d} awaits approval.'],
  ['The obstruction prevents use of {s}.', 'Using {d} is still only a proposal.'],
  ['The original route {s} is clear.', 'The alternative via {d} is approved.'],
  '{f} has already entered the alternative route.'),
 'dispatch_conflict': (
  'Tug {s} was provisionally assigned to {f}. A later received update assigns it to {o} instead. No replacement for {f} is confirmed.',
  'Who has the tug now, and is a replacement confirmed for the first flight?',
  ['Use the later tug assignment to the other flight.', 'Keep replacement availability for the first flight unconfirmed.'],
  ['Tug {s} is now assigned to {o}.', 'A replacement for {f} is unconfirmed.'],
  ['The revised allocation gives {s} to {o}.', 'There is no confirmed substitute for {f}.'],
  ['Tug {s} remains assigned to {f}.', 'A replacement for {f} is confirmed.'],
  '{f} has completed pushback.')
}


def cases(family, episode):
    raw = FAMILIES[family]
    vals = dict(f=f'AX{episode+210}', o=f'BY{episode+710}', s=f'K{episode+2}', d=f'M{episode+8}')
    fmt = lambda x: x.format(**vals)
    report, question = map(fmt, raw[:2])
    correct, para, wrong = [[fmt(x) for x in part] for part in raw[3:6]]
    extra = fmt(raw[6])
    # No hidden phrase matching: the gold statuses follow these explicit authored clauses.
    packs = [
        ('correct', correct, ['met','met','met'], [correct[0],correct[1],correct[0]]),
        ('paraphrase', para, ['met','met','met'], [para[0],para[1],para[0]]),
        ('omission', correct[:1], ['met','missing','met'], [correct[0],'',correct[0]]),
        ('contradiction', [correct[0],wrong[1]], ['met','contradicted','contradicted'], [correct[0],wrong[1],wrong[1]]),
        ('wrong_core', [wrong[0],correct[1]], ['contradicted','met','contradicted'], [wrong[0],correct[1],wrong[0]]),
        ('unsupported_extra', correct+[extra], ['met','met','contradicted'], [correct[0],correct[1],extra]),
    ]
    # Contradictions in any clause override a correct mention of the same criterion.
    if family == 'stand_occupancy':
        packs[3] = ('contradiction', [correct[0],wrong[1]], ['contradicted','contradicted','contradicted'], [wrong[1],wrong[1],wrong[1]])
    if family == 'position_destination':
        packs[4] = ('wrong_core', [wrong[0],correct[1]], ['contradicted','contradicted','contradicted'], [wrong[0],wrong[0],wrong[0]])
    eid=f'{family}-{episode}'
    criteria=[{'id':f'fact{i+1}','expected':fmt(x),'evidenceIds':['R1']} for i,x in enumerate(raw[2])]
    criteria.append({'id':'grounding','expected':'Review every claim, including extras. Unsupported or incompatible extra claims are contradicted. Supported claims alone are met; omissions belong to the fact criteria.','evidenceIds':['R1']})
    comments={'met':'Your statement matches the received report.', 'missing':'This requested point is absent from your response.', 'contradicted':'This claim is incompatible with, or not established by, the received report.'}
    for kind, clauses, statuses, quotes in packs:
        payload=dict(episodeId=eid, checkpointId='review-1', aircraftId=vals['f'],cutoff=[100,101,120,500][episode],
                     question=question,learnerResponse=' '.join(clauses),criteria=criteria,
                     reports=[dict(id='R1',episodeId=eid,receiptTime=100,message=report), dict(id='R2',episodeId=eid,receiptTime=90,message='Unrelated aircraft ZZ900 is parked at stand Z9; its fuel service is complete.')])
        verdict='needs_review' if 'contradicted' in statuses else 'supported' if all(s=='met' for s in statuses) else 'partly_supported'
        target=dict(episodeId=eid,checkpointId='review-1',verdict=verdict,
                    explanation={'supported':'Your answer is supported by the received report.','partly_supported':'Your answer covers one point; include the other requested point.','needs_review':'Check the marked claim against the received report before drawing that conclusion.'}[verdict],
                    points=[dict(criterionId=c['id'],status=s,comment=comments[s],evidenceIds=['R1'],learnerQuote=q) for c,s,q in zip(criteria,statuses,quotes)])
        validate_review(json.dumps(target),payload)
        yield dict(id=f'{eid}-{kind}',family=family,kind=kind,payload=payload,target=target)


def digest(data): return hashlib.sha256(data).hexdigest()


def build(out):
    protocol=json.loads((ROOT/'protocol.json').read_text())
    out.mkdir(parents=True,exist_ok=False)
    manifest={'protocol_sha256':digest((ROOT/'protocol.json').read_bytes()),'splits':{},'generation':'authored templates; no model-generated labels'}
    all_families=[]
    for split,families in protocol['families'].items():
        all_families+=families
        rows=[row for family in families for ep in range(4) for row in cases(family,ep)]
        data=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows).encode()
        name=split+'.jsonl'
        (out/name).write_bytes(data)
        manifest['splits'][split]={'file':name,'sha256':digest(data),'count':len(rows),'families':families}
    assert len(all_families)==len(set(all_families))
    manifest['source_sha256']=digest(Path(__file__).read_bytes())
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    print(json.dumps(build(p.parse_args().output),indent=2))
