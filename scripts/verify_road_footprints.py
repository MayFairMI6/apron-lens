"""Check the full ambient van envelope against the rendered road surface.

Requires Shapely 2.x in a separate geometry environment. No model is loaded.
Matches TrainingGeography's road ribbons and 32-sided source-node junctions.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.road_traffic import road_pose
from backend.runway_scenarios import build_demonstration, geography
from shapely.geometry import Polygon
from shapely.ops import unary_union


def verify() -> dict:
    geo = geography()
    traffic = build_demonstration(17, "rejected_takeoff")[0]["ambientTraffic"]
    road_ids = set(geo["roadTrafficRoutes"][0]["sourceWayIds"])
    surfaces = []
    for feature in geo["features"]:
        if feature["id"] not in road_ids:
            continue
        points = feature["points"]
        left, right = [], []
        radius = feature["width"] / 2
        for i, point in enumerate(points):
            before, after = points[max(i - 1, 0)], points[min(i + 1, len(points) - 1)]
            dx, dz = after["x"] - before["x"], after["z"] - before["z"]
            distance = math.hypot(dx, dz)
            nx, nz = -dz / distance * radius, dx / distance * radius
            left.append((point["x"] + nx, point["z"] + nz))
            right.append((point["x"] - nx, point["z"] - nz))
            surfaces.append(Polygon([
                (point["x"] + radius * math.cos(j * math.tau / 32),
                 point["z"] + radius * math.sin(j * math.tau / 32))
                for j in range(32)
            ]))
        surfaces.append(Polygon(left + right[::-1]).buffer(0))

    road = unary_union(surfaces)
    route = traffic["routes"][0]
    vehicle = traffic["vehicles"][2]
    period = route["lengthMetres"] / 3
    off_pavement = 0
    maximum_area = 0.0
    for i in range(4000):
        pose = road_pose(traffic, vehicle, i * period / 4000)
        yaw = math.radians(pose["heading"])
        # Includes wheels and lamps, beyond the 5.2 by 2 m body.
        corners = [
            (pose["x"] + (x * math.cos(yaw) + z * math.sin(yaw)) / 1000,
             pose["z"] + (-x * math.sin(yaw) + z * math.cos(yaw)) / 1000)
            for x, z in [(-1.08, -2.63), (-1.08, 2.63), (1.08, 2.63), (1.08, -2.63)]
        ]
        area = Polygon(corners).difference(road.buffer(1e-7)).area * 1e6
        if area > 1e-4:
            off_pavement += 1
            maximum_area = max(maximum_area, area)

    return {
        "mapVersion": geo["version"], "features": len(geo["features"]),
        "routePoints": len(route["points"]), "footprintSamples": 4000,
        "envelopeMetres": [5.26, 2.16], "offPavementSamples": off_pavement,
        "maxOffPavementAreaM2": maximum_area, "periodSeconds": period,
        "minimumSegmentMetres": min(
            b["distanceMetres"] - a["distanceMetres"]
            for a, b in zip(route["points"], route["points"][1:])
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON result path")
    args = parser.parse_args()
    result = verify()
    encoded = json.dumps(result, indent=2) + "\n"
    print(encoded, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    if result["offPavementSamples"]:
        raise SystemExit("Road vehicle envelope leaves the rendered pavement")
