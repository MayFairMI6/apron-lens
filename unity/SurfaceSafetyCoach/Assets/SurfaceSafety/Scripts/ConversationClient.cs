using System;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

namespace SurfaceSafety {
    // Client for the conversational service (backend/conversation/server.py, POST /conversation).
    // The frozen /reason path and QwenReasoningClient are unchanged.
    //
    // Each question carries the selected aircraft and its flight instance, the replay time,
    // and a live evidence image (VisualEvidenceCapture) captured at that time. One session
    // per scenario: the server keeps the conversation memory; this client keeps the session
    // ID and the revision of the last committed turn. A 409 (stale revision or conflict)
    // starts a new session. A failed connection keeps the request so Retry reuses its ID.
    //
    // Local checks before anything is shown, as for /reason: the response must belong to this
    // request, session and replay time, the selection and time must not have changed, and every
    // accepted claim must cite a report received by then for the referent flight.
    [Serializable] public class ConversationRequest {
        public string requestId, turnId, sessionId, mode = "development", scenarioId, aircraftId, flightInstance, question, imageBase64;
        public float checkpoint, imageCaptureTime;
        public int expectedRevision;
        public float[] tapViewport; // JsonUtility writes [] when unset; the server reads [] as "no tap"
    }
    [Serializable] public class FlightRef { public string aircraftId, flightInstance; }
    [Serializable] public class InterpretationDisplay { public string label, text; }
    [Serializable] public class ConversationDisplay {
        public string resultStatus, answer, validation;
        public SupportedClaim[] claims;
        public string[] unknowns;
        public InterpretationDisplay interpretation;
    }
    [Serializable] public class ConversationResponse {
        public string requestId, turnId, sessionId, returnedModel;
        public float cutoff, latencySeconds;
        public bool accepted;
        public string[] errors, changes;
        public ConversationDisplay display;
        public FlightRef referent, currentReferent;
        public int revision;
    }

    public class ConversationClient : MonoBehaviour {
        StandReplay replay;
        public const int ServicePort = 8766;
        string endpoint = "http://127.0.0.1:8766", token = "";
        public string Endpoint => endpoint;
        UnityWebRequest active;
        GameObject panel;
        Text answerText;
        public string SessionId { get; private set; }
        public int Revision { get; private set; }
        public ConversationRequest Pending { get; private set; }
        public ConversationResponse LastResponse { get; private set; }
        public string Status { get; private set; } = "";
        public bool Busy => active != null;

        public void Bind(StandReplay target) {
            replay = target;
            LoadConnection();
            replay.OpenConversation += ShowPanel;
            NewSession();
        }
        void OnDestroy() { Cancel(); if (replay != null) replay.OpenConversation -= ShowPanel; }

        // Read the shared connection settings each time, so a change saved in More -> Model connection
        // applies without a restart. The service runs on the same host as /reason, on its own port,
        // unless "conversation_endpoint" names another address.
        public void LoadConnection() {
            var explicitEndpoint = PlayerPrefs.GetString("conversation_endpoint", "");
            if (!string.IsNullOrWhiteSpace(explicitEndpoint)) endpoint = explicitEndpoint.Trim().TrimEnd('/');
            else if (Uri.TryCreate(PlayerPrefs.GetString("qwen_endpoint", ""), UriKind.Absolute, out var reason))
                endpoint = new UriBuilder(reason.Scheme, reason.Host, ServicePort).Uri.ToString().TrimEnd('/');
            token = PlayerPrefs.GetString("qwen_token", "");
#if UNITY_EDITOR
            var path = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../work/qwen-server-token.txt"));
            if (File.Exists(path)) token = File.ReadAllText(path).Trim();
#endif
        }

        public void NewSession() { SessionId = Guid.NewGuid().ToString("N"); Revision = 0; Pending = null; LastResponse = null; }

        public ConversationRequest BuildRequest(string question, Vector2? tapScreen = null) {
            var a = replay.Data.aircraft[replay.SelectedAircraftIndex];
            var evidence = VisualEvidenceCapture.Capture(replay, Camera.main, tapScreen);
            var id = Guid.NewGuid().ToString("N");
            return new ConversationRequest {
                requestId = id, turnId = id, sessionId = SessionId, scenarioId = replay.Data.scenarioId,
                aircraftId = a.id, flightInstance = a.flightInstance, checkpoint = replay.Clock.Time,
                expectedRevision = Revision, question = question.Trim(),
                imageBase64 = Convert.ToBase64String(evidence.png), imageCaptureTime = replay.Clock.Time,
                tapViewport = float.IsNaN(evidence.tapViewport.x) ? new float[0] : new[] { evidence.tapViewport.x, evidence.tapViewport.y } };
        }

