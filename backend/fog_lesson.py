"""A scored, independently timed fog lesson on the existing mapped T3 apron.

This reuses the demonstration's report meanings and stationary geometry, not its
one-hour clock. The 210-second teaching timings are authored, not operational.
"""
import random

from backend.runway_scenarios import build_demonstration
from backend.training_environment import validate_environment

FOG_LESSON = 'fog_restrictions'
TITLE = 'Fog and reported restrictions'
OBJECTIVE = 'In this condensed practice exercise, use the reports to distinguish low-visibility procedures, safeguarding and departure clearance.'
DURATION = 210


def build_fog_lesson(seed):
    world, _, _ = build_demonstration(seed, 'fog_visibility')
    world.update(scenarioId=f'LESSON-{FOG_LESSON}-{seed}', duration=DURATION,
                 trainingProfile=FOG_LESSON, trainingObjective=OBJECTIVE,
                 demoQuestions=[], flightShowcases=[], flightTeachingWindows=[])
    # Keep the measured map and parked position. Only teaching times change;
    # neither a clearer view nor a procedure cancellation moves the aircraft.
    for aircraft in world['aircraft']:
        aircraft['waypoints'] = [dict(aircraft['waypoints'][0], t=0),
                                 dict(aircraft['waypoints'][0], t=DURATION)]
    timings = {0: 0, 30: 10, 300: 20, 600: 35, 2400: 105, 2900: 145, 3000: 160}
    for event in world['events']:
        delay = event['receiptTime'] - event['eventTime']
        event['eventTime'] = float(timings[event['eventTime']])
        event['receiptTime'] = event['eventTime'] + delay
    world['events'].sort(key=lambda e: (e['receiptTime'], e['id']))
    world['lessonTiming'] = dict(kind='authored-short-lesson', duration=DURATION,
        relatedDemonstration='fog_visibility', demonstrationDuration=3600,
        note='Independently retimed for three scored checkpoints; not operational response times or a one-hour playback.')
    world['provenance']['limitations'] += ' This short scored practice is separate from the full-hour demonstration. Its timing is fictional.'
    world['assistantQuestionLabels'] = ['Reported restrictions', 'Departure authority']
    world['assistantQuestions'] = ['What restrictions are currently reported for TRN101?',
                                    'Do the received reports confirm departure clearance for TRN101?']
    times = (0, 10, 35, 65, 75, 90, 100, 160, DURATION)
    extinction = (0, .00035, .0012, .0012, .0007, .00008, 0, 0, 0)
    world['environment'] = dict(version=2, kind='fog', frames=[
        dict(t=t, precipitation=0, daylight=1, fogExtinctionPerMetre=f)
        for t, f in zip(times, extinction)])
    validate_environment(world['environment'], DURATION)
    world['predictionBoundaries'] = sorted(set(times) | {0, DURATION})

    # Report IDs are preserved from the related demonstration. Eligibility is
    # rechecked by TrainingSession against each short-lesson receipt cutoff.
    rows = [
        ('At this checkpoint, which restrictions are reported for TRN101?',
         ['Low-visibility procedures and safeguarding are active; TRN101 remains held',
          'Safeguarding was requested but has not been confirmed',
          'Only low-visibility procedures remain; safeguarding was cancelled',
          'TRN101 may depart because no aircraft is moving nearby'],
         'Airside Operations confirmed safeguarding, and the later tower report puts low-visibility procedures in force while keeping TRN101 held. Neither update is departure clearance.',
         ['R004', 'R005'], 'What restrictions are currently reported for TRN101?'),
        ('After low-visibility procedures are cancelled, what still applies to TRN101?',
         ['Safeguarding and the reported hold remain; departure is not cleared',
          'All restrictions ended with the low-visibility procedures',
          'The clearer view authorises TRN101 to depart',
          'Safeguarding is already confirmed cancelled'],
         'The cancellation report explicitly keeps safeguarding and the TRN101 hold in place. The visual improvement and cancellation of low-visibility procedures do not supply a departure clearance.',
         ['R005', 'R006'], 'What restrictions remain after low-visibility procedures are cancelled?'),
        ('Safeguarding cancellation is confirmed. What is still unconfirmed for TRN101?',
         ['Departure clearance; the flight remains parked',
          'Safeguarding cancellation, which is still only a request',
          'Whether low-visibility procedures were cancelled',
          'Nothing; cancellation of safeguarding confirms departure clearance'],
         'Airside Operations confirms safeguarding cancellation, superseding the earlier pending request. The latest report still does not confirm departure clearance for TRN101, which remains parked.',
         ['R006', 'R007', 'R008'], 'Does safeguarding cancellation confirm that TRN101 may depart?'),
    ]
    rng = random.Random(seed)
    probes = []
    for i, (question, choices, explanation, refs, assistant_question) in enumerate(rows):
        order = list(range(4)); rng.shuffle(order)
        probes.append(dict(id=f'check-{i+1}', at=float(60*(i+1)), aircraftId='A1',
            question=question, choices=[choices[k] for k in order], correct=order.index(0),
            explanation=explanation, evidenceIds=refs, assistantQuestion=assistant_question))
    return world, [], probes
