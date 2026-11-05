"""Inspect the official TerraSync T3 mesh; convert every source polygon to OBJ.

Derived from repository scripts/convert_heathrow_ac.py. Work directory only.
The output retains source metre coordinates and all five source objects.
"""
import shlex, json, math, collections
from pathlib import Path

import os
ROOT = Path(os.environ.get("APRONLENS_T3_SOURCE", Path(__file__).resolve().parents[1]/"data/geography/terminal3"))

def parse_ac():
    lines=(ROOT/'EGLL-t3.ac').read_text().splitlines()
    materials=[];objects=[];i=1
    while i<len(lines):
        t=shlex.split(lines[i]);i+=1
        if not t:continue
        if t[0]=='MATERIAL':
            materials.append({'name':t[1], 'rgb':list(map(float,t[t.index('rgb')+1:t.index('rgb')+4]))})
        elif t[:2]==['OBJECT','poly']:
            o={'name':'mesh','loc':[0,0,0],'texture':None,'vertices':[],'faces':[]}
            while i<len(lines):
                t=shlex.split(lines[i]);i+=1
                if t[0]=='name':o['name']=t[1]
                elif t[0]=='loc':o['loc']=list(map(float,t[1:]))
                elif t[0]=='rot':raise ValueError('Unexpected rotation')
                elif t[0]=='texture':o['texture']=t[1]
                elif t[0]=='numvert':
                    n=int(t[1]);o['vertices']=[list(map(float,x.split())) for x in lines[i:i+n]];i+=n
                elif t[0]=='numsurf':
                    for _ in range(int(t[1])):
                        flags=int(lines[i].split()[1],0);i+=1
                        mat=int(lines[i].split()[1]);i+=1
                        n=int(lines[i].split()[1]);i+=1
                        refs=[x.split() for x in lines[i:i+n]];i+=n
                        if flags&0xf==0:o['faces'].append((mat,refs,flags))
                elif t[0]=='kids':
                    if int(t[1]):raise ValueError('Nested geometry unsupported')
                    break
            o['vertices']=[[v[k]+o['loc'][k] for k in range(3)] for v in o['vertices']]
            objects.append(o)
    return materials,objects

def triangulate(vertices):
    # Project to the face's dominant plane and ear-clip; preserve the source winding.
    if len(vertices)==3:return [(0,1,2)]
    normal=[0.,0.,0.]
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):
        normal[0]+=(a[1]-b[1])*(a[2]+b[2])
        normal[1]+=(a[2]-b[2])*(a[0]+b[0])
        normal[2]+=(a[0]-b[0])*(a[1]+b[1])
    axis=max(range(3),key=lambda k:abs(normal[k]))
    dims=[k for k in range(3) if k!=axis]
    pts=[(v[dims[0]],v[dims[1]])for v in vertices]
    cross=lambda a,b,c:(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    area=sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(pts,pts[1:]+pts[:1]))
    if abs(area)<1e-10:return []
    sign=1 if area>0 else -1;ids=list(range(len(vertices)));out=[]
    while len(ids)>3:
        found=False
        for j,b in enumerate(ids):
            a,c=ids[j-1],ids[(j+1)%len(ids)]
            if sign*cross(pts[a],pts[b],pts[c])<=1e-9:continue
            if any(all(sign*cross(pts[u],pts[v],pts[t])>=-1e-9 for u,v in [(a,b),(b,c),(c,a)]) for t in ids if t not in [a,b,c]):continue
            out.append((a,b,c));ids.pop(j);found=True;break
        if not found:
            # Collinear vertices may be safely discarded for this source's flat surfaces.
            for j,b in enumerate(ids):
                if abs(cross(pts[ids[j-1]],pts[b],pts[ids[(j+1)%len(ids)]]))<1e-8:
                    ids.pop(j);found=True;break
        if not found:raise ValueError('Could not triangulate source polygon')
    if len(ids)==3:out.append(tuple(ids))
    return out

def main():
    mats,objects=parse_ac();obj=['mtllib HeathrowT3.mtl'];mtl=[];used=set();index=1;total=0;summary=[]
    for o in objects:
        obj.append('o '+o['name']);triangles=0
        for mat,refs,flags in o['faces']:
            key=f'm{mat}_'+('tex'if o['texture']else 'plain')
            if key not in used:
                used.add(key);mtl.extend(['newmtl '+key,'Kd '+' '.join(map(str,mats[mat]['rgb'])),'Ks 0.08 0.08 0.08','Ns 20'])
                if o['texture']:mtl.append('map_Kd '+o['texture'])
            obj.append('usemtl '+key);face=[];vertices=[]
            for r in refs:
                v=o['vertices'][int(r[0])];vertices.append(v)
                obj.append('v '+' '.join(f'{n:.7f}'for n in v));obj.append(f'vt {r[1]} {r[2]}');face.append(index);index+=1
            for tri in triangulate(vertices):
                obj.append('f '+' '.join(f'{face[n]}/{face[n]}'for n in tri));triangles+=1
        vs=o['vertices'];summary.append({'name':o['name'],'texture':o['texture'],'vertices':len(vs),'source_faces':len(o['faces']),'triangles':triangles,'bounds':[[min(v[k]for v in vs),max(v[k]for v in vs)]for k in range(3)],'face_sizes':dict(collections.Counter(len(f[1])for f in o['faces'])),'surface_flags':dict(collections.Counter(f[2]for f in o['faces']))});total+=triangles
    (ROOT/'HeathrowT3.obj').write_text('\n'.join(obj)+'\n');(ROOT/'HeathrowT3.mtl').write_text('\n'.join(mtl)+'\n');(ROOT/'geometry-inspection.json').write_text(json.dumps({'objects':summary,'triangles':total,'materials':mats,'output_face_vertices':index-1},indent=2)+'\n');print(json.dumps(summary,indent=2));print('Total triangles',total)

if __name__=='__main__':main()
