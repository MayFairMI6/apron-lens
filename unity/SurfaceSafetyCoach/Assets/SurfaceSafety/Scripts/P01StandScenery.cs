// PROCEDURAL: authored presentation geometry for the P01 lesson; never report evidence.
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace SurfaceSafety {
    /// <summary>Uses the existing fictional apron's metre positions, converted to board units.</summary>
    public sealed class P01StandScenery : MonoBehaviour {
        readonly List<Material> materials=new List<Material>();
        readonly List<Renderer> replaced=new List<Renderer>();
        public static bool Applies(Scenario data)=>data!=null&&data.trainingProfile=="stand_clearance";
        public static P01StandScenery Build(Transform parent,GameObject apron,TaxiPath[] paths){
            var root=new GameObject("P01 Stand B boundary and exit lane");root.transform.SetParent(parent,false);
            var scene=root.AddComponent<P01StandScenery>();scene.BuildMarkings(apron);scene.BuildInboundPaint(paths);return scene;
        }
        Material Paint(string name,Color color){
            var m=new Material(Shader.Find("Standard")){name=name,color=color};m.SetFloat("_Glossiness",.15f);materials.Add(m);return m;
        }
        GameObject Shape(Transform parent,string name,PrimitiveType type,Vector3 position,Vector3 size,Material material){
            var go=GameObject.CreatePrimitive(type);go.name=name;go.transform.SetParent(parent,false);
            go.transform.localPosition=position;go.transform.localScale=size;
            go.GetComponent<Renderer>().sharedMaterial=material;Release(go.GetComponent<Collider>());return go;
        }
        void Mark(string name,float x,float z,float width,float length,Material material){
            var go=Shape(transform,name,PrimitiveType.Cube,new Vector3(x,.065f,z)*.001f,new Vector3(width,.012f,length)*.001f,material);
            go.GetComponent<Renderer>().shadowCastingMode=ShadowCastingMode.Off;
        }
        void BuildMarkings(GameObject apron){
            // CustomHeathrowEnvironment: B centre x=35 m; clearance sides x=12/58,
            // z=7..57. Retain this footprint; close its two open ends for P01.
            // Hide only the replaced source paint, and restore it when leaving P01.
            if(apron!=null)foreach(var r in apron.GetComponentsInChildren<Renderer>(true)){
                var p=apron.transform.InverseTransformPoint(r.transform.position);
                if(r.name=="Equipment clearance"&&(Mathf.Abs(p.x-12)<.1f||Mathf.Abs(p.x-58)<.1f)&&r.enabled){replaced.Add(r);r.enabled=false;}
            }
            var yellow=Paint("P01 stand paint",new Color(.82f,.61f,.13f));
            foreach(float x in new[]{12f,58f})Mark("Stand B side boundary",x,32,.25f,50,yellow);
            foreach(float z in new[]{7f,57f})Mark("Stand B end boundary",35,z,46,.25f,yellow);
            // The existing service road is z=63..71 m, north of the stand. The
            // 6 m wide authored connector is inside the apron, clear of bridge B.
            var white=Paint("P01 lane paint",new Color(.79f,.80f,.78f));
            foreach(float x in new[]{42f,48f})Mark("Stand B service exit edge",x,62,.14f,10,white);
            // Authored parking bay between B/C, beyond B's footprint and clear
            // of the original equipment at x=66 and the light mast at x=85.
            foreach(float x in new[]{73f,79f})Mark("Service vehicle parking side",x,56,.14f,14,white);
            Mark("Service vehicle parking end",76,49,6,.14f,white);
        }
        void BuildInboundPaint(TaxiPath[] paths){
            if(paths==null)return;
            var yellow=Paint("P01 inbound route paint",new Color(.82f,.61f,.13f));
            foreach(var path in paths)for(int i=1;i<(path.points?.Length??0);i++){
                var a=new Vector3(path.points[i-1].x,.000065f,path.points[i-1].z);
                var b=new Vector3(path.points[i].x,.000065f,path.points[i].z);
                // Existing source paint already covers the main taxi lane and
                // straight B lead-in; add only the staging branch and turns.
                if(Mathf.Abs(a.z+.025f)<1e-6f&&Mathf.Abs(b.z+.025f)<1e-6f)continue;
                if(Mathf.Abs(a.x-.035f)<1e-6f&&Mathf.Abs(b.x-.035f)<1e-6f)continue;
                var d=b-a;if(d.sqrMagnitude<1e-12f)continue;
                var go=Shape(transform,"P01 inbound route centreline",PrimitiveType.Cube,(a+b)*.5f,new Vector3(.00023f,.000012f,d.magnitude),yellow);
                go.transform.localRotation=Quaternion.LookRotation(d);
                go.GetComponent<Renderer>().shadowCastingMode=ShadowCastingMode.Off;
            }
        }
        public GameObject BuildVehicle(string id,Transform parent){
            var root=new GameObject(id);root.transform.SetParent(parent,false);
            var body=Paint("P01 tanker body",new Color(.76f,.78f,.76f));
            var metal=Paint("P01 tanker frame",new Color(.24f,.27f,.28f));
            var rubber=Paint("P01 tanker tyres",new Color(.035f,.04f,.045f));
            var glass=Paint("P01 tanker glass",new Color(.09f,.17f,.21f));
            var amber=Paint("P01 tanker beacon",new Color(1,.48f,.06f));
            // Reuse StandReplay.BuildProps' cab/tank dimensions and relative
            // spacing, detached from aircraft. The source prop and hose stay
            // untouched. Centre the 11.2 m body longitudinally about the route.
            var tank=Shape(root.transform,"Fuel tanker tank",PrimitiveType.Cylinder,new Vector3(0,.00225f,-.0016f),new Vector3(.0034f,.004f,.0034f),body);
            tank.transform.localRotation=Quaternion.Euler(90,0,0);
            Shape(root.transform,"Fuel tanker cab",PrimitiveType.Cube,new Vector3(0,.00205f,.0042f),new Vector3(.0034f,.003f,.0028f),body);
            Shape(root.transform,"Tanker chassis",PrimitiveType.Cube,new Vector3(0,.00085f,0),new Vector3(.0032f,.0005f,.0108f),metal);
            Shape(root.transform,"Front windshield",PrimitiveType.Cube,new Vector3(0,.0027f,.00561f),new Vector3(.0028f,.00105f,.000035f),glass);
            foreach(float x in new[]{-.00171f,.00171f})Shape(root.transform,"Cab side window",PrimitiveType.Cube,new Vector3(x,.0027f,.0043f),new Vector3(.000035f,.00105f,.0017f),glass);
            foreach(float x in new[]{-.00165f,.00165f})foreach(float z in new[]{-.0041f,-.0026f,.0042f}){
                var wheel=Shape(root.transform,"Tanker wheel",PrimitiveType.Cylinder,new Vector3(x,.00058f,z),new Vector3(.00116f,.00022f,.00116f),rubber);
                wheel.transform.localRotation=Quaternion.Euler(0,0,90);
            }
            foreach(float x in new[]{-.0011f,.0011f})Shape(root.transform,"Amber beacon",PrimitiveType.Cylinder,new Vector3(x,.00365f,.0042f),new Vector3(.00022f,.00012f,.00022f),amber);
            return root;
        }
        public void RestoreSourcePaint(){foreach(var r in replaced)if(r!=null)r.enabled=true;replaced.Clear();}
        void OnDestroy(){RestoreSourcePaint();foreach(var m in materials)if(m!=null)Release(m);}
        static void Release(Object obj){if(Application.isPlaying)Destroy(obj);else DestroyImmediate(obj);}
    }
}
