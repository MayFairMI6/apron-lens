using System;
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using SurfaceSafety;

// Conversation client checks without a network: request contents, local response checks,
// revision tracking and the question overlay (visual_dev_02, A2 / F2-R1 at Stand B).
//   Unity -batchmode -quit -projectPath <project> -executeMethod ConversationClientVerification.Run -logFile <log>
public static class ConversationClientVerification {
    public static void Run() {
        Action<bool, string> check = (ok, message) => { if (!ok) throw new Exception("Conversation client check failed: " + message); };
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var boot = new GameObject("Conversation client regression").AddComponent<SceneBootstrap>();
        boot.previewMode = true; boot.scenarioResource = "visual_dev_02"; boot.Initialize();
        var replay = boot.Replay; var client = boot.GetComponent<ConversationClient>();
        check(client != null, "client bound by the scene bootstrap");
        replay.SelectAircraft(1); replay.Seek(20);

        // 1. The request carries the flight instance, the replay time and a live capture.
        var request = client.BuildRequest("  Is the fuel vehicle at this one?  ");
        var image = new Texture2D(2, 2); image.LoadImage(Convert.FromBase64String(request.imageBase64));
        check(request.aircraftId == "A2" && request.flightInstance == "F2-R1" && Mathf.Approximately(request.checkpoint, 20) &&
              Mathf.Approximately(request.imageCaptureTime, 20) && request.expectedRevision == 0 && request.sessionId == client.SessionId &&
              request.question == "Is the fuel vehicle at this one?" && image.width == 672 && request.tapViewport.Length == 0,
              "request fields, trimmed question and a 672 px capture");
        UnityEngine.Object.DestroyImmediate(image);
        var json = JsonUtility.ToJson(request);
        check(json.Contains("\"flightInstance\":\"F2-R1\"") && json.Contains("\"mode\":\"development\"") && json.Contains("\"tapViewport\":[]"),
              "JSON carries the flight instance and an empty tap, which the server reads as no tap");

        Func<ConversationRequest, string, bool, SupportedClaim[], ConversationResponse> response = (req, id, accepted, claims) =>
            new ConversationResponse { requestId = id, sessionId = req.sessionId, cutoff = req.checkpoint, accepted = accepted, revision = client.Revision + 1,
                referent = new FlightRef { aircraftId = "A2", flightInstance = "F2-R1" }, currentReferent = new FlightRef { aircraftId = "A2", flightInstance = "F2-R1" },
                display = new ConversationDisplay { resultStatus = accepted ? "answer" : "withheld", answer = "Assigned stand: B [W02]", claims = claims } };
        var stand = new[] { new SupportedClaim { fact_id = "W02:stand", value = "B", status = "current", evidence_ids = new[] { "W02" } } };

        // 2. A supported answer is shown and the revision advances.
        check(client.ApplyResponse(request, response(request, request.requestId, true, stand)) && client.Status == "CHECKED ANSWER" && client.Revision == 1,
              "supported answer accepted; revision 1");
        // 3. A claim citing a report not yet received (W05 arrives at 38 s) is withheld; the turn still counts.
        var late = new[] { new SupportedClaim { fact_id = "W05:baggage_status", value = "complete", status = "current", evidence_ids = new[] { "W05" } } };
        request = client.BuildRequest("Is baggage complete?");
        check(!client.ApplyResponse(request, response(request, request.requestId, true, late)) && client.Status == "ANSWER WITHHELD" && client.Revision == 2,
              "claim citing an unreceived report withheld; revision 2");
        // 4. A response for another request is discarded without changing the revision.
        request = client.BuildRequest("Which stand?");
        check(!client.ApplyResponse(request, response(request, "other-request", true, stand)) && client.Status == "CONTEXT CHANGED" && client.Revision == 2,
              "response for another request discarded");
        // 5. A server-withheld answer is shown as withheld.
        check(!client.ApplyResponse(request, response(request, request.requestId, false, new SupportedClaim[0])) && client.Status == "ANSWER WITHHELD" && client.Revision == 3,
              "server-withheld answer shown as withheld");
        // 6. Seeking after asking discards the answer.
        request = client.BuildRequest("Which stand?"); replay.Seek(21);
        check(!client.ApplyResponse(request, response(request, request.requestId, true, stand)) && client.Status == "CONTEXT CHANGED",
              "answer discarded after the replay time changed");
        // 7. A new session resets the revision.
        var old = client.SessionId; client.NewSession();
        check(client.SessionId != old && client.Revision == 0, "new session resets the revision");

        // 8. Connection settings saved in More -> Model connection apply without a restart, on port 8766.
        string[] keys = { "qwen_endpoint", "qwen_token", "conversation_endpoint" };
        var saved = keys.Select(k => PlayerPrefs.HasKey(k) ? PlayerPrefs.GetString(k) : null).ToArray();
        try {
            PlayerPrefs.SetString("qwen_endpoint", "http://192.168.1.20:8765"); PlayerPrefs.DeleteKey("conversation_endpoint");
            client.LoadConnection();
            check(client.Endpoint == "http://192.168.1.20:8766", "conversation endpoint follows the Model connection host (" + client.Endpoint + ")");
            PlayerPrefs.SetString("conversation_endpoint", "http://10.0.0.5:9000/");
            client.LoadConnection();
            check(client.Endpoint == "http://10.0.0.5:9000", "an explicit conversation endpoint wins");
        } finally {
            for (int i = 0; i < keys.Length; i++) { if (saved[i] == null) PlayerPrefs.DeleteKey(keys[i]); else PlayerPrefs.SetString(keys[i], saved[i]); }
            PlayerPrefs.Save();
        }

        // 9. More -> Ask a question opens one question field; Close removes the overlay.
        Click("More"); Click("Ask a question");
        check(UnityEngine.Object.FindObjectsByType<InputField>(FindObjectsSortMode.None).Length == 1 && GameObject.Find("Conversation") != null,
              "question overlay opens with one field");
        Click("Close");
        check(GameObject.Find("Conversation") == null, "Close removes the overlay");

        Debug.Log("CONVERSATION_CLIENT_CHECKS_PASS: 11");
    }

