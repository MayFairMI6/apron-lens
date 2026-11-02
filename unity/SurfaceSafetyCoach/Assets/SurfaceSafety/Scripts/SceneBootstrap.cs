using UnityEngine;
#if !APRONLENS_SIMULATOR
using Vuforia;
#endif

namespace SurfaceSafety {
    public class SceneBootstrap : MonoBehaviour {
        public bool previewMode;
        public string scenarioResource="milestone1";
        public string scenarioJson; // when set, used instead of scenarioResource (held-out renders)
        public StandReplay Replay {get;private set;}
        Camera previewCamera;
        public static void FramePreview(Camera camera){
            camera.transform.position=new Vector3(0,.29f,-.23f);camera.transform.LookAt(Vector3.zero);
            camera.orthographic=true;camera.orthographicSize=.138f/camera.aspect;
            camera.transform.position-=camera.transform.up*(camera.orthographicSize*.38f);
        }
        void LateUpdate(){if(previewCamera!=null)FramePreview(previewCamera);}
        void Awake(){Initialize();}
        public void Initialize(){
            if(Replay!=null)return;
            var lamp=new GameObject("Sun",typeof(Light));var light=lamp.GetComponent<Light>();
            light.type=LightType.Directional;light.intensity=1.3f;lamp.transform.rotation=Quaternion.Euler(50,-35,0);
            RenderSettings.ambientLight=new Color(.6f,.65f,.7f);
            var cam=new GameObject(previewMode?"PreviewCamera":"ARCamera",typeof(Camera),typeof(AudioListener));
            cam.tag="MainCamera";var camera=cam.GetComponent<Camera>();camera.nearClipPlane=.005f;camera.farClipPlane=10;
            camera.backgroundColor=new Color(.055f,.095f,.13f);camera.clearFlags=CameraClearFlags.SolidColor;
            if(previewMode){previewCamera=camera;FramePreview(camera);}
            Replay=gameObject.AddComponent<StandReplay>();
            if(string.IsNullOrEmpty(scenarioJson))Replay.Initialize(previewMode,scenarioResource);else Replay.InitializeFromJson(previewMode,scenarioJson);
            gameObject.AddComponent<QwenReasoningClient>().Bind(Replay);
            gameObject.AddComponent<ConversationClient>().Bind(Replay);
            if(!previewMode){
                Replay.Content.gameObject.SetActive(false);
                #if !APRONLENS_SIMULATOR
                var anchor=gameObject.AddComponent<VuforiaStandAnchor>();anchor.Bind(Replay);
                cam.AddComponent<VuforiaBehaviour>();
#endif
            }
        }
    }
}
