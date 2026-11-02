using System;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

namespace SurfaceSafety {
    [Serializable] public class ReasoningRequest {
        public string requestId, scenarioId, aircraftId, imageBase64;
        public float checkpoint;
        public string question="What does the latest received report say for this aircraft, when did it happen and arrive, and what remains unconfirmed?";
    }
    [Serializable] public class ReasoningResponse {
        public string requestId, scenarioId, aircraftId, flightInstance, answer, resultStatus, model, revision, validation, contextLimit, answerOrigin;
        public SupportedClaim[] claims;
        public float checkpoint, elapsedSeconds;
        public string[] evidenceIds, eligibleEvidenceIds;
        public bool insufficientEvidence, modelInsufficientEvidence;
        public int inputTokens, outputTokens;
    }
    [Serializable] public class SupportedClaim {public string fact_id,value,status;public string[] evidence_ids;}
    public class QwenReasoningClient : MonoBehaviour {
        StandReplay replay;
        string endpoint="http://127.0.0.1:8765", token="";
        UnityWebRequest active;
        ReasoningRequest pending;
        string resultFlight;
        float resultTime;
        bool hasResult;
        GameObject settings;
        public bool Busy => active!=null;
        public ReasoningResponse LastResponse { get; private set; }
        public string LastError { get; private set; }
        public event Action RequestCompleted;
        public void Bind(StandReplay target) {
            replay=target;
            endpoint=PlayerPrefs.GetString("qwen_endpoint",endpoint);
            token=PlayerPrefs.GetString("qwen_token","");
#if UNITY_EDITOR
            var path=Path.GetFullPath(Path.Combine(Application.dataPath,"../../../work/qwen-server-token.txt"));
            if(File.Exists(path))token=File.ReadAllText(path).Trim();
#endif
            replay.RequestReasoning+=Request;
            replay.OpenConnectionSettings+=ShowSettings;
            replay.SetAiResult("QWEN · READY TO CONNECT","Generate an explanation for this aircraft and replay time. Runs on your Mac using the scene and received reports.");
        }
        public void Configure(string url,string secret) {endpoint=url.Trim().TrimEnd('/');token=secret.Trim();}
        bool SameContext(string flight,float time) => replay.Data.aircraft[replay.SelectedAircraftIndex].flightInstance==flight && Mathf.Abs(replay.Clock.Time-time)<.001f;
        void Update() {
            if(replay==null||replay.Data==null||replay.Clock==null){Cancel();hasResult=false;LastResponse=null;return;}
            var pendingAircraft=pending==null?null:replay.Data.aircraft.FirstOrDefault(a=>a.id==pending.aircraftId);  // gone if the scenario changed
            if(pending!=null && (pendingAircraft==null||!SameContext(pendingAircraft.flightInstance,pending.checkpoint))) {
                Cancel(); replay.SetAiResult("CONTEXT CHANGED","Generate again for the selected aircraft and time.");
            }
            if(hasResult && !SameContext(resultFlight,resultTime)) {
                hasResult=false;LastResponse=null;
                replay.SetAiResult("CONTEXT CHANGED","Previous answer hidden. Generate again for this checkpoint.");
            }
        }
        public ReasoningRequest BuildRequest() {
            var a=replay.Data.aircraft[replay.SelectedAircraftIndex];
            return new ReasoningRequest { requestId=Guid.NewGuid().ToString("N"),scenarioId=replay.Data.scenarioId,
                aircraftId=a.id,checkpoint=replay.Clock.Time,imageBase64=Convert.ToBase64String(CaptureSyntheticScene(replay)) };
        }
        public void Request() {
            if(Busy)return;
            if(!replay.Clock.Tracked) {replay.SetAiResult("SCENE UNAVAILABLE","Acquire the printed board before generating an explanation.");return;}
            if(!Uri.TryCreate(endpoint,UriKind.Absolute,out var uri)||(uri.Scheme!="http"&&uri.Scheme!="https")||string.IsNullOrWhiteSpace(token)) {
                replay.SetAiResult("CONNECTION NEEDED","Open Connection and enter the Mac server address and local token.");return;
            }
            replay.Pause();hasResult=false;LastResponse=null;LastError=null;
            pending=BuildRequest();
            var request=pending;
            replay.SetAiResult("QWEN · THINKING",$"Reviewing {request.aircraftId} at {request.checkpoint:00.0}s. Replay paused to keep this explanation tied to its evidence.");
            active=new UnityWebRequest(endpoint+"/reason","POST");
            active.uploadHandler=new UploadHandlerRaw(Encoding.UTF8.GetBytes(JsonUtility.ToJson(request)));
            active.downloadHandler=new DownloadHandlerBuffer();active.timeout=180;
            active.SetRequestHeader("Content-Type","application/json");active.SetRequestHeader("Authorization","Bearer "+token);
            var web=active;
            web.SendWebRequest().completed+=_=> {
                if(active!=web)return;
                try {
                    if(web.result!=UnityWebRequest.Result.Success) {
                        LastError=$"Connection failed ({web.responseCode}). Check that the Mac server is running and the address/token match.";
                        replay.SetAiResult("QWEN · UNAVAILABLE",LastError);
                    } else ApplyResponse(request,JsonUtility.FromJson<ReasoningResponse>(web.downloadHandler.text));
                } catch(Exception) {LastError="Could not read the model response.";replay.SetAiResult("QWEN · UNAVAILABLE",LastError);}
                finally {active=null;pending=null;web.Dispose();RequestCompleted?.Invoke();}
            };
        }
        public bool ApplyResponse(ReasoningRequest request,ReasoningResponse response) {
            var a=replay.Data.aircraft[replay.SelectedAircraftIndex];
            if(response==null||response.requestId!=request.requestId||response.scenarioId!=replay.Data.scenarioId||
               response.aircraftId!=a.id||response.flightInstance!=a.flightInstance||
               Mathf.Abs(response.checkpoint-request.checkpoint)>.001f||!SameContext(a.flightInstance,request.checkpoint)) {
                LastError="Response belongs to a different aircraft or checkpoint.";
                replay.SetAiResult("CONTEXT CHANGED","Outdated answer discarded. Generate again for this checkpoint.");return false;
            }
            var allowed=replay.Data.KnownAt(request.checkpoint).Where(e=>e.flightInstance==a.flightInstance).Select(e=>e.id).ToArray();
            if(response.evidenceIds==null||response.evidenceIds.Any(id=>!allowed.Contains(id))||
               response.answerOrigin!="validated_fact_templates"||
               string.IsNullOrEmpty(response.answer)||(response.resultStatus!="generated"&&response.resultStatus!="withheld")) {
                LastError="Response failed local evidence checks.";replay.SetAiResult("ANSWER WITHHELD",LastError);return false;
            }
            if(response.resultStatus=="generated" && (response.claims==null || response.claims.Any(claim=>!ClaimSupported(claim,request.checkpoint,a)))) {
                LastError="A claim did not match its cited report.";replay.SetAiResult("ANSWER WITHHELD",LastError);return false;
            }
            LastResponse=response;resultFlight=a.flightInstance;resultTime=request.checkpoint;hasResult=true;
            string sources=response.evidenceIds.Length>0?string.Join(", ",response.evidenceIds):"No supporting report";
            string status=response.resultStatus=="withheld"?"SELECTION WITHHELD":"CLAIMS CHECKED";
            replay.SetAiResult(status,$"{response.answer}\n\nSources: {sources} · As of {request.checkpoint:00.0}s\nScenario limit: {response.contextLimit}\n{response.elapsedSeconds:0.0}s on Mac · Qwen selects facts; checked templates supply the wording.");
            return true;
        }
        bool ClaimSupported(SupportedClaim claim,float checkpoint,AircraftPlan aircraft) {
            if(claim==null||claim.evidence_ids==null||claim.evidence_ids.Length!=1||string.IsNullOrEmpty(claim.fact_id))return false;
            var e=replay.Data.KnownAt(checkpoint).FirstOrDefault(x=>x.id==claim.evidence_ids[0]&&x.flightInstance==aircraft.flightInstance&&x.aircraftId==aircraft.id);
            return e!=null&&e.facts!=null&&e.facts.Any(f=>claim.fact_id==e.id+":"+f.property&&claim.value==f.value);
        }
        void Cancel() {if(active!=null){var web=active;active=null;web.Abort();web.Dispose();}pending=null;}
        void OnDestroy(){Cancel();if(replay!=null){replay.RequestReasoning-=Request;replay.OpenConnectionSettings-=ShowSettings;}}
        static void Remove(UnityEngine.Object item){if(Application.isPlaying)Destroy(item);else DestroyImmediate(item);}
        // Render only the synthetic world, never the phone camera or desktop UI.
        public static byte[] CaptureSyntheticScene(StandReplay target) {
            var nodes=target.Content.GetComponentsInChildren<Transform>(true);
            var layers=nodes.Select(n=>n.gameObject.layer).ToArray();
            var host=new GameObject("Synthetic evidence camera");var cam=host.AddComponent<Camera>();
            var rt=new RenderTexture(672,448,24);var image=new Texture2D(672,448,TextureFormat.RGB24,false);
            var previous=RenderTexture.active;
            try {
                foreach(var n in nodes)n.gameObject.layer=30;
                cam.cullingMask=1<<30;cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.055f,.09f,.12f);
                cam.transform.position=target.Content.TransformPoint(new Vector3(0,.29f,-.23f));
                cam.transform.LookAt(target.Content.position,target.Content.up);
                cam.orthographic=true;cam.orthographicSize=.105f*target.Content.lossyScale.x;
                cam.nearClipPlane=.005f;cam.farClipPlane=10;cam.aspect=1.5f;cam.targetTexture=rt;
                cam.Render();RenderTexture.active=rt;image.ReadPixels(new Rect(0,0,672,448),0,0);image.Apply();
                return image.EncodeToPNG();
            } finally {
                for(int i=0;i<nodes.Length;i++)nodes[i].gameObject.layer=layers[i];
                RenderTexture.active=previous;cam.targetTexture=null;Remove(image);Remove(rt);Remove(host);
            }
        }
        static RectTransform Box(Transform parent,string name,Vector2 min,Vector2 max,Color color) {
            var g=new GameObject(name,typeof(RectTransform),typeof(Image));g.transform.SetParent(parent,false);
            var r=g.GetComponent<RectTransform>();r.anchorMin=min;r.anchorMax=max;r.offsetMin=r.offsetMax=Vector2.zero;g.GetComponent<Image>().color=color;return r;
        }
        static Text TextAt(Transform parent,string value,Vector2 min,Vector2 max,int size) {
            var g=new GameObject("Text",typeof(RectTransform),typeof(Text));g.transform.SetParent(parent,false);
            var r=g.GetComponent<RectTransform>();r.anchorMin=min;r.anchorMax=max;r.offsetMin=new Vector2(16,0);r.offsetMax=new Vector2(-16,0);
            var t=g.GetComponent<Text>();t.font=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");t.fontSize=size;t.text=value;t.color=Color.white;t.alignment=TextAnchor.MiddleLeft;t.supportRichText=false;t.raycastTarget=false;return t;
        }
        static InputField Field(Transform parent,string value,float bottom,float top,bool password=false) {
            var r=Box(parent,"Connection field",new Vector2(.06f,bottom),new Vector2(.94f,top),new Color(.13f,.2f,.26f));
            var label=TextAt(r,"",Vector2.zero,Vector2.one,39);var input=r.gameObject.AddComponent<InputField>();input.textComponent=label;
            input.contentType=password?InputField.ContentType.Password:InputField.ContentType.Standard;input.text=value;return input;
        }
        void ShowSettings() {
            if(settings!=null)return;
            var canvas=new GameObject("Qwen connection",typeof(Canvas),typeof(CanvasScaler),typeof(GraphicRaycaster));settings=canvas;
            var c=canvas.GetComponent<Canvas>();c.renderMode=RenderMode.ScreenSpaceOverlay;c.sortingOrder=50;
            var scaler=canvas.GetComponent<CanvasScaler>();scaler.uiScaleMode=CanvasScaler.ScaleMode.ScaleWithScreenSize;scaler.referenceResolution=new Vector2(1080,1920);scaler.matchWidthOrHeight=.5f;
            var shade=Box(canvas.transform,"Dim",Vector2.zero,Vector2.one,new Color(0,0,0,.8f));
            var card=Box(shade,"Connection",new Vector2(.05f,.12f),new Vector2(.95f,.88f),new Color(.035f,.075f,.11f));
            TextAt(card,"Connect to Qwen on your Mac",new Vector2(.04f,.84f),new Vector2(.96f,.98f),40);
            TextAt(card,"Server address",new Vector2(.04f,.74f),new Vector2(.96f,.83f),33);
            var url=Field(card,endpoint,.62f,.74f);
            TextAt(card,"Local connection token",new Vector2(.04f,.51f),new Vector2(.96f,.61f),33);
            var secret=Field(card,token,.39f,.51f,true);
            TextAt(card,"Use the Mac address on trusted Wi-Fi, or 127.0.0.1 with USB forwarding. Only synthetic scene images are sent. Settings stay on this device.",new Vector2(.04f,.17f),new Vector2(.96f,.37f),33);
            var save=Box(card,"Save",new Vector2(.06f,.04f),new Vector2(.57f,.15f),new Color(.05f,.48f,.48f));
            TextAt(save,"Save connection",Vector2.zero,Vector2.one,39);
            save.gameObject.AddComponent<Button>().onClick.AddListener(()=>{Configure(url.text,secret.text);PlayerPrefs.SetString("qwen_endpoint",endpoint);PlayerPrefs.SetString("qwen_token",token);PlayerPrefs.Save();Remove(settings);settings=null;replay.SetAiResult("CONNECTION SAVED","Tap Generate to request an explanation from your Mac.");});
            var close=Box(card,"Cancel",new Vector2(.61f,.04f),new Vector2(.94f,.15f),new Color(.13f,.2f,.26f));TextAt(close,"Cancel",Vector2.zero,Vector2.one,39);
            close.gameObject.AddComponent<Button>().onClick.AddListener(()=>{Remove(settings);settings=null;});
        }
    }
}
