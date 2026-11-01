using System;
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
        GameObject[] propObjects;
        VisualProp[] props;
        LineRenderer selectionRing;
        RectTransform safeRoot, body;
        Text status, clockLabel, playLabel, selectionLabel;
        Image[] aircraftChips, tabChips;
        Text[] aircraftChipLabels;
        Slider slider;
        Button playButton;
        string logPath, bodyKey, aiStatus="Not requested", aiText="Generate an explanation of this checkpoint using the configured local model service.";
        bool updatingSlider, showBaseline, showAiDetails, showTools, logCopied;
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
        // Replay time when the board left the camera's view, held until the next conversation turn is committed
        // (ConversationClient sends it as lastSeen). The earliest loss counts: the user missed everything since.
        public float? InterruptedAt {get;private set;}
        public void ClearInterruption(){InterruptedAt=null;}
        public void Tracking(bool found){
            if(Clock==null)return;
            if(Clock.Tracked!=found)Log(found?"target_found":"target_lost");
            if(Clock.Tracked&&!found&&!InterruptedAt.HasValue)InterruptedAt=Clock.Time;
            Clock.SetTracking(found);Content.gameObject.SetActive(found);ApplyScene();
        }
        public void Play(){Clock.Play();Log("play");ApplyScene();}
        public void Pause(){Clock.Pause();Log("pause");ApplyScene();}
        public void Restart(){Clock.Restart();InvalidateAi();Log("restart");ApplyScene();}
        public void Seek(float time){if(float.IsNaN(time)||float.IsInfinity(time))return;Clock.Seek(time);InvalidateAi();Log("seek");ApplyScene();}
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
        public void SetAiResult(string status,string text){aiStatus=status??"";aiText=text??"";showAiDetails=false;bodyKey=null;ApplyScene();}
        void InvalidateAi(){showAiDetails=false;aiStatus="Checkpoint changed";aiText="Generate a new explanation for the selected aircraft and replay time.";}
        void Update(){
            if(Clock==null)return;
            if(Input.GetMouseButtonDown(0)&&Camera.main!=null&&(EventSystem.current==null||!EventSystem.current.IsPointerOverGameObject()))
                TapSelect(Input.mousePosition,Camera.main);
            Clock.Advance(Time.unscaledDeltaTime);ApplyScene();
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
            if(planes==null)return;
            for(int i=0;i<planes.Length;i++) {
                planes[i].localPosition=Scenario.Position(Data.aircraft[i],Clock.Time)+Vector3.up*.003f;
                planes[i].localRotation=Quaternion.LookRotation(Scenario.Direction(Data.aircraft[i],Clock.Time),Vector3.up);
            }
            if(propObjects!=null)for(int i=0;i<propObjects.Length;i++){
                var v=Scenario.PropValueAt(props[i],Clock.Time);propObjects[i].SetActive(v=="connected"||v=="open");
            }
            if(selectionRing!=null){selectionRing.transform.localPosition=Scenario.Position(SelectedAircraft,Clock.Time);selectionRing.startColor=selectionRing.endColor=SelectedAircraftIndex==1?new Color(1f,.72f,.33f):new Color(.28f,.84f,.78f);}
            if(!VisibleReports.Any(e=>e.id==InspectedReportId))InspectedReportId="";
            if(clockLabel!=null)clockLabel.text=$"{Clock.Time:00.0}<size=33> / {Data.duration:00} s</size>";
            if(status!=null){status.text=previewMode?"Desktop preview · tracking untested":
                (Clock.Tracked?"Board tracked · "+(Clock.Playing?"replaying":"paused"):"Find printed board · playback paused");status.color=Clock.Tracked?teal:amber;}
            if(playLabel!=null)playLabel.text=Clock.Playing?"Pause":"Play";
            if(playButton!=null)playButton.interactable=Clock.Tracked;
            if(selectionLabel!=null)selectionLabel.text=SelectedAircraft.id+" · "+CurrentSceneState+" · simulated";
            if(aircraftChips!=null)for(int i=0;i<aircraftChips.Length;i++)aircraftChips[i].color=i==SelectedAircraftIndex?new Color(.82f,.92f,.92f):panel;
            // Chip labels follow the rotation under way; single-flight aircraft never change.
            if(aircraftChipLabels!=null)for(int i=0;i<aircraftChipLabels.Length;i++){var label=ChipLabel(Data.aircraft[i]);if(aircraftChipLabels[i].text!=label)aircraftChipLabels[i].text=label;}
            if(tabChips!=null)for(int i=0;i<tabChips.Length;i++){bool selected=SelectedTab==new[]{"now","why","history"}[i];tabChips[i].color=selected?teal:card;tabChips[i].GetComponentInChildren<Text>().color=selected?Color.white:ink;}
            if(slider!=null){updatingSlider=true;slider.SetValueWithoutNotify(Clock.Time);updatingSlider=false;}
            UpdateSafeArea();
            var key=SelectedAircraftIndex+"|"+SelectedFlight+"|"+SelectedTab+"|"+AllFlightsHistory+"|"+InspectedReportId+"|"+
                string.Join(",",Data.KnownAt(Clock.Time).Select(e=>e.id))+"|"+CurrentSceneState+"|"+aiStatus+"|"+aiText+"|"+showBaseline+"|"+showAiDetails+"|"+showTools+"|"+logCopied;
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
            planes=new Transform[Data.aircraft.Length];
            for(int i=0;i<planes.Length;i++) {
                var root=new GameObject(Data.aircraft[i].id).transform;root.SetParent(Content,false);planes[i]=root;
                AircraftVisual.Build(root,LiveryOf(i));
            }
            BuildProps();
            // Occluders (for example a service canopy) are neutral roof slabs; they hide what lies under them from the camera.
            foreach(var o in Data.occluders??new Occluder[0])
                Shape(PrimitiveType.Cube,"Occluder "+o.id,new Vector3(o.x,o.height,o.z),new Vector3(o.width,.0008f,o.depth),new Color(.62f,.66f,.68f),Content);
            foreach(var a in Data.aircraft) {
                var g=new GameObject(a.id+" authored path");g.transform.SetParent(Content,false);
                var l=g.AddComponent<LineRenderer>();l.useWorldSpace=false;l.positionCount=a.waypoints.Length;l.widthMultiplier=.0007f;
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
        void BuildUI(){
            font=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var canvas=new GameObject("Coordinator UI",typeof(Canvas),typeof(CanvasScaler),typeof(GraphicRaycaster));canvas.transform.SetParent(transform,false);
            canvas.GetComponent<Canvas>().renderMode=RenderMode.ScreenSpaceOverlay;
            var scale=canvas.GetComponent<CanvasScaler>();scale.uiScaleMode=CanvasScaler.ScaleMode.ScaleWithScreenSize;scale.referenceResolution=new Vector2(1080,1920);scale.matchWidthOrHeight=.5f;
            if(FindFirstObjectByType<EventSystem>()==null)new GameObject("EventSystem",typeof(EventSystem),typeof(StandaloneInputModule));
            safeRoot=Panel(canvas.transform,"Safe area",Vector2.zero,Vector2.one,Color.clear);safeRoot.GetComponent<Image>().raycastTarget=false;
            var head=Panel(safeRoot,"Header",new Vector2(0,.84f),Vector2.one,card);
            Label(head,"ApronLens",new Vector2(.015f,.69f),new Vector2(.68f,.99f),47);
            Label(head,"SIMULATION",new Vector2(.67f,.69f),new Vector2(.985f,.95f),33,TextAnchor.MiddleRight,teal);
            status=Label(head,"",new Vector2(.015f,.47f),new Vector2(.985f,.68f),33);
            // Chips share the header width; with two aircraft this is the original layout.
            int count=Data.aircraft.Length;float gap=.03f,width=(.93f-(count-1)*gap)/count;
            aircraftChips=new Image[count];aircraftChipLabels=new Text[count];
            for(int i=0;i<count;i++){
                int index=i;var a=Data.aircraft[i];
                var r=Button(head,ChipLabel(a),
                    new Vector2(.035f+i*(width+gap),.025f),new Vector2(.035f+i*(width+gap)+width,.455f),()=>SelectAircraft(index),panel,count==2?39:33);
                aircraftChips[i]=r.GetComponent<Image>();aircraftChipLabels[i]=r.GetComponentInChildren<Text>();
                // Uniform-livery scenarios use one neutral marker so the chips do not imply colour identity.
                Panel(r,"Aircraft color",new Vector2(0,0),new Vector2(.015f,1),Data.UniformLivery?muted:i==0?teal:i==1?amber:LiveryOf(i));
            }
            var caption=Panel(safeRoot,"Selected scene identity",new Vector2(.035f,.529f),new Vector2(.965f,.565f),new Color(.055f,.095f,.13f,.9f));
            selectionLabel=Label(caption,"",Vector2.zero,Vector2.one,33,TextAnchor.MiddleCenter,Color.white);
            var tabs=Panel(safeRoot,"View tabs",new Vector2(0,.455f),new Vector2(1,.522f),card);
            tabChips=new Image[3];string[] names={"now","why","history"};
            for(int i=0;i<3;i++){string tab=names[i];var r=Button(tabs,char.ToUpper(tab[0])+tab.Substring(1),new Vector2(i/3f,0),new Vector2((i+1)/3f,1),()=>SelectTab(tab),card,39);tabChips[i]=r.GetComponent<Image>();}
            body=Panel(safeRoot,"Inspector",new Vector2(0,.185f),new Vector2(1,.452f),panel);
            var transport=Panel(safeRoot,"Replay transport",Vector2.zero,new Vector2(1,.18f),card);
            clockLabel=Label(transport,"",new Vector2(.015f,.77f),new Vector2(.47f,.99f),39);
            Label(transport,"Replay time",new Vector2(.5f,.77f),new Vector2(.985f,.99f),33,TextAnchor.MiddleRight,muted);
            var track=Panel(transport,"Seek timeline hit area",new Vector2(.05f,.46f),new Vector2(.95f,.89f),Color.clear);
            var rail=Panel(track,"Visible timeline",new Vector2(0,.33f),new Vector2(1,.37f),new Color(.71f,.78f,.8f));rail.GetComponent<Image>().raycastTarget=false;
            slider=track.gameObject.AddComponent<Slider>();slider.minValue=0;slider.maxValue=Data.duration;
            var handle=Panel(track,"Handle",new Vector2(0,.10f),new Vector2(0,.60f),teal);handle.sizeDelta=new Vector2(36,0);
            slider.handleRect=handle;slider.targetGraphic=handle.GetComponent<Image>();
            slider.onValueChanged.AddListener(t=>{if(!updatingSlider)Seek(t);});
            var play=Button(transport,"Play",new Vector2(.035f,.035f),new Vector2(.535f,.45f),()=>{if(Clock.Playing)Pause();else Play();},teal,39);
            playLabel=play.GetComponentInChildren<Text>();playLabel.color=Color.white;playButton=play.GetComponent<Button>();
            Button(transport,"Restart",new Vector2(.555f,.035f),new Vector2(.795f,.45f),Restart,panel,39);
            Button(transport,"More",new Vector2(.815f,.035f),new Vector2(.965f,.45f),()=>{showTools=!showTools;bodyKey=null;ApplyScene();},panel,39);
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
        string ShortReport(ScenarioEvent report){
            if(report==null)return "No report received";
            if(report.facts!=null && report.facts.Length>0){
                var f=report.facts[0];
                switch(f.property){
                    case "stand":return "Stand "+f.value+" assigned";
                    case "baggage_status":return "Baggage service "+f.value;
                    case "fuel_status":return "Fuel service "+f.value;
                    case "route":return "Movement plan updated";
                    case "movement_status":return "Scripted movement "+f.value;
                    case "trajectory_checkpoint":return "Checkpoint: "+f.value;
                }
            }
            return report.message.Length>75?report.message.Substring(0,72)+"…":report.message;
        }
        void BuildNow(){
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
            readiness.gameObject.AddComponent<Button>().onClick.AddListener(()=>{showBaseline=true;SelectTab("why");});
            Label(readiness,"Departure readiness",new Vector2(.015f,0),new Vector2(.69f,1),39);
            Label(readiness,"Unknown  ›",new Vector2(.69f,0),new Vector2(.985f,1),39,TextAnchor.MiddleRight,amber);
        }
        void ScrollText(Transform parent,string value,Vector2 min,Vector2 max,int size){
            var viewport=Panel(parent,"Scrollable text",min,max,Color.clear);viewport.gameObject.AddComponent<RectMask2D>();
            var scroll=viewport.gameObject.AddComponent<ScrollRect>();scroll.horizontal=false;scroll.movementType=ScrollRect.MovementType.Clamped;
            var t=Label(viewport,value,new Vector2(0,1),Vector2.one,size,TextAnchor.UpperLeft);t.supportRichText=false;
            var content=t.rectTransform;content.pivot=new Vector2(.5f,1);
            t.gameObject.AddComponent<ContentSizeFitter>().verticalFit=ContentSizeFitter.FitMode.PreferredSize;
            scroll.content=content;scroll.viewport=viewport;
        }
        string FriendlyAiState(){
            var state=aiStatus.ToUpperInvariant();
            if(state.Contains("WITHHELD"))return "Selection needs review";
            if(state.Contains("THINKING")||state.Contains("REVIEWING"))return "Reviewing this checkpoint…";
            if(state.Contains("SCENE UNAVAILABLE"))return "Find the printed board";
            if(state.Contains("UNAVAILABLE"))return "Model service unavailable";
            if(state.Contains("CHECKED"))return "Supported claims";
            if(state.Contains("CHANGED"))return "Checkpoint changed";
            return "Explain this checkpoint";
        }
        string CompactAiText(){
            if(showAiDetails)return aiText;
            var state=aiStatus.ToUpperInvariant();
            if(state.Contains("WITHHELD"))return "The model did not return a fully supported answer. Recorded facts are still available.";
            if(state.Contains("THINKING")||state.Contains("REVIEWING"))return "Replay is paused while the selected flight's reports are reviewed.";
            if(state.Contains("SCENE UNAVAILABLE"))return "Track the printed board before reviewing this checkpoint.";
            if(state.Contains("CONNECTION NEEDED"))return "Open More → Model connection and enter the service address and token.";
            if(state.Contains("CONNECTION SAVED"))return "Connection saved. Tap Explain to review this checkpoint.";
            if(state.Contains("UNAVAILABLE"))return "Recorded facts remain available. Check the connection and try again.";
            if(state.Contains("CHANGED"))return "Generate again for the selected aircraft and replay time.";
            var text=aiText;int cut=text.IndexOf("\n\nSources:",StringComparison.Ordinal);if(cut<0)cut=text.IndexOf("\n\nEvidence:",StringComparison.Ordinal);
            if(cut>=0)text=text.Substring(0,cut);
            return System.Text.RegularExpressions.Regex.Replace(text,@" Event [\d.]+ s; received [\d.]+ s\.","");
        }
        void BuildWhy(){
            Button(body,"Qwen",new Vector2(.035f,.735f),new Vector2(.49f,.99f),()=>{showBaseline=false;showAiDetails=false;bodyKey=null;ApplyScene();},showBaseline?card:new Color(.82f,.92f,.92f),39);
            Button(body,"Recorded facts",new Vector2(.51f,.735f),new Vector2(.965f,.99f),()=>{showBaseline=true;bodyKey=null;ApplyScene();},showBaseline?new Color(.82f,.92f,.92f):card,39);
            var explanation=Card(showBaseline?"Deterministic baseline":"Qwen selection",.28f,.72f);
            Label(explanation,showBaseline?"DETERMINISTIC BASELINE":FriendlyAiState(),new Vector2(.01f,.75f),new Vector2(.99f,.98f),showBaseline?33:39,TextAnchor.MiddleLeft,showBaseline?teal:ink);
            var explanationText=showBaseline?CurrentReasoning:CompactAiText();
            ScrollText(explanation,explanationText,new Vector2(.01f,.20f),new Vector2(.99f,.75f),39);
            if(explanationText.Length>90)Label(explanation,"Swipe to read more",new Vector2(.01f,0),new Vector2(.99f,.18f),33,TextAnchor.MiddleRight,muted);
            if(showBaseline){
                Button(body,"Review source reports",new Vector2(.035f,.005f),new Vector2(.965f,.26f),()=>{InspectedReportId="";SelectTab("history");},teal,39).GetComponentInChildren<Text>().color=Color.white;
            }else{
                Button(body,"Explain",new Vector2(.035f,.005f),new Vector2(.64f,.26f),()=>{showAiDetails=false;if(RequestReasoning!=null)RequestReasoning();else SetAiResult("Not connected","Open More → Model connection to connect the service.");},teal,39).GetComponentInChildren<Text>().color=Color.white;
                Button(body,showAiDetails?"Summary":"Details",new Vector2(.66f,.005f),new Vector2(.965f,.26f),()=>{showAiDetails=!showAiDetails;bodyKey=null;ApplyScene();},card,39);
            }
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
            Button(body,$"Jump to receipt · {report.receiptTime:0} s",new Vector2(.035f,.005f),new Vector2(.965f,.26f),()=>SeekToReportReceipt(report.id),teal,39).GetComponentInChildren<Text>().color=Color.white;
        }
        void BuildTools(){
            Label(body,"Session options",new Vector2(.015f,.81f),new Vector2(.985f,.99f),39);
            Button(body,"Model connection",new Vector2(.035f,.55f),new Vector2(.965f,.805f),()=>{showTools=false;bodyKey=null;ApplyScene();OpenConnectionSettings?.Invoke();},card,39);
            // Two half-width buttons share a row so every control keeps its 48 dp height.
            Button(body,logCopied?"Log path copied":"Copy session log path",new Vector2(.035f,.28f),new Vector2(.49f,.535f),()=>{GUIUtility.systemCopyBuffer=logPath;logCopied=true;Log("log_path_copied");bodyKey=null;ApplyScene();},card,33);
            Button(body,"Ask a question",new Vector2(.51f,.28f),new Vector2(.965f,.535f),()=>{showTools=false;bodyKey=null;ApplyScene();OpenConversation?.Invoke();},card,39);
            Button(body,"Done",new Vector2(.035f,.01f),new Vector2(.965f,.265f),()=>{showTools=false;bodyKey=null;ApplyScene();},teal,39).GetComponentInChildren<Text>().color=Color.white;
        }
    }
}
