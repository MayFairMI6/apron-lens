using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;

namespace SurfaceSafety {
    public class StandReplay : MonoBehaviour {
        public bool previewMode;
        public Scenario Data {get;private set;}
        public ReplayClock Clock {get;private set;}
        public bool LiveTraffic {get;private set;}
        public bool TrainingPresentation {get;private set;}
        public void UseTrainingPresentation(){
            TrainingPresentation=true;if(safeRoot!=null)safeRoot.gameObject.SetActive(false);
            if(Content!=null)foreach(Transform child in Content)if(child.name.EndsWith(" authored path",StringComparison.Ordinal))child.GetComponent<LineRenderer>().enabled=false;
        }
        string trafficStatus="Connecting to traffic…";
        public string TrainingTitle {get;set;}="";
        public bool AwarenessTrack => LiveTraffic && (Data.trainingRole=="controller_awareness" || Data.trainingRole=="pilot_awareness");
        public string AssistantTitle => AwarenessTrack?Data.trainingRoleLabel+" · selected flight":"Ask about the selected aircraft";
        public string SuggestedLabel(int index) => LiveTraffic && Data.assistantQuestionLabels!=null && Data.assistantQuestionLabels.Length>index?Data.assistantQuestionLabels[index]:index==0?"Latest update":"Ready to depart?";
        public string SuggestedQuestion(int index) => LiveTraffic && Data.assistantQuestions!=null && Data.assistantQuestions.Length>index?Data.assistantQuestions[index]:index==0?"What is the latest update for this aircraft?":"Is this aircraft ready to depart?";
        public Transform Content {get;private set;}
        public int SelectedAircraftIndex {get;private set;} = 1;
        public string SelectedTab {get;private set;} = "now";
        public bool AllFlightsHistory {get;private set;}
        public string InspectedReportId {get;private set;} = "";
        public event Action RequestReasoning;
        public event Action OpenConnectionSettings;
        public event Action OpenConversation;
        public ScenarioEvent[] VisibleReports => Data.KnownAt(Clock.Time)
            .Where(e=>AllFlightsHistory || e.flightInstance==SelectedFlight).Reverse().ToArray();
        AircraftPlan SelectedAircraft => Data.aircraft[SelectedAircraftIndex];
        // The selected aircraft's rotation under way at the replay time.
        public string SelectedFlight => SelectedAircraft.FlightAt(Clock.Time);
        ScenarioEvent[] SelectedReports => Data.KnownAt(Clock.Time).Where(e=>e.flightInstance==SelectedFlight).ToArray();
        const string Milestone1Id="M1-stand-coordination-01";
        // Parking positions in front of the two printed stand markers.
        static readonly Vector3 StandAPark=new Vector3(-.045f,0,.04f),StandBPark=new Vector3(.035f,0,.04f);
        // Indexed liveries; the first two are the original Milestone 1 colours.
        static readonly Color[] IndexedLiveries={new Color(.15f,.68f,.86f),new Color(1,.64f,.18f),new Color(.36f,.70f,.36f),new Color(.66f,.44f,.82f)};
        static readonly Color UniformLiveryColor=new Color(.30f,.40f,.52f);
        Color LiveryOf(int index)=>Data.UniformLivery?UniformLiveryColor:IndexedLiveries[index];
        public string CurrentSceneState {
            get {
                var a=SelectedAircraft;
                var p=Scenario.Position(a,Clock.Time);
                if(Vector3.Distance(p,StandBPark)<.0001f)return "At Stand B · stationary";
                if(Vector3.Distance(p,StandAPark)<.0001f)return "At Stand A · stationary";
                if(LiveTraffic)return Vector3.Distance(p,new Vector3(.115f,0,.04f))<.0001f?"At Stand C · stationary":"On apron";
                if(Clock.Time>=a.waypoints[a.waypoints.Length-1].t)return "At final authored waypoint";
                return "On the authored movement path";
            }
        }
        public string CurrentReasoning {
            get {
                var reports=SelectedReports;
                // The authored wording below describes Milestone 1's reports only.
                if(Data.scenarioId!=Milestone1Id)
                    return (reports.Length==0?"No report for "+SelectedAircraft.id+" has been received at this replay time. ":
                        string.Join(" ",reports.Select(e=>"["+e.id+"] "+e.message))+" ")+
                        "Overall readiness remains unknown: the received reports do not establish every required service or a movement clearance.";
                if(SelectedAircraftIndex==1){
                    var baggage=reports.FirstOrDefault(e=>e.id=="E03");
                    var move=reports.FirstOrDefault(e=>e.id=="E06");
                    return "[E02] assigns A2 to Stand B. "+
                        (baggage==null?"No baggage-completion report has been received at this replay time. ":
                        "[E03] reports baggage complete at 12 s; it became available at 14 s. ")+
                        (move==null?"":"[E06] records the start of scripted movement. ")+
                        (reports.Any(e=>e.id=="E05")?"[E05] records the final authored waypoint. ":"")+
                        "Overall readiness remains unknown: the received reports do not establish every required service or a movement clearance.";
                }
                return "[E01] loads A1's authored movement plan. "+
                    (reports.Any(e=>e.id=="E04")?"[E04] reports the shared-path checkpoint at 30 s. ":"")+
                    "The displayed position comes from the scenario trajectory. A plan and a position do not establish operational readiness or authorize movement.";
            }
        }
        Transform[] planes;
        Transform[][] landingGear;
        AircraftTypeRig[] aircraftRigs;
        GameObject[] propObjects;
        VisualProp[] props;
        LineRenderer selectionRing;
        RectTransform safeRoot, body, captionPanel, tabsPanel, detailsHandle, worldAskButton;
        Text status, clockLabel, playLabel, selectionLabel;
        Image[] aircraftChips, tabChips;
        Text[] aircraftChipLabels;
        Slider slider;
        Button playButton;
        string logPath, bodyKey, aiStatus="Not requested", aiText="Ask about this aircraft using reports available at the selected time.";
        bool updatingSlider, showTools, logCopied;
        Font font;
        readonly Color ink=new Color(.055f,.095f,.13f);
        readonly Color panel=new Color(.94f,.96f,.965f);
        readonly Color card=Color.white;
        readonly Color muted=new Color(.38f,.46f,.5f);
        readonly Color teal=new Color(0f,.40f,.42f);
        readonly Color amber=new Color(.65f,.35f,.04f);
        public void Initialize(bool preview) {Initialize(preview,"milestone1");}
        public void Initialize(bool preview,string scenarioResource) {
            var asset=Resources.Load<TextAsset>(scenarioResource);
            if(asset==null)throw new ArgumentException("Unknown scenario resource: "+scenarioResource);
            InitializeFromJson(preview,asset.text);
        }
        // Scenario text from outside the app's resources (held-out renders, HeldoutRender).
        public void InitializeFromJson(bool preview,string scenarioJson) {
            previewMode=preview;
            Data=JsonUtility.FromJson<Scenario>(scenarioJson);Data.Validate();
            Clock=new ReplayClock(Data.duration,Data.ClockRunsUntracked);Clock.SetTracking(preview);
            Content=new GameObject("StandWorld").transform;Content.SetParent(transform,false);
            BuildWorld();BuildUI();
            logPath=Path.Combine(Application.persistentDataPath,"session-"+Guid.NewGuid().ToString("N")+".jsonl");
            Log("session_start");ApplyScene();
        }
        // Tracking losses not yet reported to the server, each with a sequence number and the replay time the
        // board left the camera's view. Only a clock that runs while untracked records them: with a paused clock
        // nothing can arrive unseen. ConversationClient sends them as awayIntervals and, once that turn is
        // committed, clears the losses the request carried, keeping any that happened after it was built.
        // Restarting or seeking backward starts a new timeline and discards them.
        // back is the replay time tracking returned (-1 while the board is still out of view).
        readonly List<(int id,float at,float back)> interruptions=new List<(int id,float at,float back)>();
        public int InterruptionCount {get;private set;}
        public float? InterruptedAt=>interruptions.Count==0?(float?)null:interruptions[0].at;
        // Pending losses as [start, end, start, end, ...] up to the current replay time, kept separate so the time
        // watched between them doesn't count as unseen. A loss still under way ends now. Losses less than
        // FlickerSeconds of watching apart are one loss (tracking flicker, not watching). At most MaxAwayIntervals
        // are sent, the server's limit: beyond it, the shortest watched gaps are merged first, so only those few
        // seconds can count as unseen.
        public const int MaxAwayIntervals=20;
        public const float FlickerSeconds=1f;
        public float[] AwayIntervals(){
            var spans=new List<(float start,float end)>();
            foreach(var i in interruptions){
                var end=i.back<0?Clock.Time:i.back;
                if(end<=i.at)continue;
                if(spans.Count>0&&i.at-spans[spans.Count-1].end<FlickerSeconds)spans[spans.Count-1]=(spans[spans.Count-1].start,end);
                else spans.Add((i.at,end));
            }
            while(spans.Count>MaxAwayIntervals){
                int shortest=0;
                for(int k=1;k<spans.Count-1;k++)
                    if(spans[k+1].start-spans[k].end<spans[shortest+1].start-spans[shortest].end)shortest=k;
                spans[shortest]=(spans[shortest].start,spans[shortest+1].end);spans.RemoveAt(shortest+1);
            }
            var flat=new List<float>();
            foreach(var span in spans){flat.Add(span.start);flat.Add(span.end);}
            return flat.ToArray();
        }
        public void ClearInterruptionsThrough(int count){interruptions.RemoveAll(i=>i.id<=count);}
        // "While you were away": the reports received while the board was out of view, computed by the app from the
        // scenario (not by a model) when tracking returns, and shown on the Now tab until the user dismisses it.
        // A card not yet dismissed accumulates later gaps (reports and span), so nothing is lost before the user taps it.
        public string[] AwayNotice {get;private set;}
        public string AwayNoticeSpan {get;private set;}
        readonly List<ScenarioEvent> awayMissed=new List<ScenarioEvent>();
        float awayFrom,awayTo;
        public void DismissAwayNotice(){ClearAwayNotice();Log("away_notice_dismissed");ApplyScene();}
        void ClearAwayNotice(){AwayNotice=null;AwayNoticeSpan=null;awayMissed.Clear();}
        void SetAwayNotice(float from,float to){
            if(AwayNotice==null){awayFrom=from;awayTo=to;}else{awayFrom=Mathf.Min(awayFrom,from);awayTo=Mathf.Max(awayTo,to);}
            foreach(var e in Data.events.Where(e=>e.receiptTime>from&&e.receiptTime<=to))if(!awayMissed.Contains(e))awayMissed.Add(e);
            var missed=awayMissed.OrderBy(e=>e.receiptTime).ThenBy(e=>e.id).ToArray();
            AwayNoticeSpan=$"{awayFrom:0}–{awayTo:0} s";
            AwayNotice=missed.Length==0?new[]{"Nothing new arrived."}:
                missed.Select(e=>$"{e.aircraftId}  ·  {ShortReport(e)}  ·  received {e.receiptTime:0} s  [{e.id}]").ToArray();
            Log("away_notice");
        }
        // World-scale AR (WorldArBootstrap): the replay laid out in metres on a simulated full-scale apron, seen through
        // the AR camera. The tabletop board image and stand blocks are hidden; the apron's own markings replace them.
        public bool WorldScale {get;private set;}
        public void UseWorldScale(float metresPerUnit){
            WorldScale=true;Content.localScale=Vector3.one*metresPerUnit;
            var header=safeRoot.Find("Header") as RectTransform;
            if(header!=null){
                header.anchorMin=new Vector2(0,.88f);
                foreach(var chip in aircraftChips){var rect=chip.rectTransform;rect.anchorMax=new Vector2(rect.anchorMax.x,.60f);}
                status.transform.SetParent(safeRoot,false);
                status.rectTransform.anchorMin=new Vector2(.035f,.84f);status.rectTransform.anchorMax=new Vector2(.965f,.878f);
                status.rectTransform.offsetMin=status.rectTransform.offsetMax=Vector2.zero;

            }
            // AR-first layout: the details (caption, tabs, inspector) start collapsed so the camera view fills the
            // screen between the header and the transport; a tab above the transport opens and closes them.
            if(safeRoot!=null&&detailsHandle==null){
                detailsHandle=Button(safeRoot,"Show details",Vector2.zero,Vector2.one,()=>SetDetails(!DetailsOpen),new Color(.94f,.96f,.965f,.96f),30);
                worldAskButton=Button(safeRoot,"Ask assistant",new Vector2(.52f,.186f),new Vector2(.965f,.236f),()=>OpenConversation?.Invoke(),teal,32);
                worldAskButton.GetComponentInChildren<Text>().color=Color.white;
                SetDetails(false);
            }
            foreach(Transform t in Content)
                if(t.name=="Board image"||t.name=="Terminal"||t.name.StartsWith("Stand ",StringComparison.Ordinal))
                    foreach(var r in t.GetComponentsInChildren<Renderer>())r.enabled=false;
            if(selectionRing!=null)selectionRing.widthMultiplier*=metresPerUnit;  // line width ignores transform scale
            ApplyScene();
        }
        public void UseAutonomousTraffic(){
            LiveTraffic=true;Clock.Pause();
            safeRoot.Find("Replay transport").gameObject.SetActive(false);
            body.anchorMin=new Vector2(0,.015f);
            SetDetails(false);
        }
        public void ApplyTrafficScenario(Scenario incoming){
            incoming.Validate();
            bool changed=incoming.scenarioId!=Data.scenarioId;
            if(!changed)return; // A session's plan is immutable; only its clock updates.
            string selectedId=SelectedAircraft.id,selectedFlight=SelectedFlight;
            bool visualsChanged=incoming.aircraft.Length!=Data.aircraft.Length||incoming.aircraft.Where((a,i)=>i>=Data.aircraft.Length||a.id!=Data.aircraft[i].id||a.aircraftType!=Data.aircraft[i].aircraftType).Any();
            bool tracked=Clock.Tracked;Data=incoming;Clock=new ReplayClock(Data.duration,true);Clock.SetTracking(tracked);
            int selection=Array.FindIndex(Data.aircraft,a=>a.Flies(selectedFlight));
            if(selection<0)selection=Array.FindIndex(Data.aircraft,a=>a.id==selectedId);
            SelectedAircraftIndex=selection>=0?selection:0;
            if(visualsChanged){BuildAircraft();BuildAircraftChips(safeRoot.Find("Header"));}
            interruptions.Clear();ClearAwayNotice();InspectedReportId="";
            foreach(var obj in propObjects??new GameObject[0])if(obj!=null)ReleaseObject(obj);
            props=new VisualProp[0];propObjects=new GameObject[0];BuildProps();BuildPaths();bodyKey=null;InvalidateAi();
            slider.maxValue=Data.duration;
            GetComponent<ConversationClient>()?.ResetForExercise();Log("traffic_session_started");
        }
        public void UpdateTrafficTime(float time,string state){
            if(!LiveTraffic || float.IsNaN(time) || float.IsInfinity(time))return;
            trafficStatus=state;Clock.Seek(Mathf.Max(Clock.Time,time));ApplyScene();
        }
        // World AR only: whether the caption, tabs and inspector are shown (DetailsOpen) or collapsed under the AR view.
        public bool DetailsOpen {get;private set;}=true;
        public void SetDetails(bool open){
            DetailsOpen=open;
            foreach(var panelObject in new[]{captionPanel,tabsPanel,body})if(panelObject!=null)panelObject.gameObject.SetActive(open);
            if(detailsHandle!=null){
                detailsHandle.anchorMin=new Vector2(.035f,open?.568f:(LiveTraffic?.025f:.186f));detailsHandle.anchorMax=new Vector2(.48f,open?.618f:(LiveTraffic?.085f:.236f));
                detailsHandle.GetComponentInChildren<Text>().text=open?"Hide details":"Show details";
            }
            if(worldAskButton!=null){
                worldAskButton.anchorMin=new Vector2(.52f,open?.568f:(LiveTraffic?.025f:.186f));worldAskButton.anchorMax=new Vector2(.965f,open?.618f:(LiveTraffic?.085f:.236f));
            }
            Log(open?"details_opened":"details_closed");bodyKey=null;ApplyScene();
        }
        // Aircraft with a report received while the user looked away (the pending "While you were away" card).
        public IEnumerable<string> AwayAircraft=>awayMissed.Select(e=>e.aircraftId).Distinct();
        public void Tracking(bool found){
            if(Clock==null)return;
            if(Clock.Tracked!=found)Log(found?"target_found":"target_lost");
            if(Clock.Tracked&&!found&&Data.ClockRunsUntracked)interruptions.Add((++InterruptionCount,Clock.Time,-1f));
            if(!Clock.Tracked&&found&&interruptions.Count>0&&interruptions[interruptions.Count-1].back<0){
                var last=interruptions[interruptions.Count-1];
                // A loss during which no replay time passed (playback paused by hand) hid nothing: discard it.
                if(last.at>=Clock.Time)interruptions.RemoveAt(interruptions.Count-1);
                else{interruptions[interruptions.Count-1]=(last.id,last.at,Clock.Time);SetAwayNotice(last.at,Clock.Time);}
            }
            Clock.SetTracking(found);Content.gameObject.SetActive(found||LiveTraffic);ApplyScene();
        }
        public void Play(){if(LiveTraffic)return;Clock.Play();Log("play");ApplyScene();}
        public void Pause(){if(LiveTraffic)return;Clock.Pause();Log("pause");ApplyScene();}
        public void Restart(){if(LiveTraffic)return;interruptions.Clear();ClearAwayNotice();Clock.Restart();InvalidateAi();Log("restart");ApplyScene();}
        public void Seek(float time){
            if(LiveTraffic)return;
            if(float.IsNaN(time)||float.IsInfinity(time))return;
            if(time<Clock.Time){interruptions.Clear();ClearAwayNotice();}  // a new timeline: earlier losses no longer describe what was missed
            Clock.Seek(time);InvalidateAi();Log("seek");ApplyScene();}
        // AR pointing: the aircraft nearest a tap in the AR view, if one is within the radius (pixels); else -1.
        public int AircraftAtScreen(Vector2 screen,Camera camera,float radius){
            int best=-1;float bestDistance=radius;
            for(int i=0;i<planes.Length;i++){
                var p=camera.WorldToScreenPoint(planes[i].position);
                if(p.z<=0||!planes[i].gameObject.activeInHierarchy)continue;
                var d=Vector2.Distance(screen,new Vector2(p.x,p.y));
                if(d<bestDistance){best=i;bestDistance=d;}
            }
            return best;
        }
        public bool TapSelect(Vector2 screen,Camera camera){
            var index=AircraftAtScreen(screen,camera,Mathf.Max(40,.08f*Mathf.Min(camera.pixelWidth,camera.pixelHeight)));
            if(index<0)return false;
            Log("aircraft_tapped");SelectAircraft(index);return true;
        }
        public void SelectAircraft(int index){
            if(index<0||index>=Data.aircraft.Length)return;
            if(index!=SelectedAircraftIndex){SelectedAircraftIndex=index;InspectedReportId="";InvalidateAi();Log("aircraft_selected");}
            ApplyScene();
        }
        public void SelectTab(string tab){if(tab!="now"&&tab!="why"&&tab!="history")return;SelectedTab=tab;showTools=false;Log("tab_"+tab);ApplyScene();}
        public void SetHistoryScope(bool all){AllFlightsHistory=all;Log(all?"history_all_flights":"history_selected_flight");ApplyScene();}
        public void InspectReport(string id){
            if(!VisibleReports.Any(e=>e.id==id))return;
            InspectedReportId=id;SelectedTab="history";Log("inspect_report");ApplyScene();
        }
        public void SeekToReportReceipt(string id){
            var report=VisibleReports.FirstOrDefault(e=>e.id==id);if(report==null)return;
            Seek(report.receiptTime);Log("jump_to_receipt");
        }
        public void SetAiResult(string status,string text){aiStatus=status??"";aiText=text??"";bodyKey=null;ApplyScene();}
        void InvalidateAi(){aiStatus="Checkpoint changed";aiText="Generate a new explanation for the selected aircraft and replay time.";}
        void Update(){
            if(Clock==null)return;
            if(!TrainingPresentation&&Input.GetMouseButtonDown(0)&&Camera.main!=null&&(EventSystem.current==null||!EventSystem.current.IsPointerOverGameObject()))
                TapSelect(Input.mousePosition,Camera.main);
            if(!LiveTraffic)Clock.Advance(Time.unscaledDeltaTime);ApplyScene();
        }
        void OnApplicationPause(bool paused){if(paused&&Clock!=null){Clock.Pause();Log("application_pause");ApplyScene();}}
        void OnDestroy(){if(Clock!=null)Log("session_end");}
        [Serializable] class LogRecord {
            public string kind,scenarioId,utc,mode,aircraft,tab,report;
            public float simulationTime;
            public bool tracked;
        }
        void Log(string kind){
            if(string.IsNullOrEmpty(logPath))return;
            var row=new LogRecord {kind=kind,scenarioId=Data.scenarioId,utc=DateTime.UtcNow.ToString("O"),
                simulationTime=Clock.Time,tracked=Clock.Tracked,mode=previewMode?"desktop_simulation":"image_target_ar",
                aircraft=SelectedAircraft.id,tab=SelectedTab,report=InspectedReportId};
            try {File.AppendAllText(logPath,JsonUtility.ToJson(row)+"\n");}
            catch(Exception e){Debug.LogWarning("Session log unavailable: "+e.GetType().Name);}
        }
        public void ApplyScene(){
            if(planes==null||Data==null||Clock==null)return;
            for(int i=0;i<planes.Length;i++) {
                planes[i].gameObject.SetActive(!Data.aircraft[i].hidden);
                planes[i].localRotation=Quaternion.identity;
                var direction=Scenario.Direction(Data.aircraft[i],Clock.Time);
                if(direction.sqrMagnitude>0.000001f)planes[i].localRotation=Quaternion.LookRotation(direction,Vector3.up);
                if(Data.aircraft[i].phases!=null&&new Vector2(direction.x,direction.z).sqrMagnitude>0.000001f)
                    planes[i].localRotation=Quaternion.LookRotation(new Vector3(direction.x,0,direction.z),Vector3.up)*Quaternion.Euler(-Scenario.Pitch(Data.aircraft[i],Clock.Time),0,0);
                if(Data.aircraft[i].preciseHeading)
                    planes[i].localRotation=Quaternion.Euler(0,Scenario.Heading(Data.aircraft[i],Clock.Time),0)*Quaternion.Euler(-Scenario.Pitch(Data.aircraft[i],Clock.Time),0,0);
                planes[i].localRotation*=Quaternion.Euler(0,0,Scenario.Roll(Data.aircraft[i],Clock.Time));
                var rig=aircraftRigs[i];
                float offset=rig==null?(TrainingPresentation?.00235f:.003f):
                    (Data.aircraft[i].surfaceHeightMetres+rig.ContactOffsetMetres(planes[i].localRotation))*.001f;
                planes[i].localPosition=Scenario.Position(Data.aircraft[i],Clock.Time)+Vector3.up*(offset-Scenario.BodySink(Data.aircraft[i],Clock.Time));
                if(rig!=null)rig.SetGear(Data.aircraft[i].GearRetractedAt(Clock.Time));
                else if(landingGear!=null)foreach(var part in landingGear[i])part.gameObject.SetActive(!Data.aircraft[i].GearRetractedAt(Clock.Time));
            }
            if(propObjects!=null)for(int i=0;i<propObjects.Length;i++){
                var v=Scenario.PropValueAt(props[i],Clock.Time);propObjects[i].SetActive(v=="connected"||v=="open");
            }
            if(selectionRing!=null){selectionRing.transform.localPosition=Scenario.Position(SelectedAircraft,Clock.Time);selectionRing.startColor=selectionRing.endColor=SelectedAircraftIndex==1?new Color(1f,.72f,.33f):new Color(.28f,.84f,.78f);}
            if(!VisibleReports.Any(e=>e.id==InspectedReportId))InspectedReportId="";
            if(clockLabel!=null)clockLabel.text=$"{Clock.Time:00.0}<size=33> / {Data.duration:00} s</size>";
            if(status!=null&&LiveTraffic){status.text=!string.IsNullOrEmpty(trafficStatus)?trafficStatus:Clock.Tracked?TrainingTitle:"Looking away · updates continue";status.color=string.IsNullOrEmpty(trafficStatus)?teal:amber;}
            else if(status!=null&&WorldScale){status.text=Clock.Tracked?"":
                Clock.RunsUntracked&&Clock.Playing?"Looking away · updates continue":"Looking away · replay paused";status.color=Clock.Tracked?teal:amber;}
            else if(status!=null){status.text=previewMode?"Desktop preview · tracking untested":
                (Clock.Tracked?"Board tracked · "+(Clock.Playing?"replaying":"paused"):
                Clock.RunsUntracked&&Clock.Playing?"Board out of view · apron keeps running":"Find printed board · playback paused");status.color=Clock.Tracked?teal:amber;}
            if(playLabel!=null)playLabel.text=Clock.Playing?"Pause":"Play";
            if(playButton!=null)playButton.interactable=Clock.Tracked;
            if(selectionLabel!=null)selectionLabel.text=SelectedAircraft.id+" · "+CurrentSceneState;
            if(aircraftChips!=null)for(int i=0;i<aircraftChips.Length;i++)aircraftChips[i].color=i==SelectedAircraftIndex?new Color(.82f,.92f,.92f):panel;
            // Chip labels follow the rotation under way; single-flight aircraft never change.
            if(aircraftChipLabels!=null)for(int i=0;i<aircraftChipLabels.Length;i++){var label=ChipLabel(Data.aircraft[i]);if(aircraftChipLabels[i].text!=label)aircraftChipLabels[i].text=label;}
            if(tabChips!=null)for(int i=0;i<tabChips.Length;i++){bool selected=SelectedTab==new[]{"now","why","history"}[i];tabChips[i].color=selected?teal:card;tabChips[i].GetComponentInChildren<Text>().color=selected?Color.white:ink;}
            if(slider!=null){updatingSlider=true;slider.SetValueWithoutNotify(Clock.Time);updatingSlider=false;}
            UpdateSafeArea();
            var key=SelectedAircraftIndex+"|"+SelectedFlight+"|"+SelectedTab+"|"+AllFlightsHistory+"|"+InspectedReportId+"|"+
                string.Join(",",Data.KnownAt(Clock.Time).Select(e=>e.id))+"|"+CurrentSceneState+"|"+aiStatus+"|"+aiText+"|"+showTools+"|"+logCopied+"|"+(AwayNotice==null?"":AwayNoticeSpan+string.Join(";",AwayNotice));
            if(key!=bodyKey){bodyKey=key;RebuildBody();}
        }
        void RemoveCollider(GameObject obj){
            var collider=obj.GetComponent<Collider>();if(collider==null)return;
            if(Application.isPlaying)Destroy(collider);else DestroyImmediate(collider);
        }
        Material Mat(Color color){var m=new Material(Shader.Find("Standard"));m.color=color;return m;}
        // Visual-only props in one neutral colour and without text, attached to their aircraft.
        // A fuel tanker is shown while connected; a cargo hatch flap is shown while open.
        // Near-black contrasts with the white airframe, the light apron and the darker stand bands.
        void BuildProps(){
            props=Data.visualProps??new VisualProp[0];propObjects=new GameObject[props.Length];
            var neutral=new Color(.12f,.13f,.13f);
            for(int i=0;i<props.Length;i++){
                var id=props[i].aircraftId;
                int index=Array.FindIndex(Data.aircraft,a=>a.id==id);
                var root=new GameObject("Visual prop "+props[i].id).transform;root.SetParent(planes[index],false);
                // The two props differ in side, outline and shape so they cannot be mistaken
                // for each other from above: a tanker with a cab and hose on the aircraft's
                // right, and a flat flap hinged out from the fuselage on its left.
                if(props[i].kind=="fuel_vehicle"){
                    Shape(PrimitiveType.Cylinder,"Fuel tanker tank",new Vector3(.0115f,.0019f,.0070f),new Vector3(.0034f,.0040f,.0034f),neutral,root)
                        .transform.localRotation=Quaternion.Euler(90,0,0);
                    Shape(PrimitiveType.Cube,"Fuel tanker cab",new Vector3(.0115f,.0017f,.0128f),new Vector3(.0034f,.0030f,.0028f),neutral,root);
                    Shape(PrimitiveType.Cube,"Fuel tanker hose",new Vector3(.0062f,.0014f,.0070f),new Vector3(.0072f,.0006f,.0006f),neutral,root);
                } else {
                    Shape(PrimitiveType.Cube,"Cargo hatch flap",new Vector3(-.0045f,.0035f,.0080f),new Vector3(.0050f,.0005f,.0070f),neutral,root)
                        .transform.localRotation=Quaternion.Euler(0,0,-25);
                }
                propObjects[i]=root.gameObject;
            }
        }
        GameObject Shape(PrimitiveType type,string label,Vector3 p,Vector3 scale,Color color,Transform parent){
            var g=GameObject.CreatePrimitive(type);g.name=label;g.transform.SetParent(parent,false);
            g.transform.localPosition=p;g.transform.localScale=scale;g.GetComponent<Renderer>().sharedMaterial=Mat(color);
            RemoveCollider(g);return g;
        }
        void BuildWorld(){
            var board=Shape(PrimitiveType.Cube,"Airport diagram",new Vector3(0,-.001f,0),new Vector3(.24f,.001f,.16f),Color.white,Content);
            var m=new Material(Shader.Find("Unlit/Texture"));m.mainTexture=Resources.Load<Texture2D>("AirportBoard");
            // A dedicated top-facing quad prevents cube UVs rotating the target artwork.
            board.SetActive(false);
            var top=GameObject.CreatePrimitive(PrimitiveType.Quad);top.name="Board image";top.transform.SetParent(Content,false);
            top.transform.localRotation=Quaternion.Euler(90,0,0);top.transform.localScale=new Vector3(.24f,.16f,1);
            top.GetComponent<Renderer>().sharedMaterial=m;RemoveCollider(top);
            var terminal=new Color(.17f,.28f,.36f);
            Shape(PrimitiveType.Cube,"Terminal",new Vector3(0,.004f,.061f),new Vector3(.18f,.008f,.017f),terminal,Content);
            for(int i=0;i<2;i++)Shape(PrimitiveType.Cube,"Stand "+(i==0?"A":"B"),
                new Vector3(i==0?-.045f:.035f,.002f,.047f),new Vector3(.004f,.004f,.015f),new Color(.5f,.61f,.65f),Content);
            BuildAircraft();
            BuildProps();
            // Occluders (for example a service canopy) are neutral roof slabs; they hide what lies under them from the camera.
            foreach(var o in Data.occluders??new Occluder[0])
                Shape(PrimitiveType.Cube,"Occluder "+o.id,new Vector3(o.x,o.height,o.z),new Vector3(o.width,.0008f,o.depth),new Color(.62f,.66f,.68f),Content);
            BuildPaths();
        }
        static void ReleaseObject(GameObject obj){obj.SetActive(false);if(Application.isPlaying)Destroy(obj);else DestroyImmediate(obj);}
        void BuildAircraft(){
            foreach(var old in planes??new Transform[0])if(old!=null)ReleaseObject(old.gameObject);
            planes=new Transform[Data.aircraft.Length];landingGear=new Transform[planes.Length][];aircraftRigs=new AircraftTypeRig[planes.Length];
            for(int i=0;i<planes.Length;i++){
                var root=new GameObject(Data.aircraft[i].id).transform;root.SetParent(Content,false);planes[i]=root;
                if(string.IsNullOrEmpty(Data.aircraft[i].aircraftType))AircraftVisual.Build(root,LiveryOf(i));
                else aircraftRigs[i]=AircraftTypeVisual.Build(root,LiveryOf(i),Data.aircraft[i].aircraftType);
                landingGear[i]=root.GetComponentsInChildren<Transform>(true).Where(t=>t.name=="Main wheel"||t.name=="Nose wheel"||t.name=="Gear strut").ToArray();
            }
        }
        void BuildPaths(){
            foreach(Transform child in Content.Cast<Transform>().ToArray())if(child.name.EndsWith(" authored path",StringComparison.Ordinal))ReleaseObject(child.gameObject);
            foreach(var a in Data.aircraft) {
                var g=new GameObject(a.id+" authored path");g.transform.SetParent(Content,false);
                var l=g.AddComponent<LineRenderer>();l.enabled=!TrainingPresentation;l.useWorldSpace=false;l.positionCount=a.waypoints.Length;l.widthMultiplier=.0007f;
                l.sharedMaterial=new Material(Shader.Find("Sprites/Default"));l.startColor=l.endColor=a.id=="A1"?Color.cyan:new Color(1,.7f,.2f);
                l.SetPositions(a.waypoints.Select(w=>new Vector3(w.x,.0003f,w.z)).ToArray());
            }
        }
        RectTransform Panel(Transform parent,string name,Vector2 min,Vector2 max,Color color){
            var g=new GameObject(name,typeof(RectTransform),typeof(Image));g.transform.SetParent(parent,false);
            var r=g.GetComponent<RectTransform>();r.anchorMin=min;r.anchorMax=max;r.offsetMin=r.offsetMax=Vector2.zero;
            g.GetComponent<Image>().color=color;return r;
        }
        Text Label(Transform parent,string value,Vector2 min,Vector2 max,int size,TextAnchor align=TextAnchor.MiddleLeft,Color? color=null){
            var g=new GameObject("Text",typeof(RectTransform),typeof(Text));g.transform.SetParent(parent,false);
            var r=g.GetComponent<RectTransform>();r.anchorMin=min;r.anchorMax=max;r.offsetMin=new Vector2(24,0);r.offsetMax=new Vector2(-24,0);
            var t=g.GetComponent<Text>();t.font=font;t.fontSize=size;t.color=color??ink;t.alignment=align;t.text=value;
            t.horizontalOverflow=HorizontalWrapMode.Wrap;t.verticalOverflow=VerticalWrapMode.Truncate;t.raycastTarget=false;return t;
        }
        RectTransform Button(Transform parent,string title,Vector2 min,Vector2 max,UnityEngine.Events.UnityAction action,Color? color=null,int size=27){
            var r=Panel(parent,title,min,max,color??card);var button=r.gameObject.AddComponent<Button>();
            button.targetGraphic=r.GetComponent<Image>();button.onClick.AddListener(action);
            Label(r,title,Vector2.zero,Vector2.one,size,TextAnchor.MiddleCenter);return r;
        }
        string ChipLabel(AircraftPlan a)=>Data.aircraft.Length==2?a.id+"  /  "+a.FlightAt(Clock.Time):a.id+"\n"+a.FlightAt(Clock.Time);
        void UpdateSafeArea(){
            if(safeRoot==null||Screen.width==0||Screen.height==0)return;
            var safe=Screen.safeArea;
            safeRoot.anchorMin=new Vector2(safe.xMin/Screen.width,safe.yMin/Screen.height);
            safeRoot.anchorMax=new Vector2(safe.xMax/Screen.width,safe.yMax/Screen.height);
        }
        void BuildAircraftChips(Transform head){
            foreach(var old in aircraftChips??new Image[0])if(old!=null)ReleaseObject(old.gameObject);
            int count=Data.aircraft.Length;float gap=.03f,width=(.93f-(count-1)*gap)/count;
            aircraftChips=new Image[count];aircraftChipLabels=new Text[count];
            for(int i=0;i<count;i++){
                int index=i;var a=Data.aircraft[i];
                var r=Button(head,ChipLabel(a),
                    new Vector2(.035f+i*(width+gap),.025f),new Vector2(.035f+i*(width+gap)+width,.455f),()=>SelectAircraft(index),panel,count==2?39:33);
                aircraftChips[i]=r.GetComponent<Image>();aircraftChipLabels[i]=r.GetComponentInChildren<Text>();
                // Uniform-livery scenarios use one neutral marker so the chips do not imply colour identity.
                Panel(r,"Aircraft color",new Vector2(0,0),new Vector2(.015f,1),Data.UniformLivery?muted:i==0?teal:i==1?amber:LiveryOf(i));
                if(WorldScale)r.anchorMax=new Vector2(r.anchorMax.x,.60f);
            }
        }
        void BuildUI(){
            font=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var canvas=new GameObject("Coordinator UI",typeof(Canvas),typeof(CanvasScaler),typeof(GraphicRaycaster));canvas.transform.SetParent(transform,false);
            canvas.GetComponent<Canvas>().renderMode=RenderMode.ScreenSpaceOverlay;
            var scale=canvas.GetComponent<CanvasScaler>();scale.uiScaleMode=CanvasScaler.ScaleMode.ScaleWithScreenSize;scale.referenceResolution=new Vector2(1080,1920);scale.matchWidthOrHeight=.5f;
            if(FindFirstObjectByType<EventSystem>()==null)new GameObject("EventSystem",typeof(EventSystem),typeof(StandaloneInputModule));
            safeRoot=Panel(canvas.transform,"Safe area",Vector2.zero,Vector2.one,Color.clear);safeRoot.GetComponent<Image>().raycastTarget=false;
            var head=Panel(safeRoot,"Header",new Vector2(0,.84f),Vector2.one,card);
            Label(head,"AirfieldLens",new Vector2(.015f,.69f),new Vector2(.68f,.99f),47);
            status=Label(head,"",new Vector2(.015f,.47f),new Vector2(.985f,.68f),33);
            BuildAircraftChips(head);
            var caption=Panel(safeRoot,"Selected scene identity",new Vector2(.035f,.529f),new Vector2(.965f,.565f),new Color(.055f,.095f,.13f,.9f));captionPanel=caption;
            selectionLabel=Label(caption,"",Vector2.zero,Vector2.one,33,TextAnchor.MiddleCenter,Color.white);
            var tabs=Panel(safeRoot,"View tabs",new Vector2(0,.455f),new Vector2(1,.522f),card);tabsPanel=tabs;
            tabChips=new Image[3];string[] names={"now","why","history"};
            for(int i=0;i<3;i++){string tab=names[i];var r=Button(tabs,char.ToUpper(tab[0])+tab.Substring(1),new Vector2(i/3f,0),new Vector2((i+1)/3f,1),()=>SelectTab(tab),card,39);tabChips[i]=r.GetComponent<Image>();}
            body=Panel(safeRoot,"Inspector",new Vector2(0,.185f),new Vector2(1,.452f),panel);
            var transport=Panel(safeRoot,"Replay transport",Vector2.zero,new Vector2(1,.18f),card);
            clockLabel=Label(transport,"",new Vector2(.015f,.77f),new Vector2(.47f,.99f),39);
            Label(transport,"Replay time",new Vector2(.5f,.77f),new Vector2(.985f,.99f),33,TextAnchor.MiddleRight,muted);
            var track=Panel(transport,"Seek timeline hit area",new Vector2(.05f,.46f),new Vector2(.95f,.89f),Color.clear);
            var rail=Panel(track,"Visible timeline",new Vector2(0,.33f),new Vector2(1,.37f),new Color(.71f,.78f,.8f));rail.GetComponent<Image>().raycastTarget=false;
            slider=track.gameObject.AddComponent<Slider>();slider.minValue=0;slider.maxValue=Data.duration;
            var handleArea=Panel(track,"Handle area",new Vector2(0,.35f),new Vector2(1,.35f),Color.clear);
            handleArea.sizeDelta=new Vector2(0,32);handleArea.GetComponent<Image>().raycastTarget=false;
            var handle=Panel(handleArea,"Handle",Vector2.zero,Vector2.up,teal);handle.sizeDelta=new Vector2(32,0);
            slider.handleRect=handle;slider.targetGraphic=handle.GetComponent<Image>();
            slider.onValueChanged.AddListener(t=>{if(!updatingSlider)Seek(t);});
            var play=Button(transport,"Play",new Vector2(.035f,.035f),new Vector2(.535f,.45f),()=>{if(Clock.Playing)Pause();else Play();},teal,39);
            playLabel=play.GetComponentInChildren<Text>();playLabel.color=Color.white;playButton=play.GetComponent<Button>();
            Button(transport,"Restart",new Vector2(.555f,.035f),new Vector2(.795f,.45f),Restart,panel,39);
            Button(transport,"More",new Vector2(.815f,.035f),new Vector2(.965f,.45f),()=>{showTools=!showTools;if(WorldScale&&!DetailsOpen)SetDetails(true);bodyKey=null;ApplyScene();},panel,39);
            var ring=new GameObject("Selected aircraft ring");ring.transform.SetParent(Content,false);selectionRing=ring.AddComponent<LineRenderer>();
            selectionRing.useWorldSpace=false;selectionRing.loop=true;selectionRing.positionCount=48;selectionRing.widthMultiplier=.0007f;
            selectionRing.sharedMaterial=new Material(Shader.Find("Sprites/Default"));
            for(int i=0;i<48;i++){float a=i*Mathf.PI*2/48;selectionRing.SetPosition(i,new Vector3(Mathf.Sin(a)*.015f,.0009f,Mathf.Cos(a)*.015f));}
        }
        void ClearBody(){
            for(int i=body.childCount-1;i>=0;i--){var g=body.GetChild(i).gameObject;g.SetActive(false);if(Application.isPlaying)Destroy(g);else DestroyImmediate(g);}
        }
        void RebuildBody(){ClearBody();if(showTools)BuildTools();else if(SelectedTab=="now")BuildNow();else if(SelectedTab=="why")BuildWhy();else BuildHistory();}
        RectTransform Card(string name,float bottom,float top){return Panel(body,name,new Vector2(.035f,bottom),new Vector2(.965f,top),card);}
        public string ShortReport(ScenarioEvent report){
            if(report==null)return "No report received";
            if(report.facts!=null && report.facts.Length>0){
                var f=report.facts[0];
                switch(f.property){
                    case "stand":return "Stand "+f.value+" assigned";
                    case "baggage_status":return "Baggage service "+f.value;
                    case "fuel_status":return "Fuel service "+f.value;
                    case "route":return "Movement plan updated";
                    case "movement_status":return (LiveTraffic?"Movement: ":"Scripted movement ")+f.value;
                    case "movement_condition":return LiveTraffic?(f.value.StartsWith("hold")?"Movement on hold":f.value=="released"?"Hold released":f.value):report.message;
                    case "tobt":return "Off-block estimate: "+f.value;
                    case "trajectory_checkpoint":return "Checkpoint: "+f.value;
                }
            }
            return report.message.Length>75?report.message.Substring(0,72)+"…":report.message;
        }
        void BuildNow(){
            if(AwayNotice!=null){BuildAwayNotice();return;}
            var latest=SelectedReports.LastOrDefault();
            var update=Card("Latest change",.325f,.965f);
            Label(update,"LATEST RECEIVED UPDATE",new Vector2(.015f,.78f),new Vector2(.985f,.98f),33,TextAnchor.MiddleLeft,muted);
            Label(update,ShortReport(latest),new Vector2(.015f,.40f),new Vector2(.985f,.80f),43);
            Label(update,latest==null?"Nothing available at this checkpoint":$"Received {latest.receiptTime:0} s  ·  {latest.id}",new Vector2(.015f,.22f),new Vector2(.985f,.43f),33,TextAnchor.MiddleLeft,muted);
            if(latest!=null){
                update.gameObject.AddComponent<Button>().onClick.AddListener(()=>InspectReport(latest.id));
                Label(update,"Source & timing  →",new Vector2(.015f,.025f),new Vector2(.70f,.24f),39,TextAnchor.MiddleLeft,teal);
                if(latest.receiptTime>latest.eventTime)Label(update,"LATE",new Vector2(.72f,.025f),new Vector2(.985f,.24f),33,TextAnchor.MiddleRight,amber);
            }
            var readiness=Card("Readiness summary",.035f,.29f);
            readiness.gameObject.AddComponent<Button>().onClick.AddListener(()=>SelectTab("why"));
            Label(readiness,AwarenessTrack?"Reported restriction":"Departure readiness",new Vector2(.015f,0),new Vector2(.69f,1),39);
            var restriction=SelectedReports.LastOrDefault(e=>e.facts!=null && e.facts.Any(f=>f.property=="movement_condition"));
            var condition=restriction?.facts.First(f=>f.property=="movement_condition").value;
            var restrictionLabel=condition==null?"No report":condition.StartsWith("hold")?"Hold reported":condition=="released"?"Hold released":"See report";
            Label(readiness,AwarenessTrack?restrictionLabel+" ›":"Unknown  ›",new Vector2(.63f,0),new Vector2(.985f,1),AwarenessTrack?30:39,TextAnchor.MiddleRight,amber);
        }
        void BuildAwayNotice(){
            var notice=Card("While you were away",.035f,.965f);
            notice.gameObject.AddComponent<Button>().onClick.AddListener(DismissAwayNotice);
            Label(notice,"WHILE YOU WERE AWAY  ·  "+AwayNoticeSpan,new Vector2(.015f,.84f),new Vector2(.985f,.98f),33,TextAnchor.MiddleLeft,amber);
            const int shown=4;
            for(int i=0;i<Mathf.Min(shown,AwayNotice.Length);i++)
                Label(notice,AwayNotice[i],new Vector2(.015f,.66f-i*.16f),new Vector2(.985f,.82f-i*.16f),30);
            var more=AwayNotice.Length>shown?$"+{AwayNotice.Length-shown} more in History  ·  ":"";
            Label(notice,more+"Tap to dismiss",new Vector2(.015f,.02f),new Vector2(.985f,.14f),30,TextAnchor.MiddleRight,teal);
        }
        void ScrollText(Transform parent,string value,Vector2 min,Vector2 max,int size){
            var viewport=Panel(parent,"Scrollable text",min,max,Color.clear);viewport.gameObject.AddComponent<RectMask2D>();
            var scroll=viewport.gameObject.AddComponent<ScrollRect>();scroll.horizontal=false;scroll.movementType=ScrollRect.MovementType.Clamped;
            var t=Label(viewport,value,new Vector2(0,1),Vector2.one,size,TextAnchor.UpperLeft);t.supportRichText=false;
            var content=t.rectTransform;content.pivot=new Vector2(.5f,1);
            t.gameObject.AddComponent<ContentSizeFitter>().verticalFit=ContentSizeFitter.FitMode.PreferredSize;
            scroll.content=content;scroll.viewport=viewport;
        }
        void BuildWhy(){
            var explanation=Card("Assistant explanation",.28f,.965f);
            Label(explanation,"Understand this aircraft",new Vector2(.01f,.70f),new Vector2(.99f,.98f),39);
            ScrollText(explanation,AwarenessTrack?Data.trainingObjective+" Answers describe received reports; they do not issue a clearance.":"Ask about its status, recent changes, or departure readiness. Answers use reports received by the selected time.",new Vector2(.01f,.05f),new Vector2(.99f,.69f),36);
            Button(body,"Ask assistant",new Vector2(.035f,.005f),new Vector2(.64f,.26f),()=>OpenConversation?.Invoke(),teal,39).GetComponentInChildren<Text>().color=Color.white;
            Button(body,"Sources",new Vector2(.66f,.005f),new Vector2(.965f,.26f),()=>{InspectedReportId="";SelectTab("history");},card,39);
        }
        void BuildHistory(){
            if(!string.IsNullOrEmpty(InspectedReportId)){BuildReportDetail(VisibleReports.First(e=>e.id==InspectedReportId));return;}
            Label(body,"Received reports",new Vector2(.015f,.86f),new Vector2(.985f,.99f),39);
            Button(body,SelectedAircraft.id+" only",new Vector2(.035f,.59f),new Vector2(.49f,.845f),()=>SetHistoryScope(false),!AllFlightsHistory?new Color(.82f,.92f,.92f):card,39);
            Button(body,"All flights",new Vector2(.51f,.59f),new Vector2(.965f,.845f),()=>SetHistoryScope(true),AllFlightsHistory?new Color(.82f,.92f,.92f):card,39);
            var viewport=Panel(body,"History viewport",new Vector2(.035f,.02f),new Vector2(.965f,.57f),Color.clear);viewport.gameObject.AddComponent<RectMask2D>();
            var scroll=viewport.gameObject.AddComponent<ScrollRect>();scroll.horizontal=false;scroll.movementType=ScrollRect.MovementType.Clamped;
            var content=new GameObject("Reports",typeof(RectTransform)).GetComponent<RectTransform>();content.SetParent(viewport,false);
            content.anchorMin=new Vector2(0,1);content.anchorMax=Vector2.one;content.pivot=new Vector2(.5f,1);content.sizeDelta=new Vector2(0,VisibleReports.Length*148);
            scroll.content=content;scroll.viewport=viewport;
            int row=0;foreach(var report in VisibleReports){
                var r=Panel(content,report.id,new Vector2(0,1),new Vector2(1,1),card);r.pivot=new Vector2(.5f,1);r.anchoredPosition=new Vector2(0,-row*148);r.sizeDelta=new Vector2(0,140);row++;
                r.gameObject.AddComponent<Button>().onClick.AddListener(()=>InspectReport(report.id));
                Label(r,ShortReport(report),new Vector2(.01f,.40f),new Vector2(.94f,.97f),39);
                Label(r,$"{report.flightInstance}  ·  {report.id}  ·  received {report.receiptTime:0} s",new Vector2(.01f,.04f),new Vector2(.94f,.42f),33,TextAnchor.MiddleLeft,muted);
                Label(r,"›",new Vector2(.91f,0),Vector2.one,35,TextAnchor.MiddleCenter,teal);
            }
        }
        void BuildReportDetail(ScenarioEvent report){
            Button(body,"‹  Reports",new Vector2(.035f,.735f),new Vector2(.39f,.99f),()=>{InspectedReportId="";ApplyScene();},card,39);
            Label(body,report.id+" / "+report.flightInstance,new Vector2(.40f,.735f),new Vector2(.985f,.99f),39,TextAnchor.MiddleRight);
            var message=Card("Report text",.45f,.73f);
            Label(message,report.source,new Vector2(.01f,.60f),new Vector2(.99f,1f),33,TextAnchor.MiddleLeft,teal);
            ScrollText(message,report.message,new Vector2(.01f,0),new Vector2(.99f,.60f),39);
            var timing=Card("Two timestamps",.28f,.44f);
            Label(timing,"Occurred",new Vector2(.01f,.51f),new Vector2(.49f,1),33,TextAnchor.MiddleLeft,muted);
            Label(timing,"Received",new Vector2(.51f,.51f),new Vector2(.99f,1),33,TextAnchor.MiddleLeft,muted);
            Label(timing,$"{report.eventTime:0} s",new Vector2(.01f,0),new Vector2(.49f,.58f),39);
            Label(timing,$"{report.receiptTime:0} s",new Vector2(.51f,0),new Vector2(.99f,.58f),39,TextAnchor.MiddleLeft,teal);
            Button(body,LiveTraffic?"Back to reports":$"Jump to receipt · {report.receiptTime:0} s",new Vector2(.035f,.005f),new Vector2(.965f,.26f),()=>{if(LiveTraffic){InspectedReportId="";bodyKey=null;ApplyScene();}else SeekToReportReceipt(report.id);},teal,39).GetComponentInChildren<Text>().color=Color.white;
        }
        void BuildTools(){
            Label(body,"Session options",new Vector2(.015f,.81f),new Vector2(.985f,.99f),39);
            Button(body,"Ask assistant",new Vector2(.035f,.55f),new Vector2(.965f,.805f),()=>{showTools=false;bodyKey=null;ApplyScene();OpenConversation?.Invoke();},card,39);
            Button(body,"Report history",new Vector2(.035f,.28f),new Vector2(.965f,.535f),()=>{showTools=false;InspectedReportId="";SelectTab("history");},card,39);
            Button(body,"Done",new Vector2(.035f,.01f),new Vector2(.965f,.265f),()=>{showTools=false;bodyKey=null;ApplyScene();},teal,39).GetComponentInChildren<Text>().color=Color.white;
        }
    }
}
