"""PROCEDURAL: seeded capture plans for the Stand B detector revision (v2).

Writes one JSON plan per purpose for `P01CaptureBatch` (plan mode). Every
number that shapes the data comes from the pre-registered seeds and ranges in
PROTOCOL.md; nothing here reads rendered frames or model results.

    .venv-candidates/bin/python -m experiments.apron_detector.plan development work/detector-v2/plan-development.json
    .venv-candidates/bin/python -m experiments.apron_detector.plan heldout work/detector-v2/plan-heldout.json
"""
import argparse
import colorsys
import json
import math
import random
from pathlib import Path

from backend.lessons import build_lesson

VERSION = 'stand-b-detector-v2'
SEEDS = {'development': 20261117, 'heldout': 20261118}
# (split, number of domains); development holds training and validation domains.
SPLITS = {'development': (('train', 12), ('validation', 4)), 'heldout': (('heldout', 5),)}
FRAMES_PER_DOMAIN = 40
BRIDGE_CAB = (22.0, 4.0, 70.0)  # existing opaque Stand B bridge cab, apron metres


def route():
    world, _, _ = build_lesson(17, 'stand_clearance')
    plan = next(v for v in world['groundVehicles'] if v['id'] == 'service-vehicle')
    return [(p['t'], p['x'] * 1000, p['z'] * 1000) for p in plan['waypoints']]


def tanker_at(points, t):
    for (t0, x0, z0), (t1, x1, z1) in zip(points, points[1:]):
        if t0 <= t <= t1:
            u = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            return x0 + (x1 - x0) * u, z0 + (z1 - z0) * u
    return points[-1][1], points[-1][2]


def sample_time(rng):
    roll = rng.random()
    if roll < .5:
        return round(rng.uniform(2, 87.5), 2)    # parked on Stand B
    if roll < .8:
        return round(rng.uniform(88, 100), 2)    # leaving along the service road
    return round(rng.uniform(100.5, 200), 2)     # parked off the stand; TRN103 taxies in after 158 s


def frame(rng, points, split, domain, index, body, scale):
    t = sample_time(rng)
    tx, tz = tanker_at(points, t)
    kind = rng.random()
    if kind < .10 and t < 88:
        # Behind the bridge cab, so the cab partly or fully blocks the parked tanker.
        bx, by, bz = BRIDGE_CAB
        dx, dz = bx - tx, bz - tz
        norm = math.hypot(dx, dz)
        distance = rng.uniform(10, 30)
        position = (bx + dx / norm * distance, by + rng.uniform(-1, 3), bz + dz / norm * distance)
        look = (tx, 1.8, tz)
        viewpoint = 'bridge'
    else:
        # South, east or west of the tanker; the terminal is to the north.
        bearing = math.radians(rng.uniform(200, 340))
        distance = rng.uniform(25, 160)
        position = (tx + math.cos(bearing) * distance, rng.uniform(2.5, 35), tz + math.sin(bearing) * distance)
        look = (tx + rng.gauss(0, 12), rng.uniform(0, 3), tz + rng.gauss(0, 12))
        viewpoint = 'apron'
        if kind > .85:
            # Look away: rotate the aim 70-150 degrees about the camera, so the tanker leaves the view.
            yaw = math.radians(rng.choice((-1, 1)) * rng.uniform(70, 150))
            dx, dz = look[0] - position[0], look[2] - position[2]
            look = (position[0] + dx * math.cos(yaw) - dz * math.sin(yaw), look[1],
                    position[2] + dx * math.sin(yaw) + dz * math.cos(yaw))
            viewpoint = 'away'
    vec = lambda v: dict(x=round(v[0], 3), y=round(v[1], 3), z=round(v[2], 3))
    return dict(split=split, domain=domain, viewpoint=f'{viewpoint}-{index:02d}', stem=f'{domain}-{index:02d}',
                time=t, fieldOfView=round(rng.uniform(40, 65), 2), body=body, bodyScale=vec(scale),
                positionMetres=vec(position), lookAtMetres=vec(look))


def build(purpose):
    rng = random.Random(SEEDS[purpose])
    points = route()
    frames, domains = [], []
    prefix = 'h' if purpose == 'heldout' else 'd'
    number = 0
    for split, count in SPLITS[purpose]:
        for _ in range(count):
            number += 1
            domain = f'{prefix}{number:02d}'
            red, green, blue = colorsys.hsv_to_rgb(rng.random(), rng.uniform(0, .25), rng.uniform(.55, .95))
            body = dict(r=round(red, 4), g=round(green, 4), b=round(blue, 4), a=1.0)
            scale = (rng.uniform(.9, 1.1), rng.uniform(.9, 1.1), rng.uniform(.9, 1.1))
            domains.append(dict(domain=domain, split=split, body=body))
            frames += [frame(rng, points, split, domain, i, body, scale) for i in range(FRAMES_PER_DOMAIN)]
    return dict(version=VERSION, purpose=purpose, seed=SEEDS[purpose], domains=domains, frames=frames)


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument('purpose', choices=sorted(SEEDS))
    cli.add_argument('output', type=Path)
    args = cli.parse_args()
    plan = build(args.purpose)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(plan, stream, indent=1)
    print(args.purpose, len(plan['frames']), 'frames,', len(plan['domains']), 'domains ->', args.output)


if __name__ == '__main__':
    main()
