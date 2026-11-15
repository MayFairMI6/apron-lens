"""P01: an arriving stand that is not clear of equipment (M2 prevention branch).

Short scored lesson on the generic three-stand apron. A fuel-transfer vehicle
from the previous turnaround is left on Stand B while TRN103 waits to arrive.
The branch stops before any contact. Report timings are authored for three
teaching checkpoints and are not operational response times.

Informed by AAIB G-CIVU (Heathrow, 20 Dec 2019) and Heathrow OSI093. The cause
of that event is not modelled, and the vehicle leaving the scene is never
treated as evidence that the stand is clear.
"""
import random

from backend.ground_routes import rounded_path, timed_path, add_pavement

STAND_CLEARANCE_LESSON = 'stand_clearance'
TITLE = 'An arriving stand not clear of equipment'
OBJECTIVE = ('In this condensed practice exercise, keep the arrival hold until the reports confirm '
             'the stand-clearance check, not just the equipment removal.')
DURATION = 210
SOURCES = [
    'https://www.gov.uk/aaib-reports/aaib-investigation-to-boeing-747-436-g-civu',
    'https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/'
    'operational-safety-insttructions/ASGrOps_OSI_093_Aircraft_Arrival_Turnaround_and_Departure_on_Stand_v1.pdf',
]
STAND_B = (.035, .04)
STAGING = (.24, -.10)


