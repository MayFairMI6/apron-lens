using UnityEngine;
using Vuforia;

namespace SurfaceSafety {
    public class VuforiaStandAnchor : MonoBehaviour {
        public StandReplay replay;
        ObserverBehaviour target;
        public void Bind(StandReplay controller){replay=controller;VuforiaApplication.Instance.OnVuforiaStarted+=CreateTarget;}
        void CreateTarget(){
            var texture=Resources.Load<Texture2D>("AirportBoard");
            target=VuforiaBehaviour.Instance.ObserverFactory.CreateImageTarget(texture,replay.Data.targetWidth,"SurfaceSafetyBoard");
            if(target==null){Debug.LogError("Image target creation failed");return;}
            replay.Content.SetParent(target.transform,false);
            target.OnTargetStatusChanged+=StatusChanged;replay.Tracking(false);
        }
        void StatusChanged(ObserverBehaviour observer,TargetStatus status){
            // Extended or limited tracking does not count as a directly observed board.
            replay.Tracking(status.Status==Status.TRACKED);
        }
        void OnDestroy(){
            VuforiaApplication.Instance.OnVuforiaStarted-=CreateTarget;
            if(target!=null)target.OnTargetStatusChanged-=StatusChanged;
        }
    }
}
