using System;
using System.IO;
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;
using SurfaceSafety;

// Exercise the coordinator's cross-view evidence and replay contract.
public static class CoordinatorUiVerification {
    public static void Run() {
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var host = new GameObject("Coordinator UI verification");
        var bootstrap = host.AddComponent<SceneBootstrap>();
        bootstrap.previewMode = true;
        bootstrap.Initialize();
        var replay = bootstrap.Replay;
        int checks = 0;
        Action<bool, string> check = (passed, message) => {
            if (!passed) throw new Exception("COORDINATOR UI CHECK FAILED: " + message);
            checks++;
        };

        replay.SelectAircraft(1);
        replay.Seek(13);
        replay.SelectTab("history");
        check(replay.VisibleReports.All(e => e.flightInstance == "F2-R1"), "Selected-flight scope");
        check(!replay.VisibleReports.Any(e => e.id == "E03"), "Late report hidden before receipt");
        replay.InspectReport("E03");
        check(replay.InspectedReportId != "E03", "Unavailable evidence cannot open");
        replay.Seek(14);
        check(replay.VisibleReports.Any(e => e.id == "E03"), "Late report appears at receipt");
        replay.InspectReport("E03");
        check(replay.InspectedReportId == "E03", "Eligible evidence can open");
        replay.SelectTab("why");
        check(replay.CurrentReasoning.Contains("E03"), "Explanation links received evidence");
        replay.Seek(13);
        check(replay.InspectedReportId != "E03", "Rewind closes future evidence");
        check(!replay.CurrentReasoning.Contains("E03"), "Rewind removes future explanation evidence");
        replay.SelectTab("history");
        replay.InspectReport("E01");
        check(replay.InspectedReportId != "E01", "Wrong-flight report is blocked in selected-flight scope");
        replay.SetHistoryScope(true);
        check(replay.VisibleReports.Any(e => e.flightInstance == "F1-R1") &&
              replay.VisibleReports.Any(e => e.flightInstance == "F2-R1"), "Explicit all-flight scope");
        replay.InspectReport("E01");
        check(replay.InspectedReportId == "E01", "All-flight scope allows other identity evidence");
        replay.SetHistoryScope(false);
        replay.SelectAircraft(0);
        check(replay.VisibleReports.All(e => e.flightInstance == "F1-R1"), "Switching aircraft updates evidence scope");

        replay.Play();
        float timeBeforeNavigation = replay.Clock.Time;
        replay.SelectTab("now");
        replay.SelectTab("why");
        check(replay.Clock.Playing && replay.Clock.Time == timeBeforeNavigation, "Navigation preserves replay state");
        replay.SelectAircraft(1);
        replay.Seek(20);
        replay.Play();
        replay.SeekToReportReceipt("E03");
        check(replay.Clock.Time == 14 && !replay.Clock.Playing, "Evidence jump uses receipt time and pauses");
        replay.Tracking(false);
        replay.Play();
        check(!replay.Clock.Playing && !replay.Content.gameObject.activeSelf, "Tracking loss gates playback and hides scene");
        replay.Tracking(true);
        check(!replay.Clock.Playing, "Tracking recovery requires explicit resume");

        var output = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../outputs/milestone1"));
        Directory.CreateDirectory(output);
        File.WriteAllText(Path.Combine(output, "ui-verification.json"),
            "{\"status\":\"passed\",\"checks\":" + checks +
            ",\"scope\":\"Coordinator UI navigation, flight identity, evidence availability, receipt-time replay and tracking gating; physical touch and tracking untested\"}");
        Debug.Log("COORDINATOR_UI_CHECKS_PASS: " + checks);
    }
}
