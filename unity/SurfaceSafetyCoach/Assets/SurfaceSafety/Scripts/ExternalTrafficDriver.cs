using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

namespace SurfaceSafety {
    // The external service owns exercise time; the app is only a viewer.
    public class ExternalTrafficDriver : MonoBehaviour {
        [Serializable] class TrafficClock {public string runId,state;public int revision;public float rate,nextBoundary;}
        [Serializable] class Snapshot { public float serverTime; public Scenario scenario; public bool synthetic; public string exerciseTitle;public TrafficClock clock;public TrainingState training;public ReplayView replay; }
        StandReplay replay; ConversationClient connection;
        UnityWebRequest active; float serverTime, receivedAt,rate=1,nextBoundary=float.MaxValue; bool received,replayMode;int replayRevision=-1;string replayRun="";TrainingView training;
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
                        bool isReplay=snapshot.replay!=null&&!string.IsNullOrEmpty(snapshot.replay.runId);
                        // A poll that started before a newer control reply must not move the view back.
                        if(isReplay&&snapshot.replay.runId==replayRun&&snapshot.replay.viewRevision<replayRevision)
                            throw new ArgumentException("Stale replay view");
                        rate=newRate;nextBoundary=newBoundary;
                        if(snapshot.training!=null&&!string.IsNullOrEmpty(snapshot.training.runId)){
                            if(training==null){training=gameObject.AddComponent<TrainingView>();training.Bind(replay,connection);}
                            training.Connected=true;training.Apply(snapshot.training);
                        }
                        replayMode=isReplay;
                        if(isReplay){replayRun=snapshot.replay.runId;replayRevision=snapshot.replay.viewRevision;training?.ApplyReplay(snapshot.replay,this);}
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
            // The replay scene never runs more than a poll or so ahead of the report list.
            if(replayMode)replay.SetReplayTime(PredictTime(serverTime,Mathf.Min(age,1.5f),rate,nextBoundary),age>3?state:"");
            else replay.UpdateTrafficTime(PredictTime(serverTime,age,rate,nextBoundary),state);
        }
        // A control reply carries the new view; use it at once and let later polls confirm it.
        public void AcceptReplay(ReplayView view){
            if(view==null||string.IsNullOrEmpty(view.runId)||(view.runId==replayRun&&view.viewRevision<replayRevision))return;
            replayRun=view.runId;replayRevision=view.viewRevision;replayMode=true;
            serverTime=view.cutoff;rate=view.rate;nextBoundary=view.playing?view.end:view.cutoff;
            receivedAt=Time.realtimeSinceStartup;received=true;
        }
        public static float PredictTime(float source,float age,float speed,float boundary)=>Mathf.Min(boundary,source+Mathf.Clamp(age,0,3)*speed);
        void OnDestroy(){StopAllCoroutines();if(active!=null){active.Abort();active.Dispose();active=null;}}
    }
}
