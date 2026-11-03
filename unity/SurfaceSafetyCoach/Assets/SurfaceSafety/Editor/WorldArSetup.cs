using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.XR.Management;
using UnityEditor.XR.Management.Metadata;
using UnityEngine;
using UnityEngine.XR.Management;
using SurfaceSafety;

// Simulated world-scale AR setup (docs/AR_SCOPE.md). Re-runnable:
//   Unity -batchmode -quit -projectPath <project> -executeMethod WorldArSetup.Run -logFile <log>
// - enables AR Foundation's XR Simulation provider for the editor/standalone (Android is untouched);
// - builds ApronEnvironment.prefab, a full-scale fictional apron used as the XR Simulation environment, i.e. the
//   "real world" the simulated AR camera sees (asphalt, stand markings, taxiway, terminal, jet bridges);
// - writes Scenes/WorldAR.unity: AR Session, XR Origin (Mobile AR) and the world-scale replay (WorldArBootstrap).
// Then: WorldArSetup.Check renders the view from eye height and checks the in-view tracking logic.
public static class WorldArSetup {
    const string Folder = "Assets/SurfaceSafety/WorldAR";
    const string EnvironmentPath = Folder + "/ApronEnvironment.prefab";
    const string ScenePath = "Assets/SurfaceSafety/Scenes/WorldAR.unity";
    const string SimulationLoader = "UnityEngine.XR.Simulation.SimulationLoader";
    const float FarClip = 2000f;
    // Eye height, south of the taxiway, phone tilted 3 degrees down so the stands sit in the AR window above the
    // coordinator panels.
    static readonly Vector3 StartPosition = new Vector3(-5f, 1.7f, -170f);
    static readonly Quaternion StartRotation = Quaternion.Euler(3f, 0f, 0f);

    [MenuItem("AirfieldLens/Rebuild world AR (apron, XR settings, scene)")]
    public static void Run() {
        if (EditorApplication.isPlayingOrWillChangePlaymode) { Debug.LogWarning("Stop Play mode before rebuilding world AR."); return; }
        Directory.CreateDirectory(Folder + "/Materials");
        UseBothInputHandlers();
        EnableSimulationLoader();
        var environment = BuildEnvironment();
        SetSimulationEnvironment(environment);
        BuildScene();
        AssetDatabase.SaveAssets();
        Debug.Log("WORLD_AR_SETUP_PASS");
    }

    // XR Simulation navigates with the Input System; the app's uGUI and taps use the legacy input manager. Both.
    static void UseBothInputHandlers() {
        var settings = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset")[0]);
        var input = settings.FindProperty("activeInputHandler");
        if (input != null && input.intValue != 2) { input.intValue = 2; settings.ApplyModifiedPropertiesWithoutUndo(); }
    }

    static void EnableSimulationLoader() {
        EditorBuildSettings.TryGetConfigObject(XRGeneralSettings.k_SettingsKey, out XRGeneralSettingsPerBuildTarget perTarget);
        if (perTarget == null) {
            perTarget = ScriptableObject.CreateInstance<XRGeneralSettingsPerBuildTarget>();
            Directory.CreateDirectory("Assets/XR");
            AssetDatabase.CreateAsset(perTarget, "Assets/XR/XRGeneralSettingsPerBuildTarget.asset");
            EditorBuildSettings.AddConfigObject(XRGeneralSettings.k_SettingsKey, perTarget, true);
        }
        if (!perTarget.HasManagerSettingsForBuildTarget(BuildTargetGroup.Standalone))
            perTarget.CreateDefaultManagerSettingsForBuildTarget(BuildTargetGroup.Standalone);
        var manager = perTarget.ManagerSettingsForBuildTarget(BuildTargetGroup.Standalone);
        if (!manager.activeLoaders.Any(l => l.GetType().FullName == SimulationLoader) &&
            !XRPackageMetadataStore.AssignLoader(manager, SimulationLoader, BuildTargetGroup.Standalone))
            throw new Exception("Could not enable XR Simulation for Standalone");
        EditorUtility.SetDirty(perTarget);
    }

    static Material Paint(string name, Color color, float smoothness = .15f) {
        var path = $"{Folder}/Materials/{name}.mat";
        var m = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (m == null) { m = new Material(Shader.Find("Standard")); AssetDatabase.CreateAsset(m, path); }
        m.color = color; m.SetFloat("_Glossiness", smoothness); EditorUtility.SetDirty(m);
        return m;
    }

