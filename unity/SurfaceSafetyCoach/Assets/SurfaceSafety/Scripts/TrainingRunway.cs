using UnityEngine;

namespace SurfaceSafety {
    // Original lightweight training geometry, separate from the apron taxi lane.
    public static class TrainingRunway {
        public static GameObject Build(Transform parent,RunwayPlan plan,TaxiPath[] paths=null){
            if(plan==null)return null;
            var root=new GameObject("Training runway "+plan.id);root.transform.SetParent(parent,false);
            var asphalt=new Color(.13f,.16f,.18f);var white=new Color(.94f,.94f,.87f);var yellow=new Color(.96f,.72f,.12f);
            Box(root.transform,"Surrounding terrain",new Vector3(0,-.003f,-1),new Vector3(12,.002f,10),new Color(.30f,.39f,.27f));
            Box(root.transform,"Runway pavement",new Vector3(plan.x,0,plan.z),new Vector3(plan.length,.0003f,plan.width),asphalt);
            for(int side=-1;side<=1;side+=2){
                Box(root.transform,"Runway edge",new Vector3(plan.x,.00025f,plan.z+side*(plan.width/2-.001f)),new Vector3(plan.length,.0001f,.001f),white);
                for(float x=-.86f;x<=.86f;x+=.06f)Box(root.transform,"Runway edge light",new Vector3(x,.0009f,plan.z+side*.024f),new Vector3(.0008f,.001f,.0008f),white);
                for(int bar=-4;bar<=4;bar++)if(bar!=0)
                    Box(root.transform,"Threshold bars",new Vector3(side*.79f,.0003f,plan.z+bar*.004f),new Vector3(.032f,.0001f,.002f),white);
            }
            for(float x=-.66f;x<=.66f;x+=.06f)Box(root.transform,"Runway centreline",new Vector3(x,.0003f,plan.z),new Vector3(.027f,.0001f,.0012f),white);
            Mark(root.transform,"09",new Vector3(-.73f,.0004f,plan.z),white);
            Mark(root.transform,"27",new Vector3(.73f,.0004f,plan.z),white);
            if(paths!=null)foreach(var path in paths){
                Ribbon(root.transform,"Taxiway "+path.id,path,path.width,.00012f,asphalt);
                Ribbon(root.transform,"Centreline "+path.id,path,.0007f,.00044f,yellow);
            }
            for(int i=0;i<4;i++)Box(root.transform,"Hold-short marking",new Vector3(-.8f,.0005f,-.365f-i*.0015f),new Vector3(.023f,.0001f,.0006f),yellow);
            return root;
        }
        static void Ribbon(Transform parent,string name,TaxiPath path,float width,float height,Color color){
            if(path.points==null||path.points.Length<2)return;
            var n=path.points.Length;var vertices=new Vector3[n*2];var indices=new int[(n-1)*6];
            for(int i=0;i<n;i++){
                var before=path.points[Mathf.Max(0,i-1)];var after=path.points[Mathf.Min(n-1,i+1)];
                var d=new Vector3(after.x-before.x,0,after.z-before.z).normalized;
                var normal=new Vector3(-d.z,0,d.x)*width*.5f;var p=path.points[i];
                vertices[i*2]=new Vector3(p.x,height,p.z)+normal;vertices[i*2+1]=new Vector3(p.x,height,p.z)-normal;
                if(i<n-1){int j=i*6,k=i*2;indices[j]=k;indices[j+1]=k+2;indices[j+2]=k+1;indices[j+3]=k+1;indices[j+4]=k+2;indices[j+5]=k+3;}
            }
            var go=new GameObject(name,typeof(MeshFilter),typeof(MeshRenderer));go.transform.SetParent(parent,false);
            var mesh=new Mesh{name=name};mesh.vertices=vertices;mesh.triangles=indices;mesh.RecalculateNormals();mesh.RecalculateBounds();go.GetComponent<MeshFilter>().sharedMesh=mesh;
            var mat=new Material(Shader.Find("Standard"));mat.color=color;mat.SetFloat("_Glossiness",.12f);go.GetComponent<MeshRenderer>().sharedMaterial=mat;
        }
        static GameObject Box(Transform parent,string name,Vector3 position,Vector3 scale,Color color){
            var go=GameObject.CreatePrimitive(PrimitiveType.Cube);go.name=name;go.transform.SetParent(parent,false);
            go.transform.localPosition=position;go.transform.localScale=scale;
            var mat=new Material(Shader.Find("Standard"));mat.color=color;mat.SetFloat("_Glossiness",.12f);
            go.GetComponent<Renderer>().sharedMaterial=mat;
            if(Application.isPlaying)Object.Destroy(go.GetComponent<Collider>());else Object.DestroyImmediate(go.GetComponent<Collider>());return go;
        }
        static void Mark(Transform parent,string value,Vector3 position,Color color){
            var go=new GameObject("Runway "+value);go.transform.SetParent(parent,false);go.transform.localPosition=position;
            go.transform.localRotation=Quaternion.Euler(90,0,0);var text=go.AddComponent<TextMesh>();
            text.font=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");go.GetComponent<MeshRenderer>().sharedMaterial=text.font.material;
            text.text=value;text.fontSize=64;text.characterSize=.002f;text.anchor=TextAnchor.MiddleCenter;text.color=color;
        }
    }
}
