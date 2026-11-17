# SUBSTANTIVE: authored surface movements, queue scheduling and report cutoffs for M2.
"""Bounded demonstrations of obstruction, road notices and weather-driven queues."""
import copy
import math
import random

from backend.ground_routes import add_pavement, departure_path, rounded_path, timed_path
from backend.runway_scenarios import build_demonstration
from backend.training_environment import validate_environment

APRON_OBSTRUCTION = 'apron_route_obstruction'
CONNECTOR_CLOSURE = 'connector_road_closure'
WEATHER_QUEUES = 'weather_runway_queues'
SURFACE_VARIATIONS = (APRON_OBSTRUCTION, CONNECTOR_CLOSURE, WEATHER_QUEUES)
SURFACE_TITLES = {
    APRON_OBSTRUCTION: 'An obstruction on the taxi route',
    CONNECTOR_CLOSURE: 'A connector road closure',
    WEATHER_QUEUES: 'Arrival and departure queues in fog',
}
SURFACE_OBJECTIVES = {
    APRON_OBSTRUCTION: 'Reconcile an issued taxi route with a newer obstruction report and identify the separate movement release.',
    CONNECTOR_CLOSURE: 'Follow the effective window, authorised diversion and reported reopening of an airside road.',
    WEATHER_QUEUES: 'Distinguish weather restrictions, stand availability and aircraft movement releases as the queues change.',
}
AAIB_OBSTRUCTION = 'https://www.gov.uk/aaib-reports/aaib-investigation-to-boeing-777-300-er-hl-7782-and-boeing-757-256-tf-fik'
HEATHROW_CLOSURE = ('https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/'
                    'operational-advice-notices/ASWorks_OAN_510_v4-1.pdf')
NATS_LOW_VISIBILITY = 'https://nats.aero/blog/2025/10/low-visibility-procedures-what-you-need-to-know/'
DURATION = 3600
STANDS = {'A': (-.045, .04), 'B': (.035, .04), 'C': (.115, .04)}


def pose(t, x, z, heading=0, y=0, pitch=0, gear=False):
    return dict(t=float(t), x=x, z=z, y=y, heading=heading, pitch=pitch, gearRetracted=gear)


def aircraft(aid, waypoints, phases):
    return dict(id=aid, flightInstance='TRN10' + aid[-1], preciseHeading=True, waypoints=waypoints, phases=phases)


def phase(t, key, label):
    return dict(t=t, id=key, label=label)


def report_writer(world):
    # Every operational fact is attributed to its reporting source and becomes
    # eligible only at receipt. Supersession invalidates stale versions even
    # when the old version arrives after the update.
    earlier = {}

    def report(aid, at, prop, value, message, source, lag=2, valid_from=None, valid_until=None):
        event_id = f'Q{len(world["events"]) + 1:03d}'
        fact = dict(property=prop, value=value)
        key = (aid, prop)
        if key in earlier:
            # Include older IDs directly so an unreceived intermediate update
            # cannot break supersession at this cutoff.
            fact['supersedes'] = list(earlier[key])
        earlier.setdefault(key, []).append(event_id + ':' + prop)
        if valid_from is not None:
            fact['validFrom'] = valid_from
        if valid_until is not None:
            fact['validUntil'] = valid_until
        world['events'].append(dict(id=event_id, aircraftId=aid, flightInstance='TRN10' + aid[-1],
                                    source=source, eventTime=float(at), receiptTime=float(at + lag),
                                    facts=[fact], message=message))
        return at + lag

    return report


def cue(world, aid, at, key, question):
    world['demoQuestions'].append(dict(id=key, at=at, aircraftId=aid, assistantQuestion=question))


def new_world(seed, exercise, objective, sources, limitations):
    return dict(scenarioId=f'SURFACE-{exercise}-{seed}', duration=DURATION, targetWidth=.7,
                livery='indexed', clockWhileUntracked='runs', trainingProfile=exercise,
                trainingRole='controller_awareness', trainingRoleLabel='Airfield operations',
                trainingObjective=objective,
                assistantQuestionLabels=['Latest report', 'What changed?'],
                assistantQuestions=['What is the latest report for this flight?', 'What changed for this flight?'],
                aircraft=[], events=[], visualProps=[], groundVehicles=[], incidents=[], demoQuestions=[],
                flightShowcases=[], flightTeachingWindows=[], taxiPaths=[], runwayReservations=[],
                provenance=dict(kind='authored-precedent-informed', sources=sources, limitations=limitations))