    static GameObject Block(Transform parent, string name, Vector3 centre, Vector3 size, Material m) {
        var g = GameObject.CreatePrimitive(PrimitiveType.Cube); g.name = name; g.transform.SetParent(parent, false);
        g.transform.localPosition = centre; g.transform.localScale = size; g.GetComponent<Renderer>().sharedMaterial = m;
        return g;
    }

    // Board coordinates x 1000 = metres: stands A and B at x = -45 and 35 m (z = 40 m), the taxiway at z = -25 m.
    static GameObject BuildEnvironment() {
        var asphalt = Paint("Asphalt", new Color(.20f, .21f, .22f));
        var concrete = Paint("Concrete", new Color(.55f, .56f, .55f));
        var taxiway = Paint("Taxiway", new Color(.16f, .17f, .18f));
        var yellow = Paint("PaintYellow", new Color(.95f, .76f, .16f), .3f);
        var white = Paint("PaintWhite", new Color(.92f, .93f, .92f), .3f);
        var building = Paint("Terminal", new Color(.62f, .64f, .66f));
        var glass = Paint("Glass", new Color(.20f, .32f, .40f), .85f);
        var bridge = Paint("JetBridge", new Color(.78f, .79f, .80f));
        var grass = Paint("Grass", new Color(.30f, .42f, .26f));

        var root = new GameObject("ApronEnvironment");
        Block(root.transform, "Grass", new Vector3(0, -.12f, 0), new Vector3(800, .2f, 600), grass);
        Block(root.transform, "Apron asphalt", new Vector3(0, -.05f, 0), new Vector3(300, .1f, 260), asphalt);
        Block(root.transform, "Taxiway", new Vector3(0, -.04f, -25), new Vector3(300, .1f, 32), taxiway);
        Block(root.transform, "Taxiway centreline", new Vector3(0, .02f, -25), new Vector3(300, .02f, .35f), yellow);
        foreach (var edge in new[] { -41f, -9f }) Block(root.transform, "Taxiway edge", new Vector3(0, .02f, edge), new Vector3(300, .02f, .25f), white);
        foreach (var (stand, x) in new[] { ("A", -45f), ("B", 35f) }) {
            Block(root.transform, $"Stand {stand} pad", new Vector3(x, -.03f, 45), new Vector3(46, .1f, 60), concrete);
            Block(root.transform, $"Stand {stand} lead-in line", new Vector3(x, .02f, 8), new Vector3(.35f, .02f, 66), yellow);
            Block(root.transform, $"Stand {stand} stop bar", new Vector3(x, .02f, 58), new Vector3(8, .02f, .5f), white);
            Block(root.transform, $"Stand {stand} safety line", new Vector3(x - 22, .02f, 45), new Vector3(.25f, .02f, 60), white);
            Block(root.transform, $"Stand {stand} jet bridge", new Vector3(x - 6, 4.5f, 72), new Vector3(4, 3.5f, 26), bridge);
            var label = new GameObject($"Stand {stand} marking", typeof(TextMesh)); label.transform.SetParent(root.transform, false);
            label.transform.localPosition = new Vector3(x + 4, .05f, 28); label.transform.localRotation = Quaternion.Euler(90, 0, 0);
            var text = label.GetComponent<TextMesh>(); text.text = stand; text.characterSize = 2.2f; text.fontSize = 64;
            text.anchor = TextAnchor.MiddleCenter; text.color = new Color(.95f, .76f, .16f);
            text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf"); label.GetComponent<MeshRenderer>().sharedMaterial = text.font.material;
        }
        Block(root.transform, "Terminal", new Vector3(0, 9, 100), new Vector3(240, 18, 26), building);
        Block(root.transform, "Terminal glazing", new Vector3(0, 10, 86.9f), new Vector3(236, 6, .4f), glass);
        foreach (var x in new[] { -120f, -60f, 0f, 60f, 120f })
            Block(root.transform, "Floodlight mast", new Vector3(x, 12, 80), new Vector3(.6f, 24, .6f), building);
        // The sky: XR Simulation's camera draws no skybox, so the environment carries an inward-facing gradient dome.
        var skyPath = $"{Folder}/Materials/SkyDome.mat";
        var sky = AssetDatabase.LoadAssetAtPath<Material>(skyPath);
        if (sky == null) { sky = new Material(Shader.Find("SurfaceSafety/SkyDome")); AssetDatabase.CreateAsset(sky, skyPath); }
        var dome = GameObject.CreatePrimitive(PrimitiveType.Sphere); dome.name = "Sky dome"; dome.transform.SetParent(root.transform, false);
        dome.transform.localScale = Vector3.one * 1800f; dome.GetComponent<Renderer>().sharedMaterial = sky;
        UnityEngine.Object.DestroyImmediate(dome.GetComponent<Collider>());  // not a surface for plane detection
        var sun = new GameObject("Sun", typeof(Light)); sun.transform.SetParent(root.transform, false);
        var light = sun.GetComponent<Light>(); light.type = LightType.Directional; light.intensity = 1.2f;
        sun.transform.localRotation = Quaternion.Euler(50, -35, 0);

        CustomHeathrowEnvironment.Decorate(root);
        AddSimulationEnvironment(root);
        var prefab = PrefabUtility.SaveAsPrefabAsset(root, EnvironmentPath);
        UnityEngine.Object.DestroyImmediate(root);
        return prefab;
    }