    // Optional live check against a running service (not part of the standard suite):
    //   python -m backend.conversation.server --profile apronlens-v2-mps
    // Sends one real request built by the client and applies the real response, so the
    // JSON that Unity writes and reads is checked against the server end to end.
    // AR pointing and tracking interruptions (docs/AR_SCOPE.md, M1):
    //   Unity -batchmode -quit -projectPath <project> -executeMethod ConversationClientVerification.RunArContext -logFile <log>
    public static void RunArContext() {
        Action<bool, string> check = (ok, message) => { if (!ok) throw new Exception("AR context check failed: " + message); };
        Func<string, SceneBootstrap> boot = scenario => {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var b = new GameObject("AR context " + scenario).AddComponent<SceneBootstrap>();
            b.previewMode = true; b.scenarioResource = scenario; b.Initialize(); return b;
        };

        // 1. Pointing: a tap on an aircraft in the AR view selects it, and the request names it.
        var pointing = boot("visual_dev_02"); var replay = pointing.Replay; var client = pointing.GetComponent<ConversationClient>();
        replay.SelectAircraft(0); replay.Seek(20);
        var a3 = Camera.main.WorldToScreenPoint(replay.Content.Find("A3").position);
        check(replay.TapSelect(new Vector2(a3.x, a3.y), Camera.main) && replay.SelectedAircraftIndex == 2, "a tap on A3 selects it");
        check(client.BuildRequest("Where is this one heading?").aircraftId == "A3", "the request names the tapped aircraft");
        check(!replay.TapSelect(new Vector2(2, 2), Camera.main) && replay.SelectedAircraftIndex == 2, "a tap on empty board changes nothing");

        // 2. A scenario that pauses (the default): no time passes out of view, so no interruption is recorded,
        //    even after playback resumes and later reports arrive while the user watches.
        replay.Clock.Play(); replay.Tracking(false); replay.Clock.Advance(10); replay.Tracking(true);
        check(Mathf.Approximately(replay.Clock.Time, 20), "the default clock pauses while the board is out of view");
        replay.Clock.Play(); replay.Clock.Advance(10);
        check(!replay.InterruptedAt.HasValue && client.BuildRequest("Anything new?").awayIntervals.Length == 0,
              "no away interval from a paused clock, even after playback resumes");

        // 3. A running clock: reports keep arriving out of view, and the next request carries the interval.
        var running = boot("visual_dev_03"); replay = running.Replay; client = running.GetComponent<ConversationClient>();
        replay.SelectAircraft(1); replay.Seek(20); replay.Clock.Play();
        replay.Tracking(false); replay.Clock.Advance(6); replay.Tracking(false); replay.Clock.Advance(4); replay.Tracking(true);
        var request = client.BuildRequest("I was looking away. Is it done now?");
        check(replay.Data.ClockRunsUntracked && Mathf.Approximately(request.checkpoint, 30), "the clock ran 10 s out of view");
        check(request.awayIntervals.Length == 2 && Mathf.Approximately(request.awayIntervals[0], 20) && Mathf.Approximately(request.awayIntervals[1], 30)
              && JsonUtility.ToJson(request).Contains("\"awayIntervals\":[20.0,30.0]"), "one interval, 20 to 30 s");
        var response = new ConversationResponse { requestId = request.requestId, sessionId = request.sessionId, cutoff = request.checkpoint,
            accepted = true, revision = 1, display = new ConversationDisplay { resultStatus = "answer", answer = "", claims = new SupportedClaim[0] } };
        // A second loss after the request was built must survive the first request's response.
        replay.Clock.Play(); replay.Tracking(false); replay.Clock.Advance(5); replay.Tracking(true);
        client.ApplyResponse(request, response);
        var next = client.BuildRequest("And now?");
        check(next.awayIntervals.Length == 2 && Mathf.Approximately(next.awayIntervals[0], 30) && Mathf.Approximately(next.awayIntervals[1], 35),
              "a committed turn clears only the interruption it carried");
        client.ApplyResponse(next, new ConversationResponse { requestId = next.requestId, sessionId = next.sessionId, cutoff = next.checkpoint,
            accepted = true, revision = 2, display = new ConversationDisplay { resultStatus = "answer", answer = "", claims = new SupportedClaim[0] } });
        check(client.BuildRequest("And after that?").awayIntervals.Length == 0, "nothing left once every interruption was sent");

        // 4. Two separate losses, 20-25 s and 35-38 s, then a question at 45 s: the watched time between them stays out.
        replay.Seek(20); replay.Clock.Play(); replay.Tracking(false); replay.Clock.Advance(5); replay.Tracking(true);
        replay.Clock.Play(); replay.Clock.Advance(10); replay.Tracking(false); replay.Clock.Advance(3); replay.Tracking(true);
        replay.Clock.Play(); replay.Clock.Advance(7);
        var watched = client.BuildRequest("Anything new?");
        check(watched.awayIntervals.Length == 4 && Mathf.Approximately(watched.awayIntervals[1], 25) && Mathf.Approximately(watched.awayIntervals[2], 35)
              && Mathf.Approximately(watched.awayIntervals[3], 38) && Mathf.Approximately(watched.checkpoint, 45), "two intervals, 20-25 and 35-38 s");
        replay.Seek(10);  // discard it before the next case

        // 4b. Many losses: flicker (under a second of watching) is one loss, and no more than the server's limit is sent.
        replay.Seek(5); replay.Clock.Play();
        for (int k = 0; k < 3; k++) { replay.Tracking(false); replay.Clock.Advance(1); replay.Tracking(true); replay.Clock.Play(); replay.Clock.Advance(.5f); }
        var flicker = client.BuildRequest("Anything new?");
        check(flicker.awayIntervals.Length == 2 && Mathf.Approximately(flicker.awayIntervals[0], 5) && Mathf.Approximately(flicker.awayIntervals[1], 9),
              "three flickering losses are one interval, 5 to 9 s");
        replay.Seek(1); replay.Clock.Play();
        for (int k = 0; k < 25; k++) { replay.Tracking(false); replay.Clock.Advance(1); replay.Tracking(true); replay.Clock.Play(); replay.Clock.Advance(1.5f + (k % 3)); }
        var many = client.BuildRequest("Anything new?");
        check(many.awayIntervals.Length == 2 * StandReplay.MaxAwayIntervals && Mathf.Approximately(many.awayIntervals[0], 1),
              "25 losses are sent as at most the server's limit, starting at the first loss");
        replay.Seek(0);

        // 5. Paused by hand in a running scenario: a loss during which no replay time passed hides nothing.
        replay.Seek(20); replay.Clock.Pause(); replay.Tracking(false); replay.Tracking(true);
        replay.Clock.Play(); replay.Clock.Advance(10);
        check(client.BuildRequest("Anything new?").awayIntervals.Length == 0, "a loss with no replay time passing is discarded");

        // 6. Restarting or seeking backward starts a new timeline: an unreported loss from the old one is discarded.
        replay.Seek(20); replay.Clock.Play(); replay.Tracking(false); replay.Clock.Advance(10); replay.Tracking(true);
        replay.Restart(); replay.Clock.Play(); replay.Clock.Advance(25);
        check(client.BuildRequest("Anything new?").awayIntervals.Length == 0, "a restart discards the earlier loss");
        replay.Clock.Play(); replay.Tracking(false); replay.Clock.Advance(10); replay.Tracking(true); replay.Seek(10);
        check(client.BuildRequest("Anything new?").awayIntervals.Length == 0, "a backward seek discards the earlier loss");
        // 7. "While you were away": looking away from 25 to 50 s in the demo scenario lists the three reports received
        //    meanwhile (32, 36 and 48 s), not the one at 52 s; a tap dismisses it.
        var demo = boot("ar_demo_01"); replay = demo.Replay;
        replay.Seek(25); replay.Clock.Play(); replay.Tracking(false); replay.Clock.Advance(25); replay.Tracking(true);
        var notice = replay.AwayNotice;
        check(notice != null && notice.Length == 3 && notice[0].Contains("[D05]") && notice[1].Contains("[D06]") && notice[2].Contains("[D07]")
              && replay.AwayNoticeSpan == "25–50 s", "the notice lists the reports received while away");
        // A flicker before the card is dismissed adds to it rather than replacing it.
        replay.Tracking(false); replay.Clock.Advance(1); replay.Tracking(true);
        check(replay.AwayNotice.Length == 3 && replay.AwayNotice[0].Contains("[D05]") && replay.AwayNoticeSpan == "25–51 s",
              "an undismissed card keeps its reports through a later empty gap");
        replay.DismissAwayNotice();
        check(replay.AwayNotice == null, "a tap dismisses the notice");
        replay.Tracking(false); replay.Clock.Advance(2); replay.Tracking(true);
        check(replay.AwayNotice != null && replay.AwayNotice.Length == 1 && replay.AwayNotice[0].Contains("[D08]"),
              "after a dismissal, a later look-away gets its own card");
        Debug.Log("AR_CONTEXT_CHECKS_PASSED");
    }

