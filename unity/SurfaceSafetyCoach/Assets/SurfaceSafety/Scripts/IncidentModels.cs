using System.Collections.Generic;
using UnityEngine;

namespace SurfaceSafety {
    // Original lightweight meshes in metres; their roots convert to board units.
    // Poses are pure functions of source time, including after reconnect/rewind.
    public sealed class IncidentModels {
        readonly List<Object> owned=new List<Object>();
        readonly Material white,grey,dark,yellow,metal,rubber,orange,glass;
        readonly Material[] luggage;
        public IncidentModels(){
            white=Mat(new Color(.91f,.93f,.91f));grey=Mat(new Color(.55f,.60f,.63f));
            dark=Mat(new Color(.065f,.075f,.085f));yellow=Mat(new Color(.92f,.68f,.15f));
            metal=Mat(new Color(.60f,.65f,.67f),.4f);rubber=Mat(new Color(.035f,.04f,.045f));
            orange=Mat(new Color(1,.34f,.035f));glass=Mat(new Color(.08f,.18f,.24f),.7f);
            luggage=new[]{Mat(new Color(.13f,.23f,.33f)),Mat(new Color(.52f,.10f,.11f)),
                Mat(new Color(.23f,.31f,.23f)),Mat(new Color(.40f,.25f,.12f))};
        }
        Material Mat(Color c,float gloss=.15f){var m=new Material(Shader.Find("Standard"));m.color=c;m.SetFloat("_Glossiness",gloss);owned.Add(m);return m;}
        public void Dispose(){foreach(var asset in owned)Destroy(asset);owned.Clear();}
        static void Destroy(Object asset){if(Application.isPlaying)Object.Destroy(asset);else Object.DestroyImmediate(asset);}
        static Transform Node(Transform p,string name,Vector3 pos){var go=new GameObject(name);go.transform.SetParent(p,false);go.transform.localPosition=pos;return go.transform;}
        Transform Primitive(Transform p,string name,PrimitiveType type,Vector3 pos,Vector3 size,Material material){
            var go=GameObject.CreatePrimitive(type);go.name=name;go.transform.SetParent(p,false);
            go.transform.localPosition=pos;go.transform.localScale=size;go.GetComponent<Renderer>().sharedMaterial=material;
            Destroy(go.GetComponent<Collider>());return go.transform;
        }
        Transform Box(Transform p,string n,Vector3 v,Vector3 s,Material m)=>Primitive(p,n,PrimitiveType.Cube,v,s,m);
        void Feather(Transform p,string name,Vector3 from,Vector3 to,float width,Material material){
            var side=Vector3.Cross((to-from).normalized,Vector3.up)*width*.5f;
            var a=from-side;var b=from+side;var c=to+side*.22f;var d=to-side*.22f;
            var mesh=new Mesh{name=name};mesh.vertices=new[]{a,b,c,d,a,b,c,d};
            mesh.triangles=new[]{0,1,2,0,2,3,4,6,5,4,7,6};mesh.RecalculateNormals();mesh.RecalculateBounds();owned.Add(mesh);
            var go=new GameObject(name,typeof(MeshFilter),typeof(MeshRenderer));go.transform.SetParent(p,false);
            go.GetComponent<MeshFilter>().sharedMesh=mesh;go.GetComponent<Renderer>().sharedMaterial=material;
        }
        void Body(Transform parent){
            // One continuous tapered surface from tail to forehead.
            float[] z={-.32f,-.24f,-.12f,.02f,.14f,.23f,.30f,.36f,.39f};
            float[] rx={.008f,.055f,.085f,.095f,.075f,.045f,.058f,.047f,.012f};
            float[] ry={.012f,.052f,.078f,.092f,.073f,.055f,.061f,.045f,.018f};
            float[] cy={-.015f,-.005f,0,0,.015f,.035f,.06f,.06f,.045f};
            const int sides=24;var vertices=new Vector3[z.Length*(sides+1)];var underside=new List<int>();var back=new List<int>();
            for(int r=0;r<z.Length;r++)for(int j=0;j<=sides;j++){
                float a=j*Mathf.PI*2/sides;vertices[r*(sides+1)+j]=new Vector3(Mathf.Sin(a)*rx[r],cy[r]+Mathf.Cos(a)*ry[r],z[r]);
                if(r==z.Length-1||j==sides)continue;
                int k=r*(sides+1)+j;var target=r<4&&Mathf.Cos(a)>.4f?back:underside;
                target.AddRange(new[]{k,k+sides+1,k+1,k+1,k+sides+1,k+sides+2});
            }
            var mesh=new Mesh{name="Continuous bird body"};mesh.vertices=vertices;mesh.subMeshCount=2;
            mesh.SetTriangles(underside,0);mesh.SetTriangles(back,1);mesh.RecalculateNormals();mesh.RecalculateBounds();owned.Add(mesh);
            var go=new GameObject("Body",typeof(MeshFilter),typeof(MeshRenderer));go.transform.SetParent(parent,false);
            go.GetComponent<MeshFilter>().sharedMesh=mesh;go.GetComponent<Renderer>().sharedMaterials=new[]{white,grey};
            Node(parent,"Head",new Vector3(0,.06f,.30f));
        }
        void WingSurface(Transform parent,int side,bool outer){
            Vector3[] points=outer?new[]{new Vector3(0,0,.07f),new Vector3(.18f,.015f,.035f),new Vector3(.40f,0,-.10f),new Vector3(.32f,0,-.23f),new Vector3(.14f,0,-.28f),new Vector3(0,0,-.19f)}:
                new[]{new Vector3(0,0,.11f),new Vector3(.22f,.025f,.10f),new Vector3(.40f,.025f,-.01f),new Vector3(.39f,0,-.20f),new Vector3(.12f,0,-.22f),new Vector3(0,0,-.13f)};
            var vertices=new Vector3[points.Length*2];for(int i=0;i<points.Length;i++){points[i].x*=side;vertices[i]=vertices[i+points.Length]=points[i];}
            var triangles=new List<int>();for(int i=1;i<points.Length-1;i++)triangles.AddRange(new[]{0,i,i+1,points.Length,points.Length+i+1,points.Length+i});
            var mesh=new Mesh{name="Wing coverts"};mesh.vertices=vertices;mesh.triangles=triangles.ToArray();mesh.RecalculateNormals();mesh.RecalculateBounds();owned.Add(mesh);
            var go=new GameObject("Wing coverts",typeof(MeshFilter),typeof(MeshRenderer));go.transform.SetParent(parent,false);
            go.GetComponent<MeshFilter>().sharedMesh=mesh;go.GetComponent<Renderer>().sharedMaterial=grey;
        }
        public sealed class BirdRig {
            public Transform root;public readonly Transform[] shoulders=new Transform[2],wrists=new Transform[2];
            public void Pose(float age,int index,float duration){
                float phase=index*1.71f,leave=Mathf.Clamp01((age-duration+8)/8);
                root.localPosition=new Vector3((index%3-1)*.005f+Mathf.Sin(age*.7f+phase)*.003f,
                    .002f+(index/3)*.0007f+Mathf.Sin(age*.9f+phase)*.0004f+leave*leave*.018f,
                    -.035f+age*.0025f+(index/3-1)*.004f+leave*leave*.06f);
                float dx=Mathf.Cos(age*.7f+phase)*2.1f,dz=2.5f+leave*15;
                root.localRotation=Quaternion.Euler(-4-leave*10,Mathf.Atan2(dx,dz)*Mathf.Rad2Deg,Mathf.Sin(age*.7f+phase)*-12);
                float glide=Mathf.SmoothStep(0,1,Mathf.Clamp01((Mathf.Sin(age*.52f+phase)-.25f)*3));
                float flap=Mathf.Sin(age*(17.5f+index*.22f)+phase)*(1-glide);
                for(int w=0;w<2;w++){
                    float side=w==0?-1:1;
                    shoulders[w].localRotation=Quaternion.Euler(3,0,side*(8+32*flap));
                    wrists[w].localRotation=Quaternion.Euler(0,0,side*(-6+14*Mathf.Sin(age*(17.5f+index*.22f)+phase-.45f)*(1-glide)));
                }
            }
        }
        public BirdRig Bird(Transform parent,int index){
            var rig=new BirdRig{root=Node(parent,"Bird "+(index+1),Vector3.zero)};rig.root.localScale=Vector3.one*.001f;
            Body(rig.root);
            Primitive(rig.root,"Bill",PrimitiveType.Sphere,new Vector3(0,.041f,.405f),new Vector3(.028f,.027f,.11f),yellow);
            for(int side=-1;side<=1;side+=2){
                Primitive(rig.root,"Eye",PrimitiveType.Sphere,new Vector3(side*.052f,.076f,.321f),Vector3.one*.009f,dark);
                int w=side<0?0:1;rig.shoulders[w]=Node(rig.root,side<0?"Left wing":"Right wing",new Vector3(side*.07f,.045f,.02f));
                WingSurface(rig.shoulders[w],side,false);
                Feather(rig.shoulders[w],"Upper wing",new Vector3(0,0,.025f),new Vector3(side*.40f,.025f,-.045f),.26f,grey);
                for(int j=0;j<7;j++)Feather(rig.shoulders[w],"Secondary "+j,new Vector3(side*(.025f+j*.054f),0,-.015f),new Vector3(side*(.08f+j*.048f),-.015f,-.24f),.065f,white);
                rig.wrists[w]=Node(rig.shoulders[w],"Wrist",new Vector3(side*.37f,.02f,-.04f));
                WingSurface(rig.wrists[w],side,true);
                for(int j=0;j<8;j++){
                    var from=new Vector3(side*j*.018f,0,-j*.018f);var to=new Vector3(side*(.43f-j*.029f),-.015f,-.11f-j*.039f);
                    Feather(rig.wrists[w],"Primary feather "+j,from,to,.057f,j<5?dark:grey);
                    if(j<5)Feather(rig.wrists[w],"White primary base "+j,from,Vector3.Lerp(from,to,.59f),.058f,grey);
                }
            }
            for(int j=0;j<5;j++)Feather(rig.root,"Tail feather "+j,new Vector3((j-2)*.023f,-.025f,-.20f),new Vector3((j-2)*.042f,-.015f,-.44f),.058f,white);
            return rig;
        }
        public sealed class BaggageRig {
            public Transform root,train,gate;public Transform[] bags;public GameObject cones;
            public Vector3[] loaded,fallen;
            public void Pose(float t,TrainingIncident plan){
                float age=t-plan.start,spill=plan.onset-plan.start;
                float travel=age<spill?Mathf.Lerp(-9,0,Mathf.Clamp01(age/spill)):age>74?Mathf.Lerp(0,16,Mathf.Clamp01((age-74)/11)):0;
                train.localPosition=new Vector3(0,0,travel);
                gate.localRotation=Quaternion.Euler(-75*Mathf.Clamp01((age-spill)/.7f),0,0);
                cones.SetActive(t>=plan.onset+3&&age<72);
                for(int i=0;i<bags.Length;i++){
                    float u=Mathf.Clamp01((age-spill-i*.16f)/1.5f);
                    bags[i].gameObject.SetActive(t<plan.clearedAt-(bags.Length-1-i)*.4f);
                    var from=loaded[i]+new Vector3(0,0,Mathf.Min(0,travel));
                    bags[i].localPosition=Vector3.Lerp(from,fallen[i],u)+Vector3.up*(Mathf.Sin(u*Mathf.PI)*.65f);
                    bags[i].localRotation=Quaternion.Slerp(Quaternion.identity,Quaternion.Euler(90,(i*47)%180,0),u);
                }
            }
        }
        public BaggageRig Baggage(Transform parent){
            var rig=new BaggageRig{root=Node(parent,"Baggage recovery",Vector3.zero)};rig.root.localScale=Vector3.one*.001f;
            rig.train=Node(rig.root,"Tug and baggage cart",Vector3.zero);
            Box(rig.train,"Cart deck",new Vector3(0,.65f,0),new Vector3(2.15f,.18f,3.3f),metal);
            for(int side=-1;side<=1;side+=2){
                Box(rig.train,"Side wall",new Vector3(side*1.02f,1.15f,0),new Vector3(.07f,.9f,3.25f),metal);
                Box(rig.train,"Reflective side strip",new Vector3(side*1.065f,.92f,0),new Vector3(.012f,.12f,3.0f),yellow);
                for(int j=0;j<2;j++)Wheel(rig.train,new Vector3(side*1.05f,.34f,j==0?-1.1f:1.1f),.65f);
            }
            Box(rig.train,"Front rail",new Vector3(0,1.15f,1.6f),new Vector3(2.1f,.9f,.08f),metal);
            rig.gate=Node(rig.train,"Dropped rear gate",new Vector3(0,.65f,-1.62f));
            Box(rig.gate,"Gate",new Vector3(0,.45f,0),new Vector3(2.1f,.9f,.07f),metal);
            Box(rig.train,"Tow bar",new Vector3(0,.45f,2.35f),new Vector3(.16f,.13f,1.5f),dark);
            var tug=Node(rig.train,"Baggage tug",new Vector3(0,0,4.1f));
            Box(tug,"Chassis",new Vector3(0,.6f,0),new Vector3(1.75f,.65f,2.65f),yellow);
            Box(tug,"Cab",new Vector3(0,1.36f,.1f),new Vector3(1.5f,1.05f,1.4f),white);
            Box(tug,"Windshield",new Vector3(0,1.48f,.81f),new Vector3(1.30f,.62f,.025f),glass);
            for(int side=-1;side<=1;side+=2){
                Box(tug,"Side window",new Vector3(side*.756f,1.48f,.12f),new Vector3(.025f,.62f,1.08f),glass);
                for(int j=0;j<2;j++)Wheel(tug,new Vector3(side*.84f,.34f,j==0?-.92f:.92f),.68f);
            }
            Primitive(tug,"Amber beacon",PrimitiveType.Sphere,new Vector3(0,1.99f,.15f),new Vector3(.20f,.23f,.20f),orange);
            rig.bags=new Transform[9];rig.loaded=new Vector3[9];rig.fallen=new Vector3[9];
            for(int i=0;i<rig.bags.Length;i++){
                var bag=Node(rig.root,"Bag "+(i+1),Vector3.zero);rig.bags[i]=bag;
                Box(bag,"Case",Vector3.zero,new Vector3(.50f,.65f,.28f),luggage[i%luggage.Length]);
                Box(bag,"Case seam",new Vector3(0,0,.146f),new Vector3(.46f,.025f,.013f),dark);
                Box(bag,"Handle",new Vector3(0,.37f,0),new Vector3(.20f,.035f,.07f),dark);
                for(int j=-1;j<=1;j+=2)Box(bag,"Handle support",new Vector3(j*.08f,.335f,0),new Vector3(.025f,.07f,.07f),dark);
                rig.loaded[i]=new Vector3((i%3-1)*.62f,1.06f,(i/3-1)*.88f);
                rig.fallen[i]=new Vector3(Mathf.Sin(i*2.3f)*2.5f,.16f,-3.1f-(i/3)*1.05f-Mathf.Cos(i)*.3f);
            }
            rig.cones=Node(rig.root,"Recovery area cones",Vector3.zero).gameObject;
            for(int i=0;i<4;i++){
                var pos=new Vector3(i%2==0?-3.4f:3.4f,.03f,i<2?-6.3f:1.4f);
                Box(rig.cones.transform,"Cone base",pos,new Vector3(.55f,.06f,.55f),rubber);
                Primitive(rig.cones.transform,"Cone marker",PrimitiveType.Cylinder,pos+Vector3.up*.36f,new Vector3(.22f,.34f,.22f),orange);
                Primitive(rig.cones.transform,"Reflective band",PrimitiveType.Cylinder,pos+Vector3.up*.48f,new Vector3(.23f,.065f,.23f),white);
            }
            return rig;
        }
        public sealed class ResponseRig {
            public Transform root,vehicle;public GameObject markers;public bool runway;
            public void Pose(float t,TrainingIncident plan){
                float age=t-plan.onset;
                if(runway){
                    vehicle.gameObject.SetActive(age>=38);
                    vehicle.localPosition=new Vector3(Mathf.Lerp(-95,-55,Mathf.Clamp01((age-38)/15)),0,-15);
                    vehicle.localRotation=Quaternion.Euler(0,90,0);
                    markers.SetActive(age>=6);
                }else{
                    float travel=age<0?Mathf.Lerp(-42,0,Mathf.Clamp01((t-plan.start)/(plan.onset-plan.start))):0;
                    vehicle.localPosition=new Vector3(0,0,travel);
                    vehicle.localRotation=Quaternion.Euler(0,age<0?0:8*Mathf.Clamp01(age/.8f),0);
                    markers.SetActive(age>=5);
                }
            }
        }
        public ResponseRig Response(Transform parent,bool runway){
            var rig=new ResponseRig{root=Node(parent,runway?"Runway response":"Ground vehicle contact",Vector3.zero),runway=runway};
            rig.root.localScale=Vector3.one*.001f;
            rig.vehicle=Node(rig.root,runway?"Airport response vehicle":"Service vehicle",Vector3.zero);
            var color=runway?luggage[1]:yellow;
            Box(rig.vehicle,"Chassis",new Vector3(0,.95f,0),new Vector3(2.6f,1.0f,5.5f),color);
            Box(rig.vehicle,"Cab",new Vector3(0,2.35f,1.65f),new Vector3(2.4f,2.2f,2.1f),white);
            Box(rig.vehicle,"Windscreen",new Vector3(0,2.7f,2.71f),new Vector3(2.1f,.85f,.04f),glass);
            Box(rig.vehicle,"Equipment body",new Vector3(0,2.0f,-.9f),new Vector3(2.5f,1.75f,2.9f),color);
            for(int side=-1;side<=1;side+=2){
                Box(rig.vehicle,"Reflective strip",new Vector3(side*1.265f,1.75f,-.9f),new Vector3(.03f,.18f,2.8f),white);
                Box(rig.vehicle,"Cab side window",new Vector3(side*1.21f,2.7f,1.65f),new Vector3(.03f,.85f,1.6f),glass);
                for(int j=0;j<2;j++)Wheel(rig.vehicle,new Vector3(side*1.28f,.52f,j==0?-1.8f:1.8f),1.03f);
                Primitive(rig.vehicle,"Beacon",PrimitiveType.Sphere,new Vector3(side*.8f,3.53f,1.6f),new Vector3(.25f,.25f,.25f),orange);
            }
            rig.markers=Node(rig.root,runway?"Closed runway markers":"Contact area markers",Vector3.zero).gameObject;
            if(runway){
                for(int end=0;end<2;end++)for(int side=-1;side<=1;side+=2){
                    var marker=Box(rig.markers.transform,"Runway closed X",new Vector3(end==0?-95:55,.18f,0),new Vector3(12,.18f,1.1f),yellow);
                    marker.localRotation=Quaternion.Euler(0,side*45,0);
                }
            }else for(int i=0;i<4;i++){
                var pos=new Vector3(i%2==0?-5:5,.06f,i<2?-5:4);
                Box(rig.markers.transform,"Cone base",pos,new Vector3(.6f,.1f,.6f),rubber);
                Primitive(rig.markers.transform,"Response marker",PrimitiveType.Cylinder,pos+Vector3.up*.4f,new Vector3(.24f,.38f,.24f),orange);
            }
            return rig;
        }
        void Wheel(Transform p,Vector3 pos,float diameter){
            var wheel=Primitive(p,"Tyre",PrimitiveType.Cylinder,pos,new Vector3(diameter,.13f,diameter),rubber);wheel.localRotation=Quaternion.Euler(0,0,90);
            var hub=Primitive(p,"Hub",PrimitiveType.Cylinder,pos,new Vector3(diameter*.46f,.14f,diameter*.46f),metal);hub.localRotation=Quaternion.Euler(0,0,90);
        }
    }
}