def build_stand_clearance_lesson(seed):
    rng = random.Random(seed)
    world = dict(scenarioId=f'LESSON-{STAND_CLEARANCE_LESSON}-{seed}', duration=DURATION, targetWidth=.7,
        livery='uniform', clockWhileUntracked='runs', trainingProfile=STAND_CLEARANCE_LESSON,
        trainingRole='controller_awareness', trainingRoleLabel='Controller awareness', trainingObjective=OBJECTIVE,
        assistantQuestionLabels=['Arrival hold', 'Stand B status'],
        assistantQuestions=['Why is TRN103 holding?', 'Is Stand B confirmed clear for TRN103?'],
        aircraft=[], events=[], visualProps=[], groundVehicles=[],
        provenance=dict(kind='authored-precedent-informed', sources=SOURCES,
            limitations='Generic aircraft and stands; authored report wording, delays and timings. '
                        'Informed by an AAIB report and Heathrow OSI093, not a reconstruction. '
                        'The branch stops before contact and supplies no operational clearance.'),
        lessonTiming=dict(kind='authored-short-lesson', duration=DURATION,
            note='Three scored checkpoints in 210 source seconds; not operational response times.'))
    last = {}; named = {}

    def report(name, aircraft, at, prop, value, text, lag, source):
        event_id = 'S' + str(len(world['events']) + 1).zfill(3)
        fact = dict(property=prop, value=value)
        if (aircraft, prop) in last: fact['supersedes'] = [last[aircraft, prop]]
        last[aircraft, prop] = event_id + ':' + prop
        world['events'].append(dict(id=event_id, aircraftId=aircraft, flightInstance='TRN10' + aircraft[-1],
            source=source, eventTime=float(at), receiptTime=float(at + lag), facts=[fact], message=text))
        named[name] = event_id

    def still(t, x, z):
        return dict(t=float(t), x=x, z=z, reverse=False, heading=0)

    # TRN101 and TRN102 stay parked on A and C. Stand B is empty apart from the vehicle.
    for aid, (x, z), stand in (('A1', (-.045, .04), 'A'), ('A2', (.115, .04), 'C')):
        world['aircraft'].append(dict(id=aid, flightInstance='TRN10' + aid[-1], preciseHeading=True,
                                      waypoints=[still(0, x, z)]))
        report(aid + 'stand', aid, 0, 'stand', stand, f'TRN10{aid[-1]} is parked at Stand {stand}.', 0, 'stand-planning')
    inbound = dict(id='A3', flightInstance='TRN103', preciseHeading=True, waypoints=[still(0, *STAGING)])
    world['aircraft'].append(inbound)
    report('assigned', 'A3', 0, 'stand', 'B', 'Inbound TRN103 is assigned Stand B.', 0, 'stand-planning')
    report('waiting', 'A3', 1, 'movement_status', 'holding at ground staging area',
           'TRN103 is holding at the ground staging area.', 0, 'ground-control')

    # Report sequence from the register: vehicle reported, hold with check pending,
    # removal reported, then the completed check and an explicit release.
    report('vehicle', 'A3', 20, 'movement_condition', 'hold: equipment reported on Stand B',
           'A fuel-transfer vehicle from the previous turnaround is reported on Stand B. '
           'TRN103 is held at the ground staging area.', rng.uniform(1, 3), 'ground-handling')
    report('pending', 'A3', 30, 'movement_condition', 'hold: Stand B clearance check pending',
           'TRN103 remains held. A Stand B clearance check is requested and has not been completed.',
           3, 'stand-planning')
    report('removed', 'A3', 92, 'movement_condition',
           'hold: equipment removal reported; Stand B clearance check pending',
           'Ground handling reports the fuel-transfer vehicle removed from Stand B. '
           'The stand-clearance check is not yet reported complete, so TRN103 remains held.', 3, 'ground-handling')
    report('released', 'A3', 146, 'movement_condition',
           'Stand B clearance check complete; exercise arrival hold released',
           'The Stand B clearance check is complete. The exercise arrival hold for TRN103 is released.',
           4, 'stand-planning')

    # The vehicle drives off at 88 s, before the removal report reaches anyone.
    # An empty-looking stand is scenery, not a completed check.
    world['groundVehicles'] = [dict(id='service-vehicle', waypoints=[
        still(0, .045, .025), still(88, .045, .025), still(100, -.05, -.06), still(DURATION, -.05, -.06)])]

    path, turns = rounded_path([STAGING, (.24, -.025), (STAND_B[0], -.025), STAND_B])
    start = 158.
    movement = timed_path(path, start, speed=8)
    add_pavement(world, path, turns)
    end = movement[-1]['t']
    inbound['waypoints'].extend(movement)
    report('taxi', 'A3', start, 'movement_status', 'taxiing', 'TRN103 is taxiing to Stand B.', 1, 'ground-control')
    report('parked', 'A3', end, 'movement_status', 'parked', 'TRN103 has parked at Stand B.', 1, 'ground-control')
    for aircraft in world['aircraft']:
        aircraft['waypoints'].append(dict(aircraft['waypoints'][-1], t=float(DURATION)))
    world['events'].sort(key=lambda e: (e['receiptTime'], e['id']))
    world['predictionBoundaries'] = sorted({0., 88., 100., start, end, float(DURATION)})

    rows = [
        ('Why is TRN103 holding at the staging area?',
         ['Equipment is reported on Stand B and the stand-clearance check is pending',
          'Stand B is occupied by TRN102',
          'TRN103 is waiting for takeoff clearance',
          'A fuel spill has closed Stand B'],
         'Ground handling reports a fuel-transfer vehicle on Stand B, and stand planning keeps TRN103 held '
         'until a clearance check is done. Nothing reports a spill or another aircraft on the stand.',
         ['vehicle', 'pending'], 'Why is TRN103 holding?'),
        ('The vehicle removal has been reported. Is Stand B confirmed clear for TRN103?',
         ['Not yet; the stand-clearance check is still pending',
          'Yes, the removal report confirms the stand is clear',
          'Yes, the stand looks empty in the scene',
          'No, Stand B has been closed for the rest of the day'],
         'The removal report says the clearance check is not yet complete and TRN103 remains held. '
         'An empty-looking stand does not replace the check.',
         ['pending', 'removed'], 'Is Stand B confirmed clear for TRN103?'),
        ('Which update allowed TRN103 to continue to Stand B?',
         ['The completed Stand B clearance check and the explicit hold release',
          'The vehicle removal report on its own',
          'The vehicle no longer being visible on the stand',
          'A takeoff clearance for TRN103'],
         'Stand planning reports the clearance check complete and releases the exercise arrival hold. '
         'The earlier removal report kept the hold in place.',
         ['removed', 'released'], 'What allowed TRN103 to continue?'),
    ]
    probes = []
    for i, (question, choices, explanation, refs, assistant_question) in enumerate(rows):
        order = list(range(4)); rng.shuffle(order)
        probes.append(dict(id=f'check-{i+1}', at=float(60*(i+1)), aircraftId='A3', question=question,
            choices=[choices[k] for k in order], correct=order.index(0), explanation=explanation,
            evidenceIds=[named[k] for k in refs], assistantQuestion=assistant_question))
    return world, [], probes
