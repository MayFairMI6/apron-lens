"""Externally timed visual conditions; never operational report evidence.

Fog extinction is an authored rendering coefficient per metre, not measured
visibility, RVR, a weather report, or an operational threshold. Its recovery
intentionally precedes the separate scenario's restriction-release reports.
"""
import math

ENVIRONMENTS = ('clear', 'rain', 'snow', 'dusk', 'fog')


def validate_environment(plan, duration):
    """Validate the same versioned wire contract consumed by TrainingWeather."""
    if plan is None or plan == {}:
        return
    version, kind, frames = plan.get('version'), plan.get('kind'), plan.get('frames')
    if not ((version == 1 and kind in ('rain', 'snow', 'dusk')) or
            (version == 2 and kind == 'fog')) or not isinstance(frames, list) or not 2 <= len(frames) <= 32:
        raise ValueError('Unsupported environment plan')
    def finite(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    if not finite(duration) or duration <= 0:
        raise ValueError('Invalid environment duration')
    previous = -1
    for index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise ValueError('Invalid environment frame')
        t, precipitation, daylight, extinction = (frame.get('t', 0), frame.get('precipitation', 0),
            frame.get('daylight', 1), frame.get('fogExtinctionPerMetre', 0))
        if not all(finite(v) for v in (t, precipitation, daylight, extinction)) or not (
                0 <= t <= duration and t > previous and (index != 0 or t == 0) and
                0 <= precipitation <= 1 and 0 <= daylight <= 1 and 0 <= extinction <= .01) or (
                version == 1 and extinction != 0) or (kind == 'fog' and precipitation != 0):
            raise ValueError('Invalid environment frame')
        previous = t


def attach_environment(world, environment):
    if environment not in ENVIRONMENTS:
        raise ValueError('Unknown environment')
    if environment == 'clear':
        return  # Preserve old snapshots and their default daytime appearance.
    if environment == 'fog':
        # Source seconds. Dense fog holds across 600–1600; the view improves
        # through 1800–2200, independently of later operational reports.
        times = (0, 300, 600, 1600, 1800, 2200, 2400, 3000, 3600)
        extinction = (0, .00035, .0012, .0012, .0007, .00008, 0, 0, 0)
        world['environment'] = dict(version=2, kind='fog', frames=[
            dict(t=t, precipitation=0, daylight=1, fogExtinctionPerMetre=f)
            for t, f in zip(times, extinction)])
    else:
        # The version-one profiles and their exact values remain unchanged.
        times = (0, 600, 1800, 3000, 3600)
        precipitation = dict(rain=(.15, .5, .85, .35, .1),
                             snow=(.1, .4, .7, .25, .1), dusk=(0, 0, 0, 0, 0))[environment]
        daylight = (.95, .7, .3, .08, .05) if environment == 'dusk' else (1,) * 5
        world['environment'] = dict(version=1, kind=environment,
            frames=[dict(t=t, precipitation=p, daylight=d)
                    for t, p, d in zip(times, precipitation, daylight)])
    validate_environment(world['environment'], 3600)
    world['predictionBoundaries'] = sorted(set(world.get('predictionBoundaries', [])) | set(times))
