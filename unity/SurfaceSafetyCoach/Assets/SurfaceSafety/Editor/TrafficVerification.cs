using System;
using System.IO;
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using SurfaceSafety;
public static class TrafficVerification {
    public static void Run(){
        ConversationClientVerification.Run();
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
        var boot=new GameObject("Traffic test").AddComponent<WorldArBootstrap>();boot.Initialize();
        var r=boot.Replay;var c=boot.GetComponent<ConversationClient>();r.UseAutonomousTraffic();
        Action<bool,string> check=(ok,label)=>{if(!ok)throw new Exception("Traffic check: "+label);};
        check(ExternalTrafficDriver.PredictTime(55,1,30,60)==60,"accelerated prediction stops at checkpoint boundary");
        check(ExternalTrafficDriver.PredictTime(10,9,1,3600)==13,"prediction freezes after three seconds without update");
        check(ExternalTrafficDriver.PredictTime(60,2,0,60)==60,"paused clock does not drift");
        check(ExternalTrafficDriver.PredictTime(10,2,1,3600)==12,"legacy snapshot advances at normal speed");
        check(!UnityEngine.Object.FindObjectsByType<Button>(FindObjectsSortMode.None).Any(b=>new[]{"Play","Restart","More"}.Contains(b.GetComponentInChildren<Text>()?.text)),"no replay controls");
        check(!UnityEngine.Object.FindObjectsByType<Text>(FindObjectsSortMode.None).Any(t=>t.text=="SIMULATION"),"no simulation label");
        var data=JsonUtility.FromJson<Scenario>(File.ReadAllText(Environment.GetEnvironmentVariable("APRONLENS_TRAFFIC_FIXTURE")));
        r.ApplyTrafficScenario(data);r.UpdateTrafficTime(10,"");r.Pause();r.Seek(0);r.UpdateTrafficTime(20,"");
        check(r.Clock.Time==20,"external clock survives pause and seek");
        r.Tracking(false);r.UpdateTrafficTime(25,"");check(r.Clock.Time==25&&r.Content.gameObject.activeSelf,"traffic runs while looking away");
        r.SelectAircraft(1);
        var request=new ConversationRequest{requestId="live",sessionId=c.SessionId,scenarioId=data.scenarioId,aircraftId="A2",flightInstance="TRN102",checkpoint=25};
        r.UpdateTrafficTime(40,"");
        var stand=data.events.First(e=>e.aircraftId=="A2"&&e.facts.Any(f=>f.property=="stand"));
        var response=new ConversationResponse{requestId="live",sessionId=c.SessionId,cutoff=25,revision=1,accepted=true,
            referent=new FlightRef{aircraftId="A2",flightInstance="TRN102"},display=new ConversationDisplay{answer="Stand B",claims=new[]{new SupportedClaim{fact_id=stand.id+":stand",value="B",evidence_ids=new[]{stand.id}}}}};
        check(c.ApplyResponse(request,response),"answer remains valid at its captured cutoff as traffic advances");
        r.SelectAircraft(0);check(!c.ApplyResponse(request,response),"changed aircraft rejects old answer");
        check(r.AwarenessTrack && r.Data.trainingRole=="controller_awareness" && r.SuggestedLabel(1)=="Reported hold","controller exercise drives the questions");
        c.ShowPanel();
        check(UnityEngine.Object.FindObjectsByType<Text>(FindObjectsSortMode.None).Any(x=>x.text=="Traffic update"),"controller question visible");
        var pilot=JsonUtility.FromJson<Scenario>(JsonUtility.ToJson(data));pilot.scenarioId+="-pilot";pilot.trainingRole="pilot_awareness";pilot.trainingRoleLabel="Pilot awareness";
        pilot.assistantQuestionLabels=new[]{"Route briefing","What changed?"};pilot.assistantQuestions=new[]{"What route is reported?","What changed?"};
        r.ApplyTrafficScenario(pilot);
        check(GameObject.Find("Conversation")==null && c.Revision==0,"exercise change closes old conversation and resets context");
        c.ShowPanel();check(UnityEngine.Object.FindObjectsByType<Text>(FindObjectsSortMode.None).Any(x=>x.text=="Route briefing"),"pilot question visible");
        var flightFixture=Environment.GetEnvironmentVariable("APRONLENS_FLIGHT_FIXTURE");
        if(!string.IsNullOrEmpty(flightFixture)){
            var flight=JsonUtility.FromJson<Scenario>(File.ReadAllText(flightFixture));flight.Validate();
            var plane=flight.aircraft[0];var phases=plane.phases.GroupBy(p=>p.id).ToDictionary(g=>g.Key,g=>g.First().t);
            check(Scenario.Position(plane,phases["climb"]).y>0,"aircraft has positive climb altitude");
            check(Scenario.Position(plane,phases["landing_roll"]).y==0,"touchdown reaches runway height");
            check(Scenario.Direction(plane,phases["climb"]).y>0,"climb attitude follows vertical path");
            check(Scenario.Direction(plane,phases["approach"]).y<0,"approach attitude descends");
            check(Scenario.Pitch(plane,phases["flare"])>0&&Scenario.Direction(plane,phases["flare"]).y<0,"flare attitude is nose-up while path descends");
            check(plane.GearRetractedAt(phases["circuit"])&&!plane.GearRetractedAt(phases["flare"]),"gear retracts then deploys for landing");
            check(Scenario.Position(data.aircraft[0],10).y==0,"legacy ground path remains at ground level");
            var runway=TrainingRunway.Build(r.Content,flight.runway,flight.taxiPaths);
            check(runway!=null&&runway.transform.Find("Runway pavement")!=null,"separate runway geometry created");
            check(plane.preciseHeading&&Mathf.Abs(Scenario.Heading(plane,phases["takeoff_roll"])-90)<.01f,"departure aligns to 090 degrees");
            check(Mathf.Abs(Scenario.Heading(plane,phases["landing_roll"])-90)<.01f,"landing aligns to 090 degrees");
            check(runway.transform.Find("Taxiway "+flight.taxiPaths[0].id)!=null,"taxi pavement uses external geometry");
            var wrapped=new AircraftPlan{preciseHeading=true,waypoints=new[]{new Waypoint{t=0,heading=355},new Waypoint{t=10,heading=5}}};
            check(Mathf.Abs(Scenario.Heading(wrapped,5))<.01f,"heading crosses north by the short turn");
            check(flight.incidents.Length==2&&flight.incidents[0].kind=="wildlife"&&flight.incidents[1].kind=="engine_fire","wildlife and fire are separate timed incidents");
            r.ApplyTrafficScenario(flight);
            var effectsObject=new GameObject("Incident verification");effectsObject.transform.SetParent(r.Content,false);
            var effects=effectsObject.AddComponent<TrainingIncidentEffects>();effects.Bind(r);
            effects.RenderAt(flight.incidents[1].start+5);
            check(effects.GetComponentsInChildren<ParticleSystem>().Sum(p=>p.particleCount)>0,"fire particles exist at external source time");
            check(effects.GetComponentsInChildren<ParticleSystem>().All(p=>p.main.scalingMode==ParticleSystemScalingMode.Hierarchy),"effects inherit the world metre scale");
            effects.RenderAt(flight.incidents[1].end);
            check(effects.GetComponentsInChildren<ParticleSystem>().Length==0,"contained fire is hidden at its external boundary");
            UnityEngine.Object.DestroyImmediate(effectsObject);
            plane.waypoints[0].y=float.NaN;bool rejected=false;try{flight.Validate();}catch(ArgumentException){rejected=true;}
            check(rejected,"invalid altitude is rejected");
            Debug.Log("FLIGHT_CLIENT_CHECKS_PASS: 17");
        }
        Debug.Log("TRAFFIC_CLIENT_CHECKS_PASS: 14 plus conversation regression");
    }
}
