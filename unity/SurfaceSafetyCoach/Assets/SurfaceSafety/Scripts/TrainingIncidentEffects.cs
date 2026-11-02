using System.Collections.Generic;
using UnityEngine;

namespace SurfaceSafety {
    // Original visual assets. Every pose and effect age uses the external clock.
    // These visuals are never promoted to assistant evidence.
    public class TrainingIncidentEffects : MonoBehaviour {
        StandReplay replay;Material particleMaterial;IncidentModels models;
        class Effect {public TrainingIncident plan;public GameObject root;public readonly List<IncidentModels.BirdRig> birds=new List<IncidentModels.BirdRig>();public IncidentModels.BaggageRig baggage;public ParticleSystem flames,smoke;public float lastAge=-1;}
        readonly List<Effect> effects=new List<Effect>();
        public void Bind(StandReplay owner){
            replay=owner;models=new IncidentModels();
            var texture=new Texture2D(32,32,TextureFormat.RGBA32,false);texture.wrapMode=TextureWrapMode.Clamp;
            for(int y=0;y<32;y++)for(int x=0;x<32;x++){float r=Vector2.Distance(new Vector2(x,y),new Vector2(15.5f,15.5f))/16;
                texture.SetPixel(x,y,new Color(1,1,1,Mathf.Pow(Mathf.Clamp01(1-r),1.5f)));}texture.Apply();
            particleMaterial=new Material(Shader.Find("Sprites/Default"));particleMaterial.mainTexture=texture;
            if(owner.Data.incidents==null)return;
            foreach(var plan in owner.Data.incidents){
                var e=new Effect{plan=plan,root=new GameObject(plan.id)};e.root.transform.SetParent(transform,false);
                e.root.transform.localPosition=new Vector3(plan.x,plan.y,plan.z);effects.Add(e);
                if(plan.kind=="wildlife")for(int i=0;i<9;i++)e.birds.Add(models.Bird(e.root.transform,i));
                else if(plan.kind=="baggage_spill")e.baggage=models.Baggage(e.root.transform);
                else if(plan.kind=="engine_fire"){
                    e.flames=Particles(e.root.transform,"Flames",new Color(1,.18f,.01f,.9f),new Color(1,.8f,.12f,0),.004f,.007f,1.2f,35);
                    e.smoke=Particles(e.root.transform,"Smoke",new Color(.12f,.13f,.14f,.65f),new Color(.24f,.25f,.27f,0),.008f,.008f,4.5f,12);
                }
                e.root.SetActive(false);
            }
        }
        ParticleSystem Particles(Transform parent,string name,Color begin,Color end,float size,float speed,float life,float rate){
            var go=new GameObject(name);go.transform.SetParent(parent,false);go.transform.localRotation=Quaternion.Euler(-90,0,0);
            var ps=go.AddComponent<ParticleSystem>();ps.Stop(true,ParticleSystemStopBehavior.StopEmittingAndClear);
            var main=ps.main;main.playOnAwake=false;main.loop=true;main.duration=5;main.simulationSpace=ParticleSystemSimulationSpace.Local;main.scalingMode=ParticleSystemScalingMode.Hierarchy;
            main.startLifetime=life;main.startSpeed=new ParticleSystem.MinMaxCurve(speed*.6f,speed);main.startSize=new ParticleSystem.MinMaxCurve(size*.6f,size);main.startColor=Color.white;main.maxParticles=200;
            var emission=ps.emission;emission.rateOverTime=rate;var shape=ps.shape;shape.shapeType=ParticleSystemShapeType.Cone;shape.angle=12;shape.radius=.0013f;
            var color=ps.colorOverLifetime;color.enabled=true;var gradient=new Gradient();gradient.SetKeys(new[]{new GradientColorKey(begin,0),new GradientColorKey(end,1)},new[]{new GradientAlphaKey(begin.a,0),new GradientAlphaKey(0,1)});color.color=gradient;
            var renderer=go.GetComponent<ParticleSystemRenderer>();renderer.sharedMaterial=particleMaterial;renderer.maxParticleSize=.3f;
            ps.useAutoRandomSeed=false;ps.randomSeed=17;return ps;
        }
        void LateUpdate(){
            if(replay?.Clock!=null)RenderAt(replay.Clock.Time);
        }
        public void RenderAt(float t){
            foreach(var e in effects){
                bool active=t>=e.plan.start&&t<e.plan.end;e.root.SetActive(active);if(!active){e.lastAge=-1;continue;}
                float age=t-e.plan.start;
                for(int i=0;i<e.birds.Count;i++)e.birds[i].Pose(age,i,e.plan.end-e.plan.start);
                if(e.baggage!=null)e.baggage.Pose(t,e.plan);
                if(e.flames!=null){
                    bool reset=e.lastAge<0||age<e.lastAge||age-e.lastAge>2;float dt=reset?age:age-e.lastAge;
                    if(reset){e.flames.Play(true);e.smoke.Play(true);}
                    e.flames.Simulate(dt,true,reset,false);e.smoke.Simulate(dt,true,reset,false);e.lastAge=age;
                }
            }
        }
        void OnDestroy(){
            if(particleMaterial!=null){Destroy(particleMaterial.mainTexture);Destroy(particleMaterial);}models?.Dispose();
        }
    }
}
