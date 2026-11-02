"""Convert selected AC3D polygon objects to OBJ, preserving face UVs and materials.
The source file remains the editable original and is shipped alongside output.
"""
import argparse, shlex
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
lines=a.source.read_text().splitlines();materials=[];objects=[];i=1
while i<len(lines):
 t=shlex.split(lines[i]);i+=1
 if not t:continue
 if t[0]=='MATERIAL':materials.append((t[1],list(map(float,t[t.index('rgb')+1:t.index('rgb')+4]))))
 elif t[:2]==['OBJECT','poly']:
  o={'name':'mesh','loc':[0,0,0],'texture':None,'vertices':[],'faces':[]}
  while i<len(lines):
   t=shlex.split(lines[i]);i+=1
   if t[0]=='name':o['name']=t[1]
   elif t[0]=='loc':o['loc']=list(map(float,t[1:]))
   elif t[0]=='rot':raise ValueError('Rotation requires explicit conversion')
   elif t[0]=='texture':o['texture']=t[1]
   elif t[0]=='numvert':
    n=int(t[1]);o['vertices']=[list(map(float,x.split())) for x in lines[i:i+n]];i+=n
   elif t[0]=='numsurf':
    for _ in range(int(t[1])):
     flags=int(lines[i].split()[1],0);i+=1
     mat=int(lines[i].split()[1]);i+=1
     n=int(lines[i].split()[1]);i+=1
     refs=[x.split() for x in lines[i:i+n]];i+=n
     if flags&0xf==0:o['faces'].append((mat,refs))
   elif t[0]=='kids':
    if int(t[1]):raise ValueError('Nested geometry not supported')
    break
  objects.append(o)
selected=[o for o in objects if o['name'] in {'5A','interiour'}]
a.output.mkdir(parents=True,exist_ok=True)
obj=['mtllib HeathrowT5.mtl'];mtl=[];used=set();index=1
for o in selected:
 obj.append('o '+o['name'])
 for mat,refs in o['faces']:
  key=f'm{mat}_'+('tex' if o['texture'] else 'plain')
  if key not in used:
   used.add(key);mtl.extend(['newmtl '+key,'Kd '+' '.join(map(str,materials[mat][1])),'Ks 0.08 0.08 0.08','Ns 20'])
   if o['texture']:mtl.append('map_Kd '+o['texture'])
  obj.append('usemtl '+key);face=[]
  for r in refs:
   v=o['vertices'][int(r[0])];v=[v[k]+o['loc'][k] for k in range(3)]
   # Centre Terminal 5A; rotate its long facade towards the apron.
   x,y,z=v[2]+33.3850327,v[1],-(v[0]+369.5924988)
   obj.append(f'v {x:.6f} {y:.6f} {z:.6f}');obj.append(f'vt {r[1]} {r[2]}');face.append(index);index+=1
  for j in range(1,len(face)-1):obj.append('f '+' '.join(f'{n}/{n}' for n in [face[0],face[j],face[j+1]]))
(a.output/'HeathrowT5.obj').write_text('\n'.join(obj)+'\n');(a.output/'HeathrowT5.mtl').write_text('\n'.join(mtl)+'\n')
print(f'Converted {len(selected)} objects, {index-1} face vertices, {len(used)} materials')
