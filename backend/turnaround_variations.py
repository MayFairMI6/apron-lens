# SUBSTANTIVE: authored evidence transitions for M2 restriction and turnaround tasks.
"""Report-led debris recovery, winter handover and fuel interruption cases."""
import random

from backend.ground_routes import departure_path, rounded_path, timed_path
from backend.surface_queue_variations import STANDS, aircraft, cue, finish_world, new_world, phase, pose, report_writer
from backend.training_environment import validate_environment

DEBRIS_RECOVERY = 'debris_route_reopening'
WINTER_HANDOVER = 'winter_surface_handover'
FUEL_INTERRUPTION = 'fuel_service_interruption'
TURNAROUND_VARIATIONS = (DEBRIS_RECOVERY, WINTER_HANDOVER, FUEL_INTERRUPTION)
TURNAROUND_TITLES = {
    DEBRIS_RECOVERY: 'A debris report on the apron',
    WINTER_HANDOVER: 'A winter turnaround handover',
    FUEL_INTERRUPTION: 'An interruption to fuelling',
}
TURNAROUND_OBJECTIVES = {
    DEBRIS_RECOVERY: 'Track the object report, route closure, inspection and explicit reopening.',
    WINTER_HANDOVER: 'Keep surface treatment, aircraft de-icing, readiness and movement release separate in a winter handover.',
    FUEL_INTERRUPTION: 'Report what interrupted fuelling, which restriction applies and what remains outstanding for the departure.',
}
HEATHROW_BASE = 'https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/'
FOD_GUIDANCE = HEATHROW_BASE + 'operational-safety-insttructions/ASGrOps_OSI_081-Airside-Cleanliness-and-FOD-Management_v-2.pdf'
SNOW_PLAN = HEATHROW_BASE + 'winter-operations/Airside_SMS_Plan_AdverseWeather_Heathrow_Snow_Plan_Airside_2026_27.pdf'
FUELLING_GUIDANCE = HEATHROW_BASE + 'operational-safety-insttructions/ASGrOps_OSI_019_Fuelling_of_Aircraft_v3.pdf'


def build_turnaround_variation(seed, exercise):
    builders = {DEBRIS_RECOVERY: build_debris_recovery, WINTER_HANDOVER: build_winter_handover,
                FUEL_INTERRUPTION: build_fuel_interruption}
    if exercise not in builders:
        raise ValueError('Unknown turnaround variation')
    return finish_world(builders[exercise](seed))


def turnaround_world(seed, exercise, source, limitations):
    world = new_world(seed, exercise, TURNAROUND_OBJECTIVES[exercise], [source], limitations)
    for aid, stand in (('A2', 'B'), ('A3', 'C')):
        world['aircraft'].append(aircraft(aid, [pose(0, *STANDS[stand])], [phase(0, 'parked', f'Parked at Stand {stand}')]))
    return world


