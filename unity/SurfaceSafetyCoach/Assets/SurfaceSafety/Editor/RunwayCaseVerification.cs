using System;
using System.IO;
using System.Linq;
using UnityEngine;
using SurfaceSafety;

public static class RunwayCaseVerification {
    public static void Run(){
        var folder=Environment.GetEnvironmentVariable("APRONLENS_RUNWAY_FIXTURES");if(string.IsNullOrEmpty(folder))throw new Exception("Runway fixtures required");
        int n=0;Action<bool,string> check=(ok,label)=>{if(!ok)throw new Exception("Runway case: "+label);n++;};
        foreach(var name in new[]{"rejected_takeoff","occupied_runway_go_around","runway_incursion","water_landing"}){
            var json=File.ReadAllText(Path.Combine(folder,name+".json"));var data=JsonUtility.FromJson<Scenario>(json);data.Validate();
            check(TrainingGeography.Present(data.geography),name+" regional data");
            var water=data.geography.features.Single(f=>f.id=="osm-way-147855503");
            var triangles=TrainingGeography.Triangulate(water.points);
            check(triangles.Length==(water.points.Length-3)*3,"complete concave water triangulation");
            check(data.aircraft.All(a=>a.waypoints.Last().t==3600),name+" complete hour");
            var root=new GameObject("Runway case verification");var replay=root.AddComponent<StandReplay>();replay.InitializeFromJson(true,json);
            replay.UseWorldScale(WorldArBootstrap.MetresPerBoardUnit);replay.UseTrainingPresentation();replay.ApplyScene();
            foreach(var aircraft in data.aircraft){
                bool expectedVisible=aircraft.id=="A1"||(name=="occupied_runway_go_around"&&aircraft.id=="A2");
                var visual=replay.Content.Find(aircraft.id);
                bool visible=visual!=null&&visual.gameObject.activeInHierarchy&&visual.GetComponentsInChildren<Renderer>().Any(r=>r.enabled&&r.gameObject.activeInHierarchy);
                check(aircraft.hidden!=expectedVisible&&visible==expectedVisible,name+" "+aircraft.id+" participant visibility");
            }
            var map=new GameObject("Map");map.transform.SetParent(replay.Content,false);var renderer=map.AddComponent<TrainingGeography>();renderer.Bind(replay);
            var road=map.AddComponent<TrainingRoadTraffic>();road.Bind(replay);
            check(map.GetComponentsInChildren<Transform>().Count(t=>t.name.StartsWith("Road vehicle "))==6,"six ambient road vehicles");
            road.RenderAt(20);var car=map.GetComponentsInChildren<Transform>().First(t=>t.name.StartsWith("Road vehicle "));var before=car.localPosition;
            road.RenderAt(20);check(car.localPosition==before,"paused source clock holds road position");road.RenderAt(21);check((car.localPosition-before).magnitude>0,"source clock moves road traffic");
            if(name=="rejected_takeoff"){
                var t3=map.GetComponentInChildren<TerminalThree>();check(t3!=null,"Terminal 3 hybrid resource builds");
                var detail=t3.GetComponentsInChildren<MeshFilter>().Where(m=>m.name.StartsWith("Source ",StringComparison.Ordinal)).ToArray();
                check(detail.Length==4&&detail.Sum(m=>m.sharedMesh.triangles.Length)==3936,"original detailed pier surfaces retained");
                check(detail.Any(m=>m.GetComponent<Renderer>().sharedMaterial.mainTexture!=null),"original terminal texture present");
                check(map.GetComponentsInChildren<MeshFilter>().Count(m=>m.name=="Mapped apron pavement"||m.name=="Cargo Apron pavement")==34,"all sourced apron surfaces present");
                check(map.GetComponentInChildren<TerminalTwo>()!=null,"Terminal 2 mapped hall builds");
                check(map.GetComponentsInChildren<MeshFilter>().Any(m=>m.name=="Road centreline junctions"),"road junction paving present");
                Capture(replay.Content,new Vector3(480,8,40),1250,Path.Combine(folder,"connected-terminals-check.png"),225,40);
                Capture(replay.Content,new Vector3(720,12,-20),650,Path.Combine(folder,"terminal2-check.png"),180,32);
                Capture(replay.Content,new Vector3(410,1,193),95,Path.Combine(folder,"road-vehicles-check.png"),225,42);
                Capture(replay.Content,new Vector3(264,8,43),800,Path.Combine(folder,"terminal3-check.png"),225,32);
                Capture(replay.Content,new Vector3(264,8.5f,43),100,Path.Combine(folder,"terminal3-canopy-check.png"),225,18);
            }
            check(map.GetComponentsInChildren<MeshFilter>().Length>400,"all mapped paths rendered");
            var walls=map.GetComponentsInChildren<MeshFilter>().Where(f=>f.sharedMesh!=null&&f.sharedMesh.name.StartsWith("Regional ",StringComparison.Ordinal)&&f.name.EndsWith(" walls",StringComparison.Ordinal)).ToArray();
            check(walls.Length>0&&walls.All(f=>f.sharedMesh.normals.Length==f.sharedMesh.vertexCount&&f.sharedMesh.normals.All(v=>v.sqrMagnitude>.99f&&v.sqrMagnitude<1.01f&&Mathf.Abs(v.y)<.00001f)),name+" regional walls retain nonzero horizontal lighting normals");
            if(name=="water_landing"){
                var incident=data.incidents.Single();
                var aircraft=data.aircraft.Single(a=>a.id==incident.aircraftId);
                var fuselage=replay.Content.Find(aircraft.id).GetComponentsInChildren<MeshFilter>(true).Single(f=>f.name=="Tapered fuselage");
                var surface=map.GetComponentsInChildren<MeshFilter>().Single(f=>f.name==water.name);
                float waterY=LowestWorldVertex(surface),metre=replay.Content.lossyScale.y*.001f;
                // Check rendered vertices, including the model's offset and pitch,
                // rather than assuming that a zero trajectory altitude means contact.
                replay.Clock.Seek(incident.start);replay.ApplyScene();
                check(Mathf.Abs(LowestWorldVertex(fuselage)-waterY)<=.15f*metre,"fuselage reaches water at contact");
                replay.Clock.Seek(aircraft.phases.Single(p=>p.id=="afloat").t);replay.ApplyScene();
                float stoppedGap=LowestWorldVertex(fuselage)-waterY;
                check(stoppedGap<=.1f*metre&&stoppedGap>=-.6f*metre,"stopped fuselage has no water gap or excessive immersion");
                renderer.RenderAt(incident.start-1);check(!map.GetComponentsInChildren<Transform>().Any(t=>t.name=="Water spray"),"no spray before contact");
                renderer.RenderAt(incident.start+5);check(map.GetComponentsInChildren<Transform>().Count(t=>t.name=="Water spray")==64,"water spray at contact");
                var first=map.GetComponentsInChildren<Transform>().First(t=>t.name=="Water spray").localPosition;
                renderer.RenderAt(incident.start+5);check(map.GetComponentsInChildren<Transform>().First(t=>t.name=="Water spray").localPosition==first,"source-time effects repeat");
                renderer.RenderAt(incident.start+40);check(!map.GetComponentsInChildren<Transform>().Any(t=>t.name=="Water spray"),"spray ends after stopping");
            }
            UnityEngine.Object.DestroyImmediate(root);
        }
        TrainingGeography.Validate(new RegionalGeography());check(!TrainingGeography.Present(new RegionalGeography()),"legacy optional map absent");
        check(TrainingRunway.Build(null,new RunwayPlan())==null,"absent runway cannot add a second ground rectangle");
        Debug.Log("RUNWAY_CASE_CHECKS_PASS: "+n);
    }
    static float LowestWorldVertex(MeshFilter mesh)=>mesh.sharedMesh.vertices.Min(v=>mesh.transform.TransformPoint(v).y);
    static void Capture(Transform parent,Vector3 centre,float distance,string path,float yaw=0,float pitch=48){
        var go=new GameObject("Geometry review camera",typeof(Camera));var camera=go.GetComponent<Camera>();
        var objects=parent.GetComponentsInChildren<Transform>();var layers=objects.Select(t=>t.gameObject.layer).ToArray();
        for(int i=0;i<objects.Length;i++)objects[i].gameObject.layer=31;camera.cullingMask=1<<31;
        var lights=UnityEngine.Object.FindObjectsByType<Light>(FindObjectsSortMode.None);var enabled=lights.Select(l=>l.enabled).ToArray();
        var sun=lights.FirstOrDefault(l=>l.isActiveAndEnabled&&l.type==LightType.Directional);
        for(int i=0;i<lights.Length;i++)if(lights[i]!=sun)lights[i].enabled=false;
        camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.54f,.64f,.70f);camera.farClipPlane=15000;camera.fieldOfView=55;
        camera.transform.rotation=Quaternion.Euler(pitch,yaw,0);camera.transform.position=centre-camera.transform.forward*distance;
        var target=new RenderTexture(1280,720,24);camera.targetTexture=target;camera.Render();
        var previous=RenderTexture.active;RenderTexture.active=target;var pixels=new Texture2D(1280,720,TextureFormat.RGB24,false);pixels.ReadPixels(new Rect(0,0,1280,720),0,0);pixels.Apply();File.WriteAllBytes(path,pixels.EncodeToPNG());
        RenderTexture.active=previous;camera.targetTexture=null;UnityEngine.Object.DestroyImmediate(pixels);UnityEngine.Object.DestroyImmediate(target);UnityEngine.Object.DestroyImmediate(go);
        for(int i=0;i<objects.Length;i++)objects[i].gameObject.layer=layers[i];
        for(int i=0;i<lights.Length;i++)lights[i].enabled=enabled[i];
    }
}
