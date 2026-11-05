using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor.SceneManagement;
using SurfaceSafety;

public static class AircraftTypeVerification {
    public static void Run(){
        Action<bool,string> check=(ok,label)=>{if(!ok)throw new Exception("Aircraft type check: "+label);};
        var destination=Environment.GetEnvironmentVariable("AIRFIELDLENS_FLEET_PREVIEW");
        if(!string.IsNullOrEmpty(destination))Directory.CreateDirectory(destination);
        foreach(var p in AircraftTypeVisual.Profiles){
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
            var parent=new GameObject("Aircraft verification").transform;parent.localScale=Vector3.one*1000;
            var rig=AircraftTypeVisual.Build(parent,Color.white,p.Id);
            var exterior=rig.transform.Find("AMV Lab exterior").GetComponent<MeshFilter>();var b=exterior.sharedMesh.bounds;
            check(Mathf.Abs(b.size.z-p.LengthMetres)<.002f&&Mathf.Abs(b.size.x-p.WingspanMetres)<.002f,p.Id+" normalized length/span");
            check(Mathf.Abs(b.max.y-p.HeightMetres)<.002f,p.Id+" reference height");
            check(Mathf.Abs(b.max.z-p.NoseAheadOfMainGearMetres)<.002f,p.Id+" nose/main-gear datum");
            check(rig.Wheels.Length==p.MainWheelCount+2,p.Id+" wheel arrangement");
            check(exterior.GetComponent<Renderer>().sharedMaterial.mainTexture!=null,p.Id+" source texture loaded");
            foreach(float pitch in new[]{0f,5f,8f}){
                var attitude=Quaternion.Euler(-pitch,0,0);float offset=rig.ContactOffsetMetres(attitude);
                check(Mathf.Abs(rig.TyreContactVertices.Min(v=>(attitude*v).y)+offset)<.0001f,p.Id+" wheel contact at pitch "+pitch);
                check(exterior.sharedMesh.vertices.Min(v=>(attitude*v).y)+offset>=-.01f,p.Id+" exterior clear of pavement at pitch "+pitch);
            }
            float before=rig.ContactOffsetMetres(Quaternion.Euler(-7,0,0));rig.SetGear(true);
            check(!rig.Gear.gameObject.activeSelf&&rig.ContactOffsetMetres(Quaternion.Euler(-7,0,0))==before,p.Id+" retraction preserves datum");rig.SetGear(false);
            if(!string.IsNullOrEmpty(destination))Render(rig,p,destination);
            UnityEngine.Object.DestroyImmediate(parent.gameObject);
        }
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
        var fixtures=Environment.GetEnvironmentVariable("AIRFIELDLENS_FLEET_FIXTURES");
        if(string.IsNullOrEmpty(fixtures))throw new Exception("AIRFIELDLENS_FLEET_FIXTURES required");
        var fleet=Directory.GetFiles(fixtures,"*.json").Select(f=>JsonUtility.FromJson<Scenario>(File.ReadAllText(f))).Where(s=>s.aircraft!=null&&s.aircraft.Length==4).First();
        fleet.Validate();
        var legacy=JsonUtility.FromJson<Scenario>(File.ReadAllText(Environment.GetEnvironmentVariable("APRONLENS_TRAFFIC_FIXTURE")));
        var replay=new GameObject("Fleet rebind").AddComponent<StandReplay>();replay.InitializeFromJson(true,JsonUtility.ToJson(legacy));replay.UseTrainingPresentation();replay.UseWorldScale(1000);replay.UseAutonomousTraffic();replay.SelectAircraft(1);
        replay.ApplyTrafficScenario(fleet);replay.UpdateTrafficTime(0,"");
        check(replay.Content.GetComponentsInChildren<AircraftTypeRig>().Length==4,"3 to 4 imported models");
        check(replay.SelectedAircraftIndex==1,"selected identity retained across resize");
        var first=replay.Content.GetComponentsInChildren<AircraftTypeRig>()[0];replay.UpdateTrafficTime(2,"");replay.ApplyTrafficScenario(fleet);
        check(replay.Clock.Time==2&&replay.Content.GetComponentsInChildren<AircraftTypeRig>().Contains(first),"same scenario snapshot preserves clock/models");
        legacy.scenarioId+="-return";replay.ApplyTrafficScenario(legacy);replay.UpdateTrafficTime(0,"");
        check(replay.Content.GetComponentsInChildren<AircraftTypeRig>().Length==0&&replay.Data.aircraft.Length==3,"4 to 3 restores generic models");
        check(replay.SelectedAircraftIndex==1,"selection survives return");
        Debug.Log("AIRCRAFT_TYPE_CHECKS_PASS: source exteriors, dimensions, wheel arrangements, pitch contact, retraction, 3-4-3 lifecycle");
    }
    static void Render(AircraftTypeRig rig,AircraftTypeProfile p,string destination){
        RenderSettings.ambientLight=new Color(.65f,.68f,.72f);
        var light=new GameObject("Sun").AddComponent<Light>();light.type=LightType.Directional;light.intensity=1.1f;light.transform.rotation=Quaternion.Euler(40,-35,0);
        var camera=new GameObject("Aircraft camera").AddComponent<Camera>();camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.80f,.85f,.89f);camera.orthographic=true;camera.orthographicSize=p.WingspanMetres*.60f;camera.nearClipPlane=.1f;camera.farClipPlane=1000;
        camera.transform.position=new Vector3(p.WingspanMetres*.9f,p.HeightMetres*1.7f,p.LengthMetres*.9f);camera.transform.LookAt(new Vector3(0,p.HeightMetres*.28f,-(p.LengthMetres*.5f-p.NoseAheadOfMainGearMetres)));
        var target=new RenderTexture(1400,1000,24);camera.targetTexture=target;camera.Render();var previous=RenderTexture.active;RenderTexture.active=target;
        var image=new Texture2D(1400,1000,TextureFormat.RGB24,false);image.ReadPixels(new Rect(0,0,1400,1000),0,0);image.Apply();File.WriteAllBytes(Path.Combine(destination,p.Id+".png"),image.EncodeToPNG());
        RenderTexture.active=previous;camera.targetTexture=null;UnityEngine.Object.DestroyImmediate(image);UnityEngine.Object.DestroyImmediate(target);
    }
}
