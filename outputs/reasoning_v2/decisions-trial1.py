"""Qwen binary decisions, followed by lossless provenance projection.
No deterministic answer selector or gold labels are called by this inference path.
"""
import json
from backend.evidence import classify
VERSION='balanced-decisions-v1'

RULES={
 'current':'Include a record only if it matches the selected aircraft, flight and requested property, AND its status is current. Exclude scheduled, superseded, expired and conflicting records.',
 'change':'Include EVERY received record matching the selected aircraft, flight and requested properties. Include old, superseded, scheduled, expired and conflicting records as well as current ones. A change history must not drop an earlier matching record.',
 'latest':'Among records matching the selected aircraft, flight and requested properties (or all properties if none requested), include ALL records at the greatest receiptTime. Ties all count. Event time and status do not decide which report arrived latest.'}

def model_facts(context,unfiltered=False):
    return classify(context['receivedFacts'],context['checkpoint']) if unfiltered else context['facts']

def compact(f):
    return {k:f[k] for k in ('fact_id','aircraftId','flightInstance','property','value','receiptTime','status')}

def decision_prompt(context,facts,task,candidate,true_label):
    false_label='B' if true_label=='A' else 'A'
    identity=f"Selected aircraft {context['aircraftId']}; selected flight {context['flightInstance']}."
    requested=', '.join(context['properties']) or 'any property'
    if task=='include':
        question=f"Should candidate {candidate} be INCLUDED in the answer?"
        rule=RULES[context['queryType']]
        true_meaning='INCLUDE this candidate';false_meaning='EXCLUDE this candidate'
    else:
        question=f"Should {candidate} be listed as UNKNOWN for this query?"
        if context['queryType']=='latest':
            rule='UNKNOWN only when there is NO received record for the selected aircraft and flight matching ANY requested property. If there is at least one matching received record, it is NOT UNKNOWN. If no properties are requested, any received record for this identity counts.'
        else:
            rule=f'UNKNOWN means there is NO record for property {candidate} matching the selected aircraft and flight with status current. A missing record, expired-only, scheduled-only, superseded-only or conflicting-only set means UNKNOWN. If a matching current record exists, it is NOT UNKNOWN.'
        true_meaning='UNKNOWN, no qualifying evidence';false_meaning='NOT UNKNOWN, qualifying evidence exists'
    return ("Make one decision about fictional airport reports. Use the status and identity exactly as supplied. Do not infer services or clearance from other properties.\n"
            +identity+f" Requested properties: {requested}. Query: {context['queryType']}.\n"
            +rule+'\nRecords: '+json.dumps([compact(f) for f in facts],separators=(',',':'))+'\n'
            +question+f'\n{true_label} = {true_meaning}.\n{false_label} = {false_meaning}.\nReply with only A or B.')

def select_claims(engine,context,image=None,unfiltered=False):
    facts=model_facts(context,unfiltered);decisions=[];selected=[];unknown=[];input_tokens=0
    def choose(task,candidate):
        nonlocal input_tokens
        orientations=[]
        for true_label in ('A','B'):
            prompt=decision_prompt(context,facts,task,candidate,true_label)
            scores,tokens=engine.score_labels(prompt,image,('A','B'));input_tokens+=tokens
            false_label='B' if true_label=='A' else 'A'
            orientations.append(dict(trueLabel=true_label,prompt=prompt,scores=scores,
                trueMinusFalse=scores[true_label]-scores[false_label],choice=scores[true_label]>scores[false_label]))
        margin=sum(o['trueMinusFalse'] for o in orientations)/2
        decision=margin>0
        decisions.append(dict(task=task,candidate=candidate,selected=decision,meanLogPreference=margin,
                              orientationDisagreement=orientations[0]['choice']!=orientations[1]['choice'],orientations=orientations))
        return decision
    for f in facts:
        if choose('include',f['fact_id']):
            selected.append(dict(fact_id=f['fact_id'],value=f['value'],status=f['status'],evidence_ids=[f['event_id']]))
    for prop in context['properties'] or ['overall_readiness']:
        if choose('unknown',prop):unknown.append(prop)
    raw=json.dumps(dict(claims=selected,unknown_properties=unknown))
    return raw,dict(version=VERSION,decisions=decisions,inputTokens=input_tokens,forwardPasses=2*len(decisions),
                   outputTokens=0,provenance='Qwen chooses inclusion and missing-evidence flags; immutable values/status/source are projected, not generated.',
                   confidenceNote='Log preferences are not calibrated confidence probabilities.')
