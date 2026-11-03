using System.Collections.Generic;
using UnityEngine;

namespace SurfaceSafety {
    // Original lightweight geometry: a generic twin-engine airliner, not a named aircraft type.
    // The model faces +Z so the replay's existing trajectory orientation remains authoritative.
    public static class AircraftVisual {
        public static void Build(Transform parent, Color livery) {
            var model=new GameObject("Airliner visual").transform;
            model.SetParent(parent,false);model.localScale=Vector3.one*.031f;
            var white=Material(new Color(.91f,.94f,.95f),.23f,.50f);
            var wing=Material(new Color(.69f,.76f,.80f),.45f,.38f);
            var accent=Material(livery,.12f,.40f);
            var glass=Material(new Color(.025f,.09f,.13f),.30f,.72f);
            var rubber=Material(new Color(.035f,.045f,.05f),0,.12f);
            var metal=Material(new Color(.32f,.38f,.41f),.7f,.48f);
            Loft(model,"Tapered fuselage",Vector3.zero,
                new[]{-.50f,-.43f,-.31f,.23f,.35f,.43f,.48f,.505f},
                new[]{.008f,.033f,.070f,.070f,.066f,.052f,.029f,.003f},
                new[]{.14f,.14f,.13f,.13f,.125f,.12f,.115f,.115f},1.05f,white,24);
            for(int side=-1;side<=1;side+=2) {
                // Swept main wing and tailplane are solid, tapered surfaces rather than boxes.
                Prism(model,"Swept wing",new[]{new Vector3(side*.050f,.105f,.115f),new Vector3(side*.20f,.105f,.035f),
                    new Vector3(side*.52f,.125f,-.145f),new Vector3(side*.51f,.125f,-.205f),new Vector3(side*.075f,.105f,-.19f)},Vector3.up*.009f,wing);
                Prism(model,"Tailplane",new[]{new Vector3(side*.025f,.155f,-.32f),new Vector3(side*.22f,.17f,-.445f),
                    new Vector3(side*.22f,.17f,-.49f),new Vector3(side*.025f,.155f,-.43f)},Vector3.up*.006f,wing);
                Prism(model,"Wingtip",new[]{new Vector3(side*.51f,.12f,-.145f),new Vector3(side*.53f,.20f,-.18f),
                    new Vector3(side*.53f,.20f,-.22f),new Vector3(side*.51f,.12f,-.205f)},Vector3.right*.005f,accent);
                var engine=new Vector3(side*.185f,.058f,.035f);
                Loft(model,"Engine nacelle",engine,new[]{-.080f,-.065f,.05f,.085f},new[]{.035f,.044f,.044f,.039f},new[]{0f,0f,0f,0f},1f,white,20);
                Disk(model,"Engine intake",engine+Vector3.forward*.086f,.033f,glass,20);
                Loft(model,"Intake spinner",engine,new[]{.087f,.107f},new[]{.010f,.001f},new[]{0f,0f},1f,metal,16);
                Disk(model,"Engine exhaust",engine+Vector3.back*.081f,.024f,rubber,16,true);
                Prism(model,"Engine pylon",new[]{new Vector3(side*.18f,.062f,-.015f),new Vector3(side*.18f,.11f,-.06f),
                    new Vector3(side*.18f,.11f,.045f),new Vector3(side*.18f,.062f,.065f)},Vector3.right*.012f,wing);
                // Glazing follows the upper shoulder of the nose; visible from the elevated board view.
                Prism(model,"Cockpit glazing",new[]{new Vector3(side*.008f,.173f,.426f),new Vector3(side*.035f,.164f,.437f),
                    new Vector3(side*.054f,.161f,.392f),new Vector3(side*.013f,.185f,.392f)},Vector3.up*.0015f,glass);
                for(int n=0;n<12;n++) {
                    float z=.29f-n*.046f;
                    var window=new GameObject("Cabin window",typeof(MeshFilter),typeof(MeshRenderer));window.transform.SetParent(model,false);
                    // Small upper-side windows provide scale without texture assets.
                    Quad(window,new Vector3(side*.060f,.172f,z),new Vector3(side*.064f,.163f,z),
                        new Vector3(side*.064f,.163f,z-.019f),new Vector3(side*.060f,.172f,z-.019f),glass,side<0);
                }
                // Main gear is deliberately understated at board scale.
                Sphere(model,"Main wheel",new Vector3(side*.085f,-.052f,-.10f),new Vector3(.023f,.035f,.035f),rubber);
                Prism(model,"Gear strut",new[]{new Vector3(side*.085f,-.05f,-.11f),new Vector3(side*.085f,.08f,-.11f),
                    new Vector3(side*.085f,.08f,-.09f),new Vector3(side*.085f,-.05f,-.09f)},Vector3.right*.009f,metal);
            }
            Prism(model,"Vertical tail",new[]{new Vector3(0,.15f,-.29f),new Vector3(0,.38f,-.425f),
                new Vector3(0,.38f,-.48f),new Vector3(0,.14f,-.47f)},Vector3.right*.012f,accent);
            Sphere(model,"Nose wheel",new Vector3(0,-.052f,.32f),new Vector3(.024f,.030f,.030f),rubber);
        }
        internal static Material Material(Color color,float metallic,float smoothness) {
            var m=new Material(Shader.Find("Standard"));m.color=color;m.SetFloat("_Metallic",metallic);m.SetFloat("_Glossiness",smoothness);return m;
        }
        internal static void MeshObject(Transform parent,string name,List<Vector3> vertices,List<int> triangles,Material material) {
            var obj=new GameObject(name,typeof(MeshFilter),typeof(MeshRenderer));obj.transform.SetParent(parent,false);
            var mesh=new Mesh{name=name};mesh.SetVertices(vertices);mesh.SetTriangles(triangles,0);mesh.RecalculateNormals();mesh.RecalculateBounds();
            obj.GetComponent<MeshFilter>().sharedMesh=mesh;obj.GetComponent<MeshRenderer>().sharedMaterial=material;
        }
        internal static void Loft(Transform parent,string name,Vector3 origin,float[] z,float[] radius,float[] centerY,float heightRatio,Material material,int sides) {
            var v=new List<Vector3>();var t=new List<int>();
            for(int row=0;row<z.Length;row++)for(int j=0;j<sides;j++) {
                float a=j*Mathf.PI*2/sides;v.Add(origin+new Vector3(Mathf.Sin(a)*radius[row],centerY[row]+Mathf.Cos(a)*radius[row]*heightRatio,z[row]));
            }
            for(int row=0;row<z.Length-1;row++)for(int j=0;j<sides;j++) {
                int a=row*sides+j,b=row*sides+(j+1)%sides,c=(row+1)*sides+j,d=(row+1)*sides+(j+1)%sides;
                t.AddRange(new[]{a,c,b,b,c,d});
            }
            MeshObject(parent,name,v,t,material);
        }
        internal static void Disk(Transform parent,string name,Vector3 center,float radius,Material material,int sides,bool reverse=false) {
            var v=new List<Vector3>{center};var t=new List<int>();
            for(int i=0;i<sides;i++){float a=i*Mathf.PI*2/sides;v.Add(center+new Vector3(Mathf.Cos(a)*radius,Mathf.Sin(a)*radius,0));}
            for(int i=0;i<sides;i++){int a=i+1,b=(i+1)%sides+1;t.AddRange(reverse?new[]{0,b,a}:new[]{0,a,b});}
            MeshObject(parent,name,v,t,material);
        }
        internal static void Prism(Transform parent,string name,Vector3[] polygon,Vector3 extrusion,Material material) {
            var v=new List<Vector3>();var t=new List<int>();
            var normal=Vector3.Cross(polygon[1]-polygon[0],polygon[2]-polygon[0]);
            if(Vector3.Dot(normal,extrusion)<0)System.Array.Reverse(polygon);
            int n=polygon.Length;
            for(int i=0;i<n;i++)v.Add(polygon[i]+extrusion*.5f);
            for(int i=0;i<n;i++)v.Add(polygon[i]-extrusion*.5f);
            for(int i=1;i<n-1;i++){t.AddRange(new[]{0,i,i+1,n,n+i+1,n+i});}
            for(int i=0;i<n;i++){
                int j=(i+1)%n,k=v.Count;v.AddRange(new[]{polygon[i]+extrusion*.5f,polygon[i]-extrusion*.5f,polygon[j]-extrusion*.5f,polygon[j]+extrusion*.5f});
                t.AddRange(new[]{k,k+1,k+2,k,k+2,k+3});
            }
            MeshObject(parent,name,v,t,material);
        }
        static void Quad(GameObject obj,Vector3 a,Vector3 b,Vector3 c,Vector3 d,Material material,bool reverse) {
            var mesh=new Mesh{name="Cabin glazing"};mesh.vertices=new[]{a,b,c,d};mesh.triangles=reverse?new[]{0,2,1,0,3,2}:new[]{0,1,2,0,2,3};mesh.RecalculateNormals();mesh.RecalculateBounds();
            obj.GetComponent<MeshFilter>().sharedMesh=mesh;obj.GetComponent<MeshRenderer>().sharedMaterial=material;
        }
        static void Sphere(Transform parent,string name,Vector3 position,Vector3 size,Material material) {
            var obj=GameObject.CreatePrimitive(PrimitiveType.Sphere);obj.name=name;obj.transform.SetParent(parent,false);obj.transform.localPosition=position;obj.transform.localScale=size;
            obj.GetComponent<Renderer>().sharedMaterial=material;var collider=obj.GetComponent<Collider>();if(Application.isPlaying)Object.Destroy(collider);else Object.DestroyImmediate(collider);
        }
    }
}
