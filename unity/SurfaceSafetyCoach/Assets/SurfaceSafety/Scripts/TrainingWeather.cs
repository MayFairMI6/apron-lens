using System;
using UnityEngine;

namespace SurfaceSafety {
    [Serializable] public class EnvironmentFrame {public float t,precipitation,daylight=1;}
    [Serializable] public class TrainingEnvironment {public int version;public string kind;public EnvironmentFrame[] frames;}

    // Visual-only conditions. Source time controls intensity, motion and lighting;
    // no particle update uses wall time or asserts a report, visibility or clearance.
    public class TrainingWeather : MonoBehaviour {
        StandReplay replay;Camera view;GameObject root;Material material;
        readonly Transform[] particles=new Transform[160];
        Color originalSky,originalAmbient;UnityEngine.Rendering.AmbientMode originalMode;
        Light sun;float originalIntensity;Color originalSun;Quaternion originalRotation;
        string kind="";bool applied;
        public string ConditionLabel {
            get {var p=replay?.Data?.environment;if(p==null||p.version!=1)return "";
                if(p.kind=="dusk"){float d=At(p,replay.Clock.Time).daylight;return d>.65f?"Late afternoon":d>.2f?"Dusk":"Night";}
                return p.kind=="snow"?"Snowfall":p.kind=="rain"?"Rain":"";}
        }
        public void Bind(StandReplay owner,Camera camera,Light sharedSun=null){
            replay=owner;view=camera;originalSky=view.backgroundColor;
            originalAmbient=RenderSettings.ambientLight;originalMode=RenderSettings.ambientMode;
            sun=sharedSun;
            if(sun==null)foreach(var light in FindObjectsByType<Light>(FindObjectsSortMode.None))if(light.isActiveAndEnabled&&light.type==LightType.Directional){sun=light;break;}
            if(sun!=null){originalIntensity=sun.intensity;originalSun=sun.color;originalRotation=sun.transform.rotation;}
        }
        public static EnvironmentFrame At(TrainingEnvironment plan,float t){
            if(plan==null||plan.version!=1||plan.frames==null||plan.frames.Length==0)return new EnvironmentFrame();
            var fs=plan.frames;
            if(t<=fs[0].t)return fs[0];
            for(int i=1;i<fs.Length;i++)if(t<=fs[i].t){
                float f=Mathf.InverseLerp(fs[i-1].t,fs[i].t,t);
                return new EnvironmentFrame{t=t,precipitation=Mathf.Lerp(fs[i-1].precipitation,fs[i].precipitation,f),daylight=Mathf.Lerp(fs[i-1].daylight,fs[i].daylight,f)};
            }
            return fs[fs.Length-1];
        }
        public static void Validate(TrainingEnvironment plan,float duration){
            // JsonUtility materializes an empty optional object in legacy data.
            if(plan==null||(plan.version==0&&string.IsNullOrEmpty(plan.kind)&&(plan.frames==null||plan.frames.Length==0)))return;
            if(plan.version!=1||(plan.kind!="rain"&&plan.kind!="snow"&&plan.kind!="dusk")||plan.frames==null||plan.frames.Length<2||plan.frames.Length>32)
                throw new ArgumentException("Unsupported environment plan.");
            for(int i=0;i<plan.frames.Length;i++){
                var f=plan.frames[i];
                if(f==null||float.IsNaN(f.t)||float.IsInfinity(f.t)||f.t<0||f.t>duration||
                   float.IsNaN(f.precipitation)||f.precipitation<0||f.precipitation>1||
                   float.IsNaN(f.daylight)||f.daylight<0||f.daylight>1||
                   (i==0?f.t!=0:f.t<=plan.frames[i-1].t))throw new ArgumentException("Invalid environment frame.");
            }
        }
        static float Hash(int i,int salt)=>Mathf.Repeat(Mathf.Sin(i*127.1f+salt*311.7f)*43758.5453f,1);
        public static Vector3 ParticlePosition(int i,float t,bool snow,float aspect,float fov){
            float depth=22+Hash(i,1)*30,half=Mathf.Tan(fov*Mathf.Deg2Rad*.5f)*depth;
            float y=Mathf.Repeat(Hash(i,2)*2+1-t*(snow?.055f:.62f),2)-1;
            float x=(Hash(i,3)*2-1)*aspect+Mathf.Sin(t*.3f+i)*(snow?.065f:.02f);
            return new Vector3(x*half,y*half,depth);
        }
        void Make(string next){
            if(root!=null)Destroy(root);if(material!=null)Destroy(material);
            root=new GameObject("Source-clock weather");root.transform.SetParent(view.transform,false);
            material=new Material(Shader.Find("Sprites/Default"));
            material.color=next=="snow"?new Color(.96f,.98f,1,.78f):new Color(.7f,.8f,.9f,.5f);
            for(int i=0;i<particles.Length;i++){
                var go=GameObject.CreatePrimitive(PrimitiveType.Quad);Destroy(go.GetComponent<Collider>());
                go.name=next=="snow"?"Snowflake":"Raindrop";go.transform.SetParent(root.transform,false);
                go.GetComponent<Renderer>().sharedMaterial=material;particles[i]=go.transform;
                go.transform.localScale=next=="snow"?Vector3.one*(.07f+Hash(i,4)*.12f):new Vector3(.025f,.7f+Hash(i,4)*.5f,1);
                go.transform.localRotation=Quaternion.Euler(0,0,next=="snow"?45:12);
            }
            kind=next;
        }
        void LateUpdate(){
            if(replay==null||view==null)return;
            var plan=replay.Data?.environment;
            if(plan==null||plan.version!=1){if(applied)Restore();return;}
            if(plan.kind!="rain"&&plan.kind!="snow"&&plan.kind!="dusk"){if(applied)Restore();return;}
            applied=true;var frame=At(plan,replay.Clock.Time);float daylight=Mathf.Clamp01(frame.daylight);
            bool dusk=plan.kind=="dusk",snow=plan.kind=="snow";
            if(!dusk&&kind!=plan.kind)Make(plan.kind);
            if(root!=null)root.SetActive(!dusk);
            if(!dusk){
                int count=Mathf.RoundToInt(particles.Length*Mathf.Clamp01(frame.precipitation));
                for(int i=0;i<particles.Length;i++){
                    particles[i].gameObject.SetActive(i<count);
                    if(i<count)particles[i].localPosition=ParticlePosition(i,replay.Clock.Time,snow,view.aspect,view.fieldOfView);
                }
            }
            var overcast=snow?new Color(.69f,.72f,.76f):new Color(.32f,.4f,.47f);
            view.backgroundColor=dusk?Color.Lerp(new Color(.045f,.07f,.13f),new Color(.62f,.52f,.47f),daylight):Color.Lerp(originalSky,overcast,.4f+frame.precipitation*.55f);
            RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight=dusk?Color.Lerp(new Color(.18f,.22f,.30f),new Color(.72f,.65f,.58f),daylight):Color.Lerp(new Color(.65f,.68f,.72f),new Color(.37f,.43f,.5f),frame.precipitation*.6f);
            if(sun!=null){
                sun.intensity=dusk?Mathf.Lerp(.07f,originalIntensity*.75f,daylight):originalIntensity*(1-frame.precipitation*.55f);
                sun.color=dusk?Color.Lerp(new Color(.5f,.62f,1),new Color(1,.68f,.43f),daylight):originalSun;
                if(dusk)sun.transform.rotation=Quaternion.Euler(Mathf.Lerp(-5,18,daylight),-35,0);else sun.transform.rotation=originalRotation;
            }
        }
        void Restore(){
            if(root!=null)root.SetActive(false);if(view!=null)view.backgroundColor=originalSky;
            RenderSettings.ambientLight=originalAmbient;RenderSettings.ambientMode=originalMode;
            if(sun!=null){sun.intensity=originalIntensity;sun.color=originalSun;sun.transform.rotation=originalRotation;}
            applied=false;
        }
        void OnDestroy(){Restore();if(root!=null)Destroy(root);if(material!=null)Destroy(material);}
    }
}