def build_surface_variation(seed, exercise):
    builders = {APRON_OBSTRUCTION: build_apron_obstruction, CONNECTOR_CLOSURE: build_connector_closure,
                WEATHER_QUEUES: build_weather_queues}
    if exercise not in builders:
        raise ValueError('Unknown surface variation')
    return finish_world(builders[exercise](seed))


def finish_world(world):
    for plane in world['aircraft']:
        if plane['waypoints'][-1]['t'] < DURATION:
            plane['waypoints'].append(dict(plane['waypoints'][-1], t=float(DURATION)))
    world['predictionBoundaries'] = sorted({0., float(DURATION),
        *(p['t'] for plane in world['aircraft'] for p in plane['phases']),
        *(frame['t'] for frame in world.get('environment', {}).get('frames', []))})
    world['events'].sort(key=lambda event: (event['receiptTime'], event['id']))
    return world, copy.deepcopy(world['runwayReservations']), []


def build_apron_obstruction(seed):
    world = new_world(seed, APRON_OBSTRUCTION, SURFACE_OBJECTIVES[APRON_OBSTRUCTION], [AAIB_OBSTRUCTION],
                      'Fictional three-stand apron with authored aircraft positions and report timings. '
                      'The AAIB ground collision informs the obstruction only. Both flights stop short of contact in this exercise.')
    report = report_writer(world)
    adjustment = 130 + random.Random(seed).randrange(12)
    # The adjacent aircraft faces north. A 15.5 m tail reaches into the
    # westbound taxi envelope when the visual root is one metre north of z=0.
    # Hold the passing aircraft 55 m east of Stand B until the release arrives.
    waiting = (.090, -.025)
    passing_start = (.186, -.025)
    x_b, _ = STANDS['B']
    short_park = (x_b, .001)
    approach, _ = rounded_path([passing_start, waiting])
    approach = timed_path(approach, 12, end=24)
    correction, _ = rounded_path([short_park, STANDS['B']])
    correction = timed_path(correction, adjustment, speed=2)
    parked = correction[-1]['t']
    onward, _ = rounded_path([waiting, (-.145, -.025)])
    onward = timed_path(onward, 214, speed=6)
    west = onward[-1]['t']
    world['aircraft'] = [
        aircraft('A1', [pose(0, *passing_start, heading=270), *approach, *onward], [
            phase(0, 'waiting', 'Waiting at east staging point'), phase(12, 'taxiing', 'Apron taxi'),
            phase(24, 'holding', 'Stopped east of Stand B'), phase(214, 'resumed', 'Apron taxi resumed'),
            phase(west, 'west_staging', 'Stopped at west staging point')]),
        aircraft('A2', [pose(0, *short_park), *correction], [
            phase(0, 'stand_mouth', 'Stopped at stand entrance'), phase(adjustment, 'repositioning', 'Moving farther into Stand B'),
            phase(parked, 'parked', 'Parked at Stand B')]),
        aircraft('A3', [pose(0, *STANDS['A'])], [phase(0, 'parked', 'Parked at Stand A')]),
    ]
    report('A1', 5, 'route', 'westbound apron route past Stand B',
           'Ground control issues a westbound apron route past Stand B to TRN101.', 'exercise-ground-control')
    report('A2', 15, 'movement_status', 'stopped short of the Stand B parking position',
           'TRN102 reports stopping short of the Stand B parking position. Its tail protrudes into the adjacent taxi route.', 'exercise-flight-crew')
    report('A1', 22, 'movement_condition', 'hold east of Stand B because TRN102 protrudes into the taxi route',
           'Ground control stops TRN101 east of Stand B after TRN102 reports its tail protruding into the route. The earlier route is suspended.',
           'exercise-ground-control')
    report('A1', 24, 'movement_status', 'stopped east of Stand B',
           'TRN101 reports stopped east of Stand B.', 'exercise-flight-crew')
    report('A2', adjustment - 4, 'movement_condition', 'authorised to move farther into Stand B',
           'Ground control authorises TRN102 to move farther into Stand B while the adjacent taxi route stays held.', 'exercise-ground-control')
    report('A2', parked, 'movement_status', 'fully parked at Stand B',
           'TRN102 reports reaching its full parking position at Stand B.', 'exercise-flight-crew')
    report('A1', parked + 4, 'movement_condition', 'hold remains after TRN102 corrected its position',
           'Airfield Operations reports TRN102 fully parked. TRN101 remains held pending confirmation of the taxi route release.',
           'exercise-airfield-operations')
    report('A1', 208, 'movement_condition', 'exercise westbound apron route released past Stand B',
           'Ground control confirms the westbound apron route is released for TRN101 after the stand position is corrected.', 'exercise-ground-control')
    report('A1', 214, 'movement_status', 'taxiing westbound past Stand B',
           'TRN101 has resumed taxiing westbound.', 'exercise-ground-control')
    report('A1', west, 'movement_status', 'stopped at the west staging point',
           'TRN101 is stopped at the west staging point after passing Stand B.', 'exercise-ground-control')
    cue(world, 'A1', 65, 'obstruction-hold', 'Why did TRN101 stop even though it already had a taxi route?')
    cue(world, 'A1', 180, 'obstruction-repositioned', 'Does the new parking position release TRN101 to continue?')
    cue(world, 'A1', 272, 'obstruction-release', 'Which report let TRN101 continue past Stand B?')
    world['flightShowcases'] = [dict(id='obstruction-east-hold', aircraftId='A1', start=0, end=100),
                                dict(id='obstruction-stand', aircraftId='A2', start=100, end=parked + 12),
                                dict(id='obstruction-released', aircraftId='A1', start=208, end=west + 12)]
    world['flightTeachingWindows'] = [dict(start=10, end=30), dict(start=adjustment - 3, end=parked + 5),
                                      dict(start=208, end=west + 5)]
    return world


