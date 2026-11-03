using System;
using System.Collections.Generic;
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
        public float[] awayIntervals; // tracking losses since the last committed turn, [start, end, ...]; [] for none
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
        public bool ExternalPresentation {get;set;}
        public bool TrainingQuestionBlocked {get;set;}
        public event Action<string,string> DisplayChanged;
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
        [Serializable] class LocalConnection { public string endpoint, token; }
        public void LoadConnection() {
            var explicitEndpoint = PlayerPrefs.GetString("conversation_endpoint", "");
            if (!string.IsNullOrWhiteSpace(explicitEndpoint)) endpoint = explicitEndpoint.Trim().TrimEnd('/');
            else if (Uri.TryCreate(PlayerPrefs.GetString("qwen_endpoint", ""), UriKind.Absolute, out var reason))
                endpoint = new UriBuilder(reason.Scheme, reason.Host, ServicePort).Uri.ToString().TrimEnd('/');
            token = PlayerPrefs.GetString("qwen_token", "");
#if APRONLENS_SIMULATOR
            // Installed privately into this simulator by configure_ios_assistant.py; never bundled.
            var configPath = Path.Combine(Application.persistentDataPath, "assistant-connection.json");
            if (File.Exists(configPath)) {
                try {
                    var config = JsonUtility.FromJson<LocalConnection>(File.ReadAllText(configPath));
                    if (config != null) { endpoint = config.endpoint; token = config.token; }
                } catch (Exception) { token = ""; }
            }
#endif
#if UNITY_EDITOR
            if(replay!=null && replay.LiveTraffic && string.IsNullOrWhiteSpace(explicitEndpoint))
                endpoint=new UriBuilder(endpoint){Port=8767}.Uri.ToString().TrimEnd('/');
            var path = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../work/qwen-server-token.txt"));
            if (File.Exists(path)) token = File.ReadAllText(path).Trim();
#endif
        }

        public UnityWebRequest TrafficRequest(){
            LoadConnection();
            var request=UnityWebRequest.Get(endpoint+"/traffic");request.timeout=5;
            request.SetRequestHeader("Authorization","Bearer "+token);return request;
        }
        public UnityWebRequest TrainingActionRequest(string json){
            LoadConnection();
            var request=new UnityWebRequest(endpoint+"/training/action","POST");
            request.uploadHandler=new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
            request.downloadHandler=new DownloadHandlerBuffer();request.timeout=8;
            request.SetRequestHeader("Content-Type","application/json");
            request.SetRequestHeader("Authorization","Bearer "+token);return request;
        }
        public UnityWebRequest TrainingResponseRequest(string json){
            LoadConnection();
            var request=new UnityWebRequest(endpoint+"/training/response","POST");
            request.uploadHandler=new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
            request.downloadHandler=new DownloadHandlerBuffer();request.timeout=90;
            request.SetRequestHeader("Content-Type","application/json");
            request.SetRequestHeader("Authorization","Bearer "+token);return request;
        }
        public void NewSession() { Cancel(); SessionId = Guid.NewGuid().ToString("N"); Revision = 0; Pending = null; LastResponse = null; interruptionsCarried.Clear(); }

        // Request ID -> how many tracking losses the request carried (as awayIntervals), so a committed turn clears
        // only those, not losses that happened after the request was built.
        readonly Dictionary<string, int> interruptionsCarried = new Dictionary<string, int>();

        public ConversationRequest BuildRequest(string question, Vector2? tapScreen = null) {
            var a = replay.Data.aircraft[replay.SelectedAircraftIndex];
            var evidence = VisualEvidenceCapture.Capture(replay, Camera.main, tapScreen);
            var id = Guid.NewGuid().ToString("N");
            interruptionsCarried[id] = replay.InterruptionCount;
            return new ConversationRequest {
                requestId = id, turnId = id, sessionId = SessionId, scenarioId = replay.Data.scenarioId,
                aircraftId = a.id, flightInstance = a.FlightAt(replay.Clock.Time), checkpoint = replay.Clock.Time,
                expectedRevision = Revision, question = question.Trim(),
                imageBase64 = Convert.ToBase64String(evidence.png), imageCaptureTime = replay.Clock.Time,
                awayIntervals = replay.AwayIntervals(),
                tapViewport = float.IsNaN(evidence.tapViewport.x) ? new float[0] : new[] { evidence.tapViewport.x, evidence.tapViewport.y } };
        }

        bool SameContext(ConversationRequest request) =>
            request.sessionId == SessionId &&
            replay.Data.aircraft[replay.SelectedAircraftIndex].id == request.aircraftId &&
            (replay.LiveTraffic || Mathf.Abs(replay.Clock.Time - request.checkpoint) < .001f) && replay.Data.scenarioId == request.scenarioId &&
            replay.SelectedFlight == request.flightInstance;

        // Returns true when the response is shown. Updates the revision for every committed turn.
        public bool ApplyResponse(ConversationRequest request, ConversationResponse response) {
            if (request == null || request.sessionId != SessionId || response == null || response.requestId != request.requestId || response.sessionId != request.sessionId ||
                Mathf.Abs(response.cutoff - request.checkpoint) > .001f) {
                return Show("CONTEXT CHANGED", "This answer belongs to a different question. Ask again.");
            }
            Revision = Mathf.Max(Revision, response.revision);  // the turn is committed on the server either way
            if (interruptionsCarried.TryGetValue(request.requestId, out var carried)) {
                replay.ClearInterruptionsThrough(carried);  // the server has seen these interruptions
                interruptionsCarried.Remove(request.requestId);
            }
            if (!SameContext(request)) return Show("CONTEXT CHANGED", "The selection or replay time changed. Ask again for this checkpoint.");
            var display = response.display ?? new ConversationDisplay();
            if (response.accepted && !ClaimsSupported(request, response))
                return Show("ANSWER WITHHELD", "A claim did not match a report received for this flight.");
            LastResponse = response;
            var body = string.IsNullOrEmpty(display.answer) ? "No answer text." : display.answer;
            if(replay.LiveTraffic)body=body.Replace("Authored movement condition:","Reported movement condition:").Replace("Scripted movement:","Reported movement:").Replace("Authored movement plan:","Reported route:");
            if (display.interpretation != null && !string.IsNullOrEmpty(display.interpretation.text))
                body += $"\n\n{display.interpretation.label}: {display.interpretation.text}";
            var who = response.currentReferent != null && !string.IsNullOrEmpty(response.currentReferent.aircraftId)
                ? $"{response.currentReferent.aircraftId} / {response.currentReferent.flightInstance}" : request.aircraftId;
            body += $"\n\nAbout {who} · as of {request.checkpoint:00.0}s · {response.latencySeconds:0.0}s";
            if(replay.LiveTraffic && replay.Clock.Time-request.checkpoint>10)body+="\nNewer reports may have arrived. Ask again for an update.";
            Show(response.accepted ? "CHECKED ANSWER" : "ANSWER WITHHELD", body);
            return response.accepted;
        }

        bool ClaimsSupported(ConversationRequest request, ConversationResponse response) {
            var r = response.referent;
            if (r == null || string.IsNullOrEmpty(r.aircraftId)) return response.display?.claims == null || response.display.claims.Length == 0;
            // Any rotation of the referent aircraft: a correction such as "its next rotation" is answered about it.
            var aircraft = replay.Data.aircraft.FirstOrDefault(a => a.id == r.aircraftId && a.Flies(r.flightInstance));
            if (aircraft == null) return false;
            var received = replay.Data.KnownAt(request.checkpoint).Where(e => e.flightInstance == r.flightInstance && e.aircraftId == r.aircraftId).ToArray();
            return (response.display?.claims ?? new SupportedClaim[0]).All(claim =>
                claim != null && claim.evidence_ids != null && claim.evidence_ids.Length == 1 &&
                received.Any(e => e.id == claim.evidence_ids[0] && e.facts != null &&
                                  e.facts.Any(f => claim.fact_id == e.id + ":" + f.property && claim.value == f.value)));
        }

        public void Ask(string question) {
            if(TrainingQuestionBlocked){Show("CHECKPOINT", "Finish this checkpoint before asking a question.");return;}
            if (Busy) return;
            if (string.IsNullOrWhiteSpace(question)) { Show("QUESTION NEEDED", "Type a question or choose one of the examples above."); return; }
            if (!replay.Clock.Tracked && !replay.LiveTraffic) { Show("SCENE UNAVAILABLE", replay.WorldScale ? "Turn back to the apron before asking." : "Acquire the printed board before asking."); return; }
            LoadConnection();
            if (!Uri.TryCreate(endpoint, UriKind.Absolute, out var uri) || (uri.Scheme != "http" && uri.Scheme != "https") || string.IsNullOrWhiteSpace(token)) {
                Show("CONNECTION NEEDED", "The assistant connection is not set up on this device yet. Reports remain available in History."); return;
            }
            replay.Pause();
            try { Send(BuildRequest(question)); }
            catch (Exception) { Show("UNAVAILABLE", "Could not prepare the scene for this question. Please try again."); }
        }

        public void Retry() { if (!Busy && Pending != null && SameContext(Pending)) { LoadConnection(); Send(Pending); } }

        void Send(ConversationRequest request) {
            Pending = request;
            Show("ASKING", replay.LiveTraffic?$"Checking reports for {request.aircraftId} as of {request.checkpoint:00.0}s. Traffic continues while I answer.":$"About {request.aircraftId} at {request.checkpoint:00.0}s. Replay paused so the answer stays tied to this time.");
            active = new UnityWebRequest(endpoint + "/conversation", "POST");
            active.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(JsonUtility.ToJson(request)));
            active.downloadHandler = new DownloadHandlerBuffer(); active.timeout = ExternalPresentation ? 35 : 240;
            active.SetRequestHeader("Content-Type", "application/json"); active.SetRequestHeader("Authorization", "Bearer " + token);
            var web = active;
            web.SendWebRequest().completed += _ => {
                if (active != web) return;
                try {
                    if (web.responseCode == 409) {
                        NewSession(); Show("SESSION RESTARTED", "The conversation was out of step with the service. A new session started; ask again.");
                    } else if (web.result != UnityWebRequest.Result.Success) {
                        Show("UNAVAILABLE", ExternalPresentation ? "The assistant could not answer this request. Please try your question again." : $"Connection failed ({web.responseCode}). Check the service, then Retry.");
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
            DisplayChanged?.Invoke(status,text);
            var heading = status == "CHECKED ANSWER" ? "Report summary" : status.Replace("_", " ");
            if (answerText != null) answerText.text = heading + "\n\n" + text;
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

        public void ResetForExercise(){
            NewSession();
            if(panel!=null){Remove(panel);panel=null;answerText=null;}
        }
        public void ShowPanel() {
            if(ExternalPresentation)return;
            if (panel != null) return;
            replay.Pause();
            var canvas = new GameObject("Conversation", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster)); panel = canvas;
            var c = canvas.GetComponent<Canvas>(); c.renderMode = RenderMode.ScreenSpaceOverlay; c.sortingOrder = 50;
            var scaler = canvas.GetComponent<CanvasScaler>(); scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize; scaler.referenceResolution = new Vector2(1080, 1920); scaler.matchWidthOrHeight = .5f;
            // In world AR the panel is a bottom sheet, so the apron stays visible above it while you ask.
            var world = replay.WorldScale;
            var shade = Box(canvas.transform, "Dim", Vector2.zero, Vector2.one, new Color(0, 0, 0, world ? .25f : .8f));
            var card = world ? Box(shade, "Ask", new Vector2(.03f, .02f), new Vector2(.97f, .46f), new Color(.035f, .075f, .11f, .97f))
                             : Box(shade, "Ask", new Vector2(.05f, .1f), new Vector2(.95f, .9f), new Color(.035f, .075f, .11f));
            TextAt(card, replay.AssistantTitle, new Vector2(.04f, .9f), new Vector2(.96f, .98f), 40);
            var field = Box(card, "Question field", new Vector2(.04f, .76f), new Vector2(.96f, .88f), new Color(.13f, .2f, .26f));
            var input = field.gameObject.AddComponent<InputField>(); input.textComponent = TextAt(field, "", Vector2.zero, Vector2.one, 36);
            input.characterLimit = 400; input.lineType = InputField.LineType.MultiLineNewline;
            var placeholder = TextAt(field, "Type your question…", Vector2.zero, Vector2.one, 34);
            placeholder.color = new Color(.65f, .73f, .78f); input.placeholder = placeholder;
            ButtonAt(card, replay.SuggestedLabel(0), new Vector2(.04f,.64f), new Vector2(.49f,.74f), new Color(.13f,.2f,.26f), () => { input.text=replay.SuggestedQuestion(0); Ask(input.text); });
            ButtonAt(card, replay.SuggestedLabel(1), new Vector2(.51f,.64f), new Vector2(.96f,.74f), new Color(.13f,.2f,.26f), () => { input.text=replay.SuggestedQuestion(1); Ask(input.text); });
            var answerArea = Box(card, "Answer", new Vector2(.04f,.18f), new Vector2(.96f,.61f), Color.clear);
            answerArea.gameObject.AddComponent<RectMask2D>();
            var scroll = answerArea.gameObject.AddComponent<ScrollRect>(); scroll.horizontal=false; scroll.movementType=ScrollRect.MovementType.Clamped;
            answerText = TextAt(answerArea, "Choose a question above or type your own. Answers use reports available at the time you ask.", new Vector2(0,1), Vector2.one, 33, TextAnchor.UpperLeft);
            answerText.rectTransform.pivot = new Vector2(.5f,1);
            answerText.gameObject.AddComponent<ContentSizeFitter>().verticalFit=ContentSizeFitter.FitMode.PreferredSize;
            scroll.viewport=answerArea; scroll.content=answerText.rectTransform;
            ButtonAt(card, "Ask", new Vector2(.04f, .04f), new Vector2(.36f, .15f), new Color(.05f, .48f, .48f), () => Ask(input.text));
            ButtonAt(card, "Retry", new Vector2(.38f, .04f), new Vector2(.62f, .15f), new Color(.13f, .2f, .26f), Retry);
            ButtonAt(card, "Close", new Vector2(.64f, .04f), new Vector2(.96f, .15f), new Color(.13f, .2f, .26f), () => { Remove(panel); panel = null; answerText = null; });
        }
    }
}
