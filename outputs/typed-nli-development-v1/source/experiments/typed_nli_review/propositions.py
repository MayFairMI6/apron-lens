"""Authored rubric propositions, frozen before NLI development inference.

These are hypotheses to test against learner text, never learner input or gold
output labels. Explanatory context does not add a requirement to recite history.
"""
from backend.training_assessment import TYPED_QUESTIONS

PROPOSITIONS = {
 'surface_conflict': [
  {'flight':['TRN102 is held.'], 'reason':["A service vehicle obstructs TRN102's ground route."]},
  {'release':["TRN102's exercise ground hold has been released."], 'change':["TRN102's ground hold was released because the obstructing vehicle is now clear."]},
  {'unknown':['The reports do not confirm takeoff clearance for TRN102.'], 'scope':["Release of TRN102's ground hold does not establish permission to take off."]},
 ],
 'late_arrival': [
  {'flight':['TRN103 is waiting for Stand B.'], 'occupant':['Stand B is occupied by TRN102.']},
  {'availability':['Stand B is not yet confirmed available.'], 'plan':['A planned reposition does not confirm that Stand B is free.']},
  {'availability':['Stand B has been confirmed available for TRN103.'], 'release':["The confirmation of Stand B availability also confirms release of TRN103's exercise ground hold."]},
 ],
 'late_baggage': [
  {'delay':['A late baggage batch is delaying TRN102 loading.'], 'separation':['Fuel service for TRN102 is complete.','Fuel completion does not establish baggage-loading completion.']},
  {'estimate':['The latest target off-block estimate for TRN102 is 10:35.'], 'scope':['The target off-block time is an estimate and does not establish departure clearance.']},
  {'unknown':['Overall departure readiness remains unconfirmed despite service completion and ground release.'], 'scope':['Fuel and baggage completion and ground release do not establish takeoff clearance.','Fuel and baggage completion and ground release do not establish that every departure prerequisite is satisfied.']},
 ],
 'fog_restrictions': [
  {'procedures':['Low-visibility procedures are active.','Safeguarding is active.'], 'hold':['TRN101 remains held.','The reports do not provide departure clearance for TRN101.']},
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
