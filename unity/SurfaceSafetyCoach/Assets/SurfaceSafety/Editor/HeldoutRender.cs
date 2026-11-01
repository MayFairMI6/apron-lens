using System;
using System.Globalization;
using System.IO;
using UnityEditor.SceneManagement;
using UnityEngine;
using SurfaceSafety;

// Evidence images for a held-out set stored outside the repository (scripts/check_heldout.py).
// Run with graphics (not -nographics) so the camera renders:
//   Unity -batchmode -quit -projectPath <project> -executeMethod HeldoutRender.Run \
//     -heldoutRenders <set>/renders.json -heldoutOutput <repo>/work/heldout -logFile <log>
// renders.json: [{"scenarioFile": "scenarios/<file>.json", "times": [20, 35]}], paths relative to it.
// Each image is <output>/<scenarioId>-<time>s.png, the name check_heldout.py expects. Every scenario
// goes through Scenario.Validate, so this is also the Unity-side check of the set.
public static class HeldoutRender {
    [Serializable] class RenderList { public RenderEntry[] items; }
    [Serializable] class RenderEntry { public string scenarioFile; public float[] times; }
    [Serializable] class ScenarioId { public string scenarioId; }

    static string Argument(string name) {
        var args = Environment.GetCommandLineArgs();
        var i = Array.IndexOf(args, name);
        if (i < 0 || i + 1 >= args.Length) throw new ArgumentException("Missing " + name + " <path>");
        return args[i + 1];
    }

    public static string ImageName(string scenarioId, float time) {
        return scenarioId + "-" + time.ToString(CultureInfo.InvariantCulture) + "s.png";
    }

    public static void Run() {
        var rendersPath = Path.GetFullPath(Argument("-heldoutRenders"));
        var output = Path.GetFullPath(Argument("-heldoutOutput"));
        Directory.CreateDirectory(output);
        var list = JsonUtility.FromJson<RenderList>("{\"items\":" + File.ReadAllText(rendersPath) + "}");
        int written = 0;
        foreach (var entry in list.items) {
            var json = File.ReadAllText(Path.Combine(Path.GetDirectoryName(rendersPath), entry.scenarioFile));
            var id = JsonUtility.FromJson<ScenarioId>(json).scenarioId;
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var boot = new GameObject("Held-out render").AddComponent<SceneBootstrap>();
            boot.previewMode = true; boot.scenarioJson = json; boot.Initialize();
            foreach (var t in entry.times) {
                if (t < 0 || t > boot.Replay.Data.duration) throw new ArgumentException(id + ": time " + t + " outside the scenario");
                boot.Replay.Seek(t);
                File.WriteAllBytes(Path.Combine(output, ImageName(id, t)), VisualEvidenceCapture.Capture(boot.Replay, Camera.main, null).png);
                written++;
            }
        }
        Debug.Log("HELDOUT_RENDERS_WRITTEN: " + written + " -> " + output);
    }
}
