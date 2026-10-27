"""Typed, bitemporal evidence. No learned component and no operational authority."""
import copy
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/reasoning_v1/scenarios'
FIELDS = {
 'stand': 'Assigned stand', 'baggage_status': 'Baggage service',
 'fuel_status': 'Fuel service', 'tobt': 'Target off-block time (estimate)',
 'route': 'Authored movement plan', 'movement_status': 'Scripted movement',
 'movement_condition': 'Authored movement condition', 'trajectory_checkpoint': 'Authored checkpoint',
 'overall_readiness': 'Overall departure readiness',
}
STATUSES = ('current', 'superseded', 'scheduled', 'expired', 'conflicting')

def load_scenario(sid):
    if sid == 'M1-stand-coordination-01':
        path=ROOT/'unity/SurfaceSafetyCoach/Assets/Resources/milestone1.json'
    elif isinstance(sid,str) and sid.replace('-','').isalnum():
        path=DATA/(sid+'.json')
    else: raise ValueError('Unknown scenario')
    if not path.is_file(): raise ValueError('Unknown scenario')
    data=json.loads(path.read_text()); validate_scenario(data); return data

def validate_scenario(data):
    ids={}; facts={}
    for e in data['events']:
        if e['id'] in ids: raise ValueError('Duplicate event ID')
        ids[e['id']]=e
        for key in ('eventTime','receiptTime'):
            if not isinstance(e[key],(int,float)) or not math.isfinite(e[key]) or e[key]<0: raise ValueError('Invalid time')
        if e['receiptTime']<e['eventTime']: raise ValueError('Receipt precedes event')
        for f in e['facts']:
            fid=e['id']+':'+f['property']
            if fid in facts or f['property'] not in FIELDS or not isinstance(f['value'],str): raise ValueError('Invalid fact')
            start=f.get('validFrom',e['eventTime']); end=f.get('validUntil')
            if not math.isfinite(start) or start<0 or (end is not None and (not math.isfinite(end) or end<=start)): raise ValueError('Invalid validity')
            facts[fid]=(e,f)
    for fid,(e,f) in facts.items():
        for oldid in f.get('supersedes',[]):
            if oldid not in facts: raise ValueError('Unknown supersession reference')
            old,of=facts[oldid]
            if old['flightInstance']!=e['flightInstance'] or old['aircraftId']!=e['aircraftId'] or of['property']!=f['property']:
                raise ValueError('Cross-identity/property supersession')
            if old['eventTime']>=e['eventTime']: raise ValueError('Supersession must follow earlier event time')
    return data

def received_facts(data, checkpoint):
    result=[]
    for e in sorted(data['events'],key=lambda e:(e['receiptTime'],e['id'])):
        if e['receiptTime']>checkpoint: continue
        for f in e['facts']:
            result.append(dict(fact_id=e['id']+':'+f['property'],event_id=e['id'],
                aircraftId=e['aircraftId'],flightInstance=e['flightInstance'],source=e['source'],
                property=f['property'],value=f['value'],eventTime=e['eventTime'],receiptTime=e['receiptTime'],
                validFrom=f.get('validFrom',e['eventTime']),validUntil=f.get('validUntil'),supersedes=f.get('supersedes',[])))
    return result

def classify(facts,t):
    facts=copy.deepcopy(facts); lookup={f['fact_id']:f for f in facts}
    replaced=set()
    def walk(fid):
        if fid in replaced:return
        replaced.add(fid)
        if fid in lookup:
            for old in lookup[fid]['supersedes']:walk(old)
    for f in facts:
        # An expired replacement does not revive an explicitly superseded plan.
        if f['validFrom']<=t:
            for old in f['supersedes']:walk(old)
    for f in facts:
        if f['validFrom']>t:f['status']='scheduled'
        elif f['fact_id'] in replaced:f['status']='superseded'
        elif f['validUntil'] is not None and t>=f['validUntil']:f['status']='expired'
        else:f['status']='current'
    groups={}
    for f in facts:
        if f['status']=='current':groups.setdefault((f['aircraftId'],f['flightInstance'],f['property']),[]).append(f)
    for group in groups.values():
        if len({f['value'] for f in group})>1:
            for f in group:f['status']='conflicting'
    return facts

def build_context(data, aircraft_id, checkpoint, query_type='latest', properties=None):
    if not math.isfinite(checkpoint) or not 0<=checkpoint<=data['duration']:raise ValueError('Checkpoint outside scenario')
    a=next((a for a in data['aircraft'] if a['id']==aircraft_id),None)
    if a is None:raise ValueError('Unknown aircraft')
    if query_type not in ('latest','current','change'):raise ValueError('Unsupported query type')
    properties=properties or []
    if any(p not in FIELDS for p in properties) or len(properties)!=len(set(properties)):raise ValueError('Invalid properties')
    if query_type!='latest' and not properties:raise ValueError('Current/change query requires properties')
    all_facts=received_facts(data,checkpoint)
    selected=[f for f in all_facts if f['aircraftId']==a['id'] and f['flightInstance']==a['flightInstance']]
    classified=classify(selected,checkpoint)
    return dict(scenarioId=data['scenarioId'],aircraftId=a['id'],flightInstance=a['flightInstance'],checkpoint=checkpoint,
                queryType=query_type,properties=properties,facts=classified,receivedFacts=all_facts,
                evidence=[e for e in data['events'] if e['receiptTime']<=checkpoint and e['flightInstance']==a['flightInstance'] and e['aircraftId']==a['id']],
                imageSource='Synthetic schematic; service/plan truth comes only from reports')

def expected_selection(context):
    """Explicit deterministic baseline for the supported structured query types."""
    facts=context['facts'];props=context['properties'];kind=context['queryType']; chosen=[];unknown=[]
    if kind=='latest':
        candidates=[f for f in facts if not props or f['property'] in props]
        if candidates:
            latest=max(candidates,key=lambda f:(f['receiptTime'],f['event_id']))['event_id']
            chosen=[f for f in candidates if f['event_id']==latest]
        else:unknown=props or ['overall_readiness']
    else:
        for prop in props:
            current=[f for f in facts if f['property']==prop and f['status']=='current']
            if not current:unknown.append(prop)
            if kind=='current':chosen.extend(current)
            else:chosen.extend(f for f in facts if f['property']==prop)
    return {'claims':[dict(fact_id=f['fact_id'],value=f['value'],status=f['status'],evidence_ids=[f['event_id']]) for f in chosen],
            'unknown_properties':unknown}

def render_claim(f):
    label=FIELDS[f['property']]
    return f"{label}: {f['value']} — {f['status']}. Event {f['eventTime']:g} s; received {f['receiptTime']:g} s. [{f['event_id']}]"