def build_connector_closure(seed):
    world = new_world(seed, CONNECTOR_CLOSURE, SURFACE_OBJECTIVES[CONNECTOR_CLOSURE], [HEATHROW_CLOSURE],
                      'Fictional notice and compressed source times informed by Heathrow OAN510 v4.1. The exercise is a road-status '
                      'briefing. The parked aircraft supplies its coordination context. No vehicle route, live road authority or actual works status is depicted.')
    reference, _, _ = build_demonstration(seed, 'fog_visibility')
    world['geography'] = reference['geography']
    world['aircraft'] = reference['aircraft']
    active = world['aircraft'][0]
    world['geography']['focusX'] = active['waypoints'][0]['x']
    world['geography']['focusZ'] = active['waypoints'][0]['z']
    report = report_writer(world)
    jitter = random.Random(seed).randrange(9)
    report('A1', 30, 'trajectory_checkpoint', 'planned closure window for Pier 6 Road South, 02:00 to 05:00 scenario time',
           'Works Coordination issues a future Pier 6 Road South closure notice for 02:00 to 05:00 scenario time. '
           'A diversion across Stand 307 is planned and still needs confirmation.', 'exercise-works-coordination',
           valid_from=120, valid_until=300)
    report('A1', 120 + jitter, 'movement_condition', 'Pier 6 Road South closed for works, diversion availability pending',
           'Airfield Operations reports Pier 6 Road South closed for works. The diversion is not yet confirmed usable.',
           'exercise-airfield-operations')
    report('A1', 172, 'route', 'authorised diversion across Stand 307 for the affected ground vehicles',
           'Airfield Operations confirms vehicles supporting TRN101 may use the authorised diversion across Stand 307. Pier 6 Road South stays closed.',
           'exercise-airfield-operations')
    report('A1', 244, 'movement_condition', 'Pier 6 Road South remains closed with reopening expected at 05:00 scenario time',
           'Works Coordination expects Pier 6 Road South to reopen at 05:00 scenario time. It remains closed pending a reopening confirmation.',
           'exercise-works-coordination')
    report('A1', 315 + jitter, 'movement_condition', 'Pier 6 Road South reopened, original ground route restored',
           'Airfield Operations confirms Pier 6 Road South has reopened and the original route is restored for the ground vehicles supporting TRN101.',
           'exercise-airfield-operations')
    report('A1', 315 + jitter, 'route', 'Pier 6 Road South restored, temporary diversion ended',
           'The temporary diversion across Stand 307 has ended following the reopening of Pier 6 Road South.', 'exercise-airfield-operations')
    cue(world, 'A1', 52, 'connector-notice', 'Is the Pier 6 Road South closure active now, and is there an authorised diversion yet?')
    cue(world, 'A1', 205, 'connector-diversion', 'Which ground-vehicle route is authorised while Pier 6 Road South is closed?')
    cue(world, 'A1', 306, 'connector-expected', 'The planned reopening time has passed. What road status is confirmed?')
    cue(world, 'A1', 373, 'connector-restored', 'Which road has reopened, and what changed for the diversion?')
    return world


