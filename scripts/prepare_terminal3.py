"""Prepare source pier detail and exact OSM-minus-detail remainder in work only.

Run with work/geography-triangulation/bin/python (existing Shapely environment).
The detailed asset keeps original metre-scale geometry, source height and UVs.
Horizontal coordinates are east,north offsets from the official STG origin.
"""
import json, math, hashlib, xml.etree.ElementTree as ET
import numpy as np
import mapbox_earcut
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union, triangulate as delaunay
from shapely.affinity import affine_transform
from terminal3_source import parse_ac,triangulate

REPO=Path(__file__).resolve().parents[1]
ROOT=REPO/'data/geography/terminal3'
ORIGIN=(-.4609948,51.4720209)
S=math.sin(math.radians(124.8));C=math.cos(math.radians(124.8))
FACTOR=math.pi/180*6371008.8
PROJECTION_LATITUDE=51.47

def project(p):return ((p[0]-ORIGIN[0])*FACTOR*math.cos(math.radians(PROJECTION_LATITUDE)),(p[1]-ORIGIN[1])*FACTOR)
def geo(p):return (ORIGIN[0]+p[0]/(FACTOR*math.cos(math.radians(PROJECTION_LATITUDE))),ORIGIN[1]+p[1]/FACTOR)
def eastnorth(v):return [S*v[0]-C*v[2],v[1],-C*v[0]-S*v[2]]
def polygons(g):return [g]if g.geom_type=='Polygon'else list(g.geoms)

def main():
    mats,objects=parse_ac();objects=[o for o in objects if o['name']!='Terminal 3.001']
    obj=['mtllib HeathrowT3-Detail-EastNorth.mtl'];mtl=[];used=set();index=1;count=0;footprints=[];meshgroups=[]
    for o in objects:
        obj.append('o '+o['name']);by_material={}
        for mat,refs,flags in o['faces']:
            key=f'm{mat}_'+('tex'if o['texture']else 'plain')
            if key not in used:
                used.add(key);mtl.extend(['newmtl '+key,'Kd '+' '.join(map(str,mats[mat]['rgb'])),'Ks 0.08 0.08 0.08','Ns 20'])
                if o['texture']:mtl.append('map_Kd '+o['texture'])
            obj.append('usemtl '+key);indices=[];vv=[];uv=[]
            for r in refs:
                v=o['vertices'][int(r[0])];vv.append(v);world=eastnorth(v)
                obj.append('v '+' '.join(f'{n:.7f}'for n in world));obj.append(f'vt {r[1]} {r[2]}');indices.append(index);index+=1;uv.append(list(map(float,r[1:])))
            p=Polygon([(v[0],v[2])for v in vv])
            if p.is_valid and p.area>1e-7:footprints.append(p)
            bucket=by_material.setdefault(key,{'name':o['name']+'_'+key,'material':key,'color':mats[mat]['rgb'],'texture':o['texture'],'vertices':[],'uv':[],'triangles':[]})
            start=len(bucket['vertices']);bucket['vertices'].extend([eastnorth(v)for v in vv]);bucket['uv'].extend(uv)
            for tri in triangulate(vv):
                # Reflection from AC (x,z) to (east,north) reverses winding.
                tri=list(reversed(tri));obj.append('f '+' '.join(f'{indices[n]}/{indices[n]}'for n in tri));bucket['triangles'].extend(start+n for n in tri);count+=1
        meshgroups.extend(by_material.values())
    (ROOT/'HeathrowT3-Detail-EastNorth.obj').write_text('\n'.join(obj)+'\n');(ROOT/'HeathrowT3-Detail-EastNorth.mtl').write_text('\n'.join(mtl)+'\n')
    (ROOT/'HeathrowT3-Detail-EastNorth.json').write_text(json.dumps({'originLon':ORIGIN[0],'originLat':ORIGIN[1],'units':'metres; x=east, y=source-up, z=north','sourceStgElevationMetres':23.28,'meshes':meshgroups},separators=(',',':')))
    detail=affine_transform(unary_union(footprints),[S,-C,-C,-S,0,0])
    d=json.loads((REPO/'data/geography/heathrow-west.json').read_text());f=next(f for f in d['features']if f['id']=='osm-relation-18911624')

    holes=f.get('holes',[])
    # Existing map schema uses a coordinate ring inside each hole object.
    rings=[h['coordinates']if isinstance(h,dict)else h for h in holes]
    outline=Polygon([project(p)for p in f['coordinates']],[[project(p)for p in ring]for ring in rings])
    if not outline.is_valid:raise ValueError('Source OSM polygon invalid')
    remainder=outline.difference(detail)
    remainder_parts=[]
    for p in polygons(remainder):
        coords=[list(geo(x))for x in p.exterior.coords];interiors=[[list(geo(x))for x in r.coords]for r in p.interiors]
        # Earcut supports the courtyard plus tiny slivers left by source differences.
        plane=[];ends=[]
        for ring in [p.exterior,*p.interiors]:
            plane.extend(list(ring.coords)[:-1]);ends.append(len(plane))
        ear=mapbox_earcut.triangulate_float64(np.array(plane,dtype=np.float64),np.array(ends,dtype=np.uint32)).tolist()
        ts=[Polygon([plane[n]for n in ear[i:i+3]])for i in range(0,len(ear),3)];tri_area=sum(t.area for t in ts)
        # Full coverage is checked; no incomplete triangulation is published.
        if abs(tri_area-p.area)>max(1e-5,p.area*1e-8):raise ValueError(f'Remainder triangulation lost area {tri_area} / {p.area}')
        if unary_union(ts).symmetric_difference(p).area>max(1e-5,p.area*1e-8):raise ValueError('Roof triangles do not match remainder polygon')
        rc=[];rt=[]
        for t in ts:
            tri=list(t.exterior.coords)[:3];n=len(rc);rc.extend([list(geo(x))for x in tri]);rt.extend([n,n+1,n+2])
        remainder_parts.append({'coordinates':coords,'holes':interiors,'roofCoordinates':rc,'roofTriangles':rt,'areaSquareMetres':p.area})
    coverage={'assetDetailFootprintArea':detail.area,'detailInsideCurrentT3Area':detail.intersection(outline).area,'detailOutsideCurrentT3Area':detail.difference(outline).area,'currentT3Area':outline.area,'remainderArea':remainder.area,'remainderParts':len(remainder_parts),'detailSourceObjectNames':[o['name']for o in objects],'detailTriangles':count,'sourceOrigin':list(ORIGIN),'note':'Current OSM outer and courtyard preserved in remainder. About 16% of the source detailed roof footprint is outside the current OSM wall footprint (possible overhangs and source deviations); do not represent it as surveyed.'}
    (ROOT/'hybrid-coverage.json').write_text(json.dumps(coverage,indent=2))
    (ROOT/'osm-t3-remainder.json').write_text(json.dumps({'sourceId':f['id'],'sourceVersion':f['osmVersion'],'operation':'OSM Terminal 3 polygon including courtyard, minus union of detailed FlightGear pier plan surfaces','origin':list(ORIGIN),'parts':remainder_parts},separators=(',',':')))
    (ROOT/'hybrid-geometries.json').write_text(json.dumps({'detail':detail.__geo_interface__,'osm':outline.__geo_interface__,'remainder':remainder.__geo_interface__}))
    print(json.dumps(coverage,indent=2))
    # Canopy source ring is retained in canopy-osm-way-722642847.json.

if __name__=='__main__':main()
