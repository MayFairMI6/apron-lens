"""Evaluation-only history-aware scoring and new authored report families.

Question mode and required/allowed facts are predeclared labels, never model input.
No legacy scorer, model prompt, app validator or source evidence is changed.
"""
import json
from backend.conversation.context import snapshot

SCORER_VERSION='report-question-scorer-v2'

def score_answer(result,world,case):
    try: p=json.loads(result.get('rawModelOutput',''))
    except (ValueError,TypeError):p={}
    if not isinstance(p,dict):p={}
    claims=p.get('claims',[])
    shape=isinstance(claims,list) and all(isinstance(c,dict) for c in claims)
    if not shape:claims=[]
    facts=snapshot(world,case['aircraftId'],case['flight'],case['cutoff'])['factsById']
    ids=[c.get('fact_id') for c in claims]
    identity=p.get('referent')==dict(aircraftId=case['aircraftId'],flightInstance=case['flight'])
    supported=shape and all(isinstance(c.get('fact_id'),str) and c['fact_id'] in facts and
        c.get('value')==facts[c['fact_id']]['value'] and c.get('status')==facts[c['fact_id']]['status'] for c in claims)
    citations=shape and all(isinstance(c.get('fact_id'),str) and c['fact_id'] in facts and c.get('evidence_ids')==[facts[c['fact_id']]['event_id']] for c in claims)
    scope=shape and all(isinstance(fid,str) and fid in case['allowed'] for fid in ids)
    coverage=all(fid in ids for fid in case['required'])
    temporal=shape and all(c.get('status')=='current' or (case['mode'] in ('history','change') and c.get('status')=='superseded') for c in claims)
    unknowns=p.get('unknowns')
    uncertainty=isinstance(unknowns,list) and all(isinstance(u,str) for u in unknowns) and sorted(unknowns)==sorted(case['unknowns'])
    accepted=bool(result.get('accepted'))
    unique=shape and all(isinstance(fid,str) for fid in ids) and len(ids)==len(set(ids))
    passed=accepted and unique and p.get('status')=='answer' and identity and supported and citations and scope and coverage and temporal and uncertainty
    return dict(passed=passed,accepted=accepted,identityCorrect=identity,claimsSupported=supported,citationValid=citations if claims else None,
        relevantScope=scope,requiredCoverage=coverage,statusAllowed=temporal,unknownsCorrect=uncertainty,
        mode=case['mode'],errors=result.get('errors',[]))

