"""Bake audited Terminal 3 source meshes and OSM remainder for Unity Resources.

Inputs are versioned beside the original free scenery source. Runtime needs no
geometry libraries. No scene-relative recentering or Unity importer mirroring.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.runway_scenarios import project


def bake():
    source = ROOT / 'data/geography/terminal3'
    detail = json.loads((source / 'HeathrowT3-Detail-EastNorth.json').read_text())
    remainder = json.loads((source / 'osm-t3-remainder.json').read_text())
    canopy = json.loads((source / 'canopy-osm-way-722642847.json').read_text())
    ox, oz = project(detail['originLon'], detail['originLat'])
    def point(p):
        x, z = project(*p)
        return dict(x=x, z=z)
    def vertex(p):
        return dict(x=ox+p[0]/1000, y=p[1]/1000, z=oz+p[2]/1000)
    meshes=[]
    for m in detail['meshes']:
        meshes.append(dict(name=m['name'], vertices=[vertex(v) for v in m['vertices']],
            uv=[dict(x=u,y=v) for u,v in m['uv']], triangles=m['triangles'],
            color=dict(zip(('r','g','b','a'),[*m['color'],1])), textured=bool(m['texture'])))
    parts=[]
    for p in remainder['parts']:
        tri=p['roofTriangles']; flipped=[]
        for i in range(0,len(tri),3): flipped.extend((tri[i],tri[i+2],tri[i+1]))
        parts.append(dict(points=[point(v) for v in p['coordinates']],
            holes=[dict(points=[point(v) for v in h]) for h in p['holes']],
            roofPoints=[point(v) for v in p['roofCoordinates']], roofTriangles=flipped,
            height=.010))  # Authored massing height; OSM has no surveyed height.
    result=dict(version=1, meshes=meshes, remainders=parts,
        canopyPoints=[point(v) for v in canopy['coordinates']], canopyHeight=.011,
        canopyRectangle=[vertex([e,0,n]) for e,n in canopy['minimumRectangleEastNorthMetres'][:4]])
    out=ROOT/'unity/SurfaceSafetyCoach/Assets/Resources/HeathrowT3/model.json'
    out.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(f'Terminal 3: {len(meshes)} source mesh groups, {len(parts)} mapped building parts, mapped canopy')


if __name__=='__main__': bake()
