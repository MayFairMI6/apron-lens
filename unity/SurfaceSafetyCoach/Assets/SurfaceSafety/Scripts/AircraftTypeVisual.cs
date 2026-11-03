using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace SurfaceSafety {
    // Published reference envelope and gear stations. Exterior: attributed AMV Lab
    // family assets, normalized to reference size; not exact variant CAD.
    public sealed class AircraftTypeProfile {
        public readonly string Id;
        public readonly float LengthMetres, WingspanMetres, HeightMetres, FuselageWidthMetres;
        public readonly float NoseAheadOfMainGearMetres, NoseGearAheadMetres, MainGearTrackMetres;
        public float TailBehindMainGearMetres => LengthMetres-NoseAheadOfMainGearMetres;
        public readonly int EngineCount, MainWheelCount;
        internal readonly float BodyCentre, BodyHeight, WingLead, WingTrail, TipLead, TipChord;
        internal AircraftTypeProfile(string id,float length,float span,float height,float width,float front,float noseGear,float track,
            int engines,int wheels,float centre,float bodyHeight,float lead,float trail,float tip,float chord) {
            Id=id;LengthMetres=length;WingspanMetres=span;HeightMetres=height;FuselageWidthMetres=width;
            NoseAheadOfMainGearMetres=front;NoseGearAheadMetres=noseGear;MainGearTrackMetres=track;
            EngineCount=engines;MainWheelCount=wheels;BodyCentre=centre;BodyHeight=bodyHeight;
            WingLead=lead;WingTrail=trail;TipLead=tip;TipChord=chord;
        }
    }

    public static class AircraftTypeVisual {
        // A320ceo Sharklets; Boeing 737NG/787 airport planning drawings; Airbus
        // A380 AC Dec2025. Parked heights depend on load; A380 uses the published
        // 24.12 m reference configuration, not a claim about every loading state.
        static readonly AircraftTypeProfile[] profiles={
            new AircraftTypeProfile("a320_200",37.57f,35.80f,11.76f,3.95f,17.71f,12.64f,7.59f,2,4,3.85f,4.14f,4.2f,-5.8f,-5.5f,1.4f),
            new AircraftTypeProfile("b737_800",39.47f,35.79f,12.55f,3.76f,19.69f,15.60f,5.72f,2,4,3.30f,3.94f,3.2f,-6.8f,-6.8f,1.35f),
            new AircraftTypeProfile("b787_8",56.72f,60.12f,16.92f,5.77f,28.19f,22.78f,9.80f,2,8,5.20f,5.94f,7.5f,-10.4f,-10.8f,2.1f),
            // A380 root is its body-gear bogie centre, 36.85 m aft of the nose.
            new AircraftTypeProfile("a380_800",72.73f,79.75f,24.12f,7.14f,36.85f,31.88f,5.26f,4,20,8.60f,8.40f,10f,-14f,-13.4f,3.3f),
        };
        public static IEnumerable<AircraftTypeProfile> Profiles => profiles;
        public static AircraftTypeProfile Find(string id) => profiles.FirstOrDefault(p=>p.Id==id);
        public static void Validate(AircraftPlan plan) {
            if(string.IsNullOrEmpty(plan.aircraftType))return;
            if(Find(plan.aircraftType)==null)throw new ArgumentException("Unknown aircraft visual type.");
            if(float.IsNaN(plan.surfaceHeightMetres)||float.IsInfinity(plan.surfaceHeightMetres)||plan.surfaceHeightMetres<0||plan.surfaceHeightMetres>3)
                throw new ArgumentException("Invalid aircraft surface height.");
        }
        public static AircraftTypeRig Build(Transform parent,Color livery,string type) {
            var p=Find(type);if(p==null)throw new ArgumentException("Unknown aircraft visual type.");
            var root=new GameObject("Aircraft type "+type).transform;root.SetParent(parent,false);root.localScale=Vector3.one*.001f;
            var rig=root.gameObject.AddComponent<AircraftTypeRig>();
            var rubber=AircraftVisual.Material(new Color(.025f,.029f,.032f),0,.15f);
            var metal=AircraftVisual.Material(new Color(.36f,.40f,.42f),.65f,.48f);
            bool jumbo=type=="a380_800",dream=type=="b787_8";
            float wingY=p.BodyCentre-p.BodyHeight*.30f;
            BuildExterior(root,type);
            var gear=new GameObject("Deployed landing gear").transform;gear.SetParent(root,false);
            float wheelRadius=jumbo?.70f:dream?.63f:.57f;
            var wheelRoots=new List<Transform>();
            for(int side=-1;side<=1;side+=2){
                if(jumbo){
                    GearLeg(gear,side*6.23f,3.27f,2,1.0f,wheelRadius,.47f,wingY,metal,rubber,wheelRoots,"Wing main");
                    GearLeg(gear,side*2.63f,0,3,1.1f,wheelRadius,.47f,wingY,metal,rubber,wheelRoots,"Body main");
                }else GearLeg(gear,side*p.MainGearTrackMetres*.5f,0,dream?2:1,.82f,wheelRadius,.48f,wingY,metal,rubber,wheelRoots,"Main");
            }
            GearLeg(gear,0,p.NoseGearAheadMetres,1,0,jumbo?.52f:dream?.47f:.39f,jumbo?.32f:.25f,p.BodyCentre-p.BodyHeight*.45f,metal,rubber,wheelRoots,"Nose");
            rig.Initialize(p,gear,wheelRoots.ToArray());return rig;
        }
        [Serializable] sealed class BakedExterior {
            public int version;public string type;
            public Vector3[] vertices,normals;public Vector2[] uv;public int[] triangles;
        }
        static void BuildExterior(Transform parent,string type){
            var source=Resources.Load<TextAsset>("Aircraft/"+type);
            if(source==null)throw new InvalidOperationException("Missing aircraft exterior: "+type);
            var baked=JsonUtility.FromJson<BakedExterior>(source.text);
            if(baked.version!=1||baked.type!=type||baked.vertices==null||baked.normals.Length!=baked.vertices.Length||baked.uv.Length!=baked.vertices.Length)
                throw new InvalidOperationException("Invalid aircraft exterior: "+type);
            var mesh=new Mesh{name=type+" AMV Lab exterior"};mesh.vertices=baked.vertices;mesh.normals=baked.normals;mesh.uv=baked.uv;mesh.triangles=baked.triangles;mesh.RecalculateBounds();
            var material=AircraftVisual.Material(Color.white,.15f,.30f);
            material.mainTexture=Resources.Load<Texture2D>("Aircraft/"+type+"_texture");
            if(material.mainTexture==null)throw new InvalidOperationException("Missing aircraft texture: "+type);
            var model=new GameObject("AMV Lab exterior",typeof(MeshFilter),typeof(MeshRenderer));model.transform.SetParent(parent,false);
            model.GetComponent<MeshFilter>().sharedMesh=mesh;model.GetComponent<MeshRenderer>().sharedMaterial=material;
        }
        static void GearLeg(Transform parent,float x,float z,int axles,float axleStep,float radius,float pairOffset,float strutTop,Material metal,Material rubber,List<Transform> wheels,string label){
            AircraftVisual.Prism(parent,label+" gear strut",new[]{new Vector3(x-.10f,radius,z-.12f),new Vector3(x-.10f,strutTop,z-.12f),new Vector3(x+.10f,strutTop,z+.12f),new Vector3(x+.10f,radius,z+.12f)},Vector3.forward*.15f,metal);
            for(int axle=0;axle<axles;axle++)for(int side=-1;side<=1;side+=2){
                var wheel=new GameObject(label+" wheel").transform;wheel.SetParent(parent,false);
                wheel.localPosition=new Vector3(x+side*pairOffset,radius,z+(axle-(axles-1)*.5f)*axleStep);wheel.localRotation=Quaternion.Euler(0,90,0);
                float width=label=="Nose"?.28f:.40f;
                AircraftVisual.Loft(wheel,"Tyre tread",Vector3.zero,new[]{-width*.5f,width*.5f},new[]{radius,radius},new float[2],1,rubber,24);
                AircraftVisual.Disk(wheel,"Wheel hub",Vector3.forward*(width*.505f),radius*.53f,metal,20);
                AircraftVisual.Disk(wheel,"Wheel hub",Vector3.back*(width*.505f),radius*.53f,metal,20,true);
                wheels.Add(wheel);
            }
        }
    }

    // Source-time poses only. The cached extended tyre envelope defines height
    // even while gear is hidden, so retraction cannot move the aircraft root.
    public sealed class AircraftTypeRig : MonoBehaviour {
        public AircraftTypeProfile Profile {get;private set;}
        public Transform Gear {get;private set;}
        public Transform[] Wheels {get;private set;}
        public Vector3[] TyreContactVertices {get;private set;}
        Mesh[] ownedMeshes;Material[] ownedMaterials;
        internal void Initialize(AircraftTypeProfile profile,Transform gear,Transform[] wheels){
            Profile=profile;Gear=gear;Wheels=wheels;
            TyreContactVertices=wheels.SelectMany(w=>w.GetComponentsInChildren<MeshFilter>().Where(f=>f.name=="Tyre tread").SelectMany(f=>f.sharedMesh.vertices.Select(v=>transform.InverseTransformPoint(f.transform.TransformPoint(v))))).ToArray();
            ownedMeshes=GetComponentsInChildren<MeshFilter>(true).Select(f=>f.sharedMesh).Distinct().ToArray();
            ownedMaterials=GetComponentsInChildren<Renderer>(true).SelectMany(r=>r.sharedMaterials).Distinct().ToArray();
        }
        public float ContactOffsetMetres(Quaternion attitude){
            float lowest=float.PositiveInfinity;
            foreach(var point in TyreContactVertices)lowest=Mathf.Min(lowest,(attitude*point).y);
            return -lowest;
        }
        public void SetGear(bool retracted){Gear.gameObject.SetActive(!retracted);}
        void OnDestroy(){
            foreach(var mesh in ownedMeshes??new Mesh[0])Release(mesh);
            foreach(var material in ownedMaterials??new Material[0])Release(material);
        }
        static void Release(UnityEngine.Object item){if(item==null)return;if(Application.isPlaying)Destroy(item);else DestroyImmediate(item);}
    }
}
