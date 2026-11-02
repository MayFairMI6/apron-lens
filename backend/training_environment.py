"""Externally timed visual conditions; never operational report evidence."""

ENVIRONMENTS = ('clear', 'rain', 'snow', 'dusk')


def attach_environment(world, environment):
    if environment not in ENVIRONMENTS:
        raise ValueError('Unknown environment')
    if environment == 'clear':
        return  # Preserve old snapshots and their default daytime appearance.
    times = (0, 600, 1800, 3000, 3600)
    precipitation = dict(rain=(.15, .5, .85, .35, .1),
                         snow=(.1, .4, .7, .25, .1), dusk=(0, 0, 0, 0, 0))[environment]
    daylight = (.95, .7, .3, .08, .05) if environment == 'dusk' else (1,) * 5
    world['environment'] = dict(version=1, kind=environment,
        frames=[dict(t=t, precipitation=p, daylight=d)
                for t, p, d in zip(times, precipitation, daylight)])
    world['predictionBoundaries'] = sorted(set(world.get('predictionBoundaries', [])) | set(times))