def new_cases():
    episodes=[]
    def world(name,flights):
        return dict(scenarioId='HISTORY-V2-'+name,duration=400,aircraft=[dict(id=f'K{i+1}',flightInstance=f) for i,f in enumerate(flights)],events=[])
    def event(w,eid,aid,t,receipt,prop,value,old=None):
        fact=dict(property=prop,value=value)
        if old:fact['supersedes']=[old]
        w['events'].append(dict(id=eid,aircraftId=aid,flightInstance=next(a['flightInstance'] for a in w['aircraft'] if a['id']==aid),
            eventTime=t,receiptTime=receipt,source='authored-exercise-reports',facts=[fact],message=value))
        return eid+':'+prop
    def q(w,t,text,mode,required,allowed=None,unknowns=(),aid='K1'):
        return dict(cutoff=t,question=text,mode=mode,aircraftId=aid,flight=next(a['flightInstance'] for a in w['aircraft'] if a['id']==aid),
            required=list(required),allowed=list(required if allowed is None else allowed),unknowns=list(unknowns))
    # Delayed weather-restriction reports, a second independent restriction and an unrelated flight.
    w=world('weather-route',['WX410','WX522','WX633'])
    a=event(w,'W1','K1',5,12,'movement_condition','hold: reduced visibility')
    b=event(w,'W2','K1',30,45,'movement_condition','ground route open under escort',a)
    c=event(w,'W3','K1',65,80,'movement_condition','hold: route inspection',b)
    event(w,'W4','K2',8,10,'movement_condition','hold: service vehicle crossing')
    event(w,'W5','K3',6,9,'route','east service route')
    episodes.append(dict(name='weather_route',world=w,cases=[
        q(w,20,'What is the reported restriction for WX410?','current',[a]),
        q(w,44.999,'What restriction is still in effect for it in received reports?','current',[a]),
        q(w,45,'Compare its earlier restriction with the new route condition. Cite both.','change',[a,b]),
        q(w,46,'What was its restriction before the escort update?','history',[a],[a,b]),
        q(w,80,'What replaced the escort condition? Give the previous and current conditions.','change',[b,c]),
        q(w,81,'Does its current ground restriction establish overall departure readiness?','current',[],[c],['overall_readiness']),
    ]))
    # Three stand assignments, delayed second report, distractor with a different current stand.
    w=world('stand-reassignment',['ST204','ST305','ST406'])
    a=event(w,'S1','K1',2,4,'stand','D12')
    b=event(w,'S2','K1',21,38,'stand','E4',a)
    c=event(w,'S3','K1',60,75,'stand','D18',b)
    d=event(w,'S4','K2',3,5,'stand','F7')
    event(w,'S5','K3',4,6,'stand','E4')
    episodes.append(dict(name='stand_reassignment',world=w,cases=[
        q(w,15,'Which stand is assigned to ST204?','current',[a]),
        q(w,38,'Show its stand reassignment: the earlier stand and the replacement.','change',[a,b]),
        q(w,39,'Which stand did it have before E4?','history',[a],[a,b]),
        q(w,75,'Which stand is assigned to it now? Give only the current assignment.','current',[c]),
        q(w,76,'Compare its E4 assignment with the latest replacement.','change',[b,c]),
        q(w,77,'Correction: I mean ST305. What is its assigned stand?','current',[d],aid='K2'),
    ]))
    # Completion withdrawn and later re-confirmed; readiness is distinct and later withdrawn too.
    w=world('service-withdrawal',['SV708','SV819','SV920'])
    a=event(w,'B1','K1',4,7,'baggage_status','complete')
    b=event(w,'B2','K1',22,35,'baggage_status','reopened: additional bags to load',a)
    c=event(w,'B3','K1',52,64,'baggage_status','complete after additional loading',b)
    ready=event(w,'B4','K1',65,70,'overall_readiness','ready')
    notready=event(w,'B5','K1',83,95,'overall_readiness','not ready: additional check required',ready)
    event(w,'B6','K2',2,5,'baggage_status','loading')
    event(w,'B7','K3',3,6,'fuel_status','complete')
    episodes.append(dict(name='service_withdrawal',world=w,cases=[
        q(w,15,'Is baggage loading reported complete for SV708?','current',[a]),
        q(w,35,'How did its baggage status change? Include the earlier completion and the new status.','change',[a,b]),
        q(w,64,'What is its baggage status now?','current',[c]),
        q(w,69.999,'Is overall departure readiness established for it by the received reports?','current',[],[c],['overall_readiness']),
        q(w,70,'What is its reported overall readiness now?','current',[ready]),
        q(w,95,'Compare its earlier overall readiness with the latest readiness report.','change',[ready,notready]),
    ]))
    # Multiple successive estimate corrections plus explicit switch to another flight and follow-up.
    w=world('estimate-correction',['ET111','ET222','ET333'])
    a=event(w,'T1','K1',2,5,'tobt','14:10')
    b=event(w,'T2','K1',20,32,'tobt','14:40',a)
    c=event(w,'T3','K1',42,55,'tobt','14:25',b)
    d=event(w,'T4','K2',3,6,'tobt','15:05')
    e=event(w,'T5','K2',58,72,'tobt','15:20',d)
    event(w,'T6','K3',4,7,'tobt','16:00')
    episodes.append(dict(name='estimate_correction',world=w,cases=[
        q(w,15,'What off-block time is estimated for ET111?','current',[a]),
        q(w,32,'Compare its first estimate with the received revision.','change',[a,b]),
        q(w,55,'What is its latest estimate? Give only the current one.','current',[c]),
        q(w,56,'What estimate did it have immediately before 14:25?','history',[b],[b,c]),
        q(w,57,'I meant ET222 instead. What is its estimate?','current',[d],aid='K2'),
        q(w,72,'Compare the previous and new estimates for that flight.','change',[d,e],aid='K2'),
    ]))
    return episodes

def validate_keys(episodes):
    for ep in episodes:
        previous=-1
        for c in ep['cases']:
            assert c['mode'] in ('current','history','change') and c['cutoff']>=previous
            previous=c['cutoff'];facts=snapshot(ep['world'],c['aircraftId'],c['flight'],c['cutoff'])['factsById']
            assert set(c['required'])<=set(c['allowed'])<=facts.keys()
            assert len(c['required'])<=3 and (c['required'] or c['unknowns'])
            assert all(facts[f]['status'] in (('current',) if c['mode']=='current' else ('current','superseded')) for f in c['allowed'])
            if c['mode']=='change': assert {'current','superseded'}<={facts[f]['status'] for f in c['required']}
            if c['mode']=='history': assert any(facts[f]['status']=='superseded' for f in c['required'])
            current={f['property'] for f in facts.values() if f['status']=='current'}
            assert not current.intersection(c['unknowns'])
