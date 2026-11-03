using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace SurfaceSafety {
    // Current mapped Terminal 2A footprint, including its narrow appendages.
    // Three shallow north-facing roof waves reflect the architect's description;
    // their spacing/amplitude and the 12 m annex height are authored, not surveyed.
    // Terminal 2B is separate. No above-ground connection to it is introduced.
    public sealed class TerminalTwo:MonoBehaviour {
        const float West=.5828f,East=.851f,South=-.130f,North=.072f,AnnexHeight=.012f;
        const int Bands=3,SamplesPerBand=8;
        MapFeature feature;float peak,eave;
        readonly List<Mesh> meshes=new List<Mesh>();readonly List<Material> materials=new List<Material>();

        public static GameObject Build(Transform parent,MapFeature mapped){
            var root=new GameObject("Terminal 2A mapped hall and roof waves");root.transform.SetParent(parent,false);
            var renderer=root.AddComponent<TerminalTwo>();renderer.feature=mapped;
            renderer.peak=mapped.heightMetres>0?mapped.heightMetres/1000:.040f;renderer.eave=renderer.peak-.004f;
            try {renderer.BuildGeometry();}catch{Release(root);throw;}
            return root;
        }
        Material Paint(string name,Color color,float gloss=.3f,float metal=0){
            var material=new Material(Shader.Find("Standard")){name="Terminal 2 "+name,color=color};
            material.SetFloat("_Glossiness",gloss);material.SetFloat("_Metallic",metal);materials.Add(material);return material;
        }
        void Emit(string name,Geometry geometry,Material material){
            if(geometry.vertices.Count==0)return;
            var mesh=new Mesh{name="Terminal 2 "+name};if(geometry.vertices.Count>65535)mesh.indexFormat=UnityEngine.Rendering.IndexFormat.UInt32;
            mesh.SetVertices(geometry.vertices);mesh.SetTriangles(geometry.triangles,0);mesh.RecalculateNormals();mesh.RecalculateBounds();meshes.Add(mesh);
            var go=new GameObject(name,typeof(MeshFilter),typeof(MeshRenderer));go.transform.SetParent(transform,false);
            go.GetComponent<MeshFilter>().sharedMesh=mesh;go.GetComponent<MeshRenderer>().sharedMaterial=material;
        }
        void BuildGeometry(){
            var roof=new Geometry();var walls=new Geometry();var glazing=new Geometry();var clerestories=new Geometry();
            bool stored=feature.roofTriangles!=null&&feature.roofTriangles.Length>0;
            var points=stored?feature.roofPoints:feature.points;var triangles=stored?feature.roofTriangles:TrainingGeography.Triangulate(points);
            for(int i=0;i<triangles.Length;i+=3){
                var polygon=new[]{Point(points[triangles[i]]),Point(points[triangles[i+1]]),Point(points[triangles[i+2]])}.ToList();
                // Split, rather than cover, the actual roof triangles at the broad
                // hall's bounds. Narrow projections remain lower connected annexes.
                foreach(var plane in new[]{new Vector3(1,0,West),new Vector3(-1,0,East),new Vector3(0,1,South),new Vector3(0,-1,North)}){
                    bool x=plane.x!=0,positive=(x?plane.x:plane.y)>0;
                    roof.Surface(Clip(polygon,x,plane.z,!positive),p=>AnnexHeight);
                    polygon=Clip(polygon,x,plane.z,positive);if(polygon.Count<3)break;
                }
                if(polygon.Count<3)continue;
                for(int band=0;band<Bands;band++)for(int cell=0;cell<SamplesPerBand;cell++){
                    float lo=BandStart(band)+(North-South)/Bands*cell/SamplesPerBand;
                    float hi=BandStart(band)+(North-South)/Bands*(cell+1)/SamplesPerBand;
                    var strip=Clip(Clip(polygon,false,lo,true),false,hi,false);int captured=band;
                    roof.Surface(strip,p=>RoofHeight(p.z,captured));
                }
            }
            OuterWalls(feature.points,false,walls,glazing);
            foreach(var hole in feature.holes??new MapRing[0])OuterWalls(hole.points,true,walls,glazing);
            StepWalls(true,West,Vector3.left,walls,glazing);StepWalls(true,East,Vector3.right,walls,glazing);
            StepWalls(false,South,Vector3.back,walls,glazing);StepWalls(false,North,Vector3.forward,walls,glazing);
            for(int band=1;band<Bands;band++){
                float z=BandStart(band);
                foreach(var span in Spans(false,z)){
                    var a=span[0];var b=span[1];a.x=Mathf.Max(a.x,West);b.x=Mathf.Min(b.x,East);
                    if(b.x-a.x>.00001f)clerestories.Quad(a+Vector3.up*eave,b+Vector3.up*eave,b+Vector3.up*peak,a+Vector3.up*peak,Vector3.forward);
                }
            }
            Emit("Clipped three-wave roof and low annexes",roof,Paint("roof",new Color(.60f,.65f,.67f),.38f,.15f));
            Emit("Mapped exterior and courtyard walls",walls,Paint("cladding",new Color(.70f,.73f,.72f),.26f,.08f));
            Emit("Restrained facade glazing",glazing,Paint("glass",new Color(.15f,.28f,.33f),.63f,.3f));
            Emit("North-facing roof clerestories",clerestories,Paint("clerestory glass",new Color(.22f,.39f,.46f),.68f,.25f));
        }
        static Vector3 Point(TaxiPoint point)=>new Vector3(point.x,0,point.z);
        static float BandStart(int band)=>South+(North-South)*band/Bands;
        int Band(float z)=>Mathf.Clamp(Mathf.FloorToInt((z-South)/(North-South)*Bands),0,Bands-1);
        float RoofHeight(float z,int band)=>eave+(peak-eave)*Mathf.Sin(Mathf.Clamp01((z-BandStart(band))/((North-South)/Bands))*Mathf.PI*.5f);
        static bool MainHall(Vector3 p)=>p.x>=West&&p.x<=East&&p.z>=South&&p.z<=North;
        static List<Vector3> Clip(List<Vector3> input,bool x,float boundary,bool keepGreater){
            var output=new List<Vector3>();if(input.Count<3)return output;
            var a=input[input.Count-1];float av=(x?a.x:a.z)-boundary;bool ai=keepGreater?av>=0:av<=0;
            foreach(var b in input){
                float bv=(x?b.x:b.z)-boundary;bool bi=keepGreater?bv>=0:bv<=0;
                if(ai!=bi){float t=av/(av-bv);output.Add(Vector3.LerpUnclamped(a,b,t));}
                if(bi)output.Add(b);a=b;av=bv;ai=bi;
            }
            for(int i=output.Count-1;i>=0&&output.Count>1;i--)if((output[i]-output[(i+1)%output.Count]).sqrMagnitude<1e-16f)output.RemoveAt(i);
            return output;
        }
        IEnumerable<Vector3[]> SplitEdge(Vector3 a,Vector3 b){
            var cuts=new List<float>{0,1};var d=b-a;
            Action<bool,float> add=(x,value)=>{float delta=x?d.x:d.z;if(Mathf.Abs(delta)<1e-9f)return;float t=(value-(x?a.x:a.z))/delta;if(t>0&&t<1)cuts.Add(t);};
            add(true,West);add(true,East);
            for(int i=0;i<=Bands*SamplesPerBand;i++)add(false,South+(North-South)*i/(Bands*SamplesPerBand));
            cuts.Sort();for(int i=1;i<cuts.Count;i++)if(cuts[i]-cuts[i-1]>1e-6f)yield return new[]{Vector3.Lerp(a,b,cuts[i-1]),Vector3.Lerp(a,b,cuts[i])};
        }
        void OuterWalls(TaxiPoint[] points,bool inner,Geometry walls,Geometry glazing){
            float area=0;for(int i=0;i<points.Length;i++){var a=points[i];var b=points[(i+1)%points.Length];area+=a.x*b.z-b.x*a.z;}
            float sign=(area>=0?1:-1)*(inner?-1:1);
            for(int i=0;i<points.Length;i++){
                var a=Point(points[i]);var b=Point(points[(i+1)%points.Length]);var normal=new Vector3(b.z-a.z,0,a.x-b.x).normalized*sign;
                if((b-a).sqrMagnitude<1e-12f)continue;
                foreach(var span in SplitEdge(a,b)){
                    var middle=(span[0]+span[1])*.5f;bool main=MainHall(middle);int band=Band(middle.z);
                    Wall(span[0],span[1],normal,0,main?RoofHeight(span[0].z,band):AnnexHeight,main?RoofHeight(span[1].z,band):AnnexHeight,main,walls,glazing);
                }
            }
        }
        void StepWalls(bool x,float coordinate,Vector3 normal,Geometry walls,Geometry glazing){
            foreach(var span in Spans(x,coordinate))foreach(var edge in SplitEdge(span[0],span[1])){
                var middle=(edge[0]+edge[1])*.5f;
                // Only the internal high-hall/low-annex interface needs this wall.
                // Actual exterior walls are already represented by their own ring.
                if(!Inside(middle-normal*.00002f)||!Inside(middle+normal*.00002f))continue;
                if(x&&(middle.z<South||middle.z>North)||!x&&(middle.x<West||middle.x>East))continue;
                int band=Band(middle.z);Wall(edge[0],edge[1],normal,AnnexHeight,RoofHeight(edge[0].z,band),RoofHeight(edge[1].z,band),true,walls,glazing);
            }
        }
        static void Wall(Vector3 a,Vector3 b,Vector3 normal,float bottom,float topA,float topB,bool main,Geometry walls,Geometry glass){
            walls.Quad(a+Vector3.up*bottom,b+Vector3.up*bottom,b+Vector3.up*topB,a+Vector3.up*topA,normal);
            foreach(var band in main?new[]{new Vector2(.003f,.008f),new Vector2(.016f,.023f)}:new[]{new Vector2(.0015f,.004f),new Vector2(.006f,.0093f)}){
                float lo=Mathf.Max(bottom,band.x),hi=Mathf.Min(Mathf.Min(topA,topB),band.y);if(hi<=lo)continue;
                var offset=normal*.00006f;glass.Quad(a+offset+Vector3.up*lo,b+offset+Vector3.up*lo,b+offset+Vector3.up*hi,a+offset+Vector3.up*hi,normal);
            }
        }
        IEnumerable<Vector3[]> Spans(bool x,float coordinate){
            var cuts=new List<float>();var rings=new List<TaxiPoint[]>{feature.points};rings.AddRange((feature.holes??new MapRing[0]).Select(h=>h.points));
            foreach(var points in rings)for(int i=0;i<points.Length;i++){
                var a=points[i];var b=points[(i+1)%points.Length];float av=x?a.x:a.z,bv=x?b.x:b.z;
                if((av>coordinate)==(bv>coordinate))continue;
                cuts.Add(Mathf.Lerp(x?a.z:a.x,x?b.z:b.x,(coordinate-av)/(bv-av)));
            }
            cuts.Sort();for(int i=0;i+1<cuts.Count;i+=2)if(cuts[i+1]-cuts[i]>.00001f)
                yield return x?new[]{new Vector3(coordinate,0,cuts[i]),new Vector3(coordinate,0,cuts[i+1])}:new[]{new Vector3(cuts[i],0,coordinate),new Vector3(cuts[i+1],0,coordinate)};
        }
        bool Inside(Vector3 p)=>InsideRing(p,feature.points)&&!(feature.holes??new MapRing[0]).Any(h=>InsideRing(p,h.points));
        static bool InsideRing(Vector3 p,TaxiPoint[] points){
            bool inside=false;for(int i=0,j=points.Length-1;i<points.Length;j=i++){
                var a=points[i];var b=points[j];if((a.z>p.z)!=(b.z>p.z)&&p.x<(b.x-a.x)*(p.z-a.z)/(b.z-a.z)+a.x)inside=!inside;
            }return inside;
        }
        sealed class Geometry {
            public readonly List<Vector3> vertices=new List<Vector3>();public readonly List<int> triangles=new List<int>();
            public void Surface(List<Vector3> polygon,Func<Vector3,float> height){
                if(polygon.Count<3)return;var points=polygon.Select(p=>new Vector3(p.x,height(p),p.z)).ToArray();
                for(int i=1;i<points.Length-1;i++){
                    var a=points[0];var b=points[i];var c=points[i+1];var normal=Vector3.Cross(b-a,c-a);if(normal.sqrMagnitude<1e-18f)continue;
                    int k=vertices.Count;vertices.AddRange(new[]{a,b,c});triangles.AddRange(normal.y>=0?new[]{k,k+1,k+2}:new[]{k,k+2,k+1});
                }
            }
            public void Quad(Vector3 a,Vector3 b,Vector3 c,Vector3 d,Vector3 normal){
                if(Vector3.Cross(b-a,c-a).sqrMagnitude<1e-18f)return;
                int k=vertices.Count;vertices.AddRange(new[]{a,b,c,d});triangles.AddRange(Vector3.Dot(Vector3.Cross(b-a,c-a),normal)>=0?new[]{k,k+1,k+2,k,k+2,k+3}:new[]{k,k+2,k+1,k,k+3,k+2});
            }
        }
        static void Release(UnityEngine.Object obj){if(Application.isPlaying)Destroy(obj);else DestroyImmediate(obj);}
        void OnDestroy(){foreach(var mesh in meshes)if(mesh!=null)Release(mesh);foreach(var material in materials)if(material!=null)Release(material);}
    }
}
