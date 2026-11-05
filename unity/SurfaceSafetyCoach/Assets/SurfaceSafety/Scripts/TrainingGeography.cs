using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace SurfaceSafety {
    [Serializable] public class MapRing {public TaxiPoint[] points;}
    [Serializable] public class MapFeature {
        public string id,name,kind,widthBasis,heightBasis,deckHeightBasis,bodyHeightBasis;
        public float width,heightMetres,deckHeightMetres,bodyHeightMetres;
        public bool closed,widthAuthored;public TaxiPoint[] points,roofPoints;public int[] roofTriangles;public MapRing[] holes;
    }
    [Serializable] public class MapReferenceSite {
        public string id,name,renderAs,status,note,statusSource,statusSourceDate;
        public TaxiPoint[] points;public MapRing[] holes;
    }
    [Serializable] public class RegionalGeography {public int version;public string attribution,note;public float focusX,focusZ;public MapFeature[] features;public MapReferenceSite[] referenceSites;}

    // All map vertices arrive from the versioned, attributed OSM snapshot. Paths
    // and water effects are illustrations driven by the SAME external clock.
    public class TrainingGeography:MonoBehaviour {
        public const int RoadJunctionSegments=32;
        StandReplay replay;Light regionalSun;bool ownsSun;readonly List<Material> materials=new List<Material>();
        readonly List<GameObject> splash=new List<GameObject>();TrainingIncident water;
        readonly List<Renderer> mapLabels=new List<Renderer>();
        Material Make(Color color){var m=new Material(Shader.Find("Standard"));m.color=color;m.SetFloat("_Glossiness",.25f);materials.Add(m);return m;}
        public static bool Present(RegionalGeography geo)=>geo!=null&&geo.version!=0;
        public static void Validate(RegionalGeography geo){
            if(!Present(geo))return;
            if((geo.version!=1&&geo.version!=2)||geo.features==null||geo.features.Length>1000||string.IsNullOrEmpty(geo.attribution))throw new ArgumentException("Unsupported regional map");
            foreach(var f in geo.features){
                if(f==null||!(f.kind=="water"||f.kind=="runway"||f.kind=="taxiway"||f.kind=="building"||f.kind=="apron"||f.kind=="road"||f.kind=="pavement"||f.kind=="jet_bridge"))throw new ArgumentException("Invalid regional feature");
                ValidatePoints(f.points,2);
                if(!Finite(f.width)||f.width<0||!Finite(f.heightMetres)||f.heightMetres<0||f.heightMetres>350||
                   !Finite(f.deckHeightMetres)||f.deckHeightMetres<0||f.deckHeightMetres>50||!Finite(f.bodyHeightMetres)||f.bodyHeightMetres<0||f.bodyHeightMetres>20)
                    throw new ArgumentException("Invalid regional feature dimensions");
                foreach(var hole in f.holes??new MapRing[0]){if(hole==null)throw new ArgumentException("Invalid map hole");ValidatePoints(hole.points,3);}
                bool stored=f.roofTriangles!=null&&f.roofTriangles.Length>0;
                if(f.holes!=null&&f.holes.Length>0&&!stored)throw new ArgumentException("Holed regional surfaces require triangulation");
                if(stored){
                    if(f.roofPoints==null||f.roofTriangles.Length%3!=0||f.roofTriangles.Any(i=>i<0||i>=f.roofPoints.Length))throw new ArgumentException("Invalid building roof indices");
                    ValidatePoints(f.roofPoints,3,50000);
                }
            }
            foreach(var site in geo.referenceSites??new MapReferenceSite[0]){
                if(site==null||site.renderAs!="outline-only"||string.IsNullOrEmpty(site.name))throw new ArgumentException("Invalid geographic reference site");
                ValidatePoints(site.points,3);
                foreach(var hole in site.holes??new MapRing[0]){if(hole==null)throw new ArgumentException("Invalid reference-site hole");ValidatePoints(hole.points,3);}
            }
        }
        static bool Finite(float value)=>!float.IsNaN(value)&&!float.IsInfinity(value);
        static void ValidatePoints(TaxiPoint[] points,int minimum,int maximum=5000){
            if(points==null||points.Length<minimum||points.Length>maximum)throw new ArgumentException("Invalid map coordinate count");
            foreach(var p in points)if(p==null||!Finite(p.x)||!Finite(p.z)||Mathf.Abs(p.x)>30||Mathf.Abs(p.z)>30)throw new ArgumentException("Invalid map coordinate");
        }
        public void Bind(StandReplay r,Light sharedSun=null){
            replay=r;Validate(r.Data.geography);
            var land=Make(new Color(.34f,.40f,.29f));var asphalt=Make(new Color(.13f,.16f,.18f));
            var blue=Make(new Color(.055f,.29f,.38f));var white=Make(new Color(.92f,.94f,.88f));
            var grey=Make(new Color(.26f,.29f,.28f));
            var terminal=Make(new Color(.64f,.68f,.69f));
            var concrete=Make(new Color(.43f,.45f,.43f));
            var road=Make(new Color(.18f,.21f,.21f));var paving=Make(new Color(.36f,.39f,.38f));
            var lowRise=Make(new Color(.58f,.61f,.60f));var lowRoof=Make(new Color(.39f,.43f,.43f));
            var bridge=Make(new Color(.65f,.69f,.69f));var bridgeGlass=Make(new Color(.13f,.24f,.28f));
            var referenceLine=Make(new Color(.61f,.56f,.43f));
            // Reuse the sun already controlled by TrainingWeather. A second sun
            // overexposes roofs and breaks the existing condition timeline.
            regionalSun=sharedSun!=null?sharedSun:FindObjectsByType<Light>(FindObjectsSortMode.None).FirstOrDefault(l=>l.isActiveAndEnabled&&l.type==LightType.Directional&&l.GetComponentInParent<TrainingGeography>()==null);
            if(regionalSun==null){var sunlight=new GameObject("Regional daylight",typeof(Light));sunlight.transform.SetParent(transform,false);sunlight.transform.rotation=Quaternion.Euler(52,-25,0);regionalSun=sunlight.GetComponent<Light>();regionalSun.type=LightType.Directional;regionalSun.intensity=1.05f;regionalSun.color=new Color(1,.97f,.91f);ownsSun=true;}
            Box("Regional terrain",new Vector3(0,-.004f,-2),new Vector3(32,.002f,24),land);
            var referenceSites=r.Data.geography.referenceSites??new MapReferenceSite[0];
            var outlineOnly=new HashSet<string>(referenceSites.Select(s=>s.id));var namedWater=new HashSet<string>(StringComparer.Ordinal);
            var roadNodes=new Dictionary<Vector2,float>();
            foreach(var f in r.Data.geography.features){
                if(outlineOnly.Contains(f.id))continue;
                if(f.kind=="water"){
                    Surface(f.name,f,-.0002f,blue);
                    // Do not repeat a name across multiple polygon pieces or
                    // cover small ponds with regional-scale lettering.
                    if(!string.IsNullOrEmpty(f.name)&&f.name!="Water"&&f.name!="Mapped waterbody"&&PolygonArea(f.points)>.05f&&namedWater.Add(f.name)){
                        var mid=f.points.Aggregate(Vector2.zero,(v,p)=>v+new Vector2(p.x,p.z))/f.points.Length;
                        Label(f.name,new Vector3(mid.x,.003f,mid.y),.35f);
                    }
                }else if(f.kind=="apron"||f.kind=="pavement"){
                    Surface(f.name+" pavement",f,.00005f,f.kind=="apron"?concrete:paving);
                }else if(f.kind=="road"){
                    float width=f.width>0?f.width:.003f;Ribbon(f.name+" road",f.points,width,.00035f,road);
                    foreach(var point in f.points){var key=new Vector2(point.x,point.z);if(!roadNodes.TryGetValue(key,out var radius)||radius<width*.5f)roadNodes[key]=width*.5f;}
                }else if(f.kind=="jet_bridge"){
                    JetBridge(f,bridge,bridgeGlass);
                }else if(f.kind=="building"){
                    // The mapped outline is replaced by the current-outline /
                    // source-model hybrid, including its separate forecourt roof.
                    if(f.id=="osm-relation-18911624"){TerminalThree.Build(transform);continue;}
                    if(f.id=="osm-way-722642847")continue;
                    if(f.id=="osm-way-133146402"){TerminalTwo.Build(transform,f);continue;}
                    // Missing heights retain the existing authored 18 m fallback;
                    // extracted low-rise buildings carry explicit height metadata.
                    float height=f.heightMetres>0?f.heightMetres/1000:.018f;
                    bool shortBuilding=height<.018f;
                    Surface(f.name+" roof",f,height,shortBuilding?lowRoof:terminal);
                    Walls(f.name,f.points,height,shortBuilding?lowRise:terminal,false);
                    foreach(var hole in f.holes??new MapRing[0])Walls(f.name+" courtyard",hole.points,height,shortBuilding?lowRise:terminal,true);
                }else{
                    Ribbon(f.name,f.points,f.width,.0002f,f.kind=="runway"?asphalt:grey);
                    if(f.kind=="runway"){
                        Ribbon(f.name+" centreline",f.points,.001f,.0005f,white);
                        if(f.name.Contains("/"))Label(f.name,new Vector3(f.points[0].x,.003f,f.points[0].z+.09f),.14f);
                    }
                }
            }
            RoadJunctions(roadNodes,road);
            foreach(var site in referenceSites){
                Ribbon(site.name+" reference outline",Closed(site.points),.0015f,.00035f,referenceLine);
                foreach(var hole in site.holes??new MapRing[0])Ribbon(site.name+" reference inner outline",Closed(hole.points),.0015f,.00035f,referenceLine);
                var mid=site.points.Aggregate(Vector2.zero,(v,p)=>v+new Vector2(p.x,p.z))/site.points.Length;
                string label=site.name;
                if(!string.IsNullOrEmpty(site.status)&&site.status.IndexOf("demolition",StringComparison.OrdinalIgnoreCase)>=0)label+="\nPhased demolition";
                Label(label,new Vector3(mid.x,.003f,mid.y),.10f);
            }
            foreach(var path in r.Data.taxiPaths??new TaxiPath[0])Ribbon("Authored service connector",path.points,path.width,.0007f,grey);
            Label("N ↑",new Vector3(-3,.004f,1.8f),.3f);
            Ribbon("1 km scale",new[]{new TaxiPoint{x=-3,z=1.5f},new TaxiPoint{x=-2,z=1.5f}},.008f,.001f,white);
            Label("1 km",new Vector3(-2.5f,.004f,1.35f),.22f);
            water=(r.Data.incidents??new TrainingIncident[0]).FirstOrDefault(i=>i.kind=="water_landing");
            if(water!=null){
                var foam=Make(new Color(.84f,.93f,.92f));
                for(int i=0;i<64;i++){var p=GameObject.CreatePrimitive(PrimitiveType.Sphere);p.name="Water spray";p.transform.SetParent(transform,false);p.GetComponent<Renderer>().sharedMaterial=foam;Destroy(p.GetComponent<Collider>());p.SetActive(false);splash.Add(p);}
            }
            UpdateLabelVisibility(Camera.main);
        }
        void Update(){if(replay!=null)RenderAt(replay.Clock.Time);}
        // Camera movement occurs in TrainingView.Update. Apply the label policy
        // afterwards so a close view never renders one frame of oversized map text.
        void LateUpdate(){UpdateLabelVisibility(Camera.main);}
        public void UpdateLabelVisibility(Camera view){
            bool visible=false;
            if(view!=null){
                float downward=Vector3.Dot(view.transform.forward,-transform.up);
                float height=Vector3.Dot(view.transform.position-transform.position,transform.up);
                if(height>0&&downward>=Mathf.Sin(40*Mathf.Deg2Rad)){
                    float span=view.orthographic?view.orthographicSize*2:height/downward*2*Mathf.Tan(view.fieldOfView*Mathf.Deg2Rad*.5f);
                    float kilometre=transform.TransformVector(Vector3.right).magnitude;
                    visible=span>=2*kilometre;
                }
            }
            // Keep the existing close-view policy and avoid colliding regional
            // labels on narrow phone views. Source order gives stable priority.
            var occupied=new List<Rect>();
            foreach(var label in mapLabels){
                if(label==null)continue;label.enabled=false;if(!visible)continue;
                var bounds=label.bounds;var low=new Vector2(float.PositiveInfinity,float.PositiveInfinity);var high=new Vector2(float.NegativeInfinity,float.NegativeInfinity);bool behind=false;
                for(int mask=0;mask<8;mask++){
                    var point=bounds.center+Vector3.Scale(bounds.extents,new Vector3((mask&1)==0?-1:1,(mask&2)==0?-1:1,(mask&4)==0?-1:1));
                    var screen=view.WorldToScreenPoint(point);if(screen.z<=0){behind=true;break;}
                    low=Vector2.Min(low,new Vector2(screen.x,screen.y));high=Vector2.Max(high,new Vector2(screen.x,screen.y));
                }
                if(behind)continue;var rect=Rect.MinMaxRect(low.x-6,low.y-4,high.x+6,high.y+4);
                if(!view.pixelRect.Contains(rect.min)||!view.pixelRect.Contains(rect.max)||occupied.Any(r=>r.Overlaps(rect)))continue;
                label.enabled=true;occupied.Add(rect);
            }
        }
        public void RenderAt(float t){
            if(regionalSun!=null&&ownsSun)regionalSun.intensity=1.05f*TrainingWeather.At(replay.Data.environment,t).daylight;
            if(water==null)return;
            var a=replay.Data.aircraft.First(p=>p.id==water.aircraftId);var position=Scenario.Position(a,t);
            float age=t-water.start;
            for(int i=0;i<splash.Count;i++){
                var go=splash[i];go.SetActive(age>=0&&age<35);if(!go.activeSelf)continue;
                float cycle=(age+i*.139f)%1.4f,side=i%2==0?1:-1;
                float power=Mathf.Clamp01(1-age/24);
                go.transform.localPosition=position+new Vector3(side*(.004f+cycle*.009f),.001f+Mathf.Sin(cycle/1.4f*Mathf.PI)*.006f*power,-cycle*.025f);
                go.transform.localScale=new Vector3(.002f,.0008f+power*.0018f,.004f)*(1+cycle);
            }
        }
        void OnDestroy(){foreach(var m in materials)Destroy(m);foreach(var f in GetComponentsInChildren<MeshFilter>())if(f.sharedMesh!=null&&f.sharedMesh.name.StartsWith("Regional "))Destroy(f.sharedMesh);}
        void Box(string name,Vector3 p,Vector3 s,Material m){var go=GameObject.CreatePrimitive(PrimitiveType.Cube);go.name=name;go.transform.SetParent(transform,false);go.transform.localPosition=p;go.transform.localScale=s;go.GetComponent<Renderer>().sharedMaterial=m;Destroy(go.GetComponent<Collider>());}
        void Label(string text,Vector3 p,float size){var go=new GameObject(text,typeof(TextMesh));go.transform.SetParent(transform,false);go.transform.localPosition=p;go.transform.localRotation=Quaternion.Euler(90,0,0);go.transform.localScale=Vector3.one*size;var label=go.GetComponent<TextMesh>();label.font=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");var renderer=go.GetComponent<MeshRenderer>();renderer.sharedMaterial=label.font.material;renderer.enabled=false;mapLabels.Add(renderer);label.text=text;label.fontSize=64;label.characterSize=.15f;label.anchor=TextAnchor.MiddleCenter;label.color=new Color(.94f,.96f,.9f);}
        static TaxiPoint[] Closed(TaxiPoint[] points)=>points[0].x==points[points.Length-1].x&&points[0].z==points[points.Length-1].z?points:points.Concat(new[]{points[0]}).ToArray();
        static float PolygonArea(TaxiPoint[] points){float sum=0;for(int i=0;i<points.Length;i++){var a=points[i];var b=points[(i+1)%points.Length];sum+=a.x*b.z-b.x*a.z;}return Mathf.Abs(sum)*.5f;}
        void Surface(string name,MapFeature feature,float height,Material material){
            bool stored=feature.roofTriangles!=null&&feature.roofTriangles.Length>0;
            var points=stored?feature.roofPoints:feature.points;
            var triangles=stored?(int[])feature.roofTriangles.Clone():Triangulate(points);
            // Wire triangles are CCW in east/north coordinates. Reverse once for
            // Unity's upward Y face; precomputed holes are never filled over.
            if(stored)for(int i=0;i<triangles.Length;i+=3){int swap=triangles[i+1];triangles[i+1]=triangles[i+2];triangles[i+2]=swap;}
            Mesh(name,points.Select(p=>new Vector3(p.x,height,p.z)).ToArray(),triangles,material);
        }
        void RoadJunctions(Dictionary<Vector2,float> nodes,Material material){
            if(nodes.Count==0)return;
            var vertices=new List<Vector3>();var triangles=new List<int>();
            foreach(var node in nodes){
                int k=vertices.Count;var centre=new Vector3(node.Key.x,.00035f,node.Key.y);vertices.Add(centre);
                for(int i=0;i<RoadJunctionSegments;i++){
                    float angle=i*Mathf.PI*2/RoadJunctionSegments;
                    vertices.Add(centre+new Vector3(Mathf.Cos(angle),0,Mathf.Sin(angle))*node.Value);
                }
                for(int i=0;i<RoadJunctionSegments;i++)triangles.AddRange(new[]{k,k+(i+1)%RoadJunctionSegments+1,k+i+1});
            }
            // Round caps/joins remain within the road's existing half-width around
            // each sourced node, closing seams between independently mapped ways.
            Mesh("Road centreline junctions",vertices.ToArray(),triangles.ToArray(),material);
        }
        void JetBridge(MapFeature feature,Material body,Material glass){
            float width=feature.width>0?feature.width:.003f;
            float floor=feature.deckHeightMetres>0?feature.deckHeightMetres/1000:.005f;
            float height=feature.bodyHeightMetres>0?feature.bodyHeightMetres/1000:.003f;
            for(int i=1;i<feature.points.Length;i++){
                var a=new Vector3(feature.points[i-1].x,0,feature.points[i-1].z);var b=new Vector3(feature.points[i].x,0,feature.points[i].z);
                var delta=b-a;float length=delta.magnitude;if(length<.0001f)continue;
                var direction=delta/length;var sideways=new Vector3(-direction.z,0,direction.x);var rotation=Quaternion.LookRotation(direction);
                string name=feature.id+" mapped passenger bridge "+i;
                var centre=(a+b)*.5f+Vector3.up*(floor+height*.5f);
                AlignedBox(name,centre,new Vector3(width,height,length),rotation,body);
                foreach(int side in new[]{-1,1})AlignedBox(name+" windows",centre+sideways*(side*(width*.5f+.00002f)),new Vector3(.00004f,height*.38f,Mathf.Max(.0001f,length-.0002f)),rotation,glass);
                // Only source polylines define placement; section and support
                // dimensions are explicit authored values, not live bridge poses.
                float support=Mathf.Max(.0001f,floor-.0002f);
                Box(name+" support",b-direction*Mathf.Min(.001f,length*.25f)+Vector3.up*(.0002f+support*.5f),new Vector3(.00045f,support,.00045f),body);
            }
        }
        void AlignedBox(string name,Vector3 position,Vector3 scale,Quaternion rotation,Material material){
            var go=GameObject.CreatePrimitive(PrimitiveType.Cube);go.name=name;go.transform.SetParent(transform,false);go.transform.localPosition=position;go.transform.localRotation=rotation;go.transform.localScale=scale;go.GetComponent<Renderer>().sharedMaterial=material;Destroy(go.GetComponent<Collider>());
        }
        void Walls(string name,TaxiPoint[] points,float height,Material mat,bool inner){
            points=Closed(points);
            float area=0;for(int j=1;j<points.Length;j++)area+=points[j-1].x*points[j].z-points[j].x*points[j-1].z;
            bool reverse=(area<0)^inner;var vertices=new List<Vector3>();var indices=new List<int>();
            for(int j=1;j<points.Length;j++){
                int k=vertices.Count;var a=points[j-1];var b=points[j];if(Mathf.Abs(a.x-b.x)+Mathf.Abs(a.z-b.z)<1e-8f)continue;
                vertices.AddRange(new[]{new Vector3(a.x,0,a.z),new Vector3(b.x,0,b.z),new Vector3(a.x,height,a.z),new Vector3(b.x,height,b.z)});
                indices.AddRange(reverse?new[]{k,k+1,k+2,k+1,k+3,k+2}:new[]{k,k+2,k+1,k+1,k+2,k+3});
            }Mesh(name+" walls",vertices.ToArray(),indices.ToArray(),mat);
        }
        void Mesh(string name,Vector3[] vertices,int[] indices,Material m){var go=new GameObject(name,typeof(MeshFilter),typeof(MeshRenderer));go.transform.SetParent(transform,false);var mesh=new Mesh{name="Regional "+name};if(vertices.Length>65535)mesh.indexFormat=UnityEngine.Rendering.IndexFormat.UInt32;mesh.vertices=vertices;mesh.triangles=indices;mesh.RecalculateNormals();mesh.RecalculateBounds();go.GetComponent<MeshFilter>().sharedMesh=mesh;go.GetComponent<MeshRenderer>().sharedMaterial=m;}
        void Ribbon(string name,TaxiPoint[] points,float width,float y,Material mat){
            if(points.Length<2)return;var v=new Vector3[points.Length*2];var ids=new List<int>();
            for(int i=0;i<points.Length;i++){
                var a=points[Mathf.Max(0,i-1)];var b=points[Mathf.Min(points.Length-1,i+1)];var n=new Vector3(-(b.z-a.z),0,b.x-a.x).normalized*width/2;
                v[i*2]=new Vector3(points[i].x,y,points[i].z)+n;v[i*2+1]=new Vector3(points[i].x,y,points[i].z)-n;
                if(i>0){int k=i*2;ids.AddRange(new[]{k-2,k,k-1,k-1,k,k+1});}
            }Mesh(name,v,ids.ToArray(),mat);
        }
        // Ear clipping preserves concave shorelines, unlike a fan from a centre.
        public static int[] Triangulate(TaxiPoint[] input){
            int count=input.Length;if(input[0].x==input[count-1].x&&input[0].z==input[count-1].z)count--;
            var remaining=Enumerable.Range(0,count).ToList();var output=new List<int>();float area=0;
            for(int i=0;i<count;i++)area+=input[i].x*input[(i+1)%count].z-input[(i+1)%count].x*input[i].z;
            if(area<0)remaining.Reverse();
            float Cross(TaxiPoint a,TaxiPoint b,TaxiPoint c)=>(b.x-a.x)*(c.z-a.z)-(b.z-a.z)*(c.x-a.x);
            int guard=count*count;
            while(remaining.Count>2&&guard-->0){bool found=false;
                for(int i=0;i<remaining.Count;i++){
                    int a=remaining[(i+remaining.Count-1)%remaining.Count],b=remaining[i],c=remaining[(i+1)%remaining.Count];
                    if(Cross(input[a],input[b],input[c])<=1e-9f)continue;
                    bool contains=remaining.Any(k=>k!=a&&k!=b&&k!=c&&Cross(input[a],input[b],input[k])>=0&&Cross(input[b],input[c],input[k])>=0&&Cross(input[c],input[a],input[k])>=0);
                    if(contains)continue;output.AddRange(new[]{a,c,b});remaining.RemoveAt(i);found=true;break;
                }if(!found)throw new ArgumentException("Unable to triangulate shoreline");
            }return output.ToArray();
        }
    }
}