        bool SameContext(ConversationRequest request) =>
            replay.Data.aircraft[replay.SelectedAircraftIndex].id == request.aircraftId &&
            Mathf.Abs(replay.Clock.Time - request.checkpoint) < .001f && replay.Data.scenarioId == request.scenarioId;

        // Returns true when the response is shown. Updates the revision for every committed turn.
        public bool ApplyResponse(ConversationRequest request, ConversationResponse response) {
            if (response == null || response.requestId != request.requestId || response.sessionId != request.sessionId ||
                Mathf.Abs(response.cutoff - request.checkpoint) > .001f) {
                return Show("CONTEXT CHANGED", "This answer belongs to a different question. Ask again.");
            }
            Revision = Mathf.Max(Revision, response.revision);  // the turn is committed on the server either way
            if (!SameContext(request)) return Show("CONTEXT CHANGED", "The selection or replay time changed. Ask again for this checkpoint.");
            var display = response.display ?? new ConversationDisplay();
            if (response.accepted && !ClaimsSupported(request, response))
                return Show("ANSWER WITHHELD", "A claim did not match a report received for this flight.");
            LastResponse = response;
            var body = string.IsNullOrEmpty(display.answer) ? "No answer text." : display.answer;
            if (display.interpretation != null && !string.IsNullOrEmpty(display.interpretation.text))
                body += $"\n\n{display.interpretation.label}: {display.interpretation.text}";
            var who = response.currentReferent != null && !string.IsNullOrEmpty(response.currentReferent.aircraftId)
                ? $"{response.currentReferent.aircraftId} / {response.currentReferent.flightInstance}" : request.aircraftId;
            body += $"\n\nAbout {who} · as of {request.checkpoint:00.0}s · {response.latencySeconds:0.0}s";
            Show(response.accepted ? "CHECKED ANSWER" : "ANSWER WITHHELD", body);
            return response.accepted;
        }

        bool ClaimsSupported(ConversationRequest request, ConversationResponse response) {
            var r = response.referent;
            if (r == null || string.IsNullOrEmpty(r.aircraftId)) return response.display?.claims == null || response.display.claims.Length == 0;
            var aircraft = replay.Data.aircraft.FirstOrDefault(a => a.id == r.aircraftId && a.flightInstance == r.flightInstance);
            if (aircraft == null) return false;
            var received = replay.Data.KnownAt(request.checkpoint).Where(e => e.flightInstance == r.flightInstance && e.aircraftId == r.aircraftId).ToArray();
            return (response.display?.claims ?? new SupportedClaim[0]).All(claim =>
                claim != null && claim.evidence_ids != null && claim.evidence_ids.Length == 1 &&
                received.Any(e => e.id == claim.evidence_ids[0] && e.facts != null &&
                                  e.facts.Any(f => claim.fact_id == e.id + ":" + f.property && claim.value == f.value)));
        }

        public void Ask(string question) {
            if (Busy || string.IsNullOrWhiteSpace(question)) return;
            if (!replay.Clock.Tracked) { Show("SCENE UNAVAILABLE", "Acquire the printed board before asking."); return; }
            LoadConnection();
            if (!Uri.TryCreate(endpoint, UriKind.Absolute, out var uri) || (uri.Scheme != "http" && uri.Scheme != "https") || string.IsNullOrWhiteSpace(token)) {
                Show("CONNECTION NEEDED", $"Open More → Model connection and enter the Mac address and token. Questions go to the same host on port {ServicePort}."); return;
            }
            replay.Pause();
            Send(BuildRequest(question));
        }

        public void Retry() { if (!Busy && Pending != null && SameContext(Pending)) { LoadConnection(); Send(Pending); } }

        void Send(ConversationRequest request) {
            Pending = request;
            Show("ASKING", $"About {request.aircraftId} at {request.checkpoint:00.0}s. Replay paused so the answer stays tied to this time.");
            active = new UnityWebRequest(endpoint + "/conversation", "POST");
            active.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(JsonUtility.ToJson(request)));
            active.downloadHandler = new DownloadHandlerBuffer(); active.timeout = 240;
            active.SetRequestHeader("Content-Type", "application/json"); active.SetRequestHeader("Authorization", "Bearer " + token);
            var web = active;
            web.SendWebRequest().completed += _ => {
                if (active != web) return;
                try {
                    if (web.responseCode == 409) {
                        NewSession(); Show("SESSION RESTARTED", "The conversation was out of step with the service. A new session started; ask again.");
                    } else if (web.result != UnityWebRequest.Result.Success) {
                        Show("UNAVAILABLE", $"Connection failed ({web.responseCode}). Check the service, then Retry.");
                        return;  // keep Pending so Retry reuses the request ID
                    } else ApplyResponse(request, JsonUtility.FromJson<ConversationResponse>(web.downloadHandler.text));
                    Pending = null;
                } catch (Exception) { Show("UNAVAILABLE", "Could not read the service response."); }
                finally { active = null; web.Dispose(); }
            };
        }

