using UnityEngine;

namespace SurfaceSafety {
    // Simulated world-scale AR (docs/AR_SCOPE.md): no marker or print. The replay is laid out in metres on a
    // full-scale fictional apron, and the user sees it through the AR camera (AR Foundation; in the editor, XR
    // Simulation renders the apron environment as the camera feed). Tracking follows the camera: the apron is in
    // view while its centre is inside the camera's view, and turning away interrupts it as a lost marker did, so
    // the "While you were away" card and awayIntervals work unchanged.
    public class WorldArBootstrap : MonoBehaviour {
        public const float MetresPerBoardUnit = 1000f;  // the 0.24 m board becomes a 240 m apron
        public string scenarioResource = "ar_demo_01";
        public StandReplay Replay {get;private set;}

        void Awake(){Initialize();}

        public void Initialize(){
            if(Replay!=null)return;
            if(FindFirstObjectByType<Light>()==null){
                var sun=new GameObject("Sun",typeof(Light)).GetComponent<Light>();
                sun.type=LightType.Directional;sun.intensity=1.2f;sun.transform.rotation=Quaternion.Euler(50,-35,0);
            }
            Replay=gameObject.AddComponent<StandReplay>();Replay.Initialize(true,scenarioResource);
            Replay.UseWorldScale(MetresPerBoardUnit);
            gameObject.AddComponent<QwenReasoningClient>().Bind(Replay);
            gameObject.AddComponent<ConversationClient>().Bind(Replay);
        }

        // The apron is in view while its centre projects inside the camera's view (a small margin avoids flicker).
        public static bool ApronInView(Camera camera,Vector3 apronCentre){
            var v=camera.WorldToViewportPoint(apronCentre);
            return v.z>0&&v.x>-.05f&&v.x<1.05f&&v.y>-.05f&&v.y<1.05f;
        }

        void LateUpdate(){
            var camera=Camera.main;
            if(camera==null||Replay==null||Replay.Clock==null)return;
            var inView=ApronInView(camera,Replay.Content.position);
            if(inView!=Replay.Clock.Tracked)Replay.Tracking(inView);
        }
    }
}
