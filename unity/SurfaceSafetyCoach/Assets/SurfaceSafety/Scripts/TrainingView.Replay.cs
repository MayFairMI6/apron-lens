// SUBSTANTIVE: controller replay workspace. A read-only view of the replay service's
// single source cutoff: timeline, received reports, source inspection, handoff note, assistant.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

namespace SurfaceSafety {
    [Serializable] public class ReplayFact {public string factId,property,value,status;}
    [Serializable] public class ReplayReport {
        public string id,aircraftId,flightInstance,source,sourceKind,sourceLabel,message;
        public float eventTime,receiptTime,ageSeconds,sinceReceiptSeconds;public ReplayFact[] facts;
    }
    [Serializable] public class ReplayMarker {public string id,kind,sourceKind,aircraftId,flightInstance,label;public float time,eventTime;public bool passed;}
    [Serializable] public class ReplayNote {public string id,runId,text,aircraftId,flightInstance;public float cutoff;}
    [Serializable] public class ReplayChange {public float cutoff;public string[] factIds;}
    [Serializable] public class ReplayCameraLatest {public bool present;public string armLabel,text,meta,warning;}
    [Serializable] public class ReplayView {
        public string runId,exercise,title,scenarioId,scenarioHash,selectedAircraft,selectedFlight,evidenceDigest;
        public int viewRevision;public float cutoff,end,rate;public bool playing,readOnly,assistantPending;
        public ReplayReport[] reports,selectedReports;public ReplayMarker[] timeline;public ReplayNote[] notes;public ReplayChange changedSince;public ReplayCameraLatest cameraLatest;
    }
    [Serializable] public class ReplayActionBody {
        public string actionId,runId,action,markerId="",aircraftId="",text="";
        public int viewRevision;public float cutoff,rate=1;public bool select;
    }
    [Serializable] public class ReplayQuestionBody {public string requestId,runId,question;public int viewRevision;}
    [Serializable] public class ReplayAnswer : ConversationResponse {public int viewRevision;public string aircraftId;}

    public partial class TrainingView {
        public ReplayView Replay {get;private set;}
        public string ReplayPanelMode=>panelMode;
        bool ReplayMode=>State!=null&&State.mode=="replay";
        ExternalTrafficDriver replayDriver;
        RectTransform replayBody,markerRoot;Slider scrubber;Text replayEnd,replayStatus,replayTime,replayHeading,playLabel,rateLabel,replayAnswerText;
        InputField noteInput,questionInput;
        string panelMode="reports",bodyKey="",inspectId="",syncedAircraft="",noteDraft="",questionDraft="",replayMessage="",markerKey="",chipKey="";
        bool replayBusy,scrubDirty,askBusy,selectRetry;int retryRevision=-1;
        readonly List<(ReplayReport report,Text tag,bool changed)> ageTags=new List<(ReplayReport,Text,bool)>();float scrubTarget,lastScrub=-10,playRate=1;
        ReplayAnswer replayAnswer;
        readonly List<(ReplayMarker marker,Image image)> markerImages=new List<(ReplayMarker,Image)>();
        Text camText,camMeta;
        readonly Color camBlue=new Color(.435f,.70f,1f),camRow=new Color(.067f,.141f,.227f),camLabel=new Color(.61f,.78f,.94f);
        readonly Color amber=new Color(.89f,.72f,.29f),rowColor=new Color(.075f,.14f,.19f);
        static readonly float[] replayRates={1,4,10};

        void ReplayStarted(){
            Replay=null;panelMode="reports";bodyKey="";inspectId="";syncedAircraft="";noteDraft="";questionDraft="";replayMessage="";replayAnswer=null;
            replayBusy=false;scrubDirty=false;askBusy=false;selectRetry=false;retryRevision=-1;ageTags.Clear();RunwayView();
        }
        public void ApplyReplay(ReplayView view,ExternalTrafficDriver driver){
            if(view==null||State==null||view.runId!=State.runId)return;
            if(Replay!=null&&Replay.runId==view.runId&&view.viewRevision<Replay.viewRevision)return;
            replayDriver=driver;Replay=view;
            // The service's selection wins unless a local tap is still being sent.
            if(!replayBusy&&!selectRetry&&syncedAircraft==SelectedPlane.id&&view.selectedAircraft!=SelectedPlane.id)SelectLocal(view.selectedAircraft);
            if(syncedAircraft=="")SelectLocal(view.selectedAircraft);
        }
        void SelectLocal(string aircraftId){
            int index=Array.FindIndex(replay.Data.aircraft,a=>a.id==aircraftId);
            if(index>=0)replay.SelectAircraft(index);syncedAircraft=SelectedPlane.id;selection=replay.SelectedFlight;
        }
        static string Clock(float seconds)=>TimeSpan.FromSeconds(Mathf.Max(0,seconds)).ToString(@"mm\:ss");
        Rect ReplayTagBounds()=>new Rect(root.rect.xMin+root.rect.width*.025f,root.rect.yMin+root.rect.height*(landscape?.25f:.52f),
            root.rect.width*(landscape?.585f:.945f),root.rect.height*(landscape?.52f:.285f));

