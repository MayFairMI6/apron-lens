using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;
using SurfaceSafety;

// Development check for the visual-reference capture (review finding 1).
// Run with graphics (not -nographics) so the cameras actually render:
//   Unity -batchmode -quit -projectPath <project> -executeMethod VisualCaptureVerification.Run -logFile <log>
public static class VisualCaptureVerification {
    public static void Run() {
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var host = new GameObject("Visual capture regression");
        var boot = host.AddComponent<SceneBootstrap>(); boot.previewMode = true; boot.Initialize();
        var replay = boot.Replay; replay.Seek(14);
        var viewpoint = Camera.main;
        Action<bool, string> check = (ok, message) => { if (!ok) throw new Exception("Visual capture check failed: " + message); };
        check(viewpoint != null, "a main camera exists");

        // 1. Rendering is live and the existing capture does reveal the selection.
        replay.SelectAircraft(0); var legacyA = QwenReasoningClient.CaptureSyntheticScene(replay);
        replay.SelectAircraft(1); var legacyB = QwenReasoningClient.CaptureSyntheticScene(replay);
        check(!legacyA.SequenceEqual(legacyB), "existing capture differs by selection (rendering is live)");

        // 2. The new capture does not depend on which aircraft is selected.
        check(VisualEvidenceCapture.SelectionInvariant(replay, viewpoint), "new capture identical for either selection");

        // 3. The new capture is not blank and reports the tap separately.
        var evidence = VisualEvidenceCapture.Capture(replay, viewpoint, new Vector2(viewpoint.pixelWidth / 2f, viewpoint.pixelHeight / 2f));
        var texture = new Texture2D(2, 2); texture.LoadImage(evidence.png);
        var colours = new HashSet<Color32>();
        for (int y = 0; y < texture.height; y += 8) for (int x = 0; x < texture.width; x += 8) colours.Add(texture.GetPixel(x, y));
        UnityEngine.Object.DestroyImmediate(texture);
        check(colours.Count > 8, "new capture contains rendered content (" + colours.Count + " sampled colours)");
        var expectedTap = Rect.PointToNormalized(evidence.crop, new Vector2(.5f, .5f));
        check(Mathf.Abs(evidence.tapViewport.x - expectedTap.x) < .01f && Mathf.Abs(evidence.tapViewport.y - expectedTap.y) < .01f, "tap returned in image coordinates");

        // 4. The crop zooms in and is fitted to all aircraft, not the selection.
        replay.SelectAircraft(0); var cropA = VisualEvidenceCapture.SceneCrop(replay, viewpoint);
        replay.SelectAircraft(1); var cropB = VisualEvidenceCapture.SceneCrop(replay, viewpoint);
        check(cropA == cropB, "crop identical for either selection");
        check(cropA.width < 1 && cropA.xMin >= 0 && cropA.yMin >= 0 && cropA.xMax <= 1 && cropA.yMax <= 1, "crop lies inside the view and zooms in");

        Debug.Log("VISUAL_CAPTURE_CHECKS_PASS: 6 (" + evidence.width + "x" + evidence.height + ", " + colours.Count + " sampled colours, crop " +
                  evidence.crop.width.ToString("0.00") + " of view)");
    }

    // Visual-only props in the development scenario (visual_dev_01).
    public static void RunObservations() {
        Action<bool, string> check = (ok, message) => { if (!ok) throw new Exception("Visual observation check failed: " + message); };

        // The milestone scenario is unchanged: no props are built.
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var m1 = new GameObject("Milestone regression").AddComponent<SceneBootstrap>(); m1.previewMode = true; m1.Initialize();
        check(m1.Replay.Content.GetComponentsInChildren<Transform>(true).All(t => !t.name.StartsWith("Visual prop", StringComparison.Ordinal)),
              "milestone scenario has no visual props");

        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var boot = new GameObject("Visual observation regression").AddComponent<SceneBootstrap>();
        boot.previewMode = true; boot.scenarioResource = "visual_dev_01"; boot.Initialize();
        var replay = boot.Replay; var viewpoint = Camera.main;
        var props = replay.Content.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("Visual prop", StringComparison.Ordinal)).ToArray();
        check(props.Length == 2, "two visual props built");
        check(props.All(p => p.GetComponentsInChildren<UnityEngine.UI.Text>(true).Length == 0 && p.GetComponentsInChildren<TextMesh>(true).Length == 0),
              "props carry no text");