    static Type Find(string fullName) =>
        AppDomain.CurrentDomain.GetAssemblies().Select(a => a.GetType(fullName)).FirstOrDefault(t => t != null)
        ?? throw new Exception("Type not found: " + fullName);

    // SimulationEnvironment is internal to AR Foundation; set it up through its serialized fields.
    static void AddSimulationEnvironment(GameObject root) {
        var component = root.AddComponent(Find("UnityEngine.XR.Simulation.SimulationEnvironment"));
        var so = new SerializedObject(component);
        var start = new Pose(StartPosition, StartRotation);
        so.FindProperty("m_CameraStartingPose.position").vector3Value = start.position;
        so.FindProperty("m_CameraStartingPose.rotation").quaternionValue = start.rotation;
        so.FindProperty("m_CameraMovementBounds").boundsValue = new Bounds(new Vector3(0, 15, 0), new Vector3(400, 30, 400));
        so.FindProperty("m_DefaultViewPose.position").vector3Value = new Vector3(0, 60, -120);
        so.FindProperty("m_DefaultViewPose.rotation").quaternionValue = Quaternion.Euler(30, 0, 0);
        so.FindProperty("m_DefaultViewPivot").vector3Value = new Vector3(0, 0, 20);
        so.FindProperty("m_DefaultViewSize").floatValue = 120;
        // XR Simulation renders the environment as the camera feed; without a sky it would be black above the horizon.
        so.FindProperty("m_RenderSettings.m_Skybox").objectReferenceValue = AssetDatabase.GetBuiltinExtraResource<Material>("Default-Skybox.mat");
        so.ApplyModifiedPropertiesWithoutUndo();
    }

    static void SetSimulationEnvironment(GameObject prefab) {
        var type = Find("UnityEngine.XR.Simulation.XRSimulationPreferences");
        var instance = type.BaseType.GetProperty("Instance", System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Static)
            ?.GetValue(null) as UnityEngine.Object ?? throw new Exception("XR Simulation preferences unavailable");
        var so = new SerializedObject(instance);
        so.FindProperty("m_EnvironmentPrefab").objectReferenceValue = prefab;
        so.ApplyModifiedPropertiesWithoutUndo();
        EditorUtility.SetDirty(instance);
    }

    static void BuildScene() {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        Find("UnityEditor.XR.ARFoundation.SceneUtils").GetMethod("CreateARSessionWithParent").Invoke(null, new object[] { null });
        var origin = (Component)Find("UnityEditor.XR.ARFoundation.XROriginCreateUtil").GetMethod("CreateXROriginWithParent").Invoke(null, new object[] { null });
        // The Mobile AR default (20 m far clip) suits tabletop AR; the apron spans hundreds of metres.
        var arCamera = origin.GetComponentInChildren<Camera>(true);
        arCamera.nearClipPlane = .1f; arCamera.farClipPlane = FarClip;
        new GameObject("World AR replay").AddComponent<WorldArBootstrap>().autonomousTraffic=true;
        EditorSceneManager.SaveScene(scene, ScenePath);
    }

