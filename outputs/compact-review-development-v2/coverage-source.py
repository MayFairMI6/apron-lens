"""Predeclared report-blind coverage topics; no expected factual answers."""
from backend.training_assessment import TYPED_QUESTIONS
TOPICS = {
 'surface_conflict': [
  {'flight':['Identity of the aircraft the learner says is held'], 'reason':['Obstruction or cause the learner describes for that hold']},
  {'release':['What the learner says happened to the ground hold'], 'change':['Reported change the learner connects to that hold outcome']},
  {'unknown':['What the learner says about the certainty of takeoff permission'], 'scope':['How the learner relates ground-hold status to takeoff permission']},
 ],
 'late_arrival': [
  {'flight':['Identity and stand or destination of the inbound aircraft as described by the learner'], 'occupant':['Identity of the aircraft the learner says occupies the stand']},
  {'availability':['Current stand availability as stated by the learner'], 'plan':['What the learner says a planned reposition establishes about stand availability']},
  {'availability':['Stand availability update and inbound aircraft as stated by the learner'], 'release':['Ground-hold outcome related to the stand update as stated by the learner']},
 ],
 'late_baggage': [
  {'delay':['Cause of the aircraft delay as stated by the learner'], 'separation':['Fuel-service status as stated by the learner','Baggage-service status as stated by the learner']},
  {'estimate':['Latest target off-block time as stated by the learner'], 'scope':['How the learner relates a time estimate to departure permission or readiness']},
  {'unknown':['Certainty of overall departure readiness as stated by the learner'], 'scope':['How the learner relates service or ground-hold completion to takeoff permission and remaining prerequisites']},
 ],
 'fog_restrictions': [
  {'procedures':['Low-visibility procedure status as stated by the learner','Safeguarding status as stated by the learner'], 'hold':['Aircraft hold or movement status as stated by the learner','Certainty of departure permission as stated by the learner']},
  {'partial_cancellation':['Low-visibility procedure status as stated by the learner','Safeguarding status as stated by the learner'], 'hold':['Aircraft hold or movement status as stated by the learner','Certainty of departure permission as stated by the learner']},
  {'confirmation':['Current safeguarding status and certainty as stated by the learner'], 'authority':['Aircraft position or movement status as stated by the learner','Certainty of departure permission as stated by the learner']},
 ],
}

def facets_for(payload):
    for exercise,questions in TYPED_QUESTIONS.items():
        if payload['question'] in questions:
            index=questions.index(payload['question']);topics=TOPICS[exercise][index]
            if list(topics)!=[c['id'] for c in payload['criteria'] if c['id']!='grounding']:
                raise ValueError('unsupported coverage criteria')
            return [{'id':key+'.'+str(i+1),'criterion':key,'topic':topic}
                    for key,items in topics.items() for i,topic in enumerate(items)]
    raise ValueError('unsupported coverage question')
