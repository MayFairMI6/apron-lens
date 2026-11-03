"""Read FlightGear BTG records following the public SimGear sg_binobj.cxx format.
Independently written inspection utility. Source schema reference: FlightGear/simgear.
"""
import gzip, struct, json, math, datetime, hashlib, sys
from pathlib import Path
from collections import Counter,defaultdict
P=Path(__file__).resolve().parent
SRC=P/'EGLL-official-current.btg.gz'
SRC=Path(sys.argv[1]) if len(sys.argv)>1 else SRC
PREFIX=sys.argv[2] if len(sys.argv)>2 else 'btg'
b=gzip.open(SRC,'rb').read(); pos=0

def read(fmt):
 global pos
 r=struct.unpack_from('<'+fmt,b,pos);pos+=struct.calcsize('<'+fmt)
 return r[0] if len(r)==1 else r

def blob(n):
 global pos
 r=b[pos:pos+n];pos+=n;return r
h=read('I'); version=h&65535; created=read('I'); width='I' if version>=10 else 'H'; count=read(width)
assert h>>16==0x5347
vertices=[]; groups=[]; objects=Counter(); details=[]
for objno in range(count):
 kind=read('B');np=read(width);ne=read(width);objects[kind]+=1
 props={}
 for _ in range(np):
  pk=read('B');props[pk]=blob(read('I'))
 elements=[blob(read('I')) for _ in range(ne)]
 if kind==0:
  center=struct.unpack('<dddf',elements[0])
 elif kind==1:
  for e in elements:vertices.extend(struct.iter_unpack('<fff',e))
 elif kind in (9,10,11,12):
  material=props.get(0,b'').rstrip(b'\0').decode();mask=props.get(1,bytes([1 if kind==9 else 9]))[0]
  va=struct.unpack('<I',props.get(2,b'\0'*4))[0]; stride=bin(mask).count('1')+bin(va).count('1')
  tris=[]
  for e in elements:
   values=struct.unpack('<'+('I' if version>=10 else 'H')*(len(e)//(4 if version>=10 else 2)),e)
   ids=values[0::stride]
   if kind==10:
    assert len(ids)%3==0
    tris.extend(tuple(ids[j:j+3]) for j in range(0,len(ids),3))
   elif kind==11:tris.extend((ids[j],ids[j+1],ids[j+2]) if j%2==0 else (ids[j+1],ids[j],ids[j+2]) for j in range(len(ids)-2))
   elif kind==12:tris.extend((ids[0],ids[j],ids[j+1]) for j in range(1,len(ids)-1))
  if tris:groups.append((material,tris))
assert pos==len(b),(pos,len(b))
# WGS84 ECEF offsets from gbs_center. Bowring geodetic conversion.
a=6378137.;esq=6.6943799901413165e-3;semi_b=a*math.sqrt(1-esq);ep2=(a*a-semi_b*semi_b)/(semi_b*semi_b)
def geo(v):
 x,y,z=[v[i]+center[i] for i in range(3)];p=math.hypot(x,y);th=math.atan2(a*z,semi_b*p)
 lat=math.atan2(z+ep2*semi_b*math.sin(th)**3,p-esq*a*math.cos(th)**3);lon=math.atan2(y,x)
 height=p/math.cos(lat)-a/math.sqrt(1-esq*math.sin(lat)**2)
 return [math.degrees(lon),math.degrees(lat),height]
ll=[geo(v) for v in vertices]
material_stats=defaultdict(lambda:dict(triangles=0,indices=set()))
for mat,tt in groups:
 s=material_stats[mat];s['triangles']+=len(tt);s['indices'].update(i for t in tt for i in t)
for mat,s in material_stats.items():
 vv=[ll[i] for i in s.pop('indices')];s['bbox']=[[min(v[k] for v in vv) for k in range(3)],[max(v[k] for v in vv) for k in range(3)]]
report=dict(source=str(SRC),sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(),version=version,created_utc=datetime.datetime.fromtimestamp(created,datetime.timezone.utc).isoformat(),object_count=count,objects=dict(objects),vertex_count=len(vertices),triangle_count=sum(len(t) for _,t in groups),bounding_sphere_ecef=center,materials=dict(material_stats))
(P/(PREFIX+'-inspection.json')).write_text(json.dumps(report,indent=2))
(P/(PREFIX+'-geographic-triangles.json')).write_text(json.dumps(dict(vertices_lon_lat_height=ll,groups=[dict(material=m,triangles=t) for m,t in groups]),separators=(',',':')))
print(json.dumps({k:v for k,v in report.items() if k!='materials'},indent=2))
print('MATERIALS',json.dumps({m:s['triangles'] for m,s in material_stats.items()},indent=2))
