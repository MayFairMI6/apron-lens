using System;
using System.IO;
using System.Linq;
using UnityEngine;
using SurfaceSafety;

public static class IncidentVisualVerification {
    public static void Run(StandReplay replay,Scenario scenario,TrainingIncidentEffects effects){
        Action<bool,string> check=(ok,label)=>{if(!ok)throw new Exception("Incident check: "+label);};
        var wildlife=scenario.incidents.First(i=>i.kind=="wildlife");float at=wildlife.start+12;
        effects.RenderAt(at);
        var birds=effects.GetComponentsInChildren<Transform>().Where(t=>t.name.StartsWith("Bird ")).ToArray();
        check(birds.Length==9&&birds.All(t=>t.Find("Body")!=null&&t.Find("Head")!=null&&t.Find("Bill")!=null),"nine birds have bodies, heads and bills");
        check(birds.All(t=>t.GetComponentsInChildren<MeshFilter>().Count(m=>m.name.StartsWith("Primary feather"))==16),"individual primary feathers replace triangle silhouettes");
        var positions=birds.Select(t=>t.localPosition).ToArray();var wings=birds.Select(t=>t.Find("Left wing").localRotation).ToArray();
        effects.RenderAt(at+.4f);
        check(birds.Where((b,i)=>Vector3.Distance(b.localPosition,positions[i])>.00001f).Count()==9,"flock travels continuously with source time");
        check(birds.Where((b,i)=>Quaternion.Angle(b.Find("Left wing").localRotation,wings[i])>1).Any(),"wing poses animate");
        effects.RenderAt(at);
        check(birds.Where((b,i)=>b.localPosition!=positions[i]||Quaternion.Angle(b.Find("Left wing").localRotation,wings[i])>.01f).Count()==0,"rewind restores identical bird poses");
        var directory=Environment.GetEnvironmentVariable("APRONLENS_INCIDENT_PREVIEW");
        if(!string.IsNullOrEmpty(directory)){
            Directory.CreateDirectory(directory);replay.UpdateTrafficTime(at,"");
            foreach(var bird in birds.Skip(1))bird.gameObject.SetActive(false);
            Capture(Path.Combine(directory,"apronlens-bird-detail.png"),birds[0].position,new Vector3(1.5f,.75f,1.8f),45);
            foreach(var bird in birds.Skip(1))bird.gameObject.SetActive(true);
            Capture(Path.Combine(directory,"apronlens-bird-flock.png"),birds[4].position,new Vector3(9,5,-17),45);
        }
        var incident=scenario.incidents.First(i=>i.kind=="baggage_spill");effects.RenderAt(incident.onset+10);
        var bags=effects.GetComponentsInChildren<Transform>().Where(t=>t.name.StartsWith("Bag ")).ToArray();
        check(bags.Length==9&&bags.All(t=>t.localPosition.y<.25f),"nine spilled bags reach the ground");
        var bagPositions=bags.Select(t=>t.localPosition).ToArray();
        effects.RenderAt(incident.clearedAt);
        check(effects.GetComponentsInChildren<Transform>().Count(t=>t.name.StartsWith("Bag "))==0,"bags disappear only at collection boundary");
        effects.RenderAt(incident.onset+10);
        check(bags.Where((b,i)=>b.localPosition!=bagPositions[i]||!b.gameObject.activeInHierarchy).Count()==0,"rewind restores baggage incident");
        if(!string.IsNullOrEmpty(directory)){
            replay.UpdateTrafficTime(incident.onset+10,"");
            var centre=replay.Content.TransformPoint(new Vector3(incident.x,incident.y,incident.z));
            Capture(Path.Combine(directory,"apronlens-baggage-incident.png"),centre,new Vector3(10,9,-14),45);
        }
        effects.RenderAt(incident.end);
        check(effects.GetComponentsInChildren<Renderer>().Length==0,"incident hidden at its external end boundary");
        Debug.Log("INCIDENT_VISUAL_CHECKS_PASS: 9");
    }
    static void Capture(string path,Vector3 centre,Vector3 offset,float fov){
        var go=new GameObject("Incident preview camera");var camera=go.AddComponent<Camera>();
        camera.transform.position=centre+offset;camera.transform.LookAt(centre);camera.fieldOfView=fov;
        camera.nearClipPlane=.02f;camera.farClipPlane=10000;camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.57f,.68f,.77f);
        var render=new RenderTexture(1600,1000,24);camera.targetTexture=render;camera.Render();
        var old=RenderTexture.active;RenderTexture.active=render;
        var texture=new Texture2D(1600,1000,TextureFormat.RGB24,false);texture.ReadPixels(new Rect(0,0,1600,1000),0,0);texture.Apply();
        File.WriteAllBytes(path,texture.EncodeToPNG());RenderTexture.active=old;camera.targetTexture=null;
        UnityEngine.Object.DestroyImmediate(texture);UnityEngine.Object.DestroyImmediate(render);UnityEngine.Object.DestroyImmediate(go);
    }
}