        // Authored timeline: fuel vehicle connected until 30 s, hatch open until 28 s.
        replay.Seek(24); check(props.All(p => p.gameObject.activeSelf), "both props visible at 24 s");
        replay.Seek(29); check(!props.Single(p => p.name.EndsWith("P2", StringComparison.Ordinal)).gameObject.activeSelf &&
                               props.Single(p => p.name.EndsWith("P1", StringComparison.Ordinal)).gameObject.activeSelf, "hatch closed, vehicle present at 29 s");
        replay.Seek(31); check(props.All(p => !p.gameObject.activeSelf), "both props gone at 31 s");

        // Props appear in the capture: same time and pose, props shown versus hidden.
        replay.Seek(24);
        var shown = VisualEvidenceCapture.Capture(replay, viewpoint, null).png;
        foreach (var p in props) p.gameObject.SetActive(false);
        var hidden = VisualEvidenceCapture.Capture(replay, viewpoint, null).png;
        replay.Seek(24);
        check(!shown.SequenceEqual(hidden), "props are visible in the evidence image");
        check(VisualEvidenceCapture.SelectionInvariant(replay, viewpoint), "capture still independent of selection");

        // Each prop must stay legible: at least 0.15% of the frame (about 500 px at 672x504).
        var coverage = PropCoverage(replay, viewpoint); int frame = FramePixels(replay, viewpoint);
        check(coverage.Values.All(px => px >= .0015f * frame), "each prop covers at least 0.15% of the frame (" +
              string.Join(", ", coverage.Select(c => c.Key + "=" + c.Value + "px")) + ")");

