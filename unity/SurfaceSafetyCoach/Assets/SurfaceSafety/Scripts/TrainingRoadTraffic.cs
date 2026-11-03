using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace SurfaceSafety {
    [Serializable] public class RoadPoint {public float x,z,heading,distanceMetres;}
    [Serializable] public class AmbientRoadRoute {public string id;public RoadPoint[] points;public float lengthMetres,speedMetresPerSecond;}
    [Serializable] public class AmbientRoadVehicle {public string id,routeId,kind;public float offsetMetres;public int colourIndex;}
    [Serializable] public class AmbientRoadTraffic {public int version;public string provenance;public AmbientRoadRoute[] routes;public AmbientRoadVehicle[] vehicles;}

    // Ambient public-road cars have no flight identity, reports or selection UI.
    // Motion is sampled from the externally bounded/frozen replay clock only.
    public class TrainingRoadTraffic:MonoBehaviour {
        StandReplay replay;
        readonly List<Transform> cars=new List<Transform>();
        readonly List<Material> materials=new List<Material>();
        static bool Finite(float x)=>!float.IsNaN(x)&&!float.IsInfinity(x);
        public static void Validate(AmbientRoadTraffic data){
            if(data==null||data.version==0)return;
            if(data.version!=1||data.routes==null||data.routes.Length>8||data.vehicles==null||data.vehicles.Length>24)throw new ArgumentException("Unsupported ambient road traffic");
            if(data.routes.Select(r=>r?.id).Distinct().Count()!=data.routes.Length||data.vehicles.Select(v=>v?.id).Distinct().Count()!=data.vehicles.Length)throw new ArgumentException("Duplicate road identity");
            foreach(var r in data.routes){
                if(r==null||string.IsNullOrEmpty(r.id)||!Finite(r.lengthMetres)||r.lengthMetres<=0||!Finite(r.speedMetresPerSecond)||r.speedMetresPerSecond<=0||r.speedMetresPerSecond>12||r.points==null||r.points.Length<4||r.points.Length>5000)throw new ArgumentException("Invalid road route");
                for(int i=0;i<r.points.Length;i++){
                    var p=r.points[i];if(p==null||!Finite(p.x)||!Finite(p.z)||Mathf.Abs(p.x)>30||Mathf.Abs(p.z)>30||!Finite(p.heading)||!Finite(p.distanceMetres)||p.distanceMetres<0||(i==0&&p.distanceMetres!=0)||(i>0&&p.distanceMetres<=r.points[i-1].distanceMetres))throw new ArgumentException("Invalid road path");
                    if(i>0){var a=r.points[i-1];float length=Vector2.Distance(new Vector2(a.x,a.z),new Vector2(p.x,p.z))*1000;if(Mathf.Abs(length-(p.distanceMetres-a.distanceMetres))>.01f)throw new ArgumentException("Invalid road distance");}
                }
                var first=r.points[0];var last=r.points[r.points.Length-1];
                if(Mathf.Abs(last.distanceMetres-r.lengthMetres)>.01f||Mathf.Abs(last.x-first.x)+Mathf.Abs(last.z-first.z)>1e-6f||Mathf.Abs(Mathf.DeltaAngle(last.heading,first.heading))>.01f)throw new ArgumentException("Road loop must close continuously");
            }
            foreach(var v in data.vehicles)if(v==null||string.IsNullOrEmpty(v.id)||!data.routes.Any(r=>r.id==v.routeId)||!Finite(v.offsetMetres)||v.offsetMetres<0||(v.kind!="car"&&v.kind!="van"))throw new ArgumentException("Invalid road vehicle");
        }
        public static Vector3 Pose(AmbientRoadRoute route,AmbientRoadVehicle vehicle,float sourceTime,out float yaw){
            float d=Mathf.Repeat(vehicle.offsetMetres+Mathf.Max(0,sourceTime)*route.speedMetresPerSecond,route.lengthMetres);
            for(int i=1;i<route.points.Length;i++)if(d<=route.points[i].distanceMetres){
                var a=route.points[i-1];var b=route.points[i];float f=(d-a.distanceMetres)/(b.distanceMetres-a.distanceMetres);
                yaw=Mathf.LerpAngle(a.heading,b.heading,f);return new Vector3(Mathf.Lerp(a.x,b.x,f),.00035f,Mathf.Lerp(a.z,b.z,f));
            }
            throw new ArgumentException("Road pose outside loop");
        }
        Material Make(Color color,float gloss=.35f){var m=new Material(Shader.Find("Standard"));m.color=color;m.SetFloat("_Glossiness",gloss);materials.Add(m);return m;}
        public void Bind(StandReplay r){
            replay=r;Validate(r.Data.ambientTraffic);if(r.Data.ambientTraffic==null||r.Data.ambientTraffic.version==0)return;
            var paint=new[]{Make(new Color(.74f,.77f,.77f)),Make(new Color(.08f,.13f,.17f)),Make(new Color(.30f,.10f,.09f)),Make(new Color(.18f,.29f,.36f)),Make(new Color(.85f,.85f,.79f))};
            var glass=Make(new Color(.09f,.17f,.21f),.75f);var rubber=Make(new Color(.045f,.05f,.055f),.05f);var lamp=Make(new Color(.95f,.91f,.68f));var red=Make(new Color(.55f,.025f,.025f));
            foreach(var v in r.Data.ambientTraffic.vehicles){
                var car=new GameObject("Road vehicle "+v.id).transform;car.SetParent(transform,false);cars.Add(car);
                bool van=v.kind=="van";float length=van?5.2f:4.4f,width=van?2:1.8f;var colour=paint[Mathf.Abs(v.colourIndex)%paint.Length];
                Box(car,"Body",new Vector3(0,.66f,0),new Vector3(width,.58f,length),colour);
                Box(car,"Windows",new Vector3(0,van?1.3f:1.15f,-.12f),new Vector3(width*.88f,van?.70f:.52f,length*.56f),glass);
                if(van)Box(car,"Cargo body",new Vector3(0,1.36f,-.7f),new Vector3(width*.96f,1.12f,2.8f),colour);
                Box(car,"Roof",new Vector3(0,van?1.72f:1.44f,-.12f),new Vector3(width*.90f,.12f,length*.56f),colour);
                foreach(float side in new[]{-1f,1f})foreach(float end in new[]{-1f,1f}){
                    var wheel=GameObject.CreatePrimitive(PrimitiveType.Cylinder);wheel.name="Wheel";wheel.transform.SetParent(car,false);
                    wheel.transform.localPosition=new Vector3(side*width*.48f,.33f,end*length*.31f)*.001f;
                    wheel.transform.localRotation=Quaternion.Euler(0,0,90);wheel.transform.localScale=new Vector3(.64f,.12f,.64f)*.001f;wheel.GetComponent<Renderer>().sharedMaterial=rubber;Destroy(wheel.GetComponent<Collider>());
                }
                foreach(float side in new[]{-1f,1f}){
                    Box(car,"Headlight",new Vector3(side*width*.33f,.68f,length*.502f),new Vector3(.28f,.16f,.035f),lamp);
                    Box(car,"Rear light",new Vector3(side*width*.33f,.68f,-length*.502f),new Vector3(.20f,.16f,.035f),red);
                }
            }
            RenderAt(r.Clock.Time);
        }
        void Box(Transform parent,string name,Vector3 position,Vector3 scale,Material m){var go=GameObject.CreatePrimitive(PrimitiveType.Cube);go.name=name;go.transform.SetParent(parent,false);go.transform.localPosition=position*.001f;go.transform.localScale=scale*.001f;go.GetComponent<Renderer>().sharedMaterial=m;Destroy(go.GetComponent<Collider>());}
        void Update(){if(replay!=null)RenderAt(replay.Clock.Time);}
        public void RenderAt(float sourceTime){
            var data=replay.Data.ambientTraffic;if(data==null)return;
            for(int i=0;i<cars.Count;i++){var v=data.vehicles[i];var route=data.routes.First(r=>r.id==v.routeId);cars[i].localPosition=Pose(route,v,sourceTime,out var yaw);cars[i].localRotation=Quaternion.Euler(0,yaw,0);}
        }
        void OnDestroy(){foreach(var m in materials)Destroy(m);}
    }
}
