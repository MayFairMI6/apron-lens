using System;
using System.Linq;
using UnityEngine;

namespace SurfaceSafety {
    [Serializable] public class Waypoint { public float t, x, z; }
    [Serializable] public class AircraftPlan { public string id, flightInstance; public Waypoint[] waypoints; }
    [Serializable] public class EvidenceFact { public string property, value; }
    [Serializable] public class ScenarioEvent {
        public string id, aircraftId, flightInstance, source, message;
        public EvidenceFact[] facts;
        public float eventTime, receiptTime;
    }
    [Serializable] public class Scenario {
        public string scenarioId;
        public float duration, targetWidth;
        public AircraftPlan[] aircraft;
        public ScenarioEvent[] events;
        public void Validate() {
            if (duration <= 0 || targetWidth <= 0 || aircraft == null || aircraft.Length != 2)
                throw new ArgumentException("Scenario requires positive duration/width and two aircraft.");
            if (aircraft.Select(a => a.id).Distinct().Count() != aircraft.Length)
                throw new ArgumentException("Duplicate aircraft identity.");
            foreach (var a in aircraft) {
                if (string.IsNullOrEmpty(a.flightInstance) || a.waypoints == null || a.waypoints.Length < 2)
                    throw new ArgumentException("Missing flight identity or trajectory.");
                for (int i=0; i<a.waypoints.Length; i++) {
                    var w=a.waypoints[i];
                    if (float.IsNaN(w.t) || float.IsNaN(w.x) || float.IsNaN(w.z) ||
                        float.IsInfinity(w.t) || float.IsInfinity(w.x) || float.IsInfinity(w.z) ||
                        w.t < 0 || w.t > duration || (i>0 && w.t <= a.waypoints[i-1].t))
                        throw new ArgumentException("Invalid waypoint/time order.");
                }
            }
            if (events == null || events.Select(e=>e.id).Distinct().Count()!=events.Length)
                throw new ArgumentException("Missing events or duplicate evidence ID.");
            foreach(var e in events)
                if (e.eventTime<0 || e.receiptTime<e.eventTime || e.receiptTime>duration ||
                    string.IsNullOrEmpty(e.id) || string.IsNullOrEmpty(e.source) ||
                    !aircraft.Any(a=>a.flightInstance==e.flightInstance))
                    throw new ArgumentException("Invalid event identity or timestamps.");
        }
        public ScenarioEvent[] KnownAt(float t) => events.Where(e=>e.receiptTime<=t)
            .OrderBy(e=>e.receiptTime).ThenBy(e=>e.id, StringComparer.Ordinal).ToArray();
        public static Vector3 Position(AircraftPlan a, float t) {
            var ws=a.waypoints;
            if(t<=ws[0].t) return new Vector3(ws[0].x,0,ws[0].z);
            for(int i=1;i<ws.Length;i++) if(t<=ws[i].t) {
                float f=(t-ws[i-1].t)/(ws[i].t-ws[i-1].t);
                return Vector3.Lerp(new Vector3(ws[i-1].x,0,ws[i-1].z),new Vector3(ws[i].x,0,ws[i].z),f);
            }
            var w=ws[ws.Length-1]; return new Vector3(w.x,0,w.z);
        }
        public static Vector3 Direction(AircraftPlan a, float t) {
            for(int i=1;i<a.waypoints.Length;i++) if(t<a.waypoints[i].t) {
                var x=a.waypoints[i-1];var y=a.waypoints[i];
                var dir=new Vector3(y.x-x.x,0,y.z-x.z);
                if(dir.sqrMagnitude>0)return dir.normalized;
                for(int j=i+1;j<a.waypoints.Length;j++){
                    var next=a.waypoints[j];dir=new Vector3(next.x-y.x,0,next.z-y.z);
                    if(dir.sqrMagnitude>0)return dir.normalized;
                }
                return Vector3.forward;
            }
            var b=a.waypoints[a.waypoints.Length-2];var c=a.waypoints[a.waypoints.Length-1];
            return new Vector3(c.x-b.x,0,c.z-b.z).normalized;
        }
    }
    public class ReplayClock {
        public float Time {get;private set;}
        public bool Playing {get;private set;}
        public bool Tracked {get;private set;}
        public readonly float Duration;
        public ReplayClock(float duration){Duration=duration;}
        public void SetTracking(bool tracked){Tracked=tracked;if(!tracked)Playing=false;}
        public void Play(){Playing=Tracked && Time<Duration;}
        public void Pause(){Playing=false;}
        public void Restart(){Time=0;Playing=false;}
        public void Seek(float t){Time=Mathf.Clamp(t,0,Duration);Playing=false;}
        public void Advance(float dt){
            if(float.IsNaN(dt)||float.IsInfinity(dt)||dt<0)throw new ArgumentException("Invalid clock step");
            if(!Playing||!Tracked)return;
            Time=Mathf.Min(Duration,Time+dt);if(Time>=Duration)Playing=false;
        }
    }
}