def build_debris_recovery(seed):
    world = turnaround_world(seed, DEBRIS_RECOVERY, FOD_GUIDANCE,
                             'Generic apron and fictional closure, recovery and inspection reports informed by Heathrow FOD guidance. '
                             'The object origin is unresolved. The scenario makes no claim about real works, a specific terminal or an actual reopening.')
    report = report_writer(world)
    recovered = 122 + random.Random(seed).randrange(12)
    start = 257
    staging = (.186, -.025)
    route, _ = rounded_path([staging, (-.145, -.025)])
    movement = timed_path(route, start, speed=6)
    stop = movement[-1]['t']
    world['aircraft'].insert(0, aircraft('A1', [pose(0, *staging, heading=270), *movement], [
        phase(0, 'held', 'Waiting at east staging point'), phase(start, 'taxiing', 'Taxi on the reopened apron route'),
        phase(stop, 'west_staging', 'Stopped at west staging point')]))
    report('A1', 14, 'movement_condition', 'unidentified object reported near the westbound apron route',
           'A ground crew reports an unidentified object near the westbound apron route. Its exact location and origin are unconfirmed.', 'exercise-ground-handling')
    report('A1', 28, 'movement_condition', 'westbound apron route closed after object located',
           'Airfield Operations locates the object on the westbound apron route and closes that route. TRN101 remains at the east staging point.', 'exercise-airfield-operations')
    report('A1', recovered, 'movement_condition', 'object recovered, origin unconfirmed and route inspection pending',
           'Airfield Operations reports the object recovered. Its origin remains unknown. The route stays closed pending inspection.', 'exercise-airfield-operations')
    report('A1', 205, 'movement_condition', 'inspection complete, westbound apron route still closed',
           'Airfield Operations reports the inspection complete. The westbound route remains closed pending a separate reopening update.', 'exercise-airfield-operations')
    report('A1', 248, 'movement_condition', 'westbound apron route reopened and released for TRN101',
           'Ground control confirms the westbound apron route has reopened and releases TRN101 to taxi on it.', 'exercise-ground-control')
    report('A1', start, 'movement_status', 'taxiing westbound after the route release',
           'TRN101 has begun taxiing on the reopened apron route.', 'exercise-ground-control')
    report('A1', stop, 'movement_status', 'stopped at the west staging point',
           'TRN101 has reached the west staging point and stopped.', 'exercise-ground-control')
    cue(world, 'A1', 65, 'debris-closure', 'Which route is closed, and what is known about the object?')
    cue(world, 'A1', 160, 'debris-recovery', 'Does recovering the object reopen the route?')
    cue(world, 'A1', 223, 'debris-inspected', 'Is the westbound route released now that inspection is complete?')
    cue(world, 'A1', 300, 'debris-reopened', 'Which report allowed TRN101 to move?')
    world['flightTeachingWindows'] = [dict(start=248, end=stop + 5)]
    return world


def build_winter_handover(seed):
    world = turnaround_world(seed, WINTER_HANDOVER, SNOW_PLAN,
                             'Fictional winter reports and snow presentation informed by the Heathrow 2026/27 snow plan. '
                             'No measured surface condition, holdover time, performance limit or de-icing procedure is inferred from the view.')
    report = report_writer(world)
    treatment_done = 118 + random.Random(seed).randrange(12)
    start = 418
    point_a = STANDS['A']
    push, taxi, _ = departure_path(point_a, [(-.045, -.025), (-.145, -.025)])
    backing = timed_path(push, start, speed=2, reverse=True)
    taxiing = timed_path(taxi, backing[-1]['t'], speed=6)
    stop = taxiing[-1]['t']
    world['aircraft'].insert(0, aircraft('A1', [pose(0, *point_a), *backing, *taxiing[1:]], [
        phase(0, 'held', 'Held at Stand A'), phase(start, 'pushback', 'Pushback'),
        phase(backing[-1]['t'], 'taxiing', 'Taxi to the apron staging point'), phase(stop, 'staging', 'Stopped at apron staging point')]))
    world['environment'] = dict(version=1, kind='snow', frames=[
        dict(t=t, precipitation=amount, daylight=1) for t, amount in [(0, .7), (90, .8), (170, .15), (210, 0), (3600, 0)]])
    validate_environment(world['environment'], world['duration'])
    report('A1', 14, 'movement_condition', 'west apron lane held for reported snow contamination',
           'Airfield Operations reports snow contamination on the west apron lane. TRN101 is held at Stand A.', 'exercise-airfield-operations')
    report('A1', 35, 'movement_condition', 'west apron lane treatment underway and hold active',
           'The west apron lane is being treated. The ground movement hold remains active.', 'exercise-airfield-operations')
    report('A1', 72, 'overall_readiness', 'aircraft de-icing outstanding and turnaround readiness unconfirmed',
           'Ground handling reports TRN101 de-icing outstanding. Aircraft turnaround readiness remains unconfirmed.', 'exercise-ground-handling')
    report('A1', 91, 'tobt', '06:30 scenario time',
           'Stand Planning revises the off-block estimate for TRN101 to 06:30 scenario time. It remains an estimate.', 'exercise-stand-planning')
    report('A1', treatment_done, 'movement_condition', 'surface treatment complete, inspection and release pending',
           'The west apron lane treatment is complete. Inspection and a movement release are still pending.', 'exercise-airfield-operations')
    report('A1', 228, 'movement_condition', 'west apron lane inspection complete, movement release pending',
           'Airfield Operations reports that the treated west apron lane passed its inspection. Ground movement still requires a separate release.', 'exercise-airfield-operations')
    report('A1', 289, 'overall_readiness', 'aircraft de-icing complete, turnaround readiness still awaiting confirmation',
           'Ground handling confirms TRN101 de-icing is complete. The aircraft turnaround readiness check is still pending.', 'exercise-ground-handling')
    report('A1', 329, 'overall_readiness', 'turnaround check confirms ready for apron movement',
           'Ground handling confirms the turnaround readiness check. TRN101 is ready for apron movement when released.', 'exercise-ground-handling')
    report('A1', 407, 'movement_condition', 'TRN101 released to use the west apron lane for ground movement',
           'Ground control releases TRN101 to use the west apron lane to the staging point. No runway or takeoff clearance is reported.', 'exercise-ground-control')
    report('A1', start, 'movement_status', 'pushback from Stand A', 'TRN101 has begun pushback from Stand A.', 'exercise-ground-control')
    report('A1', stop, 'movement_status', 'stopped at the apron staging point', 'TRN101 is stopped at the apron staging point.', 'exercise-ground-control')
    cue(world, 'A1', 149, 'winter-treatment', 'What has been treated, and what still keeps TRN101 at its stand?')
    cue(world, 'A1', 259, 'winter-inspection', 'What does the surface inspection establish about the lane, the aircraft and movement authority?')
    cue(world, 'A1', 357, 'winter-ready', 'Does reported turnaround readiness allow TRN101 to move yet?')
    cue(world, 'A1', 439, 'winter-release', 'What movement has ground control authorised for TRN101?')
    world['flightTeachingWindows'] = [dict(start=407, end=stop + 5)]
    return world


