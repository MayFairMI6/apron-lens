using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.Networking;
using UnityEngine.UI;

namespace SurfaceSafety {
    [Serializable] public class TrainingCheckpoint {public string id,question;public float at;public string[] choices;}
    [Serializable] public class TrainingFeedback {
        public string checkpointId,question,chosen,correctAnswer,explanation;public bool correct;public float cutoff;
        public ScenarioEvent[] reports,laterReports;
        public string kind,verdict;public TrainingReviewPoint[] points;
    }
    [Serializable] public class TrainingReviewPoint {public string criterionId,status,comment,learnerQuote;public string[] evidenceIds;}
    [Serializable] public class TrainingResponse {public string actionId,runId,checkpointId,responseText;public int revision;}
    [Serializable] public class TrainingCue {public string id,question,status,aircraftId;public float cutoff;}
    [Serializable] public class TrainingPerspective {public string role,text;}
    [Serializable] public class TrainingState {
        public string runId,mode,phase,title,objective,exercise,targetAircraft,spotlightId,spotlightAircraft;
        public int revision,checkpointNumber,checkpointCount,score,answered;
        public float sourceTime,rate,nextBoundary;
        public TrainingCheckpoint checkpoint;public TrainingFeedback feedback;public TrainingFeedback[] reviews;
        public TrainingCue demoCue;public TrainingPerspective[] perspectives;
        public string assessmentMode,reviewStatus,reviewError,responseText;
    }
    [Serializable] public class TrainingAction {
        public string actionId,runId,action,checkpointId,cueId;public int revision,choice;public bool success;
    }

    // A presentation of the external session, never a second exercise clock.
    public class TrainingView : MonoBehaviour {
        public TrainingState State {get;private set;}
        public bool Connected {get;set;}=true;
        StandReplay replay;ConversationClient assistant;Camera camera;TrainingWeather weather;Light sceneSun;Transform sunParent;
        Canvas canvas;RectTransform root,side,tagRoot;Font font;
        Text title,subtitle,clockText,focusText,answerText,answerHeading,notice,motionText;
        GameObject runwayGeometry;TrainingIncidentEffects incidentEffects;string seenSpotlight="";bool followFlight;TrainingIncident focusIncident;
        TrainingGeography regional;GameObject apronEnvironment;RectTransform vehicleTag;
        bool Regional=>TrainingGeography.Present(replay.Data.geography);
        AircraftPlan SelectedPlane=>replay.Data.aircraft[replay.SelectedAircraftIndex];
        InputField input;Button askButton;ScrollRect answerScroll;
        InputField responseInput;Button reviewButton;Text reviewNotice;
        string responseDraft="",responseDraftKey="",responseError="",activeReviewId="";bool reviewBusy;
        string viewKey="",message="Choose a question or ask about the selected flight.",messageStatus="",seenCue="",pendingCue="";
        string selection="";bool sources,history,actionBusy,landscape,dragging;
        Vector2 lastPointer;Vector3 centre=new Vector3(75,0,-25);float distance=320;bool ground,terminalView;
        readonly List<RaycastResult> hits=new List<RaycastResult>();
        readonly List<RectTransform> tags=new List<RectTransform>();
        readonly List<RectTransform> tagLeaders=new List<RectTransform>();
        readonly List<int> tagSlots=new List<int>();
        readonly List<Rect> occupiedTags=new List<Rect>();
        RectTransform vehicleLeader;int vehicleSlot=-1;
        readonly List<GameObject> vehicles=new List<GameObject>();
        readonly Color navy=new Color(.025f,.055f,.08f),panel=new Color(.045f,.085f,.12f,.98f),
            muted=new Color(.66f,.75f,.79f),teal=new Color(.07f,.64f,.58f),line=new Color(.14f,.23f,.28f);
        int cameraMask;

