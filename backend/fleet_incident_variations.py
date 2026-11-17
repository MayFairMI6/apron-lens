# SUBSTANTIVE: authored report cutoffs and outcomes for two M2 return variations.
"""Report-led fleet returns using the existing 09R approach and rollout.

The exercise opens with the flight already airborne outside the airport view.
Early reports describe the departure incident. The visual segment covers final
approach and ground movement using the existing authored fleet trajectory.
"""
import copy

from backend.fleet_scenarios import TYPES, build_fleet

SINGLE_ENGINE_RETURN = 'fleet_b737_single_engine_return'
WILDLIFE_RETURN = 'fleet_a320_wildlife_return'
FLEET_VARIATIONS = (SINGLE_ENGINE_RETURN, WILDLIFE_RETURN)
VARIATION_TITLES = {
    SINGLE_ENGINE_RETURN: 'An emergency return',
    WILDLIFE_RETURN: 'A precautionary return',
}
VARIATION_OBJECTIVES = {
    SINGLE_ENGINE_RETURN: 'Track the reported reason for an emergency return, the landing outcome and any movement restrictions.',
    WILDLIFE_RETURN: 'Use the received reports to distinguish a wildlife sighting from a strike and assess what the aircraft inspection establishes.',
}
SYDNEY_ENGINE_FAILURE = 'https://www.atsb.gov.au/investigations/ao-2024-057'
NEWMAN_BIRD_STRIKE = 'https://www.atsb.gov.au/occurrence-briefs/ab-2025-019'
WILDLIFE_REPORTING = (
    'https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/'
    'operational-safety-insttructions/ASWHM_OSI_077_Wildlife_Hazards_and_Reporting_v3.pdf'
)


