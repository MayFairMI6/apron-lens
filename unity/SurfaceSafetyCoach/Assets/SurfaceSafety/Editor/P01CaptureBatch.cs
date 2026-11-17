// PROCEDURAL: opt-in synthetic capture export; never runs during normal app launch.
using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using SurfaceSafety;
public static class P01CaptureBatch {
    [Serializable] public sealed class PilotDomain {
        public string id,split;public Color body;public Vector3 bodyScale,cameraOffsetMetres;
    }
    [Serializable] public sealed class PilotPlan {
        public string purpose="P01 synthetic detector pilot; split assigned before generation by authored body/camera variant, shared apron and trajectories. Not a generalization acceptance set.";
        public string sourceScenario;public PilotDomain[] domains;public float[] sourceTimes;
    }
    static PilotDomain Domain(string id,string split,Color body,Vector3 scale,Vector3 offset)=>new PilotDomain{id=id,split=split,body=body,bodyScale=scale,cameraOffsetMetres=offset};
    public static void Run(){
        var input=Environment.GetEnvironmentVariable("AIRFIELDLENS_P01_SCENARIO");
        var output=Environment.GetEnvironmentVariable("AIRFIELDLENS_P01_CAPTURE_OUTPUT");
        if(string.IsNullOrEmpty(input)||string.IsNullOrEmpty(output))throw new InvalidOperationException("Set AIRFIELDLENS_P01_SCENARIO and AIRFIELDLENS_P01_CAPTURE_OUTPUT to opt in.");
        var scenario=JsonUtility.FromJson<Scenario>(File.ReadAllText(input));
        if(!P01StandScenery.Applies(scenario))throw new InvalidOperationException("Only a stand_clearance scenario is accepted.");
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
        var camera=new GameObject("P01 review camera",typeof(Camera)).GetComponent<Camera>();camera.tag="MainCamera";
        camera.nearClipPlane=.1f;camera.farClipPlane=2000;camera.aspect=16f/9;camera.backgroundColor=new Color(.54f,.64f,.70f);camera.clearFlags=CameraClearFlags.SolidColor;
        var prefab=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/SurfaceSafety/WorldAR/ApronEnvironment.prefab");
        if(prefab==null)throw new InvalidOperationException("Apron environment is missing.");
        var apron=UnityEngine.Object.Instantiate(prefab);apron.name="ApronEnvironment";
        var host=new GameObject("P01 captured replay");var replay=host.AddComponent<StandReplay>();replay.Initialize(true,"ar_demo_01");
        replay.UseWorldScale(WorldArBootstrap.MetresPerBoardUnit);replay.UseAutonomousTraffic();replay.ApplyTrafficScenario(scenario);replay.UseTrainingPresentation();
        var scenery=P01StandScenery.Build(replay.Content,apron,scenario.taxiPaths);
        var vehicle=scenery.BuildVehicle("service-vehicle",replay.Content);
        var rig=camera.gameObject.AddComponent<P01CameraRig>();rig.Bind(replay,camera);
        Directory.CreateDirectory(output);int frames=0,visible=0,hidden=0;
        // Fixed before rendering or model fitting. Body and viewpoint variants
        // are disjoint, but all share this authored apron and route: pilot only.
        var domains=new[]{
            Domain("body-a","train",new Color(.76f,.78f,.76f),new Vector3(1,1,1),new Vector3(-9,0,-3)),
            Domain("body-b","train",new Color(.58f,.64f,.66f),new Vector3(.94f,1.04f,.96f),new Vector3(-4,2,4)),
            Domain("body-c","train",new Color(.83f,.79f,.67f),new Vector3(1.04f,.96f,1.03f),new Vector3(4,-1,-7)),
            Domain("body-d","validation",new Color(.68f,.73f,.67f),new Vector3(.98f,1.02f,1.06f),new Vector3(10,3,2)),
            Domain("body-e","test",new Color(.79f,.72f,.65f),new Vector3(1.06f,.98f,.94f),new Vector3(16,1,-11))};
        var times=new[]{40f,90f,95f,120f};
        File.WriteAllText(Path.Combine(output,"pilot-split-plan.json"),JsonUtility.ToJson(new PilotPlan{sourceScenario=scenario.scenarioId,domains=domains,sourceTimes=times},true));
        foreach(var domain in domains){
            // Fresh replay of the same immutable source timeline for this domain.
            // This editor harness sets source time; it does not invent events.
            replay.Clock.Seek(0);vehicle.transform.localScale=domain.bodyScale;rig.SetCaptureOffset(domain.cameraOffsetMetres);
            foreach(var renderer in vehicle.GetComponentsInChildren<Renderer>())if(renderer.name=="Fuel tanker cab"||renderer.name=="Fuel tanker tank")renderer.sharedMaterial.color=domain.body;
            foreach(float time in times){
                replay.UpdateTrafficTime(time,"paused");
                var plan=Array.Find(scenario.groundVehicles,p=>p.id=="service-vehicle");
                if(plan==null)throw new InvalidOperationException("P01 service-vehicle route missing.");
                vehicle.transform.localPosition=Scenario.Position(plan,time);vehicle.transform.localRotation=Quaternion.Euler(0,Scenario.Heading(plan,time),0);
                foreach(P01CameraPose pose in Enum.GetValues(typeof(P01CameraPose))){
                    rig.SetPose(pose);
                    Write(replay,camera,Path.Combine(output,domain.split),domain.id+"-"+time.ToString("000")+"-"+pose,domain,ref frames,ref visible,ref hidden);
                }
            }
        }
        File.WriteAllText(Path.Combine(output,"capture-summary.json"),"{\"frames\":"+frames+",\"visibleVehicleFrames\":"+visible+",\"zeroVehiclePixelFrames\":"+hidden+",\"note\":\"Synthetic geometry labels; viewpoints at one scenario/time are a render group, not independent samples. Native scene acceptance remains separate.\"}");
        Debug.Log("P01_CAPTURE_BATCH_PASS frames="+frames+" visible="+visible+" zeroPixels="+hidden+" output="+output);
    }
    static void Write(StandReplay replay,Camera camera,string output,string stem,PilotDomain domain,ref int frames,ref int visible,ref int hidden){
        var frame=P01SynchronizedCapture.Capture(replay,camera,960);
        if(frame.depthFloat32.Length!=frame.metadata.width*frame.metadata.height*4)throw new Exception("Depth dimensions disagree.");
        if(frame.metadata.sourceTime!=replay.Clock.Time)throw new Exception("Source-time mismatch.");
        frame.metadata.split=domain.split;frame.metadata.domainVariant=domain.id;
        frame.metadata.renderGroup=domain.id+"/"+frame.metadata.renderGroup;
        frame.Export(output,stem);frames++;if(frame.metadata.visibleBoxes.Length>0)visible++;else hidden++;
    }
}
