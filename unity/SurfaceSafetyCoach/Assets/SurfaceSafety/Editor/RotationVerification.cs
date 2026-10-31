using System;
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using SurfaceSafety;

// Aircraft with several rotations (visual_dev_03: A2 flies F2-R1 until 45 s, then F2-R2).
//   Unity -batchmode -quit -projectPath <project> -executeMethod RotationVerification.Run -logFile <log>
public static class RotationVerification {
    public static void Run() {
        Action<bool, string> check = (ok, message) => { if (!ok) throw new Exception("Rotation check failed: " + message); };
        Func<SceneBootstrap, string, bool> chipShows = (b, label) => b.GetComponentsInChildren<Text>(true).Any(t => t.text == label);

        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var m1 = new GameObject("Milestone regression").AddComponent<SceneBootstrap>(); m1.previewMode = true; m1.Initialize();
        check(chipShows(m1, "A1  /  F1-R1") && chipShows(m1, "A2  /  F2-R1"), "single-flight chip labels unchanged");

        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var boot = new GameObject("Rotation regression").AddComponent<SceneBootstrap>();
        boot.previewMode = true; boot.scenarioResource = "visual_dev_03"; boot.Initialize();
        var replay = boot.Replay; var client = boot.GetComponent<ConversationClient>();
        var a2 = replay.Data.aircraft.Single(a => a.id == "A2");
        check(a2.FlightAt(30) == "F2-R1" && a2.FlightAt(45) == "F2-R2" && a2.Flies("F2-R2") && !a2.Flies("F1-R1"), "rotation under way by time");

        replay.SelectAircraft(1); replay.Seek(30);
        check(replay.SelectedFlight == "F2-R1" && chipShows(boot, "A2  /  F2-R1"), "at 30 s the chip and selection show F2-R1");
        check(replay.VisibleReports.All(e => e.flightInstance == "F2-R1") && replay.VisibleReports.Any(e => e.id == "R03"), "history scoped to F2-R1 at 30 s");
        var request = client.BuildRequest("When does this aircraft leave?");
        check(request.flightInstance == "F2-R1", "question at 30 s is about F2-R1");

        // "I mean its next rotation": an answer about F2-R2 is shown if it cites F2-R2 reports received by 30 s.
        Func<string, string, ConversationResponse> answer = (factId, value) => new ConversationResponse {
            requestId = request.requestId, sessionId = request.sessionId, cutoff = 30, accepted = true, revision = 1,
            referent = new FlightRef { aircraftId = "A2", flightInstance = "F2-R2" }, currentReferent = new FlightRef { aircraftId = "A2", flightInstance = "F2-R2" },
            display = new ConversationDisplay { answer = "Target off-block time", claims = new[] {
                new SupportedClaim { fact_id = factId, value = value, status = "current", evidence_ids = new[] { factId.Split(':')[0] } } } } };
        check(client.ApplyResponse(request, answer("R04:tobt", "70 s")), "next-rotation answer citing a received F2-R2 report is shown");
        check(!client.ApplyResponse(request, answer("R05:tobt", "80 s")), "next-rotation answer citing a report received at 36 s is withheld at 30 s");

        // Crossing 45 s with no new report and no movement still rebuilds the panel for F2-R2.
        Func<string, bool> panelShows = text => boot.GetComponentsInChildren<Text>(true).Any(t => t.gameObject.activeInHierarchy && t.text.Contains(text));
        replay.SelectTab("now"); replay.Seek(44);
        check(panelShows("R03") && !panelShows("R05"), "at 44 s the Now card shows F2-R1's latest report");
        replay.Seek(46);
        check(panelShows("R05") && !panelShows("R03"), "at 46 s the Now card shows F2-R2's latest report");

        replay.Seek(50);
        check(replay.SelectedFlight == "F2-R2" && chipShows(boot, "A2  /  F2-R2") && !chipShows(boot, "A2  /  F2-R1"), "at 50 s the chip shows F2-R2");
        check(replay.VisibleReports.All(e => e.flightInstance == "F2-R2") && replay.VisibleReports.Any(e => e.id == "R05"), "history scoped to F2-R2 at 50 s");
        check(client.BuildRequest("And now?").flightInstance == "F2-R2", "question at 50 s is about F2-R2");

        // Validation matches backend/conversation/identity.py.
        var json = Resources.Load<TextAsset>("visual_dev_03").text;
        Func<Action<Scenario>, bool> rejects = edit => {
            var s = JsonUtility.FromJson<Scenario>(json); edit(s);
            try { s.Validate(); return false; } catch (ArgumentException) { return true; }
        };
        check(!rejects(s => { }), "scenario validates");
        check(rejects(s => s.aircraft[1].rotations[1].from = 40), "overlapping rotations rejected");
        check(rejects(s => s.aircraft[1].rotations[1].flightInstance = "F1-R1"), "a flight owned by two aircraft rejected");
        check(rejects(s => s.events[2].aircraftId = "A1"), "a report whose flight is not its aircraft's rejected");

        Debug.Log("ROTATION_CHECKS_PASS: 15");
    }
}
