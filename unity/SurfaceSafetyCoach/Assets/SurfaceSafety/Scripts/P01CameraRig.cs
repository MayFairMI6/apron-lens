// PROCEDURAL: repeatable presentation/capture poses, not report or clearance evidence.
using UnityEngine;
namespace SurfaceSafety {
    public enum P01CameraPose { Stand, BridgeOccluded, LookAway }
    public sealed class P01CameraRig : MonoBehaviour {
        public bool OverrideCamera {get;private set;}
        public bool TrackingAvailable {get;private set;}=true;
        public bool Scripted {get;private set;}
        public P01CameraPose Pose {get;private set;}
        StandReplay replay;Camera view;
        Vector3 positionOffsetMetres;
        public void SetCaptureOffset(Vector3 offsetMetres){positionOffsetMetres=offsetMetres;if(OverrideCamera)ApplyPose();}
        public void Bind(StandReplay target,Camera camera){replay=target;view=camera;}
        public void SetPose(P01CameraPose pose,bool trackingAvailable=true){
            Scripted=false;OverrideCamera=true;Pose=pose;TrackingAvailable=trackingAvailable;ApplyPose();
        }
        public void SetScripted(bool enabled){Scripted=enabled;OverrideCamera=enabled;TrackingAvailable=true;if(enabled)Tick();}
        public void ReleaseCamera(){Scripted=false;OverrideCamera=false;TrackingAvailable=true;}
        public void Tick(){
            if(replay==null||!P01StandScenery.Applies(replay.Data)){ReleaseCamera();return;}
            if(Scripted){
                // Repeat the same four conditions while occupied (40–60 s), and
                // around departure (88–108 s). Only the external source clock
                // selects these poses; wall time cannot move the scenario.
                float t=replay.Clock.Time;
                float phase=t>=88&&t<108?t-88:t>=40&&t<60?t-40:-1;
                Pose=phase>=5&&phase<10?P01CameraPose.BridgeOccluded:phase>=10&&phase<15?P01CameraPose.LookAway:P01CameraPose.Stand;
                TrackingAvailable=!(phase>=15&&phase<20);
            }
            if(OverrideCamera)ApplyPose();
        }
        void ApplyPose(){
            if(view==null||replay==null)return;
            // Camera positions and targets use the existing authored apron in
            // metres; Content transforms convert through board units once.
            Vector3 position=Pose==P01CameraPose.BridgeOccluded?new Vector3(8,4,88):new Vector3(72,12,-35);
            Vector3 target=Pose==P01CameraPose.LookAway?new Vector3(140,8,-130):new Vector3(40,1.8f,39);
            position+=positionOffsetMetres;
            if(Pose==P01CameraPose.BridgeOccluded){
                var vehicle=replay.Content.Find("service-vehicle");
                if(vehicle!=null){
                    target=vehicle.localPosition*WorldArBootstrap.MetresPerBoardUnit+Vector3.up*1.8f;
                    // Sightline through the existing opaque B bridge cab, not a
                    // visibility flag. Offset controls distance behind it, keeping
                    // each pilot domain's camera distinct without missing the cab.
                    var blocker=new Vector3(22,4,70);
                    position=blocker+(blocker-target).normalized*(18+positionOffsetMetres.x*.25f);
                }
            }
            var world=replay.Content.TransformPoint(position/WorldArBootstrap.MetresPerBoardUnit);
            var aim=replay.Content.TransformPoint(target/WorldArBootstrap.MetresPerBoardUnit);
            view.transform.SetPositionAndRotation(world,Quaternion.LookRotation(aim-world,Vector3.up));view.fieldOfView=55;
        }
    }
}