        void BuildReplay(){
            replayBody=null;markerRoot=null;scrubber=null;noteInput=null;questionInput=null;replayAnswerText=null;bodyKey="";markerKey="";chipKey="";markerImages.Clear();
            camera.rect=landscape?new Rect(.015f,.06f,.61f,.78f):new Rect(.015f,.405f,.97f,.445f);
            tagRoot=Box(root,"Flight labels",Vector2.zero,Vector2.one,Color.clear,false);BuildTags();
            var tools=Box(root,"View controls",new Vector2(.025f,landscape?.78f:.815f),new Vector2(landscape?.61f:.97f,.855f),Color.clear,false);
            Button(tools,"Region",new Vector2(0,0),new Vector2(.2f,1),Overview);
            Button(tools,"Runway",new Vector2(.22f,0),new Vector2(.42f,1),RunwayView);
            Button(tools,"Follow flight",new Vector2(.44f,0),new Vector2(.72f,1),Focus);
            Button(tools,"−",new Vector2(.75f,0),new Vector2(.86f,1),()=>distance=Mathf.Min(12000,distance+(distance>400?200:35)));
            Button(tools,"+",new Vector2(.88f,0),Vector2.one,()=>distance=Mathf.Max(65,distance-(distance>400?200:35)));
            float stripBottom=landscape?.06f:.405f,stripTop=landscape?.215f:.49f;
            Label(root,"Training scenario · Map © OpenStreetMap contributors",new Vector2(.03f,stripTop),new Vector2(landscape?.62f:.97f,stripTop+(landscape?.03f:.025f)),landscape?15:17,Color.white);
            var strip=Box(root,"Replay timeline",new Vector2(.025f,stripBottom),new Vector2(landscape?.61f:.975f,stripTop),new Color(navy.r,navy.g,navy.b,.94f));
            replayStatus=Label(strip,"",new Vector2(.015f,landscape?.68f:.62f),new Vector2(.985f,.98f),landscape?20:22,Color.white);
            float rowMin=landscape?.27f:.08f,rowMax=landscape?.66f:.58f;
            playLabel=Button(strip,"Play",new Vector2(.015f,rowMin),new Vector2(landscape?.095f:.125f,rowMax),TogglePlay,true).GetComponentInChildren<Text>();
            replayTime=Label(strip,"",new Vector2(landscape?.105f:.135f,rowMin),new Vector2(landscape?.185f:.245f,rowMax),landscape?21:23,Color.white);
            BuildScrubber(strip,new Vector2(landscape?.19f:.25f,rowMin),new Vector2(landscape?.60f:.68f,rowMax));
            replayEnd=landscape?Label(strip,"",new Vector2(.605f,rowMin),new Vector2(.675f,rowMax),19,muted):null;
            rateLabel=Button(strip,"1×",new Vector2(landscape?.68f:.69f,rowMin),new Vector2(landscape?.74f:.79f,rowMax),CycleRate).GetComponentInChildren<Text>();
            Button(strip,landscape?"‹ Event":"‹",new Vector2(landscape?.75f:.805f,rowMin),new Vector2(landscape?.865f:.89f,rowMax),()=>JumpEvent(-1));
            Button(strip,landscape?"Event ›":"›",new Vector2(landscape?.875f:.9f,rowMin),new Vector2(.985f,rowMax),()=>JumpEvent(1));
            if(landscape){
                Box(strip,"Legend report",new Vector2(.017f,.07f),new Vector2(.021f,.21f),teal,false);
                Label(strip,"Report received",new Vector2(.03f,.02f),new Vector2(.19f,.25f),15,muted);
                var diamond=Box(strip,"Legend movement",new Vector2(.205f,.14f),new Vector2(.205f,.14f),amber,false);diamond.sizeDelta=new Vector2(10,10);diamond.localRotation=Quaternion.Euler(0,0,45);
                Label(strip,"Movement change",new Vector2(.22f,.02f),new Vector2(.40f,.25f),15,muted);
                Label(strip,"Later reports stay hidden until received",new Vector2(.42f,.02f),new Vector2(.985f,.25f),15,muted);
            }
            side=Box(root,"Replay panel",new Vector2(landscape?.65f:.025f,.045f),new Vector2(landscape?.98f:.975f,landscape?.85f:.395f),panel);
            replayHeading=Label(side,"",new Vector2(.04f,landscape?.82f:.75f),new Vector2(.96f,landscape?.885f:.85f),landscape?21:24,Color.white);
            replayBody=Box(side,"Replay body",new Vector2(.04f,landscape?.115f:.175f),new Vector2(.96f,landscape?.815f:.745f),Color.clear,false);
            float tabTop=landscape?.1f:.155f;
            Button(side,"Reports",new Vector2(.04f,.015f),new Vector2(.265f,tabTop),()=>SetPanel("reports"));
            Button(side,"Changed",new Vector2(.275f,.015f),new Vector2(.5f,tabTop),()=>SetPanel("changed"));
            Button(side,"Note",new Vector2(.51f,.015f),new Vector2(.725f,tabTop),()=>SetPanel("note"));
            Button(side,"Ask",new Vector2(.735f,.015f),new Vector2(.96f,tabTop),()=>SetPanel("ask"),true);
        }
        void BuildScrubber(Transform parent,Vector2 min,Vector2 max){
            // A visible hit surface: a clear Image may be culled on the iOS canvas.
            var track=Box(parent,"Timeline scrubber",min,max,new Color(.045f,.085f,.12f,.6f));
            Box(track,"Track",new Vector2(0,.46f),new Vector2(1,.54f),line,false);
            var fillArea=Box(track,"Fill area",new Vector2(0,.46f),new Vector2(1,.54f),Color.clear,false);
            var fill=Box(fillArea,"Fill",Vector2.zero,Vector2.one,teal,false);
            markerRoot=Box(track,"Markers",Vector2.zero,Vector2.one,Color.clear,false);
            var handleArea=Box(track,"Handle area",Vector2.zero,Vector2.one,Color.clear,false);
            var handle=Box(handleArea,"Handle",new Vector2(0,.08f),new Vector2(0,.92f),Color.white,false);handle.sizeDelta=new Vector2(6,0);
            scrubber=track.gameObject.AddComponent<Slider>();scrubber.fillRect=fill;scrubber.handleRect=handle;scrubber.targetGraphic=handle.GetComponent<Image>();
            scrubber.direction=Slider.Direction.LeftToRight;scrubber.minValue=0;scrubber.maxValue=Mathf.Max(1,Replay?.end??1);scrubber.transition=Selectable.Transition.None;
            scrubber.onValueChanged.AddListener(value=>{scrubTarget=value;scrubDirty=true;lastScrub=Time.unscaledTime;});
        }
        void SetPanel(string mode){
            if(mode==panelMode&&mode=="reports")inspectId="";
            panelMode=mode;if(mode!="reports")inspectId="";bodyKey="";
        }
        void UpdateReplay(){
            if(clockText!=null)clockText.text="Controller replay  ·  Read-only  ·  Source "+Clock(replay.Clock.Time);
            if(notice!=null)notice.text=!Connected?"Connection interrupted · waiting for the replay service":"";
            if(Replay==null||replayBody==null)return;
            // A tap on a label or chip changes the local selection; send it so every part uses one aircraft.
            if(SelectedPlane.id!=syncedAircraft&&!replayBusy){syncedAircraft=SelectedPlane.id;selection=replay.SelectedFlight;SendReplay("select",aircraft:syncedAircraft);}
            // After a refused control, wait for the newer view before sending it again.
            if(selectRetry&&!replayBusy&&Replay.viewRevision!=retryRevision){selectRetry=false;SendReplay("select",aircraft:SelectedPlane.id);}
            if(scrubDirty&&!replayBusy&&Replay.viewRevision!=retryRevision){scrubDirty=false;SendReplay("seek",cutoff:scrubTarget);}
            if(scrubber!=null){
                if(Mathf.Abs(scrubber.maxValue-Replay.end)>.01f)scrubber.maxValue=Replay.end;
                if(!scrubDirty&&!replayBusy&&Time.unscaledTime-lastScrub>.4f)scrubber.SetValueWithoutNotify(replay.Clock.Time);
            }
            replayTime.text=Clock(replay.Clock.Time);if(replayEnd!=null)replayEnd.text=Clock(Replay.end);playLabel.text=Replay.playing?"Pause":"Play";
            rateLabel.text=(Replay.playing?Replay.rate:playRate).ToString("0")+"×";
            replayStatus.text=StatusLine();
            replayHeading.text=panelMode=="changed"?"Changed since "+Clock(Replay.changedSince?.cutoff??0)+" · "+Replay.selectedFlight:
                panelMode=="note"?"Handoff note · "+Clock(Replay.cutoff)+" · "+Replay.selectedFlight:
                panelMode=="ask"?"Ask about "+Replay.selectedFlight+" at "+Clock(Replay.cutoff):
                "Received by "+Clock(Replay.cutoff)+" · "+Replay.selectedFlight;
            RefreshMarkers();RefreshChips();RefreshBody();UpdateCameraCard();
            // Ages follow the cutoff every frame; the rows themselves rebuild only when the received set changes.
            foreach(var (report,tag,changed) in ageTags){
                if(tag==null)continue;float since=Replay.cutoff-report.receiptTime;bool isNew=changed&&since<.5f;
                var fact=(report.facts??new ReplayFact[0]).FirstOrDefault();bool current=fact==null||fact.status=="current";
                tag.text=isNew?"New at "+Clock(report.receiptTime):!current?Sentence(fact.status):Age(Replay.cutoff-report.eventTime)+" old";tag.color=isNew?amber:muted;
            }
            // An answer belongs to the view it was asked under; a later view never shows it as current.
            if(replayAnswer!=null&&(replayAnswer.viewRevision<Replay.viewRevision||replayAnswer.aircraftId!=Replay.selectedAircraft)){
                replayAnswer=null;replayMessage="The replay moved. Ask again for this time and aircraft.";if(panelMode=="ask")RefreshAnswerText();
            }
        }
        string StatusLine(){
            // Aircraft that appear on the timeline: the ones this incident is about.
            var parts=new List<string>();
            foreach(var id in KeyAircraft()){
                var plan=Array.Find(replay.Data.aircraft,a=>a.id==id);if(plan==null)continue;
                var phase=plan.PhaseAt(replay.Clock.Time);
                parts.Add(plan.flightInstance+" · "+(plan.hidden?"Sector contact":!plan.VisibleAt(replay.Clock.Time)?"Not yet at the airport":phase==null?"On the apron":phase.label));
            }
            return string.Join("    |    ",parts);
        }
        IEnumerable<string> KeyAircraft()=>(Replay.timeline??new ReplayMarker[0]).Select(m=>m.aircraftId).Distinct().OrderBy(id=>id).Take(3);
        void RefreshMarkers(){
            var key=Replay.runId+"|"+(Replay.timeline?.Length??0)+"|"+Replay.end;
            if(key!=markerKey){
                markerKey=key;foreach(Transform child in markerRoot)Destroy(child.gameObject);markerImages.Clear();
                foreach(var marker in Replay.timeline??new ReplayMarker[0]){
                    float x=Replay.end<=0?0:Mathf.Clamp01(marker.time/Replay.end);bool movement=marker.kind=="movement";
                    var r=Box(markerRoot,marker.id,new Vector2(x,.5f),new Vector2(x,.5f),teal,false);
                    r.sizeDelta=movement?new Vector2(11,11):new Vector2(5,22);if(movement)r.localRotation=Quaternion.Euler(0,0,45);
                    markerImages.Add((marker,r.GetComponent<Image>()));
                }
            }
            foreach(var (marker,image) in markerImages){
                bool passed=marker.time<=Replay.cutoff+.001f;bool movement=marker.kind=="movement";
                image.color=movement?(passed?amber:new Color(.43f,.42f,.33f)):(passed?teal:new Color(.23f,.32f,.40f));
            }
        }
        void RefreshChips(){
            var ids=KeyAircraft().ToArray();var key=string.Join(",",ids)+"|"+Replay.selectedAircraft+"|"+landscape;
            if(key==chipKey)return;chipKey=key;
            var old=side.Find("Aircraft chips");if(old!=null)Destroy(old.gameObject);
            var chips=Box(side,"Aircraft chips",new Vector2(.04f,landscape?.895f:.865f),new Vector2(.96f,.985f),Color.clear,false);
            for(int i=0;i<ids.Length;i++){
                var plan=Array.Find(replay.Data.aircraft,a=>a.id==ids[i]);if(plan==null)continue;int index=Array.IndexOf(replay.Data.aircraft,plan);
                float width=1f/ids.Length;
                string kind=plan.hidden?"sector contact":string.IsNullOrEmpty(plan.aircraftType)?"":plan.aircraftType.Split('_')[0].ToUpperInvariant().Replace("B7","7");
                var b=Button(chips,plan.flightInstance+(kind==""?"":"  ·  "+kind),new Vector2(i*width,0),new Vector2((i+1)*width-.015f,1),()=>replay.SelectAircraft(index));
                if(ids[i]==Replay.selectedAircraft)b.GetComponent<Image>().color=new Color(.035f,.43f,.39f);
                b.GetComponentInChildren<Text>().fontSize=landscape?18:22;
            }
        }
        void RefreshBody(){
            var key=panelMode=="note"?"note|"+(Replay.notes?.Length??0)+"|"+(Replay.notes??new ReplayNote[0]).Count(n=>n.cutoff<=Replay.cutoff+.001f):panelMode=="ask"?"ask":
                panelMode+"|"+ReportKey()+"|"+(CameraCard?"cam":"")+"|"+Replay.selectedAircraft+"|"+inspectId+"|"+(inspectId==""?0:Mathf.Floor(Replay.cutoff))+"|"+(Replay.changedSince?.cutoff??0)+"|"+string.Join(",",Replay.changedSince?.factIds??new string[0]);
            if(key==bodyKey)return;bodyKey=key;
            foreach(Transform child in replayBody)Destroy(child.gameObject);
            noteInput=null;questionInput=null;replayAnswerText=null;camText=null;camMeta=null;ageTags.Clear();
            var selected=Replay.selectedReports??new ReplayReport[0];
            if(panelMode=="note"){BuildNote();return;}
            if(panelMode=="ask"){BuildAsk();return;}
            if(panelMode=="changed"){
                var ids=new HashSet<string>(Replay.changedSince?.factIds??new string[0]);
                var rows=selected.Where(r=>(r.facts??new ReplayFact[0]).Any(f=>ids.Contains(f.factId))).Reverse().ToArray();
                if(rows.Length==0){ScrollText(replayBody,"No report for "+Replay.selectedFlight+" has arrived or changed status since "+Clock(Replay.changedSince?.cutoff??0)+".\n\nMovement in the scene is authored motion. It is not a report.",Vector2.zero,Vector2.one,landscape?21:25,out _);return;}
                BuildRows(rows,true);return;
            }
            var inspected=Array.Find(selected,r=>r.id==inspectId);
            if(inspected!=null){BuildSource(inspected);return;}
            inspectId="";
            var area=replayBody;
            if(CameraCard){BuildCameraCard();area=Box(replayBody,"Report area",Vector2.zero,new Vector2(1,.555f),Color.clear,false);}
            if(selected.Length==0){ScrollText(area,"No report or observation for "+Replay.selectedFlight+" has been received by the time shown.",Vector2.zero,Vector2.one,landscape?21:25,out _);return;}
            BuildRows(selected.Reverse().ToArray(),false,area);
        }
        bool CameraCard=>Replay!=null&&Replay.cameraLatest!=null&&Replay.cameraLatest.present&&panelMode=="reports";
        string ReportKey()=>string.Join(",",(Replay.reports??new ReplayReport[0]).Select(r=>r.id+":"+string.Join("/",(r.facts??new ReplayFact[0]).Select(f=>f.status))));
        // Camera observation card: wording comes from the replay service; it is never a report and is listed apart from them.
        void BuildCameraCard(){
            int small=landscape?16:19,main=landscape?21:25;
            var card=Box(replayBody,"Camera observation",new Vector2(0,.575f),Vector2.one,camRow);
            Box(card,"Accent",Vector2.zero,new Vector2(.012f,1),camBlue,false);
            Label(card,"Camera observation · "+Replay.cameraLatest.armLabel,new Vector2(.035f,.78f),new Vector2(.75f,.98f),small,camLabel);
            var latest=Label(card,"Latest",new Vector2(.7f,.78f),new Vector2(.97f,.98f),small,camLabel);latest.alignment=TextAnchor.MiddleRight;
            camText=Label(card,"",new Vector2(.035f,.50f),new Vector2(.97f,.78f),main,Color.white);camText.alignment=TextAnchor.MiddleLeft;
            camMeta=Label(card,"",new Vector2(.035f,.25f),new Vector2(.97f,.50f),small,muted);camMeta.alignment=TextAnchor.MiddleLeft;
            var warn=Label(card,Replay.cameraLatest.warning,new Vector2(.035f,.02f),new Vector2(.97f,.25f),small,amber);warn.alignment=TextAnchor.MiddleLeft;
            UpdateCameraCard();
        }
        void UpdateCameraCard(){
            if(camText==null||Replay?.cameraLatest==null)return;
            camText.text=Replay.cameraLatest.text;camMeta.text=Replay.cameraLatest.meta;
        }
        void BuildRows(ReplayReport[] rows,bool changedOnly,RectTransform parent=null){
            var viewport=Box(parent??replayBody,"Report list",Vector2.zero,Vector2.one,panel);viewport.gameObject.AddComponent<RectMask2D>();
            var scroll=viewport.gameObject.AddComponent<ScrollRect>();scroll.horizontal=false;scroll.movementType=ScrollRect.MovementType.Clamped;scroll.scrollSensitivity=28;
            var content=new GameObject("Content",typeof(RectTransform)).GetComponent<RectTransform>();content.SetParent(viewport,false);
            content.anchorMin=new Vector2(0,1);content.anchorMax=Vector2.one;content.pivot=new Vector2(.5f,1);content.offsetMin=content.offsetMax=Vector2.zero;
            var layout=content.gameObject.AddComponent<VerticalLayoutGroup>();layout.childControlHeight=true;layout.childControlWidth=true;layout.childForceExpandHeight=false;layout.spacing=8;
            content.gameObject.AddComponent<ContentSizeFitter>().verticalFit=ContentSizeFitter.FitMode.PreferredSize;
            scroll.viewport=viewport;scroll.content=content;
            var changed=new HashSet<string>(Replay.changedSince?.factIds??new string[0]);
            int small=landscape?16:19,main=landscape?21:25;
            foreach(var report in rows){
                var fact=(report.facts??new ReplayFact[0]).FirstOrDefault();string value=fact==null?report.message:Sentence(fact.value);
                bool isNew=report.receiptTime>=(Replay.changedSince?.cutoff??0)&&(report.facts??new ReplayFact[0]).Any(f=>changed.Contains(f.factId))&&report.sinceReceiptSeconds<.5f;
                bool current=fact==null||fact.status=="current";
                var row=Box(content,"Report "+report.id,Vector2.zero,Vector2.one,rowColor);
                int lines=Mathf.CeilToInt(value.Length/(landscape?34f:42f));
                row.gameObject.AddComponent<LayoutElement>().preferredHeight=(landscape?70:82)+lines*(main+7);
                Box(row,"Accent",Vector2.zero,new Vector2(.012f,1),isNew?amber:current?teal:line,false);
                Label(row,report.sourceLabel,new Vector2(.035f,.76f),new Vector2(.6f,.97f),small,muted);
                var tag=Label(row,isNew?"New at "+Clock(report.receiptTime):!current?Sentence(fact.status):Age(report.ageSeconds)+" old",new Vector2(.5f,.76f),new Vector2(.97f,.97f),small,isNew?amber:muted);
                tag.alignment=TextAnchor.MiddleRight;ageTags.Add((report,tag,(report.facts??new ReplayFact[0]).Any(f=>changed.Contains(f.factId))));
                var text=Label(row,value,new Vector2(.035f,.25f),new Vector2(.97f,.76f),main,Color.white);text.alignment=TextAnchor.UpperLeft;
                Label(row,"Happened "+Clock(report.eventTime)+"  ·  Received "+Clock(report.receiptTime),new Vector2(.035f,.03f),new Vector2(.97f,.25f),small,muted);
                string id=report.id;row.gameObject.AddComponent<Button>().onClick.AddListener(()=>{inspectId=id;panelMode="reports";bodyKey="";});
            }
        }
        void BuildSource(ReplayReport report){
            var fact=(report.facts??new ReplayFact[0]).FirstOrDefault();float lag=report.receiptTime-report.eventTime;
            var name=report.source.Replace("exercise-","exercise ").Replace('-',' ');
            var text="“"+report.message+"”\n\nSource: "+report.sourceLabel+" · "+name+
                "\nAircraft: "+report.flightInstance+
                "\nHappened: "+Clock(report.eventTime)+
                "\nReceived: "+Clock(report.receiptTime)+(lag<.5f?" · as it happened":" · "+lag.ToString("0")+" s after it happened")+
                "\nAt "+Clock(Replay.cutoff)+": "+(fact==null?"received":fact.status)+" · "+Age(report.ageSeconds)+" old"+
                "\nReport ID: "+report.id+
                "\n\nSynthetic training report. Later reports stay hidden until their receipt time.";
            ScrollText(replayBody,text,new Vector2(0,.2f),Vector2.one,landscape?21:25,out _);
            Button(replayBody,"Back to reports",Vector2.zero,new Vector2(1,.16f),()=>{inspectId="";bodyKey="";});
        }
        void BuildNote(){
            var field=Box(replayBody,"Handoff note",new Vector2(0,.52f),Vector2.one,line);
            noteInput=field.gameObject.AddComponent<InputField>();noteInput.characterLimit=280;noteInput.lineType=InputField.LineType.MultiLineNewline;
            noteInput.textComponent=Label(field,"",new Vector2(.03f,.05f),new Vector2(.97f,.95f),landscape?21:25,Color.white);noteInput.textComponent.alignment=TextAnchor.UpperLeft;
            var hint=Label(field,"What is unresolved at this time?",new Vector2(.03f,.05f),new Vector2(.97f,.95f),landscape?21:25,muted);hint.alignment=TextAnchor.UpperLeft;
            noteInput.placeholder=hint;noteInput.text=noteDraft;noteInput.onValueChanged.AddListener(value=>noteDraft=value);
            int later=(Replay.notes??new ReplayNote[0]).Count(n=>n.cutoff>Replay.cutoff+.001f);
            var saved=(Replay.notes??new ReplayNote[0]).Where(n=>n.cutoff<=Replay.cutoff+.001f).Reverse().Select(n=>Clock(n.cutoff)+" · "+n.flightInstance+"\n"+n.text).ToArray();
            ScrollText(replayBody,(saved.Length==0?"":"SAVED NOTES\n"+string.Join("\n\n",saved)+"\n\n")+(later>0?later+" note(s) written at a later replay time are hidden here.\n\n":"")+"A note is saved with this replay run and time. It is an annotation and does not change the replay.",
                new Vector2(0,.2f),new Vector2(1,.5f),landscape?17:20,out _);
            Button(replayBody,"Save note",Vector2.zero,new Vector2(1,.16f),()=>{if(!string.IsNullOrWhiteSpace(noteDraft)&&!replayBusy)SendReplay("note",text:noteDraft.Trim());},true);
        }
        void BuildAsk(){
            var field=Box(replayBody,"Question",new Vector2(0,.8f),Vector2.one,line);
            questionInput=field.gameObject.AddComponent<InputField>();questionInput.characterLimit=400;questionInput.lineType=InputField.LineType.MultiLineNewline;
            questionInput.textComponent=Label(field,"",new Vector2(.03f,.05f),new Vector2(.97f,.95f),landscape?21:25,Color.white);
            questionInput.placeholder=Label(field,"Ask about this flight at this time…",new Vector2(.03f,.05f),new Vector2(.97f,.95f),landscape?21:25,muted);
            questionInput.text=questionDraft;questionInput.onValueChanged.AddListener(value=>questionDraft=value);
            Button(replayBody,"Latest report",new Vector2(0,.64f),new Vector2(.49f,.77f),()=>AskReplay("What is the latest reported movement for this flight?"));
            Button(replayBody,"What changed?",new Vector2(.51f,.64f),new Vector2(1,.77f),()=>AskReplay("What changed for this flight?"));
            replayAnswerText=ScrollText(replayBody,"",new Vector2(0,.2f),new Vector2(1,.62f),landscape?20:24,out _);
            Button(replayBody,"Ask assistant",Vector2.zero,new Vector2(1,.16f),()=>AskReplay(questionDraft),true);
            RefreshAnswerText();
        }
        void RefreshAnswerText(){
            if(replayAnswerText==null)return;
            if(askBusy){replayAnswerText.text="Checking the reports received by "+Clock(Replay.cutoff)+" for "+Replay.selectedFlight+"…";return;}
            if(replayAnswer==null){replayAnswerText.text=string.IsNullOrEmpty(replayMessage)?"The assistant uses only what had been received by the time shown.":replayMessage;return;}
            if(!replayAnswer.accepted){
                var pointed=replayAnswer.display?.selectedReportIds;
                replayAnswerText.text=pointed!=null&&pointed.Length>0?
                    "This answer is withheld: what is still unknown could not be stated in a supported way.\n\nRelevant report: "+string.Join(", ",pointed)+". Open Reports to read it.":
                    "That answer could not be supported by the reports received by "+Clock(replayAnswer.cutoff)+". Open Reports to read them.";
                return;
            }
            var d=replayAnswer.display??new ConversationDisplay();var lines=new List<string>();
            foreach(var claim in d.claims??new SupportedClaim[0]){
                var prop=(claim.fact_id??"").Split(':').Last();
                var label=prop=="movement_condition"?"Reported condition":prop=="movement_status"?"Movement":prop=="route"?"Reported route":prop=="trajectory_checkpoint"?"Observation":prop.Replace('_',' ');
                lines.Add(label+": "+claim.value+". ["+string.Join(", ",claim.evidence_ids??new string[0])+"]");
            }
            foreach(var unknown in d.unknowns??new string[0])lines.Add("No "+unknown.Replace('_',' ')+" report had been received.");
            if(lines.Count==0)lines.Add(d.answer??"No supported report answer is available.");
            lines.Add("Reports received by "+Clock(replayAnswer.cutoff)+" · "+(replayAnswer.referent?.flightInstance??Replay.selectedFlight));
            replayAnswerText.text=string.Join("\n\n",lines);
        }
        static string Sentence(string value)=>string.IsNullOrEmpty(value)?"":char.ToUpper(value[0])+value.Substring(1);
        static string Age(float seconds)=>seconds<60?seconds.ToString("0")+" s":Mathf.FloorToInt(seconds/60)+":"+Mathf.FloorToInt(seconds%60).ToString("00");

