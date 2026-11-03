using System;
using System.Linq;
using UnityEngine;

namespace SurfaceSafety {
    [Serializable] public class Waypoint { public float t, x, y, z,pitch,heading,roll,bodySink; public bool reverse,gearRetracted; }
    [Serializable] public class FlightPhase {public float t;public string id,label;}
    [Serializable] public class RunwayPlan {public string id;public float x,z,length,width;}
    [Serializable] public class TaxiPoint {public float x,z;}
    [Serializable] public class TaxiPath {public string id,kind;public float width;public TaxiPoint[] points;}
    [Serializable] public class TrainingIncident {public string id,kind,aircraftId;public float start,onset,clearedAt,end,x,y,z;}
    // An aircraft flies one flight (legacy "flightInstance") or several rotations, in the
    // same format as backend/conversation/identity.py: ordered, non-overlapping
    // {flightInstance, from, until}; the last may omit "until" (open). Bindings come only
    // from scenario data; a user correction selects among them and never creates one.
    [Serializable] public class RotationPlan { public string flightInstance; public float from; public float until = -1; }
    [Serializable] public class AircraftPlan {
        public string id, flightInstance;
        public bool preciseHeading;
        public bool hidden; // Nonparticipant identity slots in regional scenarios; legacy default is visible.
        public RotationPlan[] rotations;
        public Waypoint[] waypoints;
        public FlightPhase[] phases;
        public FlightPhase PhaseAt(float t) => phases==null?null:phases.LastOrDefault(p=>p.t<=t);
        public bool GearRetractedAt(float t) => waypoints.LastOrDefault(p=>p.t<=t)?.gearRetracted??false;
        public RotationPlan[] Rotations => rotations != null && rotations.Length > 0 ? rotations
            : new[] { new RotationPlan { flightInstance = flightInstance, from = 0 } };
        public bool Flies(string flight) => Rotations.Any(r => r.flightInstance == flight);
        // The rotation under way at t; between rotations, the latest one that has started.
        public string FlightAt(float t) {
            var started = Rotations.Where(r => r.from <= t).ToArray();
            return (started.Length > 0 ? started[started.Length - 1] : Rotations[0]).flightInstance;
        }
    }
    [Serializable] public class EvidenceFact { public string property, value; }
    [Serializable] public class ScenarioEvent {
        public string id, aircraftId, flightInstance, source, message;
        public EvidenceFact[] facts;
        public float eventTime, receiptTime;
    }
    // Visual-only scene state: rendered in the replay but never sent as a report.
    // The backend request path never reads it; it is ground truth for scoring only.
    [Serializable] public class PropState { public float t; public string value; }
    [Serializable] public class VisualProp {
        public string id, aircraftId, flightInstance, kind;
        public PropState[] states;
    }
    // Scene geometry that can hide props from the evidence camera (occlusion families),
    // such as a service canopy: a roof slab of width (x) by depth (z) at a height, in
    // board coordinates. Rendered and captured like the rest of the scene.
    [Serializable] public class Occluder { public string id; public float x, z, width, depth, height; }
    [Serializable] public class Scenario {
        public TrainingEnvironment environment;
        public RegionalGeography geography;
        public const int MaxAircraft = 4;
        public string scenarioId;
        public string trainingRole, trainingRoleLabel, trainingObjective;
        public string[] assistantQuestionLabels, assistantQuestions;
        // "uniform" renders every aircraft in one livery so that only position, motion
        // and props tell them apart; omitted or "indexed" keeps one colour per aircraft.
        public string livery;
        // "runs": the replay keeps running while the board is out of the camera's view, as a real apron would
        // (tracking interruptions, docs/AR_SCOPE.md). Default "pauses", the Milestone 1 behaviour.
        public string clockWhileUntracked;
        public bool ClockRunsUntracked => clockWhileUntracked == "runs";
        public bool UniformLivery => livery == "uniform";
        public float duration, targetWidth;
        public AircraftPlan[] aircraft;
        public ScenarioEvent[] events;
        public VisualProp[] visualProps;
        public Occluder[] occluders;
        public AircraftPlan[] groundVehicles; // Rendering-only vehicle routes from the external lesson driver.
        public RunwayPlan runway;
        public TaxiPath[] taxiPaths;
        public TrainingIncident[] incidents;
        static readonly string[] FuelVehicleValues = { "connected", "departed" };
        static readonly string[] CargoDoorValues = { "open", "closed" };
        public static bool AllowedPropValue(string kind, string value) =>
            kind == "fuel_vehicle" ? Array.IndexOf(FuelVehicleValues, value) >= 0 :
            kind == "cargo_door" && Array.IndexOf(CargoDoorValues, value) >= 0;
        public static string PropValueAt(VisualProp p, float t) {
            var value = p.states[0].value;
            foreach (var s in p.states) if (s.t <= t) value = s.value;
            return value;
        }
        void ValidateProps() {
            if (visualProps == null) return;
            if (visualProps.Select(p => p.id).Distinct().Count() != visualProps.Length)
                throw new ArgumentException("Duplicate visual prop ID.");
            foreach (var p in visualProps) {
                if (string.IsNullOrEmpty(p.id) || !aircraft.Any(a => a.id == p.aircraftId && a.Flies(p.flightInstance)))
                    throw new ArgumentException("Visual prop must belong to a scenario aircraft and flight.");
                if (p.states == null || p.states.Length == 0 || p.states[0].t != 0)
                    throw new ArgumentException("Visual prop states must start at time 0.");
                for (int i = 0; i < p.states.Length; i++) {
                    var s = p.states[i];
                    if (!AllowedPropValue(p.kind, s.value) || s.t < 0 || s.t > duration || (i > 0 && s.t <= p.states[i - 1].t))
                        throw new ArgumentException("Invalid visual prop kind, value or time order.");
                }
            }
        }
        public void Validate() {
            TrainingGeography.Validate(geography);
            if (duration <= 0 || targetWidth <= 0 || aircraft == null || aircraft.Length < 2 || aircraft.Length > MaxAircraft)
                throw new ArgumentException("Scenario requires positive duration/width and two to " + MaxAircraft + " aircraft.");
            if (!string.IsNullOrEmpty(livery) && livery != "indexed" && livery != "uniform")
                throw new ArgumentException("Livery must be \"indexed\" or \"uniform\".");
            if (!string.IsNullOrEmpty(clockWhileUntracked) && clockWhileUntracked != "pauses" && clockWhileUntracked != "runs")
                throw new ArgumentException("clockWhileUntracked must be \"pauses\" or \"runs\".");
            if (aircraft.Select(a => a.id).Distinct().Count() != aircraft.Length)
                throw new ArgumentException("Duplicate aircraft identity.");
            var owner = new System.Collections.Generic.Dictionary<string, string>();
            foreach (var a in aircraft) {
                if (a.waypoints == null || a.waypoints.Length < 2)
                    throw new ArgumentException("Missing trajectory.");
                if ((a.rotations == null || a.rotations.Length == 0) && string.IsNullOrEmpty(a.flightInstance))
                    throw new ArgumentException("Missing flight identity.");
                var rotations = a.Rotations;
                for (int i = 0; i < rotations.Length; i++) {
                    var r = rotations[i];
                    if (string.IsNullOrEmpty(r.flightInstance) || owner.ContainsKey(r.flightInstance))
                        throw new ArgumentException("Flight instance missing or assigned to more than one aircraft or rotation.");
                    owner[r.flightInstance] = a.id;
                    if (r.from < 0 || (r.until >= 0 && r.until <= r.from) || (i > 0 && (rotations[i - 1].until < 0 || r.from < rotations[i - 1].until)))
                        throw new ArgumentException("Rotations must be ordered and non-overlapping.");
                }
                for (int i=0; i<a.waypoints.Length; i++) {
                    var w=a.waypoints[i];
                    if (float.IsNaN(w.t) || float.IsNaN(w.x) || float.IsNaN(w.y) || float.IsNaN(w.z) ||
                        float.IsInfinity(w.t) || float.IsInfinity(w.x) || float.IsInfinity(w.y) || float.IsInfinity(w.z) || w.y<0 || float.IsNaN(w.heading)||float.IsInfinity(w.heading) || float.IsNaN(w.pitch)||float.IsInfinity(w.pitch)||Mathf.Abs(w.pitch)>30 ||
                        float.IsNaN(w.roll)||float.IsInfinity(w.roll)||Mathf.Abs(w.roll)>30 ||
                        float.IsNaN(w.bodySink)||float.IsInfinity(w.bodySink)||w.bodySink<0||w.bodySink>.005f ||
                        w.t < 0 || w.t > duration || (i>0 && w.t <= a.waypoints[i-1].t))
                        throw new ArgumentException("Invalid waypoint/time order.");
                }
                if(a.phases!=null)for(int i=0;i<a.phases.Length;i++){
                    var p=a.phases[i];
                    if(string.IsNullOrEmpty(p.id)||string.IsNullOrEmpty(p.label)||float.IsNaN(p.t)||float.IsInfinity(p.t)||p.t<0||p.t>duration||(i>0&&p.t<=a.phases[i-1].t))
                        throw new ArgumentException("Invalid flight phase order.");
                }
            }
            if (events == null || events.Select(e=>e.id).Distinct().Count()!=events.Length)
                throw new ArgumentException("Missing events or duplicate evidence ID.");
            foreach(var e in events)
                if (e.eventTime<0 || e.receiptTime<e.eventTime || e.receiptTime>duration ||
                    string.IsNullOrEmpty(e.id) || string.IsNullOrEmpty(e.source) ||
                    !owner.TryGetValue(e.flightInstance ?? "", out var flightOwner) || flightOwner != e.aircraftId)
                    throw new ArgumentException("Invalid event identity or timestamps, or the flight is not its aircraft's.");
            ValidateProps();TrainingWeather.Validate(environment,duration);
            if (occluders != null)
                foreach (var o in occluders)
                    if (string.IsNullOrEmpty(o.id) || o.width <= 0 || o.depth <= 0 || o.height <= 0 ||
                        Mathf.Abs(o.x) > targetWidth / 2 || Mathf.Abs(o.z) > targetWidth / 3)
                        throw new ArgumentException("Occluder needs an ID, positive size and height, and a position on the board.");
        }
        public ScenarioEvent[] KnownAt(float t) => events.Where(e=>e.receiptTime<=t)
            .OrderBy(e=>e.receiptTime).ThenBy(e=>e.id, StringComparer.Ordinal).ToArray();
        public static Vector3 Position(AircraftPlan a, float t) {
            var ws=a.waypoints;
            if(t<=ws[0].t) return new Vector3(ws[0].x,ws[0].y,ws[0].z);
            for(int i=1;i<ws.Length;i++) if(t<=ws[i].t) {
                float f=(t-ws[i-1].t)/(ws[i].t-ws[i-1].t);
                return Vector3.Lerp(new Vector3(ws[i-1].x,ws[i-1].y,ws[i-1].z),new Vector3(ws[i].x,ws[i].y,ws[i].z),f);
            }
            var w=ws[ws.Length-1]; return new Vector3(w.x,w.y,w.z);
        }
        public static Vector3 Direction(AircraftPlan a, float t) {
            for(int i=1;i<a.waypoints.Length;i++) if(t<a.waypoints[i].t) {
                var x=a.waypoints[i-1];var y=a.waypoints[i];
                var dir=new Vector3(y.x-x.x,y.y-x.y,y.z-x.z);
                if(dir.sqrMagnitude>0)return y.reverse?-dir.normalized:dir.normalized;
                for(int j=i+1;j<a.waypoints.Length;j++){
                    var next=a.waypoints[j];dir=new Vector3(next.x-y.x,next.y-y.y,next.z-y.z);
                    if(dir.sqrMagnitude>0)return next.reverse?-dir.normalized:dir.normalized;
                }
                return Vector3.forward;
            }
            var b=a.waypoints[a.waypoints.Length-2];var c=a.waypoints[a.waypoints.Length-1];
            return new Vector3(c.x-b.x,c.y-b.y,c.z-b.z).normalized;
        }
        public static float Heading(AircraftPlan a,float t){
            if(!a.preciseHeading){var d=Direction(a,t);return Mathf.Repeat(Mathf.Atan2(d.x,d.z)*Mathf.Rad2Deg,360);}
            var ws=a.waypoints;if(t<=ws[0].t)return ws[0].heading;
            for(int i=1;i<ws.Length;i++)if(t<=ws[i].t)return Mathf.Repeat(Mathf.LerpAngle(ws[i-1].heading,ws[i].heading,(t-ws[i-1].t)/(ws[i].t-ws[i-1].t)),360);
            return ws[ws.Length-1].heading;
        }
        public static float Pitch(AircraftPlan a,float t){
            var ws=a.waypoints;if(t<=ws[0].t)return ws[0].pitch;
            for(int i=1;i<ws.Length;i++)if(t<=ws[i].t)return Mathf.Lerp(ws[i-1].pitch,ws[i].pitch,(t-ws[i-1].t)/(ws[i].t-ws[i-1].t));
            return ws[ws.Length-1].pitch;
        }
        public static float Roll(AircraftPlan a,float t)=>Attitude(a,t,false);
        public static float BodySink(AircraftPlan a,float t)=>Attitude(a,t,true);
        static float Attitude(AircraftPlan a,float t,bool sink){
            var ws=a.waypoints;System.Func<Waypoint,float> value=w=>sink?w.bodySink:w.roll;
            if(t<=ws[0].t)return value(ws[0]);
            for(int i=1;i<ws.Length;i++)if(t<=ws[i].t)return Mathf.Lerp(value(ws[i-1]),value(ws[i]),(t-ws[i-1].t)/(ws[i].t-ws[i-1].t));
            return value(ws[ws.Length-1]);
        }
    }
    public class ReplayClock {
        public float Time {get;private set;}
        public bool Playing {get;private set;}
        public bool Tracked {get;private set;}
        public readonly float Duration;
        public readonly bool RunsUntracked;
        public ReplayClock(float duration,bool runsUntracked=false){Duration=duration;RunsUntracked=runsUntracked;}
        public void SetTracking(bool tracked){Tracked=tracked;if(!tracked&&!RunsUntracked)Playing=false;}
        public void Play(){Playing=(Tracked||RunsUntracked) && Time<Duration;}
        public void Pause(){Playing=false;}
        public void Restart(){Time=0;Playing=false;}
        public void Seek(float t){Time=Mathf.Clamp(t,0,Duration);Playing=false;}
        public void Advance(float dt){
            if(float.IsNaN(dt)||float.IsInfinity(dt)||dt<0)throw new ArgumentException("Invalid clock step");
            if(!Playing||(!Tracked&&!RunsUntracked))return;
            Time=Mathf.Min(Duration,Time+dt);if(Time>=Duration)Playing=false;
        }
    }
}