        Debug.Log("VISUAL_OBSERVATION_CHECKS_PASS: 8");
    }

    // Three aircraft in one livery (visual_dev_02); Milestone 1 keeps two indexed aircraft.
    public static void RunMultiAircraft() {
        Action<bool, string> check = (ok, message) => { if (!ok) throw new Exception("Multi-aircraft check failed: " + message); };
        Func<SceneBootstrap, int> chips = b => b.GetComponentsInChildren<Transform>(true).Count(t => t.name == "Aircraft color");

        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var m1 = new GameObject("Milestone regression").AddComponent<SceneBootstrap>(); m1.previewMode = true; m1.Initialize();
        check(m1.Replay.Data.aircraft.Length == 2 && chips(m1) == 2 && m1.GetComponentsInChildren<UnityEngine.UI.Text>(true).Any(t => t.text == "A1  /  F1-R1"),
              "milestone scenario keeps two aircraft and its chip labels");

        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var boot = new GameObject("Multi-aircraft regression").AddComponent<SceneBootstrap>();
        boot.previewMode = true; boot.scenarioResource = "visual_dev_02"; boot.Initialize();
        var replay = boot.Replay; var viewpoint = Camera.main;
        check(replay.Data.aircraft.Length == 3 && replay.Data.aircraft.All(a => replay.Content.Find(a.id) != null), "three aircraft built");
        check(chips(boot) == 3, "one selection chip per aircraft");

        // Uniform livery: every aircraft is built from the same set of material colours.
        var liveries = replay.Data.aircraft.Select(a => string.Join(",", replay.Content.Find(a.id).GetComponentsInChildren<Renderer>()
            .Where(r => !r.transform.GetComponentsInParent<Transform>().Any(p => p.name.StartsWith("Visual prop ", StringComparison.Ordinal)))
            .Select(r => r.sharedMaterial.color.ToString()).Distinct().OrderBy(c => c))).Distinct().Count();
        check(liveries == 1, "all aircraft share one livery");

        replay.SelectAircraft(0);
        check(replay.CurrentSceneState == "At Stand A · stationary", "A1 reported at Stand A");
        replay.SelectAircraft(2); replay.Seek(5);
        check(replay.CurrentReasoning.Contains("[W03]") && !replay.CurrentReasoning.Contains("[E01]"), "baseline text uses this scenario's reports");

        replay.Seek(20);
        check(VisualEvidenceCapture.SelectionInvariant(replay, viewpoint), "capture identical for each of the three selections");
        var crop = VisualEvidenceCapture.SceneCrop(replay, viewpoint);
        check(crop.xMin >= 0 && crop.yMin >= 0 && crop.xMax <= 1 && crop.yMax <= 1, "crop lies inside the view");

        var props = replay.Content.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("Visual prop", StringComparison.Ordinal)).ToArray();
        Func<string, bool> shown = id => props.Single(p => p.name.EndsWith(id, StringComparison.Ordinal)).gameObject.activeSelf;
        check(shown("P1") && shown("P2"), "both props visible at 20 s");
        replay.Seek(27); check(!shown("P1") && shown("P2"), "fuel vehicle gone, hatch open at 27 s");
        replay.Seek(33); check(!shown("P1") && !shown("P2"), "both props gone at 33 s");

        // Validation: more than four aircraft, or an unknown livery, is rejected.
        var json = Resources.Load<TextAsset>("visual_dev_02").text;
        Func<Action<Scenario>, bool> rejects = edit => {
            var s = JsonUtility.FromJson<Scenario>(json); edit(s);
            try { s.Validate(); return false; } catch (ArgumentException) { return true; }
        };
        check(rejects(s => s.aircraft = Enumerable.Range(0, Scenario.MaxAircraft + 1).Select(i => new AircraftPlan {
            id = "X" + i, flightInstance = "FX" + i, waypoints = s.aircraft[0].waypoints }).ToArray()), "five aircraft rejected");
        check(rejects(s => s.livery = "striped"), "unknown livery rejected");
        check(!rejects(s => { }), "scenario itself validates");

        Debug.Log("MULTI_AIRCRAFT_CHECKS_PASS: 14");
    }

    // Pixels each prop changes in the evidence image at 24 s (both props present), as a
    // count and a share of the frame. Hiding one prop at a time isolates its footprint.
    public static void MeasurePropCoverage() {
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var boot = new GameObject("Prop coverage measurement").AddComponent<SceneBootstrap>();
        boot.previewMode = true; boot.scenarioResource = "visual_dev_01"; boot.Initialize();
        boot.Replay.Seek(24);
        Debug.Log("VISUAL_PROP_COVERAGE: crop " + VisualEvidenceCapture.SceneCrop(boot.Replay, Camera.main) + "; " + string.Join(", ", PropCoverage(boot.Replay, Camera.main)
            .Select(c => c.Key + "=" + c.Value + "px (" + (100f * c.Value / FramePixels(boot.Replay, Camera.main)).ToString("0.00") + "%)")));
    }

    static Dictionary<string, int> PropCoverage(StandReplay replay, Camera viewpoint) {
        var props = replay.Content.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("Visual prop", StringComparison.Ordinal)).ToArray();
        var all = Pixels(VisualEvidenceCapture.Capture(replay, viewpoint, null).png);
        var result = new Dictionary<string, int>();
        foreach (var p in props) {
            p.gameObject.SetActive(false);
            var without = Pixels(VisualEvidenceCapture.Capture(replay, viewpoint, null).png);
            p.gameObject.SetActive(true);
            result[p.name.Substring("Visual prop ".Length)] = all.Zip(without, (a, b) => !a.Equals(b)).Count(d => d);
        }
        return result;
    }

    static int FramePixels(StandReplay replay, Camera viewpoint) {
        var evidence = VisualEvidenceCapture.Capture(replay, viewpoint, null);
        return evidence.width * evidence.height;
    }

    static Color32[] Pixels(byte[] png) {
        var texture = new Texture2D(2, 2); texture.LoadImage(png);
        var pixels = texture.GetPixels32();
        UnityEngine.Object.DestroyImmediate(texture);
        return pixels;
    }

    // Writes sample evidence images to work/ for human inspection of prop legibility.
    public static void SaveObservationSamples() {
        var output = System.IO.Path.GetFullPath(System.IO.Path.Combine(Application.dataPath, "../../../work"));
        System.IO.Directory.CreateDirectory(output);
        var samples = new[] { ("visual_dev_01", "visual-observation-", new[] { 24f, 29f, 31f }),
                              ("visual_dev_02", "visual-observation-dev02-", new[] { 20f, 27f, 33f }) };
        foreach (var (scenario, prefix, times) in samples) {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var boot = new GameObject("Visual observation samples").AddComponent<SceneBootstrap>();
            boot.previewMode = true; boot.scenarioResource = scenario; boot.Initialize();
            foreach (var t in times) {
                boot.Replay.Seek(t);
                System.IO.File.WriteAllBytes(System.IO.Path.Combine(output, prefix + t + "s.png"),
                    VisualEvidenceCapture.Capture(boot.Replay, Camera.main, null).png);
            }
        }
        Debug.Log("VISUAL_OBSERVATION_SAMPLES_WRITTEN: " + output);
    }
}