        void TogglePlay(){
            if(Replay==null)return;
            if(Replay.playing)SendReplay("pause");else SendReplay("play",rate:playRate);
        }
        void CycleRate(){
            playRate=replayRates[(Array.IndexOf(replayRates,playRate)+1)%replayRates.Length];
            if(Replay!=null&&Replay.playing)SendReplay("play",rate:playRate);
        }
        void JumpEvent(int direction){
            if(Replay?.timeline==null)return;float now=Replay.playing?replay.Clock.Time:Replay.cutoff;
            var marker=direction>0?Replay.timeline.FirstOrDefault(m=>m.time>now+.01f):Replay.timeline.LastOrDefault(m=>m.time<now-.01f);
            if(marker!=null)SendReplay("jump",marker:marker.id,select:true);
        }
        void SendReplay(string action,float cutoff=0,string marker="",string aircraft="",string text="",float rate=1,bool select=false){
            if(Replay==null||replayBusy)return;
            var body=new ReplayActionBody{actionId=Guid.NewGuid().ToString("N"),runId=Replay.runId,action=action,viewRevision=Replay.viewRevision,
                cutoff=cutoff,markerId=marker,aircraftId=aircraft,text=text,rate=rate,select=select};
            StartCoroutine(ReplayActionRequest(body));
        }
        IEnumerator ReplayActionRequest(ReplayActionBody body){
            replayBusy=true;
            using(var request=assistant.ReplayRequest("/replay/action",JsonUtility.ToJson(body),8)){
                yield return request.SendWebRequest();
                replayBusy=false;
                if(State==null||State.runId!=body.runId)yield break;
                if(request.result==UnityWebRequest.Result.Success){
                    var view=JsonUtility.FromJson<ReplayView>(request.downloadHandler.text);
                    replayDriver?.AcceptReplay(view);
                    if(body.action=="note"){noteDraft="";bodyKey="";}
                    ApplyReplay(view,replayDriver);
                    retryRevision=-1;
                    // Only a jump, or the selection this request asked for, sets the local aircraft; a newer tap stays.
                    if(view.selectedAircraft!=SelectedPlane.id&&(body.action=="jump"||(body.action=="select"&&SelectedPlane.id==body.aircraftId)))SelectLocal(view.selectedAircraft);
                }else if(request.responseCode==409){
                    // The view moved on (for example playback reached the end); the next poll shows it. Resend a selection.
                    retryRevision=body.viewRevision;
                    if(body.action=="select")selectRetry=true;
                    if(body.action=="seek"){scrubTarget=body.cutoff;scrubDirty=true;}
                }else if(request.responseCode==0)Connected=false;
            }
        }
        void AskReplay(string question){
            if(Replay==null||askBusy||string.IsNullOrWhiteSpace(question))return;
            questionDraft=question;if(questionInput!=null){questionInput.text=question;questionInput.DeactivateInputField();}
            StartCoroutine(ReplayQuestionRequest(new ReplayQuestionBody{requestId=Guid.NewGuid().ToString("N"),runId=Replay.runId,
                question=question.Trim(),viewRevision=Replay.viewRevision}));
        }
        IEnumerator ReplayQuestionRequest(ReplayQuestionBody body){
            askBusy=true;replayAnswer=null;replayMessage="";RefreshAnswerText();
            using(var request=assistant.ReplayRequest("/replay/question",JsonUtility.ToJson(body),90)){
                yield return request.SendWebRequest();
                askBusy=false;
                if(State==null||State.runId!=body.runId)yield break;
                if(request.result==UnityWebRequest.Result.Success){
                    var answer=JsonUtility.FromJson<ReplayAnswer>(request.downloadHandler.text);
                    // Shown only while the view it was asked under is still the current one.
                    if(Replay!=null&&answer.viewRevision>=Replay.viewRevision&&answer.aircraftId==Replay.selectedAircraft)replayAnswer=answer;
                    else replayMessage="The replay moved while the assistant was answering. Ask again for this time and aircraft.";
                }else replayMessage=request.responseCode==409?"The replay moved while the assistant was answering. Ask again for this time and aircraft.":
                    request.responseCode==429?"The assistant is answering another question. Try again shortly.":
                    request.responseCode==503?"The assistant is getting ready. Try again shortly.":"No answer was received. Open Reports to read the received reports.";
                RefreshAnswerText();
            }
        }
    }
}
