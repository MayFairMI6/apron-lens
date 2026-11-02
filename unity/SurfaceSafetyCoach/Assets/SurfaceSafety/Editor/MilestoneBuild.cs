using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.Build.Reporting;
using UnityEngine;
using UnityEngine.UI;
using SurfaceSafety;

public static class MilestoneBuild {
    static string Output => Path.GetFullPath(Path.Combine(Application.dataPath,"../../../outputs/milestone1"));
    public static void Prepare(){Prepare("milestone1");}
    // scenario: the Resources scenario the built scenes start with (milestone1, or ar_demo_01 for the AR demo build).
    static void Prepare(string scenario){
        Directory.CreateDirectory(Output);
        var importer=(TextureImporter)AssetImporter.GetAtPath("Assets/Resources/AirportBoard.png");
        importer.isReadable=true;importer.textureCompression=TextureImporterCompression.Uncompressed;
        importer.maxTextureSize=2048;importer.npotScale=TextureImporterNPOTScale.None;
        importer.mipmapEnabled=false;importer.SaveAndReimport();
        PlayerSettings.companyName="Airfield Research";PlayerSettings.productName="ApronLens";
        PlayerSettings.bundleVersion="1.5";PlayerSettings.Android.bundleVersionCode=6;
        PlayerSettings.insecureHttpOption=InsecureHttpOption.DevelopmentOnly;
        PlayerSettings.SetApplicationIdentifier(UnityEditor.Build.NamedBuildTarget.Android,"edu.airfieldresearch.standreplay");
        PlayerSettings.defaultInterfaceOrientation=UIOrientation.Portrait;
        PlayerSettings.Android.minSdkVersion=AndroidSdkVersions.AndroidApiLevel29;
        PlayerSettings.Android.targetSdkVersion=AndroidSdkVersions.AndroidApiLevelAuto;
        PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Android,ScriptingImplementation.IL2CPP);
        PlayerSettings.Android.targetArchitectures=AndroidArchitecture.ARM64;
        PlayerSettings.Android.applicationEntry=AndroidApplicationEntry.Activity;
        PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.Android,false);
        PlayerSettings.SetGraphicsAPIs(BuildTarget.Android,new[]{UnityEngine.Rendering.GraphicsDeviceType.OpenGLES3});
        PlayerSettings.MTRendering=false;PlayerSettings.Android.forceInternetPermission=true;
        // Pin legacy uGUI input for the first milestone; no Input System dependency.
        var settings=new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset")[0]);
        var input=settings.FindProperty("activeInputHandler");if(input!=null){input.intValue=0;settings.ApplyModifiedPropertiesWithoutUndo();}
        foreach(bool preview in new[]{true,false}){
            var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
            var g=new GameObject("SurfaceSafetyBootstrap");var bootstrap=g.AddComponent<SceneBootstrap>();
            bootstrap.previewMode=preview;bootstrap.scenarioResource=scenario;
            EditorSceneManager.SaveScene(scene,"Assets/SurfaceSafety/Scenes/"+(preview?"DesktopReplay":"AndroidAR")+".unity");
        }
        EditorBuildSettings.scenes=new[]{new EditorBuildSettingsScene("Assets/SurfaceSafety/Scenes/AndroidAR.unity",true)};
        AssetDatabase.SaveAssets();Verify();
        Debug.Log("MILESTONE1_PREPARE_PASS");
    }
    static void Check(bool pass,string message){if(!pass)throw new Exception("CHECK FAILED: "+message);}
    public static void Verify(){
        Directory.CreateDirectory(Output);
        var data=JsonUtility.FromJson<Scenario>(Resources.Load<TextAsset>("milestone1").text);data.Validate();
        var c=new ReplayClock(data.duration);c.Play();c.Advance(4);Check(c.Time==0,"No play without tracking");
        c.SetTracking(true);c.Play();c.Advance(13);Check(c.Time==13,"Clock advances");
        Check(!data.KnownAt(c.Time).Any(e=>e.id=="E03"),"Late event hidden at 13");
        c.Advance(1);Check(data.KnownAt(c.Time).Any(e=>e.id=="E03"),"Late event available at receipt 14");
        c.Pause();var p=Scenario.Position(data.aircraft[0],c.Time);c.Advance(10);
        Check(c.Time==14 && Scenario.Position(data.aircraft[0],c.Time)==p,"Pause freezes clock and position");
        c.Play();c.SetTracking(false);c.Advance(3);Check(c.Time==14&&!c.Playing,"Lost tracking pauses");
        c.SetTracking(true);Check(!c.Playing,"Reacquisition requires explicit play");
        c.Seek(5);Check(!data.KnownAt(c.Time).Any(e=>e.id=="E03"),"Backward replay hides later receipt");
        c.Restart();c.Play();c.Advance(14);Check(Scenario.Position(data.aircraft[0],c.Time)==p,"Restart deterministic");
        c.Advance(100);Check(c.Time==data.duration&&!c.Playing,"Stop at duration");
        Check(Scenario.Position(data.aircraft[0],30)==new Vector3(.035f,0,-.025f),"A1 checkpoint matches authored path");
        Check(Scenario.Position(data.aircraft[1],26)==new Vector3(.035f,0,-.025f),"A2 checkpoint matches authored path");
        Check(Math.Abs(data.targetWidth-.24f)<.00001f,"Printed board width 24 cm");
        File.WriteAllText(Path.Combine(Output,"verification.json"),"{\"status\":\"passed\",\"checks\":13,\"scope\":\"Unity deterministic replay and event availability; physical tracking untested\"}");
        Debug.Log("MILESTONE1_CHECKS_PASS");
    }
    public static void RenderPreview(){
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
        var g=new GameObject("Preview render");var boot=g.AddComponent<SceneBootstrap>();boot.previewMode=true;boot.Initialize();
        var replay=boot.Replay;replay.Seek(14);replay.SelectAircraft(1);
        var cam=Camera.main;var tex=new RenderTexture(1080,1920,24);cam.targetTexture=tex;cam.aspect=1080f/1920f;
        SceneBootstrap.FramePreview(cam);
        foreach(var canvas in UnityEngine.Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)){
            canvas.renderMode=RenderMode.ScreenSpaceCamera;canvas.worldCamera=cam;canvas.planeDistance=.1f;
        }
        Directory.CreateDirectory(Output);
        Action<string> capture=filename=>{
            Canvas.ForceUpdateCanvases();cam.Render();RenderTexture.active=tex;
            var image=new Texture2D(1080,1920,TextureFormat.RGB24,false);image.ReadPixels(new Rect(0,0,1080,1920),0,0);image.Apply();
            File.WriteAllBytes(Path.Combine(Output,filename),image.EncodeToPNG());UnityEngine.Object.DestroyImmediate(image);
        };
        replay.SelectTab("now");capture("desktop-preview.png");capture("coordinator-now.png");
        replay.SelectTab("why");capture("coordinator-why.png");
        var baselineButton=UnityEngine.Object.FindObjectsByType<Button>(FindObjectsSortMode.None)
            .First(b=>b.GetComponentInChildren<Text>()!=null&&b.GetComponentInChildren<Text>().text=="Recorded facts");
        baselineButton.onClick.Invoke();capture("coordinator-baseline.png");
        replay.SelectTab("history");capture("coordinator-history.png");
        replay.InspectReport("E03");capture("coordinator-report-detail.png");
        replay.Seek(13);replay.SelectTab("now");capture("coordinator-before-receipt.png");
        replay.SelectTab("history");capture("coordinator-history-before-receipt.png");
        replay.Seek(30);replay.SelectTab("now");capture("coordinator-moving.png");
        replay.Tracking(false);capture("coordinator-tracking-lost.png");replay.Tracking(true);
        cam.targetTexture=null;RenderTexture.active=null;UnityEngine.Object.DestroyImmediate(tex);
        replay.Seek(14);replay.SelectTab("now");
        QwenIntegrationVerification.CaptureScreen("coordinator-tall.png",1080,2400);
        QwenIntegrationVerification.CaptureScreen("coordinator-compact.png",720,1280);
        Debug.Log("MILESTONE1_RENDER_PASS");
    }
    static void AndroidTools(){
        var tools=Path.GetFullPath(Path.Combine(EditorApplication.applicationContentsPath,"../../PlaybackEngines/AndroidPlayer"));
        UnityEditor.Android.AndroidExternalToolsSettings.sdkRootPath=Path.Combine(tools,"SDK");
        UnityEditor.Android.AndroidExternalToolsSettings.ndkRootPath=Path.Combine(tools,"NDK");
        UnityEditor.Android.AndroidExternalToolsSettings.jdkRootPath=Path.Combine(tools,"OpenJDK");
    }
    public static void Android(){
        AndroidTools();
        Prepare();
        var report=BuildPipeline.BuildPlayer(new BuildPlayerOptions {scenes=EditorBuildSettings.scenes.Select(s=>s.path).ToArray(),
            locationPathName=Path.Combine(Output,"ApronLens-M1.apk"),target=BuildTarget.Android,options=BuildOptions.Development});
        if(report.summary.result!=BuildResult.Succeeded)throw new Exception("Android build failed: "+report.summary.result);
        Debug.Log("MILESTONE1_ANDROID_BUILD_PASS");
    }
    // The AR demo build for the course checkpoint: same settings, starting on ar_demo_01 (pointing among identical
    // aircraft, a next-rotation correction, and a clock that runs while the board is out of view). Written to the
    // ignored work/ folder, not outputs/. Restores the milestone scenes afterwards.
    public static void AndroidArDemo(){
        AndroidTools();
        Prepare("ar_demo_01");
        PlayerSettings.bundleVersion="1.6-ar-demo";PlayerSettings.Android.bundleVersionCode=7;
        var path=Path.GetFullPath(Path.Combine(Application.dataPath,"../../../work/checkpoint1/ApronLens-AR-demo.apk"));
        Directory.CreateDirectory(Path.GetDirectoryName(path));
        var report=BuildPipeline.BuildPlayer(new BuildPlayerOptions {scenes=EditorBuildSettings.scenes.Select(s=>s.path).ToArray(),
            locationPathName=path,target=BuildTarget.Android,options=BuildOptions.Development});
        Prepare("milestone1");PlayerSettings.bundleVersion="1.5";PlayerSettings.Android.bundleVersionCode=6;
        if(report.summary.result!=BuildResult.Succeeded)throw new Exception("AR demo build failed: "+report.summary.result);
        Debug.Log("AR_DEMO_ANDROID_BUILD_PASS: "+path);
    }
}