def queued_departure(world, demand, start):
    stand = STANDS[demand['stand']]
    push, taxi, turns = departure_path(stand, [(stand[0], -.025), (-.28, -.025), (-.28, -.28),
                                               (-.8, -.28), (-.8, -.35)])
    push_motion = timed_path(push, start, speed=2, reverse=True)
    stand_clear = push_motion[-1]['t']
    taxi_motion = timed_path(taxi, stand_clear, speed=8)
    lineup, lineup_turns = rounded_path([(-.8, -.35), (-.8, -.4), (-.74, -.4)], radius=.020)
    lineup_start = taxi_motion[-1]['t']
    lineup_motion = timed_path(lineup, lineup_start, speed=5)
    roll_start = lineup_motion[-1]['t']
    for path, arcs in ((push, ()), (taxi, turns), (lineup, lineup_turns)):
        add_pavement(world, path, arcs)
    points = [pose(0, *stand), *push_motion, *taxi_motion[1:], *lineup_motion[1:]]
    for seconds in range(1, 39):
        # A 38 s authored roll reaches 64 m/s. Motion uses metres, stored in km.
        distance = 32 * seconds * seconds / 38
        points.append(pose(round(roll_start + seconds, 3), -.74 + distance / 1000, -.4,
                           heading=90, pitch=max(0, 2 * (seconds - 34))))
    airborne = roll_start + 38
    clear = round(airborne + 9, 3)
    for seconds in (1, 4, 9, 20, 35, 100):
        altitude = 3 * seconds ** 2 / 8 if seconds <= 8 else 6 * (seconds - 4)
        points.append(pose(round(airborne + seconds, 3), .476 + .064 * seconds, -.4, heading=90,
                           y=altitude / 1000, pitch=8 if seconds <= 20 else 3, gear=seconds >= 20))
    # Continue beyond the depicted airport; a departure never freezes just off
    # the runway or re-enters the training scene.
    outside = points[-1]['t']
    points.append(pose(DURATION, points[-1]['x'] + .064 * (DURATION - outside), -.4, heading=90,
                       y=points[-1]['y'], pitch=0, gear=True))
    phases = [phase(0, 'at_stand', 'At Stand ' + demand['stand']), phase(start, 'pushback', 'Pushback'),
              phase(stand_clear, 'taxi_out', 'Taxi to Runway 09'), phase(lineup_start, 'line_up', 'Entering Runway 09'),
              phase(roll_start, 'takeoff_roll', 'Takeoff roll'), phase(airborne, 'liftoff', 'Liftoff'),
              phase(clear, 'departed', 'Climbing away'), phase(outside, 'outside_area', 'Beyond the airport view')]
    return dict(plane=aircraft(demand['aircraftId'], points, phases), standClear=stand_clear,
                runwayStart=lineup_start, runwayEnd=clear, complete=clear)


