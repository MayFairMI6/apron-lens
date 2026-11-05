"""Authored dropped-load demonstration after the scored lessons and flight circuit.

The cart animation is presentation input. Only timestamped reports support answers.
Cleanup, inspection, service completion and movement release are separate updates.
"""


def add_baggage_incident(world, reservations, report, start):
    aircraft = world['aircraft'][1]
    parked = aircraft['waypoints'][-1]
    stand = next(e['facts'][0]['value'] for e in reversed(world['events'])
                 if e['aircraftId'] == 'A2' and e['facts'][0]['property'] == 'stand')
    world['incidents'].append(dict(id='baggage-dropped-load', kind='baggage_spill', aircraftId='A2',
        start=start, onset=start+6, clearedAt=start+40, end=start+85,
        x=parked['x']+.018, y=.00013, z=parked['z']-.018))
    world['taxiPaths'].append(dict(id='baggage-service-lane',kind='service',width=.016,
        points=[dict(x=parked['x']+.018,z=parked['z']-.035),
                dict(x=parked['x']+.018,z=parked['z']+.010)],turns=[]))
    world['flightShowcases'].append(dict(id='baggage-incident', aircraftId='A2', start=start, end=start+95))
    world['flightTeachingWindows'].append(dict(start=start, end=start+95))
    world['demoQuestions'] += [
        dict(id='baggage-spill-hold', at=start+14, aircraftId='A2',
             assistantQuestion='Why is TRN102 held near its stand?'),
        dict(id='baggage-cleanup-hold', at=start+47, aircraftId='A2',
             assistantQuestion='Has TRN102 been released after the baggage was collected?')]
    # Background traffic starts after this reservation. A1 remains held at closed A.
    reservations.append(dict(aircraftId='A2', start=start, end=start+90, kind='dropped-load-response'))
    aircraft.setdefault('phases', [])
    aircraft['phases'] += [dict(t=start+6, id='baggage_spill', label='Dropped baggage · movement held'),
                          dict(t=start+44, id='baggage_inspection', label='Bags collected · inspection pending'),
                          dict(t=start+59, id='baggage_inspected', label='Area inspected · movement held'),
                          dict(t=start+72, id='ground_release', label='Ground hold released')]
    report('A2baggageSpill', 'A2', start+6, 'baggage_status', 'paused: bags spilled from cart',
           f'Bags have fallen from a baggage cart beside TRN102 at Stand {stand}. Loading is paused. '
           'The cause and any equipment damage are unconfirmed.', 2, 'ground-handling')
    report('A2droppedLoadHold', 'A2', start+6, 'movement_condition',
           f'hold: dropped baggage obstructing Stand {stand} service area',
           f'TRN102 remains stopped. The affected service area at Stand {stand} is held for dropped baggage recovery.',
           1, 'ground-control')
    report('A2baggageCollected', 'A2', start+42, 'movement_condition',
           'hold: bags collected; inspection and movement release pending',
           'The recovery team reports the bags collected. TRN102 remains held while the area is inspected; '
           'collection alone does not release the aircraft.', 2, 'airfield-operations')
    report('A2baggageInspected', 'A2', start+57, 'movement_condition',
           'hold: service area inspected; movement release pending',
           'The affected service area has been inspected and found clear. TRN102 still awaits the exercise movement release.',
           2, 'airfield-operations')
    report('A2baggageResumed', 'A2', start+60, 'baggage_status', 'complete',
           'Ground handling reports the recovered baggage secured and loading complete for TRN102.', 2, 'ground-handling')
    report('A2baggageRelease', 'A2', start+70, 'movement_condition',
           'exercise ground hold released; keep clear of closed Stand A',
           'The exercise controller releases the dropped-baggage hold for TRN102. Stand A remains closed; '
           'no takeoff clearance or overall departure-readiness report is issued.', 2, 'ground-control')
