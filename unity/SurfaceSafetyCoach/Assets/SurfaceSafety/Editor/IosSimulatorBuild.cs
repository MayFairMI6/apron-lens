using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.Build.Reporting;
using UnityEngine;
using SurfaceSafety;

// Run only in the disposable simulator project prepared by scripts/prepare_ios_simulator.py.
// ARKit and XR Simulation are not available in an iOS Simulator player.
public static class IosSimulatorBuild {
    public static void Run() {
#if !APRONLENS_SIMULATOR
        throw new InvalidOperationException("Use scripts/prepare_ios_simulator.py to create the isolated simulator project first.");
#else
        var path = PrepareReplayScene();
        // Retain the build artifact name; patch_ios_simulator_lifecycle.py sets the visible app name to AirfieldLens.
        PlayerSettings.productName = "ApronLens Preview";
        PlayerSettings.SetApplicationIdentifier(UnityEditor.Build.NamedBuildTarget.iOS, "edu.airfieldresearch.apronlens.simulator");
        PlayerSettings.iOS.sdkVersion = iOSSdkVersion.SimulatorSDK;
        var arch = typeof(PlayerSettings.iOS).GetProperty("simulatorSdkArchitecture");
        var arm64 = Enum.GetNames(arch.PropertyType).First(n => n.Equals("ARM64", StringComparison.OrdinalIgnoreCase));
        arch.SetValue(null, Enum.Parse(arch.PropertyType, arm64));
        PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.iOS, ScriptingImplementation.IL2CPP);
        PlayerSettings.iOS.targetOSVersionString = "15.0";
        PlayerSettings.iOS.cameraUsageDescription = "Camera access is used by the device AR version.";
        var output = Environment.GetEnvironmentVariable("APRONLENS_IOS_OUTPUT");
        BuildReplay(path, output, BuildTarget.iOS, "IOS_SIMULATOR_EXPORT_PASS");
#endif
    }

    // Builds the existing controller Board for a phone-sized Android runtime. Physical camera AR is a separate scene.
    public static void AndroidBoard() {
#if !APRONLENS_SIMULATOR
        throw new InvalidOperationException("Build the Android Board in an isolated replay project.");
#else
        var path = PrepareReplayScene();
        PlayerSettings.productName = "AirfieldLens";
        var android = UnityEditor.Build.NamedBuildTarget.Android;
        PlayerSettings.SetApplicationIdentifier(android, "edu.airfieldresearch.apronlens.replay");
        PlayerSettings.SetScriptingBackend(android, ScriptingImplementation.IL2CPP);
        PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel29;
        PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
        PlayerSettings.Android.applicationEntry = AndroidApplicationEntry.Activity;
        PlayerSettings.Android.forceInternetPermission = true;
        PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.Android, false);
        PlayerSettings.SetGraphicsAPIs(BuildTarget.Android, new[] { UnityEngine.Rendering.GraphicsDeviceType.OpenGLES3 });
        var output = Environment.GetEnvironmentVariable("AIRFIELDLENS_ANDROID_OUTPUT");
        BuildReplay(path, output, BuildTarget.Android, "ANDROID_BOARD_BUILD_PASS");
#endif
    }

#if APRONLENS_SIMULATOR
    static string PrepareReplayScene() {
        // Runtime-created materials use Shader.Find, so retain their shaders in the player.
        Directory.CreateDirectory("Assets/Resources/SimulatorShaders");
        foreach (var name in new[] { "Standard", "Unlit/Texture", "Sprites/Default" }) {
            var shader = Shader.Find(name);
            if (shader == null) throw new Exception("Missing replay shader: " + name);
            var materialPath = "Assets/Resources/SimulatorShaders/" + name.Replace('/', '_') + ".mat";
            if (AssetDatabase.LoadAssetAtPath<Material>(materialPath) == null)
                AssetDatabase.CreateAsset(new Material(shader), materialPath);
        }
        AssetDatabase.SaveAssets();
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var environment = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/SurfaceSafety/WorldAR/ApronEnvironment.prefab"));
        foreach (var component in environment.GetComponents<MonoBehaviour>()) UnityEngine.Object.DestroyImmediate(component);
        var camera = new GameObject("Simulator camera", typeof(Camera), typeof(AudioListener)).GetComponent<Camera>();
        camera.tag = "MainCamera"; camera.nearClipPlane = .1f; camera.farClipPlane = 2000;
        camera.transform.position = new Vector3(-5, 1.7f, -170); camera.transform.rotation = Quaternion.Euler(3, 0, 0);
        camera.gameObject.AddComponent<SimulatorLook>();
        new GameObject("Apron traffic").AddComponent<WorldArBootstrap>().autonomousTraffic=true;
        RenderSettings.ambientLight = new Color(.6f, .65f, .7f);
        const string path = "Assets/SurfaceSafety/Scenes/IosSimulator.unity";
        EditorSceneManager.SaveScene(scene, path);
        PlayerSettings.defaultInterfaceOrientation = UIOrientation.AutoRotation;
        PlayerSettings.allowedAutorotateToLandscapeLeft=true;PlayerSettings.allowedAutorotateToLandscapeRight=true;
        PlayerSettings.allowedAutorotateToPortrait=true;PlayerSettings.allowedAutorotateToPortraitUpsideDown=false;
        PlayerSettings.insecureHttpOption = InsecureHttpOption.DevelopmentOnly;
        return path;
    }

    static void BuildReplay(string path, string output, BuildTarget target, string completion) {
        if (string.IsNullOrWhiteSpace(output)) throw new InvalidOperationException("The replay build output path is required.");
        var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
            scenes = new[] { path }, locationPathName = output, target = target,
            options = BuildOptions.Development
        });
        if (report.summary.result != BuildResult.Succeeded) throw new Exception("Replay build failed: " + report.summary.result);
        Debug.Log(completion + ": " + output);
    }
#endif
}