def queued_arrival(world, demand, start):
    touchdown = start + 14
    final_x = -.620
    speed = 55
    slope = math.tan(math.radians(3))
    points = []
    # Reach a common final continuously from outside the local view. The queue
    # stage is a report, not a depiction of a published airborne hold pattern.
    for t in (*range(0, touchdown - 30, 30), *range(touchdown - 30, touchdown + 1)):
        remaining = touchdown - t
        x = final_x - speed * remaining / 1000
        # Match the 3-degree descent at the start of the eased flare. Root
        # height and pitch are illustrative and do not model flying technique.
        height = speed * slope * (remaining if remaining >= 6 else remaining ** 2 / 6)
        points.append(pose(t, x, -.4, heading=90, y=min(.90, height / 1000),
                           pitch=(3 + max(0, 6 - remaining) / 2), gear=remaining > 30))
    rollout = 32
    taxi_speed = 8
    for seconds in range(1, rollout + 1):
        distance = speed * seconds - (speed - taxi_speed) * seconds ** 2 / (2 * rollout)
        points.append(pose(touchdown + seconds, final_x + distance / 1000, -.4, heading=90,
                           pitch=6 * max(0, 1 - seconds / 8)))
    stand = STANDS[demand['stand']]
    exit_path, turns = rounded_path([(points[-1]['x'], -.4), (.5, -.4), (.5, -.33), (.5, -.10),
                                      (stand[0], -.10), stand], radius=.024)
    exit_motion = timed_path(exit_path, touchdown + rollout, speed=taxi_speed)
    points.extend(exit_motion[1:])
    add_pavement(world, exit_path, turns)
    clear = next(p['t'] for p in exit_motion if p['z'] >= -.33)
    at_stand = exit_motion[-1]['t']
    phases = [phase(0, 'outside_area', 'Airborne outside the airport view'),
              phase(demand['requestReceived'], 'arrival_queue', 'Arrival queue outside the airport view'),
              phase(start, 'final', 'Final approach'), phase(touchdown, 'landed', 'Touchdown and rollout'),
              phase(clear, 'taxi_in', 'Runway vacated, taxi to Stand ' + demand['stand']),
              phase(at_stand, 'parked', 'Parked at Stand ' + demand['stand'])]
    return dict(plane=aircraft(demand['aircraftId'], points, phases), touchdown=touchdown,
                runwayStart=start, runwayEnd=clear, complete=at_stand)


def allocate_queue(world, demands, restricted, limited_slot, recovered):
    """Allocate one exclusive movement at a time, with runway and stand capacity.

    Restricted mode permits at most one departure before the explicit release.
    The small authored layout serialises the shared taxi routes as well as the
    runway. Stand capacity is acquired before an arrival can get a runway slot.
    """
    free_at = {'A': DURATION, 'B': DURATION}
    waiting = sorted(demands, key=lambda d: (d['requestReceived'], d['aircraftId']))
    allocated = []
    busy_until = 0
    limited_used = False
    for clock in range(DURATION):
        if not waiting:
            return allocated
        restricted_now = restricted <= clock < recovered
        if clock < busy_until or (restricted_now and (clock < limited_slot or limited_used)):
            continue
        ready = next((job for job in waiting if job['requestReceived'] + 2 <= clock and
                      (job['direction'] == 'departure' or (not restricted_now and free_at[job['stand']] <= clock))), None)
        if ready is None:
            continue
        departure = ready['direction'] == 'departure'
        result = queued_departure(world, ready, clock) if departure else queued_arrival(world, ready, clock)
        free_at[ready['stand']] = result.get('standClear', DURATION)
        busy_until = math.ceil(result['complete']) + 20
        limited_used |= restricted_now
        waiting.remove(ready)
        allocated.append((ready, dict(result, start=clock)))
    raise ValueError('Authored queues could not clear within the exercise hour')


