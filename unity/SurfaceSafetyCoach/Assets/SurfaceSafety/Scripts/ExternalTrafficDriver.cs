using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

namespace SurfaceSafety {
    // The external service owns exercise time; the app is only a viewer.
    public class ExternalTrafficDriver : MonoBehaviour {
        [Serializable] class TrafficClock {public string runId,state;public int revision;public float rate,nextBoundary;}
        [Serializable] class Snapshot { public float serverTime; public Scenario scenario; public bool synthetic; public string exerciseTitle;public TrafficClock clock;public TrainingState training; }
        StandReplay replay; ConversationClient connection;
        UnityWebRequest active; float serverTime, receivedAt,rate=1,nextBoundary=float.MaxValue; bool received;TrainingView training;
        public void Bind(StandReplay target,ConversationClient assistant){replay=target;connection=assistant;StartCoroutine(Poll());}
        IEnumerator Poll(){
            while(true){
                active=connection.TrafficRequest();
                yield return active.SendWebRequest();
                if(active.result==UnityWebRequest.Result.Success){
                    try{
                        var snapshot=JsonUtility.FromJson<Snapshot>(active.downloadHandler.text);
                        if(snapshot==null||snapshot.scenario==null||float.IsNaN(snapshot.serverTime)||float.IsInfinity(snapshot.serverTime)||snapshot.serverTime<0||snapshot.serverTime>snapshot.scenario.duration)
                            throw new ArgumentException("Invalid traffic snapshot");
                        var newRate=snapshot.clock==null?1:snapshot.clock.rate;var newBoundary=snapshot.clock==null?snapshot.scenario.duration:snapshot.clock.nextBoundary;
                        if(float.IsNaN(newRate)||float.IsInfinity(newRate)||newRate<0||newRate>30||float.IsNaN(newBoundary)||float.IsInfinity(newBoundary)||newBoundary<snapshot.serverTime||newBoundary>snapshot.scenario.duration)
                            throw new ArgumentException("Invalid external clock");
                        replay.ApplyTrafficScenario(snapshot.scenario);replay.TrainingTitle=snapshot.exerciseTitle??"";
                        rate=newRate;nextBoundary=newBoundary;
                        if(snapshot.training!=null&&!string.IsNullOrEmpty(snapshot.training.runId)){
                            if(training==null){training=gameObject.AddComponent<TrainingView>();training.Bind(replay,connection);}
                            training.Connected=true;training.Apply(snapshot.training);
                        }
                        serverTime=snapshot.serverTime;receivedAt=Time.realtimeSinceStartup;received=true;
                    }catch(Exception ex){Debug.LogWarning("Traffic update rejected: "+ex.GetType().Name);}
                }
                active.Dispose();active=null;
                yield return new WaitForSecondsRealtime(1);
            }
        }
        void Update(){
            if(replay==null||!received)return;
            var age=Time.realtimeSinceStartup-receivedAt;
            if(training!=null)training.Connected=age<=3;
            var state=age>3?"Traffic connection interrupted":serverTime>=replay.Data.duration?"Exercise complete":"";
            // Bound prediction; a disconnected client freezes rather than inventing traffic.
            replay.UpdateTrafficTime(PredictTime(serverTime,age,rate,nextBoundary),state);
        }
        public static float PredictTime(float source,float age,float speed,float boundary)=>Mathf.Min(boundary,source+Mathf.Clamp(age,0,3)*speed);
        void OnDestroy(){StopAllCoroutines();if(active!=null){active.Abort();active.Dispose();active=null;}}
    }
}
