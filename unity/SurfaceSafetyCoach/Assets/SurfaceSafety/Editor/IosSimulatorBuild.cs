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
        // Retain the build artifact name; patch_ios_simulator_lifecycle.py sets the visible app name to AirfieldLens.
        PlayerSettings.productName = "ApronLens Preview";
        PlayerSettings.SetApplicationIdentifier(UnityEditor.Build.NamedBuildTarget.iOS, "edu.airfieldresearch.apronlens.simulator");
        PlayerSettings.iOS.sdkVersion = iOSSdkVersion.SimulatorSDK;
        var arch = typeof(PlayerSettings.iOS).GetProperty("simulatorSdkArchitecture");
        var arm64 = Enum.GetNames(arch.PropertyType).First(n => n.Equals("ARM64", StringComparison.OrdinalIgnoreCase));
        arch.SetValue(null, Enum.Parse(arch.PropertyType, arm64));
        PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.iOS, ScriptingImplementation.IL2CPP);
        PlayerSettings.defaultInterfaceOrientation = UIOrientation.AutoRotation;
        PlayerSettings.allowedAutorotateToLandscapeLeft=true;PlayerSettings.allowedAutorotateToLandscapeRight=true;
        PlayerSettings.allowedAutorotateToPortrait=true;PlayerSettings.allowedAutorotateToPortraitUpsideDown=false;
        PlayerSettings.iOS.targetOSVersionString = "15.0";
        PlayerSettings.iOS.cameraUsageDescription = "Camera access is used by the device AR version.";
        PlayerSettings.insecureHttpOption = InsecureHttpOption.DevelopmentOnly;
        var output = Environment.GetEnvironmentVariable("APRONLENS_IOS_OUTPUT");
        if (string.IsNullOrWhiteSpace(output)) throw new InvalidOperationException("APRONLENS_IOS_OUTPUT is required.");
        var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
            scenes = new[] { path }, locationPathName = output, target = BuildTarget.iOS,
            options = BuildOptions.Development
        });
        if (report.summary.result != BuildResult.Succeeded) throw new Exception("Simulator export failed: " + report.summary.result);
        Debug.Log("IOS_SIMULATOR_EXPORT_PASS: " + output);
#endif
    }
}
