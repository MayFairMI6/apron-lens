using System.Collections.Generic;
using UnityEngine;

namespace SurfaceSafety {
    // Original visual assets. Every pose and effect age uses the external clock.
    // These visuals are never promoted to assistant evidence.
    public class TrainingIncidentEffects : MonoBehaviour {
        StandReplay replay;Material birdMaterial,particleMaterial;
        class Effect {public TrainingIncident plan;public GameObject root;public readonly List<Transform> birds=new List<Transform>();public ParticleSystem flames,smoke;public float lastAge=-1;}
        readonly List<Effect> effects=new List<Effect>();
        public void Bind(StandReplay owner){
            replay=owner;birdMaterial=new Material(Shader.Find("Standard"));birdMaterial.color=new Color(.86f,.88f,.86f);
            var texture=new Texture2D(32,32,TextureFormat.RGBA32,false);texture.wrapMode=TextureWrapMode.Clamp;
            for(int y=0;y<32;y++)for(int x=0;x<32;x++){float r=Vector2.Distance(new Vector2(x,y),new Vector2(15.5f,15.5f))/16;
                texture.SetPixel(x,y,new Color(1,1,1,Mathf.Pow(Mathf.Clamp01(1-r),1.5f)));}texture.Apply();
            particleMaterial=new Material(Shader.Find("Sprites/Default"));particleMaterial.mainTexture=texture;
            if(owner.Data.incidents==null)return;
            foreach(var plan in owner.Data.incidents){
                var e=new Effect{plan=plan,root=new GameObject(plan.id)};e.root.transform.SetParent(transform,false);
                e.root.transform.localPosition=new Vector3(plan.x,plan.y,plan.z);effects.Add(e);
                if(plan.kind=="wildlife")for(int i=0;i<9;i++){
                    var bird=new GameObject("Bird "+(i+1));bird.transform.SetParent(e.root.transform,false);e.birds.Add(bird.transform);
                    Wing(bird.transform,"Left wing",-1);Wing(bird.transform,"Right wing",1);
                }
                else if(plan.kind=="engine_fire"){
                    e.flames=Particles(e.root.transform,"Flames",new Color(1,.18f,.01f,.9f),new Color(1,.8f,.12f,0),.004f,.007f,1.2f,35);
                    e.smoke=Particles(e.root.transform,"Smoke",new Color(.12f,.13f,.14f,.65f),new Color(.24f,.25f,.27f,0),.008f,.008f,4.5f,12);
                }
                e.root.SetActive(false);
            }
        }
        void Wing(Transform parent,string name,int side){
            var go=new GameObject(name,typeof(MeshFilter),typeof(MeshRenderer));go.transform.SetParent(parent,false);
            var mesh=new Mesh();mesh.vertices=new[]{new Vector3(0,0,.00065f),new Vector3(side*.0011f,0,0),new Vector3(0,0,-.00055f)};
            mesh.triangles=new[]{0,1,2,2,1,0};mesh.normals=new[]{Vector3.up,Vector3.up,Vector3.up};go.GetComponent<MeshFilter>().sharedMesh=mesh;go.GetComponent<Renderer>().sharedMaterial=birdMaterial;
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
                for(int i=0;i<e.birds.Count;i++){
                    var b=e.birds[i];float leaving=Mathf.Clamp01((t-(e.plan.end-8))/8);
                    b.localPosition=new Vector3((i%3-1)*.007f+Mathf.Sin(age*.6f+i)*.002f, .001f+Mathf.Abs(Mathf.Sin(age*.7f+i))*.002f+leaving*.018f,(i/3-1)*.006f+leaving*.09f);
                    b.localRotation=Quaternion.Euler(0,15*Mathf.Sin(age*.4f+i),0);
                    for(int wing=0;wing<2;wing++)b.GetChild(wing).localRotation=Quaternion.Euler(0,0,(wing==0?1:-1)*35*Mathf.Sin(age*9+i));
                }
                if(e.flames!=null){
                    bool reset=e.lastAge<0||age<e.lastAge||age-e.lastAge>2;float dt=reset?age:age-e.lastAge;
                    if(reset){e.flames.Play(true);e.smoke.Play(true);}
                    e.flames.Simulate(dt,true,reset,false);e.smoke.Simulate(dt,true,reset,false);e.lastAge=age;
                }
            }
        }
        void OnDestroy(){
            if(particleMaterial!=null){Destroy(particleMaterial.mainTexture);Destroy(particleMaterial);}if(birdMaterial!=null)Destroy(birdMaterial);
        }
    }
}