    public static void RunLive() {
        Action<bool, string> check = (ok, message) => { if (!ok) throw new Exception("Live conversation check failed: " + message); };
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var boot = new GameObject("Live conversation check").AddComponent<SceneBootstrap>();
        boot.previewMode = true; boot.scenarioResource = "visual_dev_02"; boot.Initialize();
        var replay = boot.Replay; var client = boot.GetComponent<ConversationClient>();
        replay.SelectAircraft(1); replay.Seek(20);
        var token = System.IO.File.ReadAllText(System.IO.Path.GetFullPath(System.IO.Path.Combine(Application.dataPath, "../../../work/qwen-server-token.txt"))).Trim();
        var request = client.BuildRequest("Which stand is this aircraft assigned to?");
        using var web = new UnityEngine.Networking.UnityWebRequest("http://127.0.0.1:8766/conversation", "POST");
        web.uploadHandler = new UnityEngine.Networking.UploadHandlerRaw(System.Text.Encoding.UTF8.GetBytes(JsonUtility.ToJson(request)));
        web.downloadHandler = new UnityEngine.Networking.DownloadHandlerBuffer(); web.timeout = 240;
        web.SetRequestHeader("Content-Type", "application/json"); web.SetRequestHeader("Authorization", "Bearer " + token);
        var operation = web.SendWebRequest();
        while (!operation.isDone) System.Threading.Thread.Sleep(100);
        check(web.result == UnityEngine.Networking.UnityWebRequest.Result.Success, $"HTTP {web.responseCode}: {web.downloadHandler.text}");
        var reply = JsonUtility.FromJson<ConversationResponse>(web.downloadHandler.text);
        check(reply.requestId == request.requestId && reply.sessionId == request.sessionId && reply.revision == 1, "response matches the request and commits revision 1");
        var shown = client.ApplyResponse(request, reply);
        check(client.Revision == 1, "client tracks the committed revision");
        Debug.Log($"CONVERSATION_LIVE_CHECK_PASS: accepted={reply.accepted} shown={shown} status={client.Status} model={reply.returnedModel} " +
                  $"errors={string.Join(",", reply.errors ?? new string[0])} answer={reply.display?.answer?.Replace('\n', ' ')}");
    }

    static void Click(string name) {
        var button = UnityEngine.Object.FindObjectsByType<Button>(FindObjectsSortMode.None).FirstOrDefault(b => b.gameObject.name == name);
        if (button == null) throw new Exception("Conversation client check failed: no button " + name);
        button.onClick.Invoke();
    }
}
