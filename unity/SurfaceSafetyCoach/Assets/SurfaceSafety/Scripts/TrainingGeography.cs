using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace SurfaceSafety {
    [Serializable] public class MapRing {public TaxiPoint[] points;}
    [Serializable] public class MapFeature {public string id,name,kind;public float width;public bool closed;public TaxiPoint[] points,roofPoints;public int[] roofTriangles;public MapRing[] holes;}
    [Serializable] public class RegionalGeography {public int version;public string attribution,note;public float focusX,focusZ;public MapFeature[] features;}

    // All map vertices arrive from the versioned, attributed OSM snapshot. Paths
    // and water effects are illustrations driven by the SAME external clock.
    public class TrainingGeography:MonoBehaviour {
        StandReplay replay;Light regionalSun;bool ownsSun;readonly List<Material> materials=new List<Material>();
        readonly List<GameObject> splash=new List<GameObject>();TrainingIncident water;
        readonly List<Renderer> mapLabels=new List<Renderer>();
        Material Make(Color color){var m=new Material(Shader.Find("Standard"));m.color=color;m.SetFloat("_Glossiness",.25f);materials.Add(m);return m;}
        public static bool Present(RegionalGeography geo)=>geo!=null&&geo.version!=0;
        public static void Validate(RegionalGeography geo){
            if(!Present(geo))return;
            if(geo.version!=1||geo.features==null||geo.features.Length>1000||string.IsNullOrEmpty(geo.attribution))throw new ArgumentException("Unsupported regional map");
            foreach(var f in geo.features){
                if(f.points==null||f.points.Length<2||f.points.Length>5000||!(f.kind=="water"||f.kind=="runway"||f.kind=="taxiway"||f.kind=="building"||f.kind=="apron"))throw new ArgumentException("Invalid regional feature");
                foreach(var p in f.points)if(float.IsNaN(p.x)||float.IsInfinity(p.x)||float.IsNaN(p.z)||float.IsInfinity(p.z)||Mathf.Abs(p.x)>30||Mathf.Abs(p.z)>30)throw new ArgumentException("Invalid map coordinate");
                if(f.roofTriangles!=null&&f.roofTriangles.Length>0){
                    if(f.roofPoints==null||f.roofTriangles.Length%3!=0||f.roofTriangles.Any(i=>i<0||i>=f.roofPoints.Length))throw new ArgumentException("Invalid building roof indices");
                    foreach(var p in f.roofPoints)if(float.IsNaN(p.x)||float.IsInfinity(p.x)||float.IsNaN(p.z)||float.IsInfinity(p.z))throw new ArgumentException("Invalid roof coordinate");
                }
            }
        }
        public void Bind(StandReplay r,Light sharedSun=null){
            replay=r;Validate(r.Data.geography);
            var land=Make(new Color(.34f,.40f,.29f));var asphalt=Make(new Color(.13f,.16f,.18f));
            var blue=Make(new Color(.055f,.29f,.38f));var white=Make(new Color(.92f,.94f,.88f));
            var grey=Make(new Color(.26f,.29f,.28f));
            var terminal=Make(new Color(.64f,.68f,.69f));
            var concrete=Make(new Color(.43f,.45f,.43f));
            // Reuse the sun already controlled by TrainingWeather. A second sun
            // overexposes roofs and breaks the existing condition timeline.
            regionalSun=sharedSun!=null?sharedSun:FindObjectsByType<Light>(FindObjectsSortMode.None).FirstOrDefault(l=>l.isActiveAndEnabled&&l.type==LightType.Directional&&l.GetComponentInParent<TrainingGeography>()==null);
            if(regionalSun==null){var sunlight=new GameObject("Regional daylight",typeof(Light));sunlight.transform.SetParent(transform,false);sunlight.transform.rotation=Quaternion.Euler(52,-25,0);regionalSun=sunlight.GetComponent<Light>();regionalSun.type=LightType.Directional;regionalSun.intensity=1.05f;regionalSun.color=new Color(1,.97f,.91f);ownsSun=true;}
            Box("Regional terrain",new Vector3(0,-.004f,-2),new Vector3(32,.002f,24),land);
            foreach(var f in r.Data.geography.features){
                if(f.kind=="water"){
                    Polygon(f.name,f.points,blue);var mid=f.points.Aggregate(Vector2.zero,(v,p)=>v+new Vector2(p.x,p.z))/f.points.Length;
                    Label(f.name,new Vector3(mid.x,.003f,mid.y),.35f);
                }else if(f.kind=="apron"){
                    var roof=(int[])f.roofTriangles.Clone();
                    for(int j=0;j<roof.Length;j+=3){int swap=roof[j+1];roof[j+1]=roof[j+2];roof[j+2]=swap;}
                    Mesh(f.name+" pavement",f.roofPoints.Select(p=>new Vector3(p.x,.00005f,p.z)).ToArray(),roof,concrete);
                }else if(f.kind=="building"){
                    // The mapped outline is replaced by the current-outline /
                    // source-model hybrid, including its separate forecourt roof.
                    if(f.id=="osm-relation-18911624"){TerminalThree.Build(transform);continue;}
                    if(f.id=="osm-way-722642847")continue;
                    // Footprints are sourced; height is an authored 18 m massing.
                    bool stored=f.roofPoints!=null&&f.roofPoints.Length>0;
                    var top=(stored?f.roofPoints:f.points).Select(p=>new Vector3(p.x,.018f,p.z)).ToArray();
                    var roof=stored?(int[])f.roofTriangles.Clone():Triangulate(f.points);
                    if(stored)for(int j=0;j<roof.Length;j+=3){int swap=roof[j+1];roof[j+1]=roof[j+2];roof[j+2]=swap;}
                    Mesh(f.name+" roof",top,roof,terminal);Walls(f.name,f.points,.018f,terminal,false);
                    foreach(var hole in f.holes??new MapRing[0])Walls(f.name+" courtyard",hole.points,.018f,terminal,true);
                }else{
                    Ribbon(f.name,f.points,f.width,.0002f,f.kind=="runway"?asphalt:grey);
                    if(f.kind=="runway"){
                        Ribbon(f.name+" centreline",f.points,.001f,.0005f,white);
                        if(f.name.Contains("/"))Label(f.name,new Vector3(f.points[0].x,.003f,f.points[0].z+.09f),.14f);
                    }
                }
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
            foreach(var label in mapLabels)if(label!=null)label.enabled=visible;
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
        void Walls(string name,TaxiPoint[] points,float height,Material mat,bool inner){
            float area=0;for(int j=1;j<points.Length;j++)area+=points[j-1].x*points[j].z-points[j].x*points[j-1].z;
            bool reverse=(area<0)^inner;var vertices=new List<Vector3>();var indices=new List<int>();
            for(int j=1;j<points.Length;j++){
                int k=vertices.Count;var a=points[j-1];var b=points[j];if(Mathf.Abs(a.x-b.x)+Mathf.Abs(a.z-b.z)<1e-8f)continue;
                vertices.AddRange(new[]{new Vector3(a.x,0,a.z),new Vector3(b.x,0,b.z),new Vector3(a.x,height,a.z),new Vector3(b.x,height,b.z)});
                indices.AddRange(reverse?new[]{k,k+1,k+2,k+1,k+3,k+2}:new[]{k,k+2,k+1,k+1,k+2,k+3});
            }Mesh(name+" walls",vertices.ToArray(),indices.ToArray(),mat);
        }
        void Mesh(string name,Vector3[] vertices,int[] indices,Material m){var go=new GameObject(name,typeof(MeshFilter),typeof(MeshRenderer));go.transform.SetParent(transform,false);var mesh=new Mesh{name="Regional "+name};mesh.vertices=vertices;mesh.triangles=indices;mesh.RecalculateNormals();mesh.RecalculateBounds();go.GetComponent<MeshFilter>().sharedMesh=mesh;go.GetComponent<MeshRenderer>().sharedMaterial=m;}
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
        void Polygon(string name,TaxiPoint[] points,Material mat){Mesh(name,points.Select(p=>new Vector3(p.x,-.0002f,p.z)).ToArray(),Triangulate(points),mat);}
    }
}