def build_fuel_interruption(seed):
    world = turnaround_world(seed, FUEL_INTERRUPTION, FUELLING_GUIDANCE,
                             'Fictional fuelling interruption and local exclusion handover. Heathrow fuelling guidance supplies background. '
                             'Fluid identification, timings and service results are authored. This exercise provides no fuelling procedure or operational clearance.')
    report = report_writer(world)
    checked = 149 + random.Random(seed).randrange(12)
    world['aircraft'].insert(0, aircraft('A1', [pose(0, *STANDS['A'])], [phase(0, 'parked', 'Parked at Stand A')]))
    report('A1', 5, 'fuel_status', 'fuelling in progress', 'Ground handling reports TRN101 fuelling is in progress.', 'exercise-ground-handling')
    report('A1', 36, 'fuel_status', 'fuelling interrupted with fluid report pending assessment',
           'Ground handling interrupts TRN101 fuelling after unidentified liquid is reported near the service point. No fuel spill has been confirmed.', 'exercise-ground-handling')
    report('A1', 42, 'movement_condition', 'local exclusion at the Stand A service point and aircraft remains stopped',
           'Airfield Operations reports a local exclusion at the Stand A service point while the liquid is checked. TRN101 remains stopped.', 'exercise-airfield-operations')
    report('A1', checked, 'movement_condition', 'liquid identified as water with exclusion still active',
           'Airfield Operations reports that the liquid was identified as water. The local exclusion remains active pending its separate release.', 'exercise-airfield-operations')
    report('A1', 220, 'movement_condition', 'Stand A local exclusion lifted and aircraft movement still unreleased',
           'Airfield Operations lifts the local service-point exclusion. Aircraft movement has not been released.', 'exercise-airfield-operations')
    report('A1', 233, 'fuel_status', 'fuelling resumed', 'Ground handling reports fuelling has resumed for TRN101.', 'exercise-ground-handling')
    report('A1', 295, 'fuel_status', 'fuelling complete', 'Ground handling confirms fuelling is complete for TRN101.', 'exercise-ground-handling')
    report('A1', 304, 'overall_readiness', 'departure readiness and movement authority still unconfirmed',
           'Stand Planning confirms no departure readiness or movement release has arrived for TRN101.', 'exercise-stand-planning')
    cue(world, 'A1', 73, 'fuel-interrupted', 'Why did fuelling stop, and is a fuel spill confirmed?')
    cue(world, 'A1', 181, 'fuel-checked', 'What did the check establish, and which restriction remains?')
    cue(world, 'A1', 327, 'fuel-handover', 'What can you report about fuelling, the local exclusion and departure readiness?')
    return world
