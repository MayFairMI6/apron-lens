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

        // 8. More -> Ask a question opens one question field; Close removes the overlay.
        Click("More"); Click("Ask a question");
        check(UnityEngine.Object.FindObjectsByType<InputField>(FindObjectsSortMode.None).Length == 1 && GameObject.Find("Conversation") != null,
              "question overlay opens with one field");
        Click("Close");
        check(GameObject.Find("Conversation") == null, "Close removes the overlay");

        Debug.Log("CONVERSATION_CLIENT_CHECKS_PASS: 9");
    }

    // Optional live check against a running service (not part of the standard suite):
    //   python -m backend.conversation.server --profile apronlens-v2-mps
    // Sends one real request built by the client and applies the real response, so the
    // JSON that Unity writes and reads is checked against the server end to end.
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
