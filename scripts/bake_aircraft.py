"""Bake pinned CC BY 4.0 AMV Lab GLBs into Unity-readable meshes (stdlib only).

Source transforms are applied before a +X nose to +Z nose rotation. Dimensions
are independently normalized to the declared reference envelope; these family
assets are not verified variant CAD. Gear is original Unity geometry.
"""
import hashlib,json,math,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROFILES={'a320_200':('A320',37.57,35.80,11.76,17.71,.65),'b737_800':('B737',39.47,35.79,12.55,19.69,.50),'b787_8':('B787',56.72,60.12,16.92,28.19,.90),'a380_800':('A380',72.73,79.75,24.12,36.85,1.50)}
def bake():
 out=ROOT/'unity/SurfaceSafetyCoach/Assets/Resources/Aircraft';out.mkdir(parents=True,exist_ok=True);records=[]
 for ident,(family,length,span,height,nose,clearance) in PROFILES.items():
  path=ROOT/'data/aircraft/amvlab'/f'{family}_nologo.glb';raw=path.read_bytes();assert raw[:4]==b'glTF'
  n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
  def accessor(idx):
   a=doc['accessors'][idx];v=doc['bufferViews'][a['bufferView']];fmt={5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']];count={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];size=struct.calcsize(fmt)*count;offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',size)
   return [list(struct.unpack_from('<'+fmt*count,binary,offset+i*stride)) for i in range(a['count'])]
  node=doc['nodes'][0];assert len(doc['nodes'])==1 and 'matrix' not in node
  x,y,z,w=node.get('rotation',[0,0,0,1]);sc=node.get('scale',[1,1,1]);tr=node.get('translation',[0,0,0])
  rotation=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
  def transform(v):return [sum(rotation[i][j]*sc[j]*v[j] for j in range(3))+tr[i] for i in range(3)]
  prim=doc['meshes'][node['mesh']]['primitives'];assert len(prim)==1 and prim[0].get('mode',4)==4;p=prim[0]
  pts=list(map(transform,accessor(p['attributes']['POSITION'])));lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)]
  scales=[length/(hi[0]-lo[0]),(height-clearance)/(hi[1]-lo[1]),span/(hi[2]-lo[2])]
  vertices=[dict(x=round(-(v[2]-(hi[2]+lo[2])/2)*scales[2],6),y=round((v[1]-lo[1])*scales[1]+clearance,6),z=round((v[0]-hi[0])*scales[0]+nose,6)) for v in pts]
  # Unity's front face convention is opposite glTF. A reflected source transform
  # already reverses triangle winding, so reflection and convention cancel.
  indices=[v[0] for v in accessor(p['indices'])];tri=[]
  for i in range(0,len(indices),3):
   a,b,c=indices[i:i+3];tri.extend([a,b,c] if math.prod(sc)<0 else [a,c,b])
  normals=[]
  for v in accessor(p['attributes']['NORMAL']):
   a=[sum(rotation[i][j]*v[j]/sc[j] for j in range(3))/scales[i] for i in range(3)];b=[-a[2],a[1],a[0]];norm=math.sqrt(sum(q*q for q in b));normals.append(dict(zip(('x','y','z'),[round(q/norm,7) for q in b])))
  uv=[dict(x=u,y=1-v) for u,v in accessor(p['attributes']['TEXCOORD_0'])]
  result=dict(version=1,type=ident,vertices=vertices,normals=normals,uv=uv,triangles=tri)
  (out/f'{ident}.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
  image=doc['images'][0];bv=doc['bufferViews'][image['bufferView']];suffix='jpg' if image['mimeType']=='image/jpeg' else 'png';(out/f'{ident}_texture.{suffix}').write_bytes(binary[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']])
  records.append(dict(type=ident,source=path.name,sha256=hashlib.sha256(raw).hexdigest(),vertices=len(vertices),triangles=len(tri)//3,sourceScale=sc,bakedAxisScales=scales,referenceLength=length,referenceSpan=span,referenceHeight=height,authoredMinimumExteriorClearance=clearance,noseAheadMainGear=nose))
 manifest=dict(version=1,source='https://github.com/amvlab/aircraft-models',commit='91d835e8e851b2317fe79af291c9fed6153fd525',license='CC BY 4.0',attribution='AMV Lab (amvlab), 2026',changes='Transforms baked, +Z nose, reference envelope normalized, textures extracted; original gear added by AirfieldLens. Family exterior geometry, not exact variant CAD.',records=records)
 (ROOT/'data/aircraft/amvlab/conversion.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps(records,indent=2))
if __name__=='__main__':bake()