    // Edit-mode check on the saved WorldAR scene and its own AR camera: renders the apron and the replay from the
    // simulated starting pose (eye height), checks that every aircraft is within the camera's clipping range, and
    // that turning away takes the apron out of view. Writes work/world-ar/*.png for review.
    [MenuItem("AirfieldLens/Check world AR (renders into the work folder)")]
    public static void Check() {
        if (EditorApplication.isPlayingOrWillChangePlaymode) { Debug.LogWarning("Stop Play mode before checking world AR."); return; }
        Action<bool, string> check = (ok, message) => { if (!ok) throw new Exception("World AR check failed: " + message); };
        EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        var environment = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(EnvironmentPath));
        check(environment != null, "environment prefab exists");
        var boot = UnityEngine.Object.FindFirstObjectByType<WorldArBootstrap>(); check(boot != null, "the scene has the world replay");
        boot.autonomousTraffic=false; // Preserve fixed replay checks.
        boot.Initialize();
        var replay = boot.Replay; var overlay = boot.Overlay;
        check(!replay.DetailsOpen, "world AR starts with the details collapsed");
        // Look away from 25 to 50 s so the banner and NEW badges show (the demo's D05-D07 arrive meanwhile).
        replay.Seek(25); replay.Clock.Play(); replay.Tracking(false); replay.Clock.Advance(25); replay.Tracking(true); replay.Pause();
        replay.SelectAircraft(1);
        var cam = UnityEngine.Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).FirstOrDefault(c => c.CompareTag("MainCamera"));
        check(cam != null, "the scene has the AR camera");
        cam.transform.position = StartPosition; cam.transform.rotation = StartRotation; cam.clearFlags = CameraClearFlags.Skybox;
        foreach (Transform aircraft in replay.Content)
            if (replay.Data.aircraft.Any(a => a.id == aircraft.name))
                check(Vector3.Distance(StartPosition, aircraft.position) < cam.farClipPlane * .9f, $"{aircraft.name} is within the AR camera's far clip");
        check(WorldArBootstrap.ApronInView(cam, replay.Content.position), "the apron is in view from the starting pose");
        check(Mathf.Abs(replay.Content.lossyScale.x - WorldArBootstrap.MetresPerBoardUnit) < .01f, "the replay is in metres");
        var output = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../work/world-ar"));
        Directory.CreateDirectory(output);
        Render(cam, Path.Combine(output, "eye-height-view.png"), false, overlay);
        Render(cam, Path.Combine(output, "eye-height-view-with-ui.png"), true, overlay);
        check(overlay.VisibleLabels >= 2, $"aircraft labels float over the apron ({overlay.VisibleLabels} visible)");
        check(overlay.BannerShown, "the While-you-were-away banner shows over the AR view");
        replay.SetDetails(true);
        Render(cam, Path.Combine(output, "eye-height-view-details.png"), true, overlay);
        check(!overlay.BannerShown, "opening the details hides the banner (the card is on the Now tab)");
        cam.transform.rotation = Quaternion.Euler(12f, 180f, 0f);
        check(!WorldArBootstrap.ApronInView(cam, replay.Content.position), "turning around takes the apron out of view");
        cam.transform.position = new Vector3(-115, 14, -70);
        cam.transform.LookAt(new Vector3(0, 12, 100));
        Render(cam, Path.Combine(output, "heathrow-overview.png"), false, overlay, 1600, 900);
        Debug.Log("WORLD_AR_CHECKS_PASS: " + output);
    }

    static void Render(Camera cam, string path, bool withUi, WorldOverlay overlay, int width = 1080, int height = 1920) {
        var tex = new RenderTexture(width, height, 24); cam.targetTexture = tex; cam.aspect = (float)width / height;
        var canvases = UnityEngine.Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None);
        foreach (var canvas in canvases) {
            canvas.enabled = withUi;
            if (withUi) { canvas.renderMode = RenderMode.ScreenSpaceCamera; canvas.worldCamera = cam; canvas.planeDistance = .5f; }
        }
        Canvas.ForceUpdateCanvases(); overlay.Refresh(cam); Canvas.ForceUpdateCanvases(); cam.Render(); RenderTexture.active = tex;
        var image = new Texture2D(width, height, TextureFormat.RGB24, false); image.ReadPixels(new Rect(0, 0, width, height), 0, 0); image.Apply();
        File.WriteAllBytes(path, image.EncodeToPNG());
        UnityEngine.Object.DestroyImmediate(image); RenderTexture.active = null; cam.targetTexture = null;
    }
}