        public void Bind(StandReplay r,ConversationClient a){
            replay=r;assistant=a;camera=Camera.main;cameraMask=camera.cullingMask;camera.farClipPlane=15000;
            replay.UseTrainingPresentation();assistant.ExternalPresentation=true;assistant.DisplayChanged+=OnAnswer;
            var look=camera.GetComponent<SimulatorLook>();if(look!=null)look.enabled=false;
            camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.54f,.64f,.70f);
            sceneSun=FindObjectsByType<Light>(FindObjectsSortMode.None).FirstOrDefault(l=>l.isActiveAndEnabled&&l.type==LightType.Directional);
            if(sceneSun!=null){sunParent=sceneSun.transform.parent;sceneSun.transform.SetParent(transform,true);}
            weather=camera.gameObject.AddComponent<TrainingWeather>();weather.Bind(replay,camera,sceneSun);
            font=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var go=new GameObject("Controller training",typeof(Canvas),typeof(CanvasScaler),typeof(GraphicRaycaster));
            go.transform.SetParent(transform,false);canvas=go.GetComponent<Canvas>();canvas.renderMode=RenderMode.ScreenSpaceOverlay;canvas.sortingOrder=20;
            root=Box(go.transform,"Safe area",Vector2.zero,Vector2.one,Color.clear,false);
            camera.transform.rotation=Quaternion.Euler(48,0,0);
        }
        void OnDestroy(){if(regional!=null)Destroy(regional.gameObject);if(apronEnvironment!=null)apronEnvironment.SetActive(true);if(sceneSun!=null)sceneSun.transform.SetParent(sunParent,true);if(weather!=null)Destroy(weather);if(runwayGeometry!=null)Destroy(runwayGeometry);if(assistant!=null){assistant.DisplayChanged-=OnAnswer;assistant.ExternalPresentation=false;assistant.TrainingQuestionBlocked=false;}}
        public void Apply(TrainingState state){
            if(state==null||string.IsNullOrEmpty(state.runId))return;
            if(State!=null&&State.runId==state.runId&&state.revision<State.revision)return;
            bool run=State==null||State.runId!=state.runId;
            bool phase=run||State.revision!=state.revision;
            var draftKey=state.runId+"|"+(state.checkpoint?.id??"");
            if(state.phase=="checkpoint"&&draftKey!=responseDraftKey){responseDraftKey=draftKey;responseDraft=state.responseText??"";responseError="";activeReviewId="";reviewBusy=false;}
            if(run){responseDraftKey=state.phase=="checkpoint"?draftKey:"";responseDraft=state.responseText??"";responseError="";reviewBusy=false;activeReviewId="";}
            if(state.phase!="checkpoint"){activeReviewId="";reviewBusy=false;responseError="";}
            State=state;
            if(phase){assistant.NewSession();assistant.TrainingQuestionBlocked=state.phase!="practice"&&state.phase!="debrief";pendingCue="";
                messageStatus="";message="Ask about the selected flight using the reports received so far.";sources=false;history=false;}
            if(run){
                sources=false;history=false;seenCue="";message="Choose a question or ask about the selected flight.";messageStatus="";
                var selected=Array.FindIndex(replay.Data.aircraft,a=>a.id==state.targetAircraft);replay.SelectAircraft(Mathf.Max(0,selected));
                selection=replay.SelectedFlight;BuildVehicles();Overview();seenSpotlight="";
                if(apronEnvironment==null)apronEnvironment=GameObject.Find("ApronEnvironment");
                if(apronEnvironment!=null)apronEnvironment.SetActive(!Regional);
                if(regional!=null){regional.gameObject.SetActive(false);Destroy(regional.gameObject);}
                if(Regional){var map=new GameObject("Heathrow regional map");map.transform.SetParent(replay.Content,false);regional=map.AddComponent<TrainingGeography>();regional.Bind(replay,sceneSun);map.AddComponent<TrainingRoadTraffic>().Bind(replay);}
                if(runwayGeometry!=null)Destroy(runwayGeometry);runwayGeometry=Regional?null:TrainingRunway.Build(replay.Content,replay.Data.runway,replay.Data.taxiPaths);
                if(incidentEffects!=null)Destroy(incidentEffects.gameObject);
                var effects=new GameObject("Training incident effects");effects.transform.SetParent(replay.Content,false);
                incidentEffects=effects.AddComponent<TrainingIncidentEffects>();incidentEffects.Bind(replay);
            }
            var spotlight=state.spotlightId??"";
            if(spotlight!=seenSpotlight){seenSpotlight=spotlight;
                if(spotlight!=""){
                    var selected=Array.FindIndex(replay.Data.aircraft,a=>a.id==state.spotlightAircraft);
                    if(selected>=0){replay.SelectAircraft(selected);ground=false;Focus();distance=spotlight=="stand-incident"?95:spotlight=="crash-landing"?125:190;}
                    if(Regional){distance=State.exercise=="water_landing"?260:State.exercise=="occupied_runway_go_around"?750:340;
                        if(spotlight=="incursion_vehicle"){followFlight=false;distance=100;}else if(spotlight=="runway_incursion"){followFlight=false;centre=new Vector3(replay.Data.geography.focusX*1000,0,replay.Data.geography.focusZ*1000);distance=2000;}}
                    // Imported fleet models use their reference length for readable framing.
                    // Incident close-ups and overview spotlights below keep their existing views.
                    if(Regional&&selected>=0&&(State.exercise??"").StartsWith("fleet_",StringComparison.Ordinal)){
                        var profile=AircraftTypeVisual.Find(replay.Data.aircraft[selected].aircraftType);
                        if(profile!=null)distance=profile.LengthMetres*3.5f;
                    }
                    if(spotlight=="goaround_overview")RunwayView();
                    if(spotlight=="region_intro")Overview();
                    if(spotlight=="wildlife-detail"||spotlight=="baggage-incident"||spotlight=="vehicle-collision"){
                        var kind=spotlight=="wildlife-detail"?"wildlife":spotlight=="vehicle-collision"?"vehicle_collision":"baggage_spill";
                        focusIncident=Array.Find(replay.Data.incidents??new TrainingIncident[0],i=>i.kind==kind);
                        followFlight=false;distance=spotlight=="wildlife-detail"?38:spotlight=="vehicle-collision"?70:45;
                    }
                }else{Overview();var selected=Array.FindIndex(replay.Data.aircraft,a=>a.id==state.targetAircraft);if(selected>=0)replay.SelectAircraft(selected);}
            }
            RebuildIfNeeded();
            if(state.demoCue!=null&&state.demoCue.status=="timeout"&&pendingCue==state.demoCue.id){
                assistant.NewSession();pendingCue="";messageStatus="UNAVAILABLE";message="The assistant request timed out. No answer was received.";RefreshAnswer();
            }
            if(state.mode=="demo"&&state.phase=="practice"&&state.demoCue!=null&&state.demoCue.status=="pending"&&seenCue!=state.demoCue.id&&!assistant.Busy){
                var cueAircraft=Array.FindIndex(replay.Data.aircraft,a=>a.id==state.demoCue.aircraftId);
                if(cueAircraft>=0&&cueAircraft!=replay.SelectedAircraftIndex){replay.SelectAircraft(cueAircraft);assistant.NewSession();selection=replay.SelectedFlight;}
                seenCue=state.demoCue.id;pendingCue=seenCue;history=false;sources=false;
                if(input!=null)input.text=state.demoCue.question;
                assistant.Ask(state.demoCue.question);
            }
        }
        void OnAnswer(string status,string text){
            messageStatus=status;message=status=="ANSWER WITHHELD"?"That answer could not be supported by the available reports. Please review Recent reports or ask again.":text;RefreshAnswer();
            if(!string.IsNullOrEmpty(pendingCue)&&status!="ASKING"){
                var cue=pendingCue;pendingCue="";SendAction("demo_answer",cue:cue,success:status=="CHECKED ANSWER");
            }
        }
        void Update(){
            if(State==null)return;
            var area=Screen.safeArea;
            root.anchorMin=new Vector2(area.xMin/Screen.width,area.yMin/Screen.height);
            root.anchorMax=new Vector2(area.xMax/Screen.width,area.yMax/Screen.height);
            RebuildIfNeeded();
            if(selection!=replay.SelectedFlight){
                selection=replay.SelectedFlight;assistant.NewSession();messageStatus="";sources=false;history=false;if(input!=null)input.text="";
                message="Ask about "+selection+" using the reports received so far.";RefreshAnswer();
            }
            clockText.text=(State.mode=="demo"?"Guided demonstration":State.mode=="continuous"?"Continuous exercise":"Practice")+
                "  ·  Scenario "+TimeSpan.FromSeconds(replay.Clock.Time).ToString(replay.Clock.Time>=3600?@"h\:mm\:ss":@"mm\:ss")+
                (State.rate>1?"  ·  Time-lapse · "+State.rate.ToString("0")+"×":"");
            if(focusText!=null)focusText.text="SELECTED FLIGHT  /  "+replay.SelectedFlight;
            if(motionText!=null){var phase=SelectedPlane.PhaseAt(replay.Clock.Time);
                var altitude=Scenario.Position(SelectedPlane,replay.Clock.Time).y*WorldArBootstrap.MetresPerBoardUnit;
                motionText.text=phase==null?"APRON  ·  Ground routes":replay.SelectedFlight+"  ·  "+phase.label+"  ·  "+altitude.ToString("0")+" m  ·  "+Scenario.Heading(SelectedPlane,replay.Clock.Time).ToString("000")+"°";}
            if(notice!=null)notice.text=!Connected?"Connection interrupted · waiting for the exercise service":actionBusy?"Updating exercise…":weather!=null?weather.ConditionLabel:"";
            if(askButton!=null)askButton.interactable=Connected&&!assistant.Busy&&!assistant.TrainingQuestionBlocked;
            if(reviewButton!=null){
                bool pending=reviewBusy||State.reviewStatus=="pending";
                reviewButton.interactable=Connected&&!pending&&!string.IsNullOrWhiteSpace(responseDraft);
                if(responseInput!=null)responseInput.interactable=!pending;
                reviewNotice.text=pending?"Reviewing your answer against the checkpoint reports…":!string.IsNullOrEmpty(responseError)?responseError:
                    State.reviewStatus=="failed"?(string.IsNullOrEmpty(State.reviewError)?"Your answer could not be reviewed. Please try again.":State.reviewError):"Explain what the reports establish and what remains unknown.";
            }
            if(history)RefreshAnswer();
            MoveCamera();UpdateTags();
            var plans=replay.Data.groundVehicles??new AircraftPlan[0];
            for(int i=0;i<vehicles.Count&&i<plans.Length;i++){
                vehicles[i].transform.localPosition=Scenario.Position(plans[i],replay.Clock.Time)+(Regional?Vector3.up*.0007f:Vector3.zero);
                var d=Scenario.Direction(plans[i],replay.Clock.Time);if(d.sqrMagnitude>.000001f)vehicles[i].transform.localRotation=Quaternion.LookRotation(d);
            }
        }
        void RebuildIfNeeded(){
            landscape=Screen.width>Screen.height;
            var key=State.runId+"|"+State.revision+"|"+landscape;
            if(key==viewKey)return;viewKey=key;
            foreach(Transform child in root)Destroy(child.gameObject);
            tags.Clear();tagLeaders.Clear();tagSlots.Clear();vehicleSlot=-1;vehicleLeader=null;vehicleTag=null;input=null;answerText=null;answerHeading=null;focusText=null;askButton=null;motionText=null;
            responseInput=null;reviewButton=null;reviewNotice=null;
            var scaler=canvas.GetComponent<CanvasScaler>();scaler.uiScaleMode=CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution=landscape?new Vector2(1600,900):new Vector2(900,1600);scaler.matchWidthOrHeight=.5f;
            bool modal=State.phase=="checkpoint"||State.phase=="feedback"||State.phase=="briefing";
            camera.cullingMask=State.phase=="checkpoint"?0:cameraMask;
            camera.rect=landscape?new Rect(.015f,.06f,.61f,.78f):new Rect(.015f,.51f,.97f,.32f);
            var header=Box(root,"Header",new Vector2(0,.87f),Vector2.one,navy);
            Label(header,"AIRFIELDLENS",new Vector2(.025f,.68f),new Vector2(.98f,.96f),landscape?18:22,muted);
            title=Label(header,State.title,new Vector2(.025f,.31f),new Vector2(.98f,.75f),landscape?32:34,Color.white);
            clockText=Label(header,"",new Vector2(.025f,.02f),new Vector2(.98f,.33f),landscape?18:22,teal);
            notice=Label(root,"",new Vector2(.025f,0),new Vector2(.98f,.035f),landscape?17:21,new Color(1,.74f,.35f));
            if(modal){BuildModal();return;}
            tagRoot=Box(root,"Flight labels",Vector2.zero,Vector2.one,Color.clear,false);
            BuildTags();
            var tools=Box(root,"View controls",new Vector2(.025f,landscape?.78f:.815f),new Vector2(landscape?.61f:.97f,.855f),Color.clear,false);
            Button(tools,Regional?"Region":"Apron",new Vector2(0,0),new Vector2(Regional?.16f:.23f,1),Overview);
            if(Regional)Button(tools,"Terminals",new Vector2(.18f,0),new Vector2(.39f,1),TerminalView);
            Button(tools,"Runway",new Vector2(Regional?.41f:.25f,0),new Vector2(Regional?.57f:.48f,1),RunwayView);
            Button(tools,"Follow flight",new Vector2(Regional?.59f:.50f,0),new Vector2(.77f,1),Focus);
            Button(tools,"−",new Vector2(.79f,0),new Vector2(.88f,1),()=>distance=Mathf.Min(Regional?12000:2400,distance+(distance>400?200:35)));
            Button(tools,"+",new Vector2(.9f,0),Vector2.one,()=>distance=Mathf.Max(65,distance-(distance>400?200:35)));
            var motion=Box(root,"Flight phase",new Vector2(.025f,landscape?.06f:.51f),new Vector2(landscape?.61f:.97f,landscape?.115f:.55f),navy,false);
            motionText=Label(motion,"",new Vector2(.025f,0),new Vector2(.98f,1),landscape?22:24,Color.white);
            if(Regional){
                Label(root,"Training scenario · Map © OpenStreetMap contributors",new Vector2(.03f,landscape?.12f:.555f),new Vector2(landscape?.62f:.97f,landscape?.15f:.58f),landscape?15:17,Color.white);
                if(vehicles.Count>0){vehicleTag=Box(tagRoot,"Vehicle label",Vector2.zero,Vector2.zero,panel);vehicleTag.sizeDelta=new Vector2(190,36);vehicleTag.pivot=new Vector2(.5f,0);vehicleLeader=BuildTagLeader();Label(vehicleTag,"Maintenance vehicle",Vector2.zero,Vector2.one,17,Color.white);}
            }
            side=Box(root,"Exercise panel",new Vector2(landscape?.65f:.025f,.045f),new Vector2(.98f,landscape?.85f:.495f),panel);
            if(State.phase=="debrief")BuildDebrief();else BuildAssistant();
        }
        void BuildModal(){
            Box(root,"Backdrop",Vector2.zero,new Vector2(1,.865f),State.phase=="checkpoint"?navy:new Color(.02f,.04f,.06f,.91f));
            var card=Box(root,"Lesson card",new Vector2(landscape?.22f:.045f,.075f),new Vector2(landscape?.78f:.955f,.81f),panel);
            if(State.phase=="briefing"){
                Label(card,"YOUR BRIEFING",new Vector2(.05f,.83f),new Vector2(.95f,.94f),22,teal);
                ScrollText(card,State.objective+"\n\nWatch the aircraft, follow reports and ask the assistant.\n\nThree questions pause the scene. "+(State.assessmentMode=="typed"?"Write your answer in your own words, then review the feedback and reports. This is practice feedback, not a competence grade.":"Answer, then review the evidence.")+"\n\nYour answers and review set the pace.",new Vector2(.05f,.23f),new Vector2(.95f,.79f),landscape?25:29,out _);
                Button(card,"Ready",new Vector2(.05f,.06f),new Vector2(.95f,.18f),()=>SendAction("ready"),true);
            }else if(State.phase=="checkpoint"){
                var p=State.checkpoint;
                Label(card,"CHECKPOINT "+State.checkpointNumber+" OF "+State.checkpointCount+"  ·  "+p.at.ToString("0")+" s",new Vector2(.05f,.88f),new Vector2(.95f,.96f),20,teal);
                Label(card,p.question,new Vector2(.05f,.65f),new Vector2(.95f,.87f),landscape?28:32,Color.white);
                if(State.assessmentMode=="typed"){
                    var field=Box(card,"Your answer",new Vector2(.05f,.29f),new Vector2(.95f,.63f),line);
                    responseInput=field.gameObject.AddComponent<InputField>();responseInput.characterLimit=1200;
                    responseInput.lineType=InputField.LineType.MultiLineNewline;
                    responseInput.textComponent=Label(field,"",new Vector2(.025f,.04f),new Vector2(.975f,.96f),landscape?24:29,Color.white);
                    responseInput.textComponent.alignment=TextAnchor.UpperLeft;
                    var hint=Label(field,"Write your answer…",new Vector2(.025f,.04f),new Vector2(.975f,.96f),landscape?24:29,muted);
                    hint.alignment=TextAnchor.UpperLeft;responseInput.placeholder=hint;responseInput.text=responseDraft;
                    responseInput.onValueChanged.AddListener(value=>{responseDraft=value;responseError="";});
                    reviewNotice=Label(card,"",new Vector2(.05f,.18f),new Vector2(.95f,.28f),landscape?19:23,muted);
                    reviewButton=Button(card,"Review my answer",new Vector2(.05f,.04f),new Vector2(.95f,.16f),ReviewResponse,true);
                }else for(int i=0;i<4;i++){int choice=i;float y=.49f-i*.145f;
                    Button(card,((char)('A'+i))+"   "+p.choices[i],new Vector2(.05f,y),new Vector2(.95f,y+.12f),()=>SendAction("answer",choice,p.id));}
            }else{
                var f=State.feedback;
                Label(card,f.kind=="typed"?"Feedback on your answer":f.correct?"That’s right":"Let’s review that",new Vector2(.05f,.84f),new Vector2(.95f,.95f),30,f.kind=="typed"||f.correct?teal:new Color(1,.72f,.34f));
                ScrollText(card,FeedbackText(f),new Vector2(.05f,.22f),new Vector2(.95f,.8f),landscape?24:28,out _);
                Button(card,"Continue",new Vector2(.05f,.05f),new Vector2(.95f,.17f),()=>SendAction("continue"),true);
            }
        }
        void BuildAssistant(){
            focusText=Label(side,"",new Vector2(.05f,.92f),new Vector2(.95f,.99f),landscape?18:23,teal);
            var visible=Enumerable.Range(0,replay.Data.aircraft.Length).Where(i=>!replay.Data.aircraft[i].hidden).ToArray();
            for(int i=0;i<visible.Length;i++){int n=visible[i];float width=.91f/visible.Length,x=.05f+i*width;
                Button(side,replay.Data.aircraft[n].FlightAt(replay.Clock.Time),new Vector2(x,.84f),new Vector2(x+width-.015f,.92f),()=>replay.SelectAircraft(n));}
            var field=Box(side,"Question",new Vector2(.05f,.70f),new Vector2(.95f,.81f),line);
            input=field.gameObject.AddComponent<InputField>();input.characterLimit=400;input.lineType=InputField.LineType.MultiLineNewline;
            input.textComponent=Label(field,"",new Vector2(.03f,.04f),new Vector2(.97f,.96f),landscape?22:27,Color.white);
            var hint=Label(field,"Ask about this flight…",new Vector2(.03f,.04f),new Vector2(.97f,.96f),landscape?22:27,muted);input.placeholder=hint;
            Button(side,"Latest update",new Vector2(.05f,.61f),new Vector2(.49f,.68f),()=>Ask("What is the latest update for this aircraft?"));
            Button(side,Regional?"Restrictions":"Readiness",new Vector2(.51f,.61f),new Vector2(.95f,.68f),()=>Ask(Regional?"What is the latest reported condition for this flight?":"Is this aircraft ready to depart?"));
            answerHeading=Label(side,"Report summary",new Vector2(.05f,.53f),new Vector2(.95f,.61f),landscape?24:29,Color.white);
            answerText=ScrollText(side,"",new Vector2(.05f,.19f),new Vector2(.95f,.53f),landscape?23:28,out answerScroll);
            Button(side,"Sources",new Vector2(.05f,.11f),new Vector2(.48f,.18f),()=>{sources=!sources;history=false;RefreshAnswer();});
            Button(side,"Recent reports",new Vector2(.51f,.11f),new Vector2(.95f,.18f),()=>{history=!history;sources=false;RefreshAnswer();});
            askButton=Button(side,"Ask assistant",new Vector2(.05f,.015f),new Vector2(.95f,.095f),()=>Ask(input.text),true);
            RefreshAnswer();
        }
        void BuildDebrief(){
            Label(side,State.mode=="lesson"?"Your debrief  ·  "+(State.assessmentMode=="typed"?State.answered+" responses":State.score+" / "+State.checkpointCount):"Demonstration complete",new Vector2(.05f,.88f),new Vector2(.95f,.98f),28,Color.white);
            var text=State.mode=="lesson"?string.Join("\n\n──────────\n\n",(State.reviews??new TrainingFeedback[0]).Select(FeedbackText)):"Review what changed, which restrictions remain, and what still needs confirmation.";
            text+="\n\nOTHER PERSPECTIVES\n\n"+string.Join("\n\n",(State.perspectives??new TrainingPerspective[0]).Where(p=>p.role!="Scenario basis").Select(p=>p.role+"\n"+p.text));
            ScrollText(side,text,new Vector2(.05f,.24f),new Vector2(.95f,.87f),landscape?22:27,out _);
            Button(side,"Ground view",new Vector2(.05f,.15f),new Vector2(.48f,.22f),()=>{ground=!ground;Focus();});
            Button(side,"Try again",new Vector2(.51f,.15f),new Vector2(.95f,.22f),()=>SendAction("retry"));
            Button(side,"Next exercise",new Vector2(.05f,.035f),new Vector2(.95f,.13f),()=>SendAction("next"),true);
        }
        string FeedbackText(TrainingFeedback f){
            if(f.kind=="typed"){
                var reviewed=f.question+"\n\nYour answer: "+f.chosen+"\n\nPRACTICE FEEDBACK\n"+f.explanation;
                foreach(var point in f.points??new TrainingReviewPoint[0]){
                    var label=point.status=="met"?"Supported point":point.status=="missing"?"Missing point":point.status=="contradicted"?"Recheck this point":"Needs clarification";
                    reviewed+="\n\n"+label+"\n"+point.comment;
                    if(!string.IsNullOrWhiteSpace(point.learnerQuote))reviewed+="\nYour words: “"+point.learnerQuote+"”";
                    if(point.evidenceIds!=null&&point.evidenceIds.Length>0)reviewed+="\nReports: "+string.Join(", ",point.evidenceIds);
                }
                return reviewed+"\n\nREPORTS AVAILABLE AT "+f.cutoff.ToString("0")+" s\n"+string.Join("\n\n",(f.reports??new ScenarioEvent[0]).Select(ReportText));
            }
            var text=f.question+"\n\nYour answer: "+f.chosen+"\nAnswer: "+f.correctAnswer+"\n\n"+f.explanation+"\n\nREPORTS AVAILABLE AT "+f.cutoff.ToString("0")+" s\n";
            text+=string.Join("\n\n",(f.reports??new ScenarioEvent[0]).Select(ReportText));
            if(f.laterReports!=null&&f.laterReports.Length>0)text+="\n\nARRIVED AFTER THIS CHECKPOINT\n"+string.Join("\n\n",f.laterReports.Select(ReportText));
            return text;
        }
        string ReportText(ScenarioEvent e){
            var source=e.source.Replace("exercise-","").Replace('-',' ');
            if(source=="emergency")source="Emergency response";else if(source.Length>0)source=char.ToUpper(source[0])+source.Substring(1);
            return e.message+"\n"+source+" · received "+TimeSpan.FromSeconds(e.receiptTime).ToString(@"mm\:ss")+" · "+e.id;
        }
        void Ask(string question){history=false;sources=false;if(input!=null)input.text=question;assistant.Ask(question);}
        void RefreshAnswer(){
            if(answerText==null)return;
            if(history){answerHeading.text="Recent reports";answerText.text=string.Join("\n\n",replay.Data.KnownAt(replay.Clock.Time).Where(e=>e.flightInstance==replay.SelectedFlight).Reverse().Take(12).Select(ReportText));return;}
            answerHeading.text=messageStatus=="ASKING"?"Checking reports…":messageStatus=="ANSWER WITHHELD"||messageStatus=="UNAVAILABLE"?"Answer unavailable":"Report summary";
            var response=assistant.LastResponse;
            if(messageStatus=="ASKING"){answerText.text="Checking the available reports for "+replay.SelectedFlight+"…";return;}
            if(messageStatus!="CHECKED ANSWER"||response==null||!response.accepted){answerText.text=message;return;}
            answerHeading.text="Report summary · "+TimeSpan.FromSeconds(response.cutoff).ToString(@"mm\:ss");
            var d=response.display;var lines=new List<string>();
            foreach(var claim in d.claims??new SupportedClaim[0]){
                var prop=claim.fact_id.Split(':').Last();
                var label=prop=="tobt"?"Target off-block estimate":prop=="movement_condition"?"Reported condition":
                    prop=="movement_status"?"Movement":prop=="baggage_status"?"Baggage":prop=="fuel_status"?"Fuel service":prop=="stand"?"Stand":prop=="route"?"Reported route":prop.Replace('_',' ');
                lines.Add(label+": "+claim.value+".");
            }
            foreach(var unknown in d.unknowns??new string[0])lines.Add(unknown=="overall_readiness"?"Overall readiness has not been confirmed.":"No confirmed "+unknown.Replace('_',' ')+" report is available.");
            if(lines.Count==0)lines.Add(d.answer??"No supported report answer is available.");
            lines.Add("\nReports up to "+TimeSpan.FromSeconds(response.cutoff).ToString(@"mm\:ss")+" · "+(response.referent?.flightInstance??replay.SelectedFlight));
            if(sources){
                var ids=new HashSet<string>((d.claims??new SupportedClaim[0]).SelectMany(c=>c.evidence_ids??new string[0]));
                lines.Add("\nSUPPORTING REPORTS\n"+string.Join("\n\n",replay.Data.KnownAt(response.cutoff).Where(e=>ids.Contains(e.id)).Select(ReportText)));
            }
            answerText.text=string.Join("\n\n",lines);Canvas.ForceUpdateCanvases();
        }
        void SendAction(string action,int choice=0,string checkpoint=null,string cue=null,bool success=false){
            if(State==null||actionBusy)return;
            var body=new TrainingAction{action=action,actionId=Guid.NewGuid().ToString("N"),runId=State.runId,revision=State.revision,
                choice=choice,checkpointId=checkpoint??"",cueId=cue??"",success=success};
            StartCoroutine(ActionRequest(body));
        }
        void ReviewResponse(){
            if(State?.checkpoint==null||reviewBusy||State.reviewStatus=="pending"||string.IsNullOrWhiteSpace(responseDraft))return;
            responseInput?.DeactivateInputField();responseError="";
            var body=new TrainingResponse{actionId=Guid.NewGuid().ToString("N"),runId=State.runId,revision=State.revision,
                checkpointId=State.checkpoint.id,responseText=responseDraft};
            activeReviewId=body.actionId;
            StartCoroutine(ResponseRequest(body));
        }
        IEnumerator ResponseRequest(TrainingResponse body){
            reviewBusy=true;var json=JsonUtility.ToJson(body);
            for(int attempt=0;attempt<2;attempt++){
                using(var request=assistant.TrainingResponseRequest(json)){
                    yield return request.SendWebRequest();
                    // Polling can finish this review before its HTTP reply, or
                    // move to another checkpoint/attempt. An old coroutine must
                    // never clear a newer request's busy flag or error text.
                    if(activeReviewId!=body.actionId||State==null||State.runId!=body.runId||
                        State.phase!="checkpoint"||State.checkpoint?.id!=body.checkpointId)yield break;
                    if(request.result==UnityWebRequest.Result.Success){
                        var next=JsonUtility.FromJson<TrainingState>(request.downloadHandler.text);
                        if(next.runId==State.runId)Apply(next);
                        if(activeReviewId==body.actionId){activeReviewId="";reviewBusy=false;}yield break;
                    }
                    if(request.responseCode==409){responseError="This checkpoint has changed. Your current step will appear shortly.";break;}
                    if(request.responseCode>=400&&request.responseCode<500){responseError="Your answer could not be reviewed. Please try again.";break;}
                }
            }
            if(activeReviewId!=body.actionId)yield break;
            activeReviewId="";reviewBusy=false;
            if(State.phase=="checkpoint"&&string.IsNullOrEmpty(responseError))responseError="The review did not arrive. Your answer is kept here; try again when connected.";
        }
        IEnumerator ActionRequest(TrainingAction body){
            actionBusy=true;var json=JsonUtility.ToJson(body);
            for(int attempt=0;attempt<2;attempt++){
                using(var request=assistant.TrainingActionRequest(json)){
                    yield return request.SendWebRequest();
                    if(request.result==UnityWebRequest.Result.Success){
                        var next=JsonUtility.FromJson<TrainingState>(request.downloadHandler.text);
                        // A new attempt needs its matching immutable world from /traffic.
                        if(next.runId==State.runId)Apply(next);
                        actionBusy=false;yield break;
                    }
                    if(request.responseCode==409){message="The exercise has moved on. The current step will appear shortly.";break;}
                }
            }
            actionBusy=false;Connected=false;
        }
        void Overview(){focusIncident=null;followFlight=false;ground=false;terminalView=false;centre=Regional?new Vector3(-2000,0,-700):new Vector3(75,0,-25);distance=Regional?8200:320;}
        void RunwayView(){focusIncident=null;followFlight=false;ground=false;terminalView=false;centre=Regional?new Vector3(0,0,-570):new Vector3(0,0,-400);distance=Regional?4200:1600;}
        void TerminalView(){focusIncident=null;followFlight=false;ground=false;terminalView=true;centre=new Vector3(480,8,40);distance=1250;}
        void Focus(){focusIncident=null;followFlight=true;terminalView=false;centre=replay.Content.TransformPoint(Scenario.Position(SelectedPlane,replay.Clock.Time));distance=ground?85:190;}
        bool OverUI(Vector2 p){hits.Clear();EventSystem.current?.RaycastAll(new PointerEventData(EventSystem.current){position=p},hits);return hits.Count>0;}
        void MoveCamera(){
            if(State.phase=="checkpoint")return;
            Vector2 pos=Input.mousePosition;bool begin=Input.GetMouseButtonDown(0),held=Input.GetMouseButton(0),end=Input.GetMouseButtonUp(0);
            if(Input.touchCount>0){var t=Input.GetTouch(0);pos=t.position;begin=t.phase==TouchPhase.Began;held=t.phase!=TouchPhase.Ended&&t.phase!=TouchPhase.Canceled;end=!held;}
            if(begin){dragging=camera.pixelRect.Contains(pos)&&!OverUI(pos);lastPointer=pos;if(dragging){followFlight=false;focusIncident=null;}}
            if(dragging&&held){var delta=pos-lastPointer;lastPointer=pos;centre-=(camera.transform.right*delta.x+Vector3.ProjectOnPlane(camera.transform.forward,Vector3.up).normalized*delta.y)*distance/Mathf.Max(1,Screen.height);}
            if(end)dragging=false;
            if(Input.touchCount==2){var a=Input.GetTouch(0);var b=Input.GetTouch(1);if(!OverUI(a.position)&&!OverUI(b.position)){
                var before=(a.position-a.deltaPosition-(b.position-b.deltaPosition)).magnitude;distance-=((a.position-b.position).magnitude-before)*.25f;}}
            distance=Mathf.Clamp(distance-Input.mouseScrollDelta.y*10,focusIncident==null?65:28,Regional?12000:2400);
            if(State.spotlightId=="incursion_vehicle"&&vehicles.Count>0)centre=vehicles[0].transform.position;
            if(followFlight)centre=replay.Content.TransformPoint(Scenario.Position(SelectedPlane,replay.Clock.Time));
            if(focusIncident!=null){
                var p=new Vector3(focusIncident.x,focusIncident.y+.002f,focusIncident.z);
                if(focusIncident.kind=="wildlife"){
                    float age=Mathf.Max(0,replay.Clock.Time-focusIncident.start),leave=Mathf.Clamp01((replay.Clock.Time-focusIncident.end+8)/8);
                    p.z+=-.035f+age*.0025f+leave*leave*.06f;p.y+=leave*leave*.018f;
                }
                centre=replay.Content.TransformPoint(p);
            }
            centre.x=Mathf.Clamp(centre.x,Regional?-12000:-5000,Regional?12000:5000);centre.z=Mathf.Clamp(centre.z,Regional?-12000:-4000,Regional?6000:500);
            camera.transform.rotation=Quaternion.Euler(focusIncident!=null?(focusIncident.kind=="wildlife"?18:38):ground?12:followFlight?24:terminalView?32:48,terminalView?225:0,0);
            camera.transform.position=centre-camera.transform.forward*distance;camera.fieldOfView=55;
        }
        void BuildTags(){for(int i=0;i<replay.Data.aircraft.Length;i++){
            int n=i;var r=Box(tagRoot,"Flight "+i,Vector2.zero,Vector2.zero,panel);r.sizeDelta=new Vector2(125,39);r.pivot=new Vector2(.5f,0);
            Label(r,replay.Data.aircraft[i].flightInstance,Vector2.zero,Vector2.one,20,Color.white);
            r.gameObject.AddComponent<Button>().onClick.AddListener(()=>replay.SelectAircraft(n));tags.Add(r);tagSlots.Add(-1);tagLeaders.Add(BuildTagLeader());
        }}
        RectTransform BuildTagLeader(){
            var line=Box(tagRoot,"Label connector",Vector2.zero,Vector2.zero,new Color(.8f,.9f,.9f,.8f),false);
            line.pivot=new Vector2(0,.5f);line.SetAsFirstSibling();return line;
        }
        bool PlaceTag(RectTransform tag,RectTransform leader,Vector3 world,Rect bounds,ref int slot,bool selected){
            var screen=camera.WorldToScreenPoint(world);
            if(screen.z<=0||!camera.pixelRect.Contains(screen)){tag.gameObject.SetActive(false);leader.gameObject.SetActive(false);return false;}
            RectTransformUtility.ScreenPointToLocalPointInRectangle(root,screen,null,out var point);
            bool visible=TrainingLabelLayout.Place(point,tag.sizeDelta,bounds,occupiedTags,
                selected?0:slot,tag.gameObject.activeSelf,out var rect,out var nextSlot);
            tag.gameObject.SetActive(visible);leader.gameObject.SetActive(false);
            if(!visible)return false;
            slot=nextSlot;occupiedTags.Add(rect);
            tag.anchorMin=tag.anchorMax=new Vector2(.5f,.5f);tag.anchoredPosition=new Vector2(rect.center.x,rect.yMin);
            // A short connector identifies displaced labels without intercepting taps.
            var end=new Vector2(Mathf.Clamp(point.x,rect.xMin,rect.xMax),Mathf.Clamp(point.y,rect.yMin,rect.yMax));
            var start=new Vector2(Mathf.Clamp(point.x,bounds.xMin,bounds.xMax),Mathf.Clamp(point.y,bounds.yMin,bounds.yMax));
            var delta=end-start;
            if(delta.magnitude>3){
                leader.gameObject.SetActive(true);leader.anchorMin=leader.anchorMax=new Vector2(.5f,.5f);
                leader.anchoredPosition=start;leader.sizeDelta=new Vector2(delta.magnitude,2);
                leader.localRotation=Quaternion.Euler(0,0,Mathf.Atan2(delta.y,delta.x)*Mathf.Rad2Deg);
            }
            return true;
        }
        void UpdateTags(){
            if(tags.Count==0)return;
            occupiedTags.Clear();
            // Keep full tags clear of camera controls, phase strip, map credit and side panel.
            var bounds=new Rect(root.rect.xMin+root.rect.width*.025f,root.rect.yMin+root.rect.height*(landscape?.16f:.59f),
                root.rect.width*(landscape?.585f:.945f),root.rect.height*(landscape?.61f:.215f));
            var order=Enumerable.Range(0,tags.Count).OrderBy(i=>i==replay.SelectedAircraftIndex?0:
                replay.Data.aircraft[i].id==State.spotlightAircraft?1:replay.Data.aircraft[i].id==State.targetAircraft?2:3).ThenBy(i=>i);
            foreach(int i in order){
                var plan=replay.Data.aircraft[i];var aircraft=replay.Content.Find(plan.id);
                if(plan.hidden||aircraft==null){tags[i].gameObject.SetActive(false);tagLeaders[i].gameObject.SetActive(false);continue;}
                bool selected=i==replay.SelectedAircraftIndex;int slot=tagSlots[i];
                PlaceTag(tags[i],tagLeaders[i],aircraft.position+Vector3.up*14,bounds,ref slot,selected);tagSlots[i]=slot;
                tags[i].GetComponent<Image>().color=selected?new Color(.04f,.44f,.40f):panel;
                tags[i].GetComponentInChildren<Text>(true).text=plan.FlightAt(replay.Clock.Time);
            }
            if(vehicleTag!=null&&vehicles.Count>0)
                PlaceTag(vehicleTag,vehicleLeader,vehicles[0].transform.position+Vector3.up*10,bounds,ref vehicleSlot,false);
        }
        void BuildVehicles(){
            foreach(var v in vehicles)Destroy(v);vehicles.Clear();
            foreach(var plan in replay.Data.groundVehicles??new AircraftPlan[0]){
                var vehicle=new GameObject(plan.id);vehicle.transform.SetParent(replay.Content,false);
                Cube(vehicle.transform,"Body",new Vector3(0,.0016f,0),new Vector3(.0028f,.0022f,.0055f),new Color(.9f,.62f,.10f));
                Cube(vehicle.transform,"Cab",new Vector3(0,.0028f,.0018f),new Vector3(.0027f,.0014f,.0018f),new Color(.85f,.87f,.85f));
                Cube(vehicle.transform,"Windshield",new Vector3(0,.0029f,.00272f),new Vector3(.0022f,.0008f,.0001f),new Color(.06f,.13f,.18f));
                for(int i=0;i<4;i++)Cube(vehicle.transform,"Wheel",new Vector3(i%2==0?-.0015f:.0015f,.0006f,i<2?-.0017f:.0017f),new Vector3(.0005f,.0012f,.0012f),new Color(.04f,.05f,.055f));
                vehicles.Add(vehicle);
            }
        }
        void Cube(Transform p,string name,Vector3 pos,Vector3 scale,Color color){var go=GameObject.CreatePrimitive(PrimitiveType.Cube);go.name=name;go.transform.SetParent(p,false);go.transform.localPosition=pos;go.transform.localScale=scale;go.GetComponent<Renderer>().material.color=color;Destroy(go.GetComponent<Collider>());}
        RectTransform Box(Transform parent,string name,Vector2 min,Vector2 max,Color color,bool raycast=true){
            var go=new GameObject(name,typeof(RectTransform),typeof(Image));go.transform.SetParent(parent,false);var r=go.GetComponent<RectTransform>();
            r.anchorMin=min;r.anchorMax=max;r.offsetMin=r.offsetMax=Vector2.zero;var image=go.GetComponent<Image>();image.color=color;image.raycastTarget=raycast;return r;
        }
        Text Label(Transform parent,string value,Vector2 min,Vector2 max,int size,Color color){
            var go=new GameObject("Text",typeof(RectTransform),typeof(Text));go.transform.SetParent(parent,false);var t=go.GetComponent<Text>();
            t.font=font;t.fontSize=size;t.color=color;t.text=value;t.supportRichText=false;t.raycastTarget=false;t.alignment=TextAnchor.MiddleLeft;
            t.horizontalOverflow=HorizontalWrapMode.Wrap;t.verticalOverflow=VerticalWrapMode.Truncate;
            var r=t.rectTransform;r.anchorMin=min;r.anchorMax=max;r.offsetMin=r.offsetMax=Vector2.zero;return t;
        }
        Button Button(Transform p,string text,Vector2 min,Vector2 max,UnityEngine.Events.UnityAction action,bool primary=false){
            var r=Box(p,text,min,max,primary?new Color(.035f,.43f,.39f):line);var t=Label(r,text,new Vector2(.04f,.02f),new Vector2(.96f,.98f),landscape?21:26,Color.white);
            t.alignment=TextAnchor.MiddleCenter;var b=r.gameObject.AddComponent<Button>();b.onClick.AddListener(action);return b;
        }
        Text ScrollText(Transform p,string text,Vector2 min,Vector2 max,int size,out ScrollRect scroll){
            // A visible hit surface is required on the iOS canvas; a nearly
            // transparent Image may be culled and never receive drag events.
            var viewport=Box(p,"Scrollable text",min,max,panel);viewport.gameObject.AddComponent<RectMask2D>();
            scroll=viewport.gameObject.AddComponent<ScrollRect>();scroll.horizontal=false;scroll.movementType=ScrollRect.MovementType.Clamped;scroll.scrollSensitivity=28;
            var content=new GameObject("Content",typeof(RectTransform)).GetComponent<RectTransform>();content.SetParent(viewport,false);
            content.anchorMin=new Vector2(0,1);content.anchorMax=new Vector2(.94f,1);content.pivot=new Vector2(.5f,1);content.offsetMin=content.offsetMax=Vector2.zero;
            var label=Label(content,text,Vector2.zero,Vector2.one,size,new Color(.90f,.94f,.95f));
            label.alignment=TextAnchor.UpperLeft;label.verticalOverflow=VerticalWrapMode.Overflow;label.lineSpacing=1.12f;
            var layout=content.gameObject.AddComponent<VerticalLayoutGroup>();layout.childControlHeight=true;layout.childControlWidth=true;layout.childForceExpandHeight=false;layout.padding=new RectOffset(0,12,6,12);
            content.gameObject.AddComponent<ContentSizeFitter>().verticalFit=ContentSizeFitter.FitMode.PreferredSize;
            scroll.viewport=viewport;scroll.content=content;
            var track=Box(viewport,"Scroll track",new Vector2(.955f,0),Vector2.one,line);
            var handle=Box(track,"Scroll handle",Vector2.zero,Vector2.one,muted);
            var bar=track.gameObject.AddComponent<Scrollbar>();bar.handleRect=handle;bar.targetGraphic=handle.GetComponent<Image>();bar.direction=Scrollbar.Direction.BottomToTop;
            scroll.verticalScrollbar=bar;scroll.verticalScrollbarVisibility=ScrollRect.ScrollbarVisibility.AutoHide;
            return label;
        }
    }
}
