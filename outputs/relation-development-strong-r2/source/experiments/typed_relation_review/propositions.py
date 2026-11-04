"""Authored rubric propositions, frozen before NLI development inference.

These are hypotheses to test against learner text, never learner input or gold
output labels. Explanatory context does not add a requirement to recite history.
"""
from backend.training_assessment import TYPED_QUESTIONS

PROPOSITIONS = {
 'surface_conflict': [
  {'flight':['TRN102 is held.'], 'reason':["A service vehicle obstructs TRN102's ground route."]},
  {'release':["TRN102's ground hold has been released."], 'change':["TRN102's ground hold was released because the obstructing vehicle is now clear."]},
  {'unknown':['Takeoff clearance for TRN102 remains unconfirmed.'], 'scope':["Release of TRN102's ground hold does not establish permission to take off."]},
 ],
 'late_arrival': [
  {'flight':['TRN103 is waiting for Stand B.'], 'occupant':['Stand B is occupied by TRN102.']},
  {'availability':['Stand B is not yet confirmed available.'], 'plan':['A planned reposition does not confirm that Stand B is free.']},
  {'availability':['Stand B has been confirmed available for TRN103.'], 'release':["The confirmation of Stand B availability also confirms release of TRN103's ground hold."]},
 ],
 'late_baggage': [
  {'delay':['A late baggage batch is delaying TRN102.'], 'separation':['Fuel service for TRN102 is complete.','Fuel completion does not establish baggage-loading completion.']},
  {'estimate':['The latest target off-block estimate for TRN102 is 10:35.'], 'scope':['The target off-block time is an estimate and does not establish departure clearance.']},
  {'unknown':['Overall departure readiness remains unconfirmed despite service completion and ground release.'], 'scope':['Fuel and baggage completion and ground release do not establish takeoff clearance.','Fuel and baggage completion and ground release do not establish that every departure prerequisite is satisfied.']},
 ],
 'fog_restrictions': [
  {'procedures':['Low-visibility procedures are active.','Safeguarding is active.'], 'hold':['TRN101 remains held.','Departure clearance for TRN101 remains unconfirmed.']},
  {'partial_cancellation':['Low-visibility procedures have been cancelled.','Safeguarding remains in place.'], 'hold':['TRN101 is still held.','Departure clearance for TRN101 remains unconfirmed.']},
  {'confirmation':['Safeguarding cancellation has been confirmed.'], 'authority':['Departure clearance for TRN101 remains unconfirmed.','TRN101 remains parked.']},
 ],
}


def propositions_for(payload):
    for exercise, questions in TYPED_QUESTIONS.items():
        if payload['question'] in questions:
            rows = PROPOSITIONS[exercise][questions.index(payload['question'])]
            if list(rows) != [c['id'] for c in payload['criteria'] if c['id'] != 'grounding']:
                raise ValueError('unsupported proposition criteria')
            return rows
    raise ValueError('unsupported proposition question')