        void Cancel() { if (active != null) { var web = active; active = null; web.Abort(); web.Dispose(); } }

        bool Show(string status, string text) {
            Status = status;
            if (answerText != null) answerText.text = status + "\n\n" + text;
            return false;
        }

        static void Remove(UnityEngine.Object item) { if (Application.isPlaying) Destroy(item); else DestroyImmediate(item); }
        static RectTransform Box(Transform parent, string name, Vector2 min, Vector2 max, Color color) {
            var g = new GameObject(name, typeof(RectTransform), typeof(Image)); g.transform.SetParent(parent, false);
            var r = g.GetComponent<RectTransform>(); r.anchorMin = min; r.anchorMax = max; r.offsetMin = r.offsetMax = Vector2.zero; g.GetComponent<Image>().color = color; return r;
        }
        static Text TextAt(Transform parent, string value, Vector2 min, Vector2 max, int size, TextAnchor align = TextAnchor.MiddleLeft) {
            var g = new GameObject("Text", typeof(RectTransform), typeof(Text)); g.transform.SetParent(parent, false);
            var r = g.GetComponent<RectTransform>(); r.anchorMin = min; r.anchorMax = max; r.offsetMin = new Vector2(16, 0); r.offsetMax = new Vector2(-16, 0);
            var t = g.GetComponent<Text>(); t.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf"); t.fontSize = size; t.text = value; t.color = Color.white;
            t.alignment = align; t.supportRichText = false; t.raycastTarget = false; t.horizontalOverflow = HorizontalWrapMode.Wrap; t.verticalOverflow = VerticalWrapMode.Truncate; return t;
        }
        static Button ButtonAt(Transform parent, string title, Vector2 min, Vector2 max, Color color, UnityEngine.Events.UnityAction action) {
            var r = Box(parent, title, min, max, color); TextAt(r, title, Vector2.zero, Vector2.one, 36, TextAnchor.MiddleCenter);
            var b = r.gameObject.AddComponent<Button>(); b.onClick.AddListener(action); return b;
        }

        public void ShowPanel() {
            if (panel != null) return;
            var canvas = new GameObject("Conversation", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster)); panel = canvas;
            var c = canvas.GetComponent<Canvas>(); c.renderMode = RenderMode.ScreenSpaceOverlay; c.sortingOrder = 50;
            var scaler = canvas.GetComponent<CanvasScaler>(); scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize; scaler.referenceResolution = new Vector2(1080, 1920); scaler.matchWidthOrHeight = .5f;
            var shade = Box(canvas.transform, "Dim", Vector2.zero, Vector2.one, new Color(0, 0, 0, .8f));
            var card = Box(shade, "Ask", new Vector2(.05f, .1f), new Vector2(.95f, .9f), new Color(.035f, .075f, .11f));
            TextAt(card, "Ask about the selected aircraft", new Vector2(.04f, .9f), new Vector2(.96f, .98f), 40);
            var field = Box(card, "Question field", new Vector2(.04f, .78f), new Vector2(.96f, .89f), new Color(.13f, .2f, .26f));
            var input = field.gameObject.AddComponent<InputField>(); input.textComponent = TextAt(field, "", Vector2.zero, Vector2.one, 36);
            input.characterLimit = 400;
            answerText = TextAt(card, Status == "" ? "Answers use only reports received by this replay time. Visual observations are labelled as unverified." : Status,
                                new Vector2(.04f, .18f), new Vector2(.96f, .76f), 33, TextAnchor.UpperLeft);
            ButtonAt(card, "Ask", new Vector2(.04f, .04f), new Vector2(.36f, .15f), new Color(.05f, .48f, .48f), () => Ask(input.text));
            ButtonAt(card, "Retry", new Vector2(.38f, .04f), new Vector2(.62f, .15f), new Color(.13f, .2f, .26f), Retry);
            ButtonAt(card, "Close", new Vector2(.64f, .04f), new Vector2(.96f, .15f), new Color(.13f, .2f, .26f), () => { Remove(panel); panel = null; answerText = null; });
        }
    }
}
