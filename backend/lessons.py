"""Three authored controller lessons over reproducible hour-long ground worlds.

Answer keys stay on the service. Movement plans are rendering input, never model
evidence. Every teaching answer cites reports received before its checkpoint.
"""
import random
from backend.traffic import DURATION
from backend.flight_cycle import add_flight_cycle
from backend.ground_routes import rounded_path, departure_path, timed_path, add_pavement

EXERCISES = ('surface_conflict', 'late_arrival', 'late_baggage')
TITLES = dict(surface_conflict='A vehicle on the route', late_arrival='An occupied arrival stand',
              late_baggage='A changing departure estimate')
OBJECTIVES = dict(surface_conflict='Follow a reported hold, recognise its release, and keep unknowns separate.',
                  late_arrival='Track the inbound aircraft and the stand it needs as the situation changes.',
                  late_baggage='Distinguish service progress, departure estimates and confirmed readiness.')

def build_lesson(seed, exercise):
    if exercise not in EXERCISES:
        raise ValueError('Unknown lesson')
    rng = random.Random(seed)
    world = dict(scenarioId=f'LESSON-{exercise}-{seed}', duration=DURATION, targetWidth=.7, livery='uniform',
        clockWhileUntracked='runs', trainingProfile=exercise, trainingRole='controller_awareness',
        trainingRoleLabel='Controller awareness', trainingObjective=OBJECTIVES[exercise],
        assistantQuestionLabels=['Latest report', 'What is still unknown?'],
        assistantQuestions=['What is the latest update for this aircraft?', 'Is this aircraft ready to depart?'],
        aircraft=[], events=[], visualProps=[], groundVehicles=[])
    last = {}; named = {}; reservations = []
    def report(name, aircraft, at, prop, value, text, lag=1, source='ground-control'):
        event_id = 'L'+str(len(world['events'])+1).zfill(3)
        fact = dict(property=prop, value=value)
        key = (aircraft, prop)
        if key in last: fact['supersedes'] = [last[key]]
        last[key] = event_id+':'+prop
        world['events'].append(dict(id=event_id, aircraftId=aircraft, flightInstance='TRN10'+aircraft[-1],
            source=source, eventTime=float(at), receiptTime=float(at+lag), facts=[fact], message=text))
        named[name] = event_id
        return event_id
    def waypoint(t, x, z, reverse=False):
        return dict(t=round(t, 3), x=x, z=z, reverse=reverse,heading=0)
    for i, x in enumerate((-.045, .035, .115)):
        aid = f'A{i+1}'; staging = exercise == 'late_arrival' and i == 2
        world['aircraft'].append(dict(id=aid, flightInstance=f'TRN10{i+1}',preciseHeading=True,
            waypoints=[waypoint(0, .24 if staging else x, -.10 if staging else .04)]))
        report(aid+'stand', aid, 0, 'stand', 'ground staging area' if staging else 'ABC'[i],
               f'TRN10{i+1} is at '+('the ground staging area.' if staging else 'Stand '+'ABC'[i]+'.'), 0, 'stand-planning')
        report(aid+'state', aid, 1, 'movement_status', 'holding at ground staging area' if staging else 'holding at stand',
               f'TRN10{i+1} is holding.', 0)
        report(aid+'route', aid, 2, 'route', 'apron ground circuit',
               'The reported route is within the apron. No runway or takeoff clearance is represented.', 0)

    def route(aid, start, points, speed=5, pushback=True):
        a = world['aircraft'][int(aid[-1])-1]; old = a['waypoints'][-1]
        if pushback:
            push,taxi,turns=departure_path((old['x'],old['z']),points)
            first=timed_path(push,start,speed=2,reverse=True);taxi_start=first[-1]['t']
            movement=first+timed_path(taxi,taxi_start,speed=speed)[1:]
            add_pavement(world,push);add_pavement(world,taxi,turns)
        else:
            taxi,turns=rounded_path([(old['x'],old['z']),*points]);taxi_start=start
            movement=timed_path(taxi,start,speed=speed);add_pavement(world,taxi,turns)
        a['waypoints'].extend(movement);t=movement[-1]['t']
        reservations.append(dict(aircraftId=aid, start=start, end=t, taxiStart=taxi_start,
                                 speedMetresPerSecond=speed))
        report(f'{aid}move{start}', aid, start, 'movement_status', 'pushback' if pushback else 'taxiing',
               f'{a["flightInstance"]} has started '+('pushback.' if pushback else 'taxiing.'), 1)
        if pushback: report(f'{aid}taxi{start}', aid, taxi_start, 'movement_status', 'taxiing',
                           f'{a["flightInstance"]} is taxiing on the apron.', 2)
        report(f'{aid}park{start}', aid, t, 'movement_status', 'parked', f'{a["flightInstance"]} has parked.', 1)
        if 'phases' in a:
            a['phases'] += [dict(t=start,id='pushback' if pushback else 'taxi_in',label='Pushback' if pushback else 'Apron taxi'),
                           dict(t=taxi_start,id='taxi_in',label='Apron taxi'),dict(t=t,id='parked',label='Parked')]
        return t

    if exercise == 'surface_conflict':
        report('hold', 'A2', 25, 'movement_condition', 'hold: vehicle obstructing ground route',
               'TRN102 is held because a service vehicle is obstructing its ground route.', rng.uniform(1,4))
        report('clear', 'A2', 100, 'movement_condition', 'exercise ground hold released',
               'The vehicle is clear. The exercise ground hold for TRN102 is released.', 4)
        world['groundVehicles'] = [dict(id='service-vehicle', waypoints=[waypoint(0,-.05,-.06),
            waypoint(25,.035,-.025),waypoint(90,.035,-.025),waypoint(100,-.05,-.06),waypoint(DURATION,-.05,-.06)])]
        route('A2', 110, [(.035,-.025),(.24,-.025),(.24,-.10),(-.12,-.10),(-.12,-.005),(.035,-.005),(.035,.04)])
        probes = [
            ('Which aircraft is held because of the vehicle?', ['TRN102','TRN101','TRN103','All three aircraft'],0,
             'The hold report names TRN102 and the service vehicle.', ['hold']),
            ('What has changed since the hold report?', ['The ground hold was released','Takeoff was cleared','All services were confirmed complete','The route is still reported blocked'],0,
             'The later report releases the ground hold after the vehicle clears.', ['hold','clear']),
            ('What is still unconfirmed?', ['Takeoff clearance','The vehicle obstruction was reported','TRN102 received a ground-hold update','The ground hold was released'],0,
             'The reports cover an apron hold and ground movement. They do not establish takeoff clearance.', ['A2route','clear'])]
        questions = ['Why is TRN102 holding?', 'What changed for TRN102?', 'Is TRN102 ready to depart?']
    elif exercise == 'late_arrival':
        report('arrival', 'A3', 20, 'movement_condition', 'hold: Stand B occupied by TRN102',
               'The late inbound TRN103 is waiting in the ground staging area. Stand B is occupied by TRN102.', 3, 'stand-planning')
        report('reposition', 'A2', 50, 'movement_condition', 'reposition to Stand C',
               'TRN102 will reposition from B to C. Stand B is not yet confirmed available.', 2, 'stand-planning')
        end = route('A2', 65, [(.035,-.025),(.115,-.025),(.115,.04)])
        report('parkC', 'A2', end, 'stand', 'C', 'TRN102 has parked at Stand C.', 1, 'stand-planning')
        report('available', 'A3', 132, 'movement_condition', 'Stand B available; exercise ground hold released',
               'Stand B is confirmed available for TRN103. Its exercise ground hold is released.', 2, 'stand-planning')
        report('assigned', 'A3', 133, 'stand', 'B', 'TRN103 is assigned Stand B.', 2, 'stand-planning')
        route('A3', 140, [(.24,-.025),(.035,-.025),(.035,.04)], speed=6, pushback=False)
        probes = [
            ('Which aircraft is waiting for the occupied stand?', ['TRN103','TRN102','TRN101','No aircraft'],0,
             'The inbound report identifies TRN103 as waiting for B, occupied by TRN102.', ['arrival']),
            ('At this checkpoint, is Stand B confirmed available?', ['Not yet confirmed','Yes, repositioning means it is free','Yes, the inbound is late','No, it is permanently closed'],0,
             'The repositioning report does not confirm availability. That confirmation arrives later.', ['reposition']),
            ('Which update allows the exercise arrival to continue?', ['Stand B was confirmed available','TRN103 was cleared for takeoff','Baggage completion was assumed','The inbound delay disappeared'],0,
             'Stand planning confirms B is available and releases the ground hold.', ['available','assigned'])]
        questions = ['Why is TRN103 waiting?', 'Is Stand B confirmed available for TRN103?', 'What changed for TRN103?']
    else:
        report('fuel', 'A2', 5, 'fuel_status', 'in progress', 'Fuel service for TRN102 is in progress.', 1, 'ground-handling')
        report('bags', 'A2', 10, 'baggage_status', 'delayed', 'A late baggage batch is delaying TRN102 loading.', 3, 'ground-handling')
        report('estimate', 'A2', 12, 'tobt', '10:20', 'The target off-block estimate for TRN102 is 10:20.', 2, 'operations')
        report('hold', 'A2', 15, 'movement_condition', 'hold: ground handling incomplete', 'TRN102 remains held while ground handling is incomplete.', 1)
        report('fuelDone', 'A2', 45, 'fuel_status', 'complete', 'Fuel service is complete for TRN102.', 2, 'ground-handling')
        report('newEstimate', 'A2', 75, 'tobt', '10:35', 'The target off-block estimate for TRN102 changes from 10:20 to 10:35.', 7, 'operations')
        report('bagsDone', 'A2', 130, 'baggage_status', 'complete', 'Baggage loading is complete for TRN102.', 4, 'ground-handling')
        report('clear', 'A2', 155, 'movement_condition', 'exercise ground hold released', 'The exercise ground hold for TRN102 is released.', 3)
        route('A2', 166, [(.035,-.025),(.24,-.025),(.24,-.10),(-.12,-.10),(-.12,-.005),(.035,-.005),(.035,.04)])
        probes = [
            ('What is delaying TRN102 in the received reports?', ['A late baggage batch','An occupied arrival stand','An engine failure','A confirmed runway closure'],0,
             'Ground handling reports delayed baggage. Fuel completion does not complete baggage loading.', ['bags','fuelDone']),
            ('What is the latest target off-block estimate?', ['10:35','10:20','Takeoff cleared now','No estimate was received'],0,
             'The received 10:35 estimate supersedes 10:20. It is still an estimate.', ['estimate','newEstimate']),
            ('Do service completion and ground release confirm overall departure readiness?', ['No, overall readiness remains unconfirmed','Yes, every prerequisite is established','Yes, takeoff clearance is implied','Yes, because the original estimate passed'],0,
             'Fuel, baggage and ground release are reported separately. No overall-readiness or takeoff-clearance report was received.', ['fuelDone','bagsDone','clear'])]
        questions = ['What is delaying TRN102?', 'What is the latest departure estimate for TRN102?', 'Is TRN102 ready to depart?']

    # The scored 210-second lesson is unchanged. A continuous local flight
    # circuit then demonstrates real altitude changes, departure and arrival.
    add_flight_cycle(world,reservations,report)
    # Reproducible background activity continues across the full hour, with one
    # whole-circuit reservation at a time. Each aircraft returns to its actual stand.
    slot = max(300, max((s['end'] for s in reservations), default=0)+15)
    order = [1,2]; rng.shuffle(order); cycle = 0
    while slot < DURATION-400:
        a=world['aircraft'][order[cycle%len(order)]]; x=a['waypoints'][-1]['x']; z=a['waypoints'][-1]['z']
        start = slot+rng.uniform(3,12)
        end=route(a['id'], start, [(x,-.025),(.28,-.025),(.28,-.14),(-.23,-.14),(-.23,-.005),(x,-.005),(x,z)],
                  speed=rng.uniform(4,6))
        slot=end+15;cycle+=1
    for a in world['aircraft']:
        p=a['waypoints'][-1];a['waypoints'].append(waypoint(DURATION,p['x'],p['z']))
    # Interpolation samples are immutable geometry, not new information boundaries.
    # Stop prediction at report arrivals, phase changes and actual stops/starts.
    world['predictionBoundaries']=sorted({t for r in reservations for k,t in r.items() if k in ('start','end','taxiStart')} |
        {p['t'] for a in world['aircraft'] for p in a.get('phases',[])} |
        {p['t'] for a in world['groundVehicles'] for p in a['waypoints']} |
        {i[k] for i in world.get('incidents',[]) for k in ('start','end')})
    world['events'].sort(key=lambda e:(e['receiptTime'],e['id']))
    checkpoints=[]
    for i,(question,choices,correct,explanation,refs) in enumerate(probes):
        # Shuffle answers without changing the answer key or world timing.
        order=list(range(4));rng.shuffle(order)
        checkpoints.append(dict(id=f'check-{i+1}',at=float(60*(i+1)),question=question,
            choices=[choices[k] for k in order],correct=order.index(correct),explanation=explanation,
            evidenceIds=[named[k] for k in refs],assistantQuestion=questions[i]))
    return world,reservations,checkpoints
