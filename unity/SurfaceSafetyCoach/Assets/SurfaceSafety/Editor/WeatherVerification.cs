using System;
using UnityEngine;
using UnityEngine.Rendering;
using SurfaceSafety;

public static class WeatherVerification {
    static bool Rejected(TrainingEnvironment p,float duration=3600){try{TrainingWeather.Validate(p,duration);return false;}catch(ArgumentException){return true;}}
    static TrainingEnvironment Fog()=>new TrainingEnvironment{version=2,kind="fog",frames=new[]{
        new EnvironmentFrame{t=0},new EnvironmentFrame{t=600,fogExtinctionPerMetre=.0012f},
        new EnvironmentFrame{t=1600,fogExtinctionPerMetre=.0012f},new EnvironmentFrame{t=2200,fogExtinctionPerMetre=.00008f},
        new EnvironmentFrame{t=2400},new EnvironmentFrame{t=3600}}};
    public static void Run(){
        int n=0;Action<bool,string> check=(ok,label)=>{if(!ok)throw new Exception("Weather check: "+label);n++;};
        var plan=new TrainingEnvironment{version=1,kind="rain",frames=new[]{
            new EnvironmentFrame{t=0,precipitation=.1f,daylight=1},
            new EnvironmentFrame{t=3600,precipitation=.9f,daylight=.1f}}};
        TrainingWeather.Validate(plan,3600);
        check(Mathf.Abs(TrainingWeather.At(plan,1800).precipitation-.5f)<.001f,"source-time interpolation");
        check(TrainingWeather.At(null,100).daylight==1,"legacy scene retains daylight");
        TrainingWeather.Validate(new TrainingEnvironment(),3600);
        check(TrainingWeather.At(new TrainingEnvironment(),100).daylight==1,"JsonUtility empty optional object retains daylight");
        var original=TrainingWeather.ParticlePosition(8,250,false,1.8f,60);
        check(original==TrainingWeather.ParticlePosition(8,250,false,1.8f,60),"same source time freezes rain");
        check(original!=TrainingWeather.ParticlePosition(8,250.1f,false,1.8f,60),"advanced source time moves rain");
        check(TrainingWeather.ParticlePosition(8,250,true,1.8f,60)!=original,"snow has distinct fall behavior");
        check(Mathf.Abs(TrainingWeather.At(plan,3500).daylight-.125f)<.001f,"daylight follows source time");
        plan.version=2;check(Rejected(plan),"version2 cannot reinterpret legacy rain");plan.version=1;
        plan.frames[1].t=float.NaN;check(Rejected(plan),"invalid environment timing rejected");
        var fog=Fog();TrainingWeather.Validate(fog,3600);
        check(Mathf.Abs(TrainingWeather.At(fog,300).fogExtinctionPerMetre-.0006f)<.000001f,"fog interpolates in source seconds");
        check(TrainingWeather.At(fog,700).fogExtinctionPerMetre==TrainingWeather.At(fog,1500).fogExtinctionPerMetre,"dense interval remains steady");
        float paused=TrainingWeather.At(fog,1850).fogExtinctionPerMetre;
        check(paused==TrainingWeather.At(fog,1850).fogExtinctionPerMetre,"paused source time freezes fog");
        check(TrainingWeather.At(fog,0).fogExtinctionPerMetre==0&&TrainingWeather.At(fog,1850).fogExtinctionPerMetre==paused,"restart is deterministic");
        check(TrainingWeather.At(fog,2400).fogExtinctionPerMetre==0,"view recovers before final restriction release");
        check(TrainingWeather.At(plan,0).fogExtinctionPerMetre==0&&new EnvironmentFrame().fogExtinctionPerMetre==0,"legacy fog defaults clear");
        check(TrainingWeather.At(fog,float.NaN).fogExtinctionPerMetre==0,"nonfinite source time defaults clear");
        foreach(var version in new[]{0,1,3}){var bad=Fog();bad.version=version;check(Rejected(bad),"invalid fog version "+version);}
        foreach(var value in new[]{-.001f,.0101f,float.NaN,float.PositiveInfinity,float.NegativeInfinity}){
            var bad=Fog();bad.frames[1].fogExtinctionPerMetre=value;check(Rejected(bad),"invalid fog coefficient "+value);
        }
        var wrong=Fog();wrong.frames[1].precipitation=.1f;check(Rejected(wrong),"fog cannot introduce rain particles");
        wrong=Fog();wrong.frames[1].daylight=float.PositiveInfinity;check(Rejected(wrong),"nonfinite daylight rejected");
        wrong=Fog();wrong.frames[1].t=0;check(Rejected(wrong),"duplicate fog times rejected");
        check(Rejected(Fog(),float.PositiveInfinity),"nonfinite duration rejected");
        check(Mathf.Abs(TrainingWeather.FogTransmission(1000,.001f)-Mathf.Exp(-1))<.00001f,"attenuation uses metres");
        check(TrainingWeather.FogTransmission(1000,.001f)<TrainingWeather.FogTransmission(100,.001f),"farther surfaces lose more contrast");
        VerifyRestorationAndRendering(check);
        Debug.Log("WEATHER_CLIENT_CHECKS_PASS: "+n);
    }
    static Color Pixel(Camera camera,RenderTexture target,float x=.5f,float y=.5f){
        camera.Render();var previous=RenderTexture.active;RenderTexture.active=target;
        var sample=new Texture2D(1,1,TextureFormat.RGB24,false);
        sample.ReadPixels(new Rect((int)(target.width*x),(int)(target.height*y),1,1),0,0);sample.Apply();
        var color=sample.GetPixel(0,0);UnityEngine.Object.DestroyImmediate(sample);RenderTexture.active=previous;return color;
    }
    static void VerifyRestorationAndRendering(Action<bool,string> check){
        var go=new GameObject("Fog verification camera");var camera=go.AddComponent<Camera>();camera.enabled=false;
        camera.cullingMask=1<<30;camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.2f,.3f,.4f);
        camera.nearClipPlane=.1f;camera.farClipPlane=4000;camera.fieldOfView=60;camera.allowHDR=false;camera.allowMSAA=false;
        var weather=go.AddComponent<TrainingWeather>();var sunObject=new GameObject("Fog verification sun");var sun=sunObject.AddComponent<Light>();sun.type=LightType.Directional;sun.intensity=.8f;
        var sky=camera.backgroundColor;var ambient=RenderSettings.ambientLight;var ambientMode=RenderSettings.ambientMode;
        bool globalFog=RenderSettings.fog;var fogMode=RenderSettings.fogMode;var fogColor=RenderSettings.fogColor;
        float fogDensity=RenderSettings.fogDensity,fogStart=RenderSettings.fogStartDistance,fogEnd=RenderSettings.fogEndDistance;
        var depthMode=camera.depthTextureMode;RenderTexture target=null;GameObject block=null,farBlock=null;Material mat=null;
        try{
            weather.Bind(null,camera,sun);weather.ApplyAt(Fog(),1000);
            check(camera.backgroundColor!=sky,"fog changes sky consistently");
            check(RenderSettings.ambientLight==ambient&&RenderSettings.ambientMode==ambientMode&&sun.intensity==.8f,"fog leaves shared lighting untouched");
            check(RenderSettings.fog==globalFog&&RenderSettings.fogMode==fogMode&&RenderSettings.fogColor==fogColor&&RenderSettings.fogDensity==fogDensity&&RenderSettings.fogStartDistance==fogStart&&RenderSettings.fogEndDistance==fogEnd,"global fog preserved");
            if(SystemInfo.graphicsDeviceType!=GraphicsDeviceType.Null){
                target=new RenderTexture(64,64,24);target.Create();camera.targetTexture=target;
                block=GameObject.CreatePrimitive(PrimitiveType.Cube);block.layer=30;block.transform.position=new Vector3(0,0,100);block.transform.localScale=new Vector3(100,100,2);
                mat=new Material(Shader.Find("Unlit/Color")){color=Color.red};block.GetComponent<Renderer>().sharedMaterial=mat;
                weather.ApplyAt(null,0);var clear=Pixel(camera,target);
                weather.ApplyAt(Fog(),1000);var near=Pixel(camera,target);
                block.transform.position=new Vector3(0,0,1000);block.transform.localScale=new Vector3(1000,1000,2);var far=Pixel(camera,target);
                Debug.Log($"WEATHER_RENDER_PIXELS: clear={clear}, near={near}, far={far}");
                check(clear.r>.9f&&clear.b<.05f,"unlit geometry is rendered by test camera");
                check(near.b>clear.b+.02f&&far.b>near.b+.1f,"actual pixels show distance fog on opaque unlit geometry");
                camera.fieldOfView=35;var zoom=Pixel(camera,target);check(Mathf.Abs(zoom.b-far.b)<.025f,"camera zoom preserves metre attenuation at same surface");
                camera.transform.position=new Vector3(0,0,900);var moved=Pixel(camera,target);check(moved.b<far.b-.1f,"camera movement recomputes surface distance");
                camera.transform.position=Vector3.zero;camera.fieldOfView=60;
                block.transform.position=new Vector3(0,30,100);block.transform.localScale=new Vector3(90,40,2);
                farBlock=GameObject.CreatePrimitive(PrimitiveType.Cube);farBlock.layer=30;farBlock.GetComponent<Renderer>().sharedMaterial=mat;
                farBlock.transform.position=new Vector3(0,-300,1000);farBlock.transform.localScale=new Vector3(900,400,2);
                foreach(var size in new[]{new Vector2Int(128,64),new Vector2Int(64,128)}){
                    target.Release();target.width=size.x;target.height=size.y;target.Create();
                    var top=Pixel(camera,target,.5f,.75f);var bottom=Pixel(camera,target,.5f,.25f);
                    check(top.b<bottom.b-.1f,"asymmetric depth orientation "+size.x+"x"+size.y);
                }
                farBlock.SetActive(false);block.transform.position=new Vector3(0,0,100);block.transform.localScale=new Vector3(100,100,2);
                weather.ApplyAt(null,0);check(camera.GetCommandBuffers(CameraEvent.BeforeImageEffects).Length==0,"clear removes camera fog commands");
                check(Pixel(camera,target).b<.05f,"clear restores original unlit appearance");
            }else Debug.Log("WEATHER_RENDER_CHECKS_SKIPPED: null graphics device; native render acceptance required");
            weather.ApplyAt(null,0);check(camera.backgroundColor==sky&&camera.depthTextureMode==depthMode,"clear restores sky and camera mode");
            weather.ApplyAt(Fog(),1000);weather.Bind(null,camera,sun);check(camera.backgroundColor==sky,"rebind restores original sky before capturing baseline");
            var dusk=new TrainingEnvironment{version=1,kind="dusk",frames=new[]{new EnvironmentFrame{t=0,daylight=.1f},new EnvironmentFrame{t=3600,daylight=.1f}}};
            weather.ApplyAt(dusk,0);check(sun.intensity!=.8f,"legacy dusk still adjusts sun");
            weather.ApplyAt(Fog(),1000);check(sun.intensity==.8f&&RenderSettings.ambientLight==ambient&&RenderSettings.ambientMode==ambientMode,"dusk to fog restores shared lighting");
            UnityEngine.Object.DestroyImmediate(weather);check(camera.backgroundColor==sky&&camera.GetCommandBuffers(CameraEvent.BeforeImageEffects).Length==0,"destroy restores sky and releases camera commands");
        }finally{
            camera.targetTexture=null;if(weather!=null)UnityEngine.Object.DestroyImmediate(weather);
            if(farBlock!=null)UnityEngine.Object.DestroyImmediate(farBlock);if(block!=null)UnityEngine.Object.DestroyImmediate(block);if(mat!=null)UnityEngine.Object.DestroyImmediate(mat);
            if(target!=null){target.Release();UnityEngine.Object.DestroyImmediate(target);}
            UnityEngine.Object.DestroyImmediate(go);UnityEngine.Object.DestroyImmediate(sunObject);
        }
    }
}
