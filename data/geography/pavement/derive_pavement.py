"""Reproduce the clipped historical pavement polygons; no application dependency.

Offline requirements: Python 3.9+, Shapely 2.0.7, numpy 2.0.2,
mapbox-earcut 2.0.0. Run: python derive_pavement.py /tmp/pavement.json
This independently written conversion is distributed under GPL-2.0.
"""
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import mapbox_earcut
import numpy as np
from shapely.geometry import Polygon, box, mapping, shape
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
FACTOR = math.pi * 6371008.8 / 180
COS = math.cos(math.radians(51.47))


def project(c):
    return ((c[0] + .46) * FACTOR * COS, (c[1] - 51.47) * FACTOR)


def geographic(c):
    return [c[0] / (FACTOR * COS) - .46, c[1] / FACTOR + 51.47]


def parts(geometry):
    if geometry.geom_type == 'Polygon':
        return [geometry]
    return [p for child in getattr(geometry, 'geoms', []) for p in parts(child)]


with tempfile.TemporaryDirectory() as temp:
    prefix = str(Path(temp) / 'source')
    subprocess.run([sys.executable, str(HERE / 'read_btg.py'),
                    str(HERE / 'EGLL-official-current.btg.gz'), prefix], check=True)
    source = json.loads(Path(prefix + '-geographic-triangles.json').read_text())

vertices = [project(c) for c in source['vertices_lon_lat_height']]
polygons = [Polygon([vertices[i] for i in triangle])
            for group in source['groups']
            if group['material'] in ('pa_tiedown', 'pc_tiedown', 'pa_shoulder_f')
            for triangle in group['triangles']]
pavement = unary_union([p for p in polygons if p.area > 1e-9])
mask = json.loads((HERE / 'clip-metre-geometry.json').read_text())
safe = pavement.intersection(shape(mask['crop'])).difference(shape(mask['exclusions']))
result = []
for ix in range(-3, 7):
    for iy in range(-2, 4):
        tile = box(ix * 200, iy * 200, (ix + 1) * 200, (iy + 1) * 200)
        for p in parts(safe.intersection(tile)):
            if p.area <= 1e-6:
                continue
            rings = [list(p.exterior.coords)] + [list(r.coords) for r in p.interiors]
            rings = [[geographic(c) for c in ring] for ring in rings]
            roof = [c for ring in rings for c in ring[:-1]]
            points = np.array([project(c) for c in roof], dtype=np.float64)
            ends = np.cumsum([len(r) - 1 for r in rings]).astype(np.uint32)
            triangles = mapbox_earcut.triangulate_float64(points, ends).reshape(-1, 3).tolist()
            clean = []
            for triangle in triangles:
                a, b, c = (points[i] for i in triangle)
                cross = (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
                if abs(cross) < 1e-12:
                    continue
                if cross < 0:
                    triangle[1], triangle[2] = triangle[2], triangle[1]
                clean.append(triangle)
            union = unary_union([Polygon(points[t]) for t in clean])
            assert union.symmetric_difference(p).area < 1e-6
            result.append(dict(id='flightgear-2013-t3-pavement-' + str(len(result) + 1),
                               coordinates=rings[0], holes=[dict(coordinates=r) for r in rings[1:]],
                               roofCoordinates=roof, roofTriangles=[i for t in clean for i in t]))
Path(sys.argv[1]).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(dict(parts=len(result), areaSquareMetres=safe.area)))