# V2 neutral topical relevance, authored across every live question before calls.
# These contain topic names only, never expected values or correctness labels.
TOPIC_PATTERNS = {
 'movement': r'\b(held|hold|holding|release\w*|park\w*|mov\w*|reposition\w*|wait\w*|depart\w*|ready|readiness|prerequisites?)\b',
 'vehicle': r'\b(vehicle|obstruct\w*|block\w*|route|clear\w*)\b',
 'permission': r'\b(clearance|permission|authori[sz]\w*|takeoff|take.off|depart\w*)\b',
 'stand': r'\b(stand|occup\w*|reposition\w*|available|availability|free|destination)\b',
 'fuel': r'\b(fuel\w*|refu\w*)\b',
 'baggage': r'\b(baggage|bags?|loading)\b',
 'time': r'\b(tobt|estimate\w*|target|off.block|\d{1,2}:\d{2})\b',
 'lvp': r'\blow.visibility\b|\blvp\b',
 'safeguarding': r'\b(safeguard\w*|cancellation|cancelled|canceled)\b',
}
RELEVANCE = {
 'surface_conflict': [
  {'flight':[('movement',)],'reason':[('vehicle',)]},
  {'release':[('movement',)],'change':[('vehicle','movement')]},
  {'unknown':[('permission',)],'scope':[('permission','movement')]},
 ],
 'late_arrival': [
  {'flight':[('stand','movement')],'occupant':[('stand',)]},
  {'availability':[('stand',)],'plan':[('stand','movement')]},
  {'availability':[('stand',)],'release':[('stand','movement')]},
 ],
 'late_baggage': [
  {'delay':[('baggage',)],'separation':[('fuel',),{'all':('fuel','baggage')}]},
  {'estimate':[('time',)],'scope':[('time','permission')]},
  {'unknown':[('movement',)],'scope':[('permission','movement','fuel','baggage'),('permission','movement','fuel','baggage')]},
 ],
 'fog_restrictions': [
  {'procedures':[('lvp',),('safeguarding',)],'hold':[('movement',),('permission',)]},
  {'partial_cancellation':[('lvp',),('safeguarding',)],'hold':[('movement',),('permission',)]},
  {'confirmation':[('safeguarding',)],'authority':[('permission',),('movement',)]},
 ],
}


def relevance_for(payload):
    for exercise,questions in TYPED_QUESTIONS.items():
        if payload['question'] in questions:
            index=questions.index(payload['question'])
            rows=RELEVANCE[exercise][index]
            props=propositions_for(payload)
            if list(rows)!=list(props) or any(len(rows[c])!=len(props[c]) for c in props):
                raise ValueError('relevance/proposition mismatch')
            return rows
    raise ValueError('unsupported relevance question')


def occupancy_counter_for(payload, criterion_id, facet):
    # Domain-exclusive present relation: an aircraft waiting FOR a stand is not
    # already occupying that same stand. No general position-to-clearance rule.
    if payload['question']==TYPED_QUESTIONS['late_arrival'][0] and criterion_id=='flight' and facet==0:
        return dict(flight='TRN103',stand='B',hypothesis='TRN103 is occupying Stand B.')
    return None

# Neutral relation coverage. Modes describe what assertion is present, never
# its expected truth value. Atomic modes receive exact clauses; relation modes
# receive minimal contiguous clause windows that express both arguments.
RELATIONS = {
 'surface_conflict':[
  {'flight':['movement_status'],'reason':['vehicle_obstruction']},
  {'release':['hold_status'],'change':['hold_change_link']},
  {'unknown':['permission_status'],'scope':['authority_distinction']},
 ],
 'late_arrival':[
  {'flight':['waiting_position'],'occupant':['occupancy']},
  {'availability':['availability_status'],'plan':['plan_availability_relation']},
  {'availability':['availability_status'],'release':['stand_hold_link']},
 ],
 'late_baggage':[
  {'delay':['baggage_delay'],'separation':['fuel_state','service_relation']},
  {'estimate':['estimate'],'scope':['estimate_authority']},
  {'unknown':['readiness_status'],'scope':['readiness_authority','readiness_authority']},
 ],
 'fog_restrictions':[
  {'procedures':['lvp_status','safeguarding_status'],'hold':['movement_status','permission_status']},
  {'partial_cancellation':['lvp_status','safeguarding_status'],'hold':['movement_status','permission_status']},
  {'confirmation':['safeguarding_status'],'authority':['permission_status','movement_status']},
 ],
}


def relations_for(payload):
    for exercise,questions in TYPED_QUESTIONS.items():
        if payload['question'] in questions:
            rows=RELATIONS[exercise][questions.index(payload['question'])]
            props=propositions_for(payload)
            if list(rows)!=list(props) or any(len(rows[c])!=len(props[c]) for c in props):
                raise ValueError('relation/proposition mismatch')
            return rows
    raise ValueError('unsupported relation question')