def build_fleet_variation(seed, exercise):
    if exercise not in FLEET_VARIATIONS:
        raise ValueError('Unknown fleet incident variation')

    # Reuse the published-reference approach and visually checked rollout. No
    # changes to the original builder, its four exercises or its outputs.
    world, _, _ = build_fleet(seed, 'fleet_b787_priority_landing')
    engine_case = exercise == SINGLE_ENGINE_RETURN
    aircraft_type = 'b737_800' if engine_case else 'a320_200'
    aircraft_order = (aircraft_type, *(kind for kind in TYPES if kind != aircraft_type))
    for plane, kind in zip(world['aircraft'], aircraft_order):
        plane['aircraftType'] = kind
    aircraft = world['aircraft'][0]
    phases = {p['id']: p['t'] for p in aircraft['phases']}
    touchdown, stop = phases['landing_roll'], phases['stopped']
    final = touchdown - 60
    aircraft['phases'] = [
        dict(t=0, id='airborne', label='Airborne outside the airport view'),
        dict(t=final, id='return_approach', label='Return approach'),
        *aircraft['phases'][1:],
    ]
    world.update(scenarioId=f'FLEET-{exercise}-{seed}', trainingProfile=exercise,
                 trainingObjective=VARIATION_OBJECTIVES[exercise], events=[], demoQuestions=[])
    world['provenance']['kind'] = 'authored-precedent-informed-fleet-variation'
    world['provenance']['sources'] += [SYDNEY_ENGINE_FAILURE] if engine_case else [NEWMAN_BIRD_STRIKE, WILDLIFE_REPORTING]
    world['provenance']['limitations'] = (
        'Fictional Heathrow report sequence, informed by the ATSB account of a single-engine return at Sydney. '
        if engine_case else
        'Fictional Heathrow report sequence, informed by the ATSB occurrence brief on an A320 bird strike at Newman '
        'and Heathrow wildlife reporting guidance. '
    ) + ('The visual shows the final approach and rollout using the fleet 09R reference motion. '
         'The departure occurrence, return routing, engine behaviour and the inspection itself are conveyed in the exercise reports. '
         'Timings, delay and findings are authored. This exercise gives no operational clearance or type-performance guidance.')

    last = {}

    def report(t, prop, value, message, source, lag=2):
        event_id = f'V{len(world["events"]) + 1:03d}'
        fact = dict(property=prop, value=value)
        if prop in last:
            fact['supersedes'] = [last[prop]]
        last[prop] = f'{event_id}:{prop}'
        world['events'].append(dict(id=event_id, aircraftId='A1', flightInstance='TRN101', source=source,
                                    eventTime=float(t), receiptTime=float(t + lag), facts=[fact], message=message))

    def cue(at, key, question):
        world['demoQuestions'].append(dict(id=key, at=at, aircraftId='A1', assistantQuestion=question))

    if engine_case:
        report(8, 'movement_condition', 'crew reports right engine failure after departure, cause unconfirmed',
               'TRN101 crew reports that its right engine failed after departure. The cause remains unconfirmed.', 'exercise-flight-crew')
        report(22, 'movement_status', 'airborne on one engine with emergency return requested',
               'TRN101 remains airborne on one engine and requests an emergency return. A landing is not yet reported.', 'exercise-flight-crew')
        cue(34, 'engine-return-request', 'What engine problem did TRN101 report, and what did the crew request?')
    else:
        report(0, 'movement_condition', 'birds sighted near departure path, strike not reported',
               'Airfield Operations reports birds near the departure path used by TRN101. No strike is reported.', 'exercise-airfield-operations', lag=0)
        report(60, 'movement_condition', 'crew suspects a bird strike, damage and engine effects unconfirmed',
               'TRN101 crew reports hearing impacts during departure and suspects a bird strike. Damage and any effect on the engines remain unconfirmed.',
               'exercise-flight-crew')
        report(74, 'movement_status', 'airborne with precautionary return requested',
               'TRN101 requests a precautionary return for inspection after the suspected strike. A landing is not yet reported.', 'exercise-flight-crew')
        cue(15, 'wildlife-warning', 'Does the bird sighting establish that TRN101 was struck?')
        cue(90, 'wildlife-return-request', 'Why did TRN101 request a return, and what remains unknown about the strike and engines?')

    report(final, 'route', 'return approach to Runway 09R',
           'The exercise tower reports TRN101 approaching Runway 09R for the return landing.', 'exercise-tower')
    report(touchdown, 'movement_status', 'landed and rolling out on Runway 09R',
           'TRN101 has landed and is rolling out on Runway 09R.', 'exercise-tower')
    report(stop, 'movement_status', 'landed safely and stopped on Runway 09R for inspection',
           'TRN101 landed safely and stopped on Runway 09R for inspection.', 'exercise-tower')
    if engine_case:
        report(stop + 3, 'movement_condition', 'runway occupied with inspection and recovery assessment pending',
               'Airfield Operations reports TRN101 still occupies Runway 09R. Inspection and recovery assessment are pending.',
               'exercise-airfield-operations')
        report(stop + 75, 'movement_condition', 'onward movement held with recovery requested and runway release unconfirmed',
               'TRN101 remains held on Runway 09R. Recovery assistance has been requested. Neither completed recovery nor a runway release has been reported.',
               'exercise-airfield-operations')
        cue(stop + 8, 'engine-landing', 'Has TRN101 landed, and where is it now?')
        cue(stop + 88, 'engine-recovery', 'May TRN101 move again, and has the runway been released?')
    else:
        report(stop + 65, 'movement_condition', 'inspection confirms bird strike and minor flap damage, engine condition unconfirmed',
               'Engineers confirm bird residue and minor flap damage on TRN101. Engine assessment is still pending. There is no onward movement or runway release.',
               'exercise-engineering')
        cue(stop + 76, 'wildlife-inspection', 'What did inspection confirm on TRN101, and what remains unknown about its engines?')

    world['flightShowcases'] = [dict(id=exercise, aircraftId='A1', start=final, end=3600)]
    world['flightTeachingWindows'] = [dict(start=touchdown - 15, end=stop + 12)]
    world['runwayReservations'] = [dict(aircraftId='A1', start=final, end=3600, kind=exercise)]
    world['predictionBoundaries'] = sorted({0., 3600., *(phase['t'] for phase in aircraft['phases'])})
    return world, copy.deepcopy(world['runwayReservations']), []