def build_weather_queues(seed):
    world = new_world(seed, WEATHER_QUEUES, SURFACE_OBJECTIVES[WEATHER_QUEUES], [NATS_LOW_VISIBILITY],
                      'Fictional runway and stands. NATS supports the qualitative link between low visibility and additional precautions. '
                      'Demand, reservation windows and the limited-capacity policy use authored teaching values. They do not estimate Heathrow throughput, '
                      'spacing or operational minima. Airborne queue positions outside the airport view are illustrative. Fog rendering never issues a clearance.')
    world['runway'] = dict(id='09/27', x=0, z=-.4, length=1.8, width=.045)
    rng = random.Random(seed)
    demands = [dict(aircraftId=aid, direction=direction, stand=stand, scheduled=scheduled,
                    requestReceived=scheduled + rng.randrange(0, 11))
               for aid, direction, stand, scheduled in [('A1', 'departure', 'A', 35), ('A2', 'arrival', 'B', 345),
                                                         ('A3', 'departure', 'B', 380), ('A4', 'arrival', 'A', 410)]]
    restricted, limited_slot, recovered = 305, 550, 750
    allocated = allocate_queue(world, demands, restricted, limited_slot, recovered)
    world['aircraft'] = sorted((movement['plane'] for _, movement in allocated), key=lambda plane: plane['id'])
    world['environment'] = dict(version=2, kind='fog', frames=[
        dict(t=t, precipitation=0, daylight=1, fogExtinctionPerMetre=density)
        for t, density in [(0, 0), (230, 0), (290, .0012), (475, .0012), (570, .00035), (625, 0), (3600, 0)]])
    validate_environment(world['environment'], DURATION)
    append_queue_reports(world, allocated, restricted, limited_slot, recovered)
    return world


def append_queue_reports(world, allocated, restricted, limited_slot, recovered):
    report = report_writer(world)
    departures = {job['stand']: result for job, result in allocated if job['direction'] == 'departure'}
    demand_records = []
    stands = []
    for job, result in allocated:
        aid = job['aircraftId']
        flight = result['plane']['flightInstance']
        direction, stand = job['direction'], job['stand']
        start, finish = result['start'], result['complete']
        scheduled, received = job['scheduled'], job['requestReceived']
        departure = direction == 'departure'
        schedule_label = f'{scheduled // 60:02d}:{scheduled % 60:02d}'
        report(aid, 0, 'route', f'planned {direction} via Runway 09 at {schedule_label} scenario time',
               f'The original plan lists {flight} for {direction} via Runway 09 at {schedule_label} scenario time. '
               f'Stand {stand} is planned. The schedule gives no movement authority.', 'exercise-sequencing', lag=0)
        queue = 'waiting at its stand in the departure queue' if departure else 'waiting in the arrival queue outside the airport view'
        report(aid, scheduled, 'movement_status', queue,
               f'{flight} is {queue}.', 'exercise-sequencing', lag=received - scheduled)
        if start >= restricted:
            report(aid, restricted - 2, 'movement_condition', 'low-visibility restriction active with a single departure slot and arrivals held',
                   'The exercise tower confirms low-visibility restrictions. The runway plan changes to one departure slot with arrivals held. '
                   f'{flight} still requires its own movement release.', 'exercise-tower')
            estimate = limited_slot if departure else recovered + 30
            estimate_label = f'{estimate // 60:02d}:{estimate % 60:02d}'
            report(aid, received + 4, 'route', f'revised {direction} estimate at or after {estimate_label} scenario time',
                   f'The sequencing estimate for {flight} is now {estimate_label} scenario time or later. '
                   'The estimate does not confirm a runway slot or movement release.', 'exercise-sequencing')
        if aid == 'A2':
            report(aid, received + 9, 'movement_condition', 'arrival held with Stand B occupied by TRN103',
                   'Sequencing holds TRN102 in the arrival queue. TRN103 still occupies Stand B, and limited runway sequencing remains active.',
                   'exercise-sequencing')
            old_update = 490
            report(aid, old_update, 'movement_condition', 'Stand B occupied with no slot for TRN102',
                   'Sequencing lists Stand B as occupied by TRN103. No runway slot is assigned to TRN102.',
                   'exercise-sequencing', lag=start + 4 - old_update)
            stand_clear = departures[stand]['standClear']
            report(aid, stand_clear, 'movement_condition', 'Stand B now available, arrival release still awaited',
                   'Stand Planning confirms TRN103 moved clear of Stand B. TRN102 now has an available stand and still awaits its runway release.',
                   'exercise-stand-planning')
        if start >= recovered:
            report(aid, recovered - 2, 'movement_condition', 'low-visibility restriction lifted, flight-specific release still awaited',
                   'The exercise tower confirms the low-visibility restriction has lifted. Runway 09 resumes shared arrivals and departures. The remaining arrival queue still needs sequencing, '
                   f'and {flight} still awaits its own runway movement release.', 'exercise-tower')
        report(aid, start - 1, 'movement_condition', f'exercise {direction} released for Runway 09',
               f'The exercise tower authorises the next {direction} movement for {flight} via Runway 09. '
               + (f'Stand {stand} is reserved for its arrival.' if not departure else f'{flight} may push back and taxi for this departure sequence.'),
               'exercise-tower', lag=1)
        if departure:
            report(aid, start, 'movement_status', f'pushback from Stand {stand}',
                   f'{flight} begins pushback from Stand {stand}.', 'exercise-ground-control')
            report(aid, finish, 'movement_status', 'departed Runway 09 and climbing',
                   f'{flight} has departed Runway 09 and is climbing.', 'exercise-tower')
            stands.append(dict(stand=stand, aircraftId=aid, start=0, end=result['standClear'], occupiedAt=0))
        else:
            report(aid, result['touchdown'], 'movement_status', 'landed on Runway 09 and rolling out',
                   f'{flight} has landed and is rolling out on Runway 09.', 'exercise-tower')
            report(aid, finish, 'movement_status', f'parked at Stand {stand}',
                   f'{flight} has parked at Stand {stand}.', 'exercise-ground-control')
            stands.append(dict(stand=stand, aircraftId=aid, start=start, end=DURATION, occupiedAt=finish))
        world['runwayReservations'].append(dict(aircraftId=aid, start=result['runwayStart'],
                                                end=result['runwayEnd'], kind=direction))
        world['flightShowcases'].append(dict(id=f'queue-{aid}', aircraftId=aid, start=start, end=finish + 5))
        world['flightTeachingWindows'].append(dict(start=result['runwayStart'], end=result['runwayEnd'] + 4))
        demand_records.append(dict(job, movementStart=start, complete=finish, waitSeconds=start - received))

    arrival = next(job for job in demand_records if job['aircraftId'] == 'A2')
    cue(world, 'A2', 465, 'queue-building', 'Why is TRN102 waiting, and what is reported about its stand?')
    cue(world, 'A3', 660, 'queue-visibility', 'What permits TRN103 to move, and does the limited sequence release other flights?')
    cue(world, 'A2', arrival['movementStart'] + 10, 'queue-recovery', 'Which update now governs TRN102 after the older stand report arrived?')
    world['standReservations'] = sorted(stands, key=lambda r: (r['stand'], r['start']))
    world['queueDemand'] = demand_records
    world['queueOperatingStates'] = [dict(t=0, status='normal'), dict(t=restricted, status='restricted'),
                                     dict(t=limited_slot, status='one_limited_departure_available'), dict(t=recovered, status='recovery')]
    # Telemetry is independent of guidance or learner responses and is never
    # supplied as evidence. Joining occurs at request receipt, leaving at release.
    times = sorted({0, *(r['requestReceived'] for r in demand_records), *(r['movementStart'] for r in demand_records)})
    world['queueTrace'] = [dict(t=t, **{direction: [r['aircraftId'] for r in demand_records
        if r['direction'] == direction and r['requestReceived'] <= t < r['movementStart']]
        for direction in ('arrival', 'departure')}) for t in times]
    world['queueMetrics'] = dict(
        peakArrival=max(len(row['arrival']) for row in world['queueTrace']),
        peakDeparture=max(len(row['departure']) for row in world['queueTrace']),
        totalWaitSeconds=sum(row['waitSeconds'] for row in demand_records),
        recoverySeconds=round(max(row['complete'] for row in demand_records) - recovered, 3))
