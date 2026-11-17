// PROCEDURAL: synchronized synthetic RGB/depth export for bounded P01 review.
using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
namespace SurfaceSafety {
    [Serializable] public sealed class P01VisibleBox {
        public string actorId="service-vehicle",className="fuel-transfer vehicle";
        public int classId=0,xMin,yMin,width,height,visiblePixels;
    }
    [Serializable] public sealed class P01CaptureMetadata {
        public string version="p01-rgb-depth-v1",scenarioId,pose,capturedUtc,renderGroup;
        public string split,domainVariant;
        public string datasetPurpose="Synthetic P01 detector pilot only; no independent real-world or frozen research acceptance claim.";
        public string boxCoordinates="pixels, bottom-left origin, visible mask extent; omitted when no pixels survive depth test";
        public P01VisibleBox[] visibleBoxes;
        public float sourceTime,nearClip,farClip;
        public int width,height,unityFrame;
        public bool trackingAvailable,lookingAway;
        public Vector3 cameraPositionMetres;
        public Quaternion cameraRotation;
        public float[] projection;
        public string depthEncoding="float32 little-endian, row-major bottom-left, linear camera-space Z metres; 0 means no surface";
        public string provenance="Synthetic authored apron rendering; depth is geometric, not a physical sensor measurement. Tracking loss is metadata; retained RGB/depth are simulation ground truth.";
    }
    public sealed class P01RgbDepthFrame {
        public byte[] rgbPng,depthFloat32,maskPng;
        public P01CaptureMetadata metadata;
        public void Export(string directory,string stem){
            if(string.IsNullOrWhiteSpace(stem)||Path.GetFileName(stem)!=stem)throw new ArgumentException("A filename stem is required.",nameof(stem));
            Directory.CreateDirectory(directory);
            File.WriteAllBytes(Path.Combine(directory,stem+".png"),rgbPng);
            File.WriteAllBytes(Path.Combine(directory,stem+".depth.f32"),depthFloat32);
            File.WriteAllBytes(Path.Combine(directory,stem+".mask.png"),maskPng);
            File.WriteAllText(Path.Combine(directory,stem+".json"),JsonUtility.ToJson(metadata,true));
        }
    }
    public static class P01SynchronizedCapture {
        public static P01RgbDepthFrame Capture(StandReplay replay,Camera viewpoint,int width=672){
            if(replay==null||viewpoint==null)throw new ArgumentNullException("Capture needs a replay and viewpoint.");
            if(!P01StandScenery.Applies(replay.Data))throw new InvalidOperationException("P01 capture requires stand_clearance.");
            if(!replay.WorldScale)throw new InvalidOperationException("P01 metric capture requires world-scale presentation.");
            replay.ApplyScene();replay.GetComponent<TrainingView>()?.SynchronizeGroundVehicles();
            viewpoint.GetComponent<P01CameraRig>()?.Tick();
            if(width<64||width>2048)throw new ArgumentOutOfRangeException(nameof(width));
            if(!SystemInfo.SupportsRenderTextureFormat(RenderTextureFormat.RFloat)||!SystemInfo.SupportsTextureFormat(TextureFormat.RFloat))throw new NotSupportedException("Float depth capture is unavailable on this renderer.");
            var shader=Resources.Load<Shader>("P01LinearDepth");if(shader==null||!shader.isSupported)throw new InvalidOperationException("P01 linear-depth shader is unavailable.");
            var maskShader=Resources.Load<Shader>("P01ObjectMask");if(maskShader==null||!maskShader.isSupported)throw new InvalidOperationException("P01 mask shader is unavailable.");
            int height=Mathf.Clamp(Mathf.RoundToInt(width/Mathf.Max(.01f,viewpoint.aspect)),64,2048);
            var host=new GameObject("P01 synchronized capture camera");var camera=host.AddComponent<Camera>();camera.enabled=false;
            var rgb=new RenderTexture(width,height,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB);
            var depth=new RenderTexture(width,height,24,RenderTextureFormat.RFloat,RenderTextureReadWrite.Linear);
            var image=new Texture2D(width,height,TextureFormat.RGB24,false);
            var depthImage=new Texture2D(width,height,TextureFormat.RFloat,false,true);
            var mask=new RenderTexture(width,height,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.Linear);
            var maskImage=new Texture2D(width,height,TextureFormat.RGB24,false,true);
            var maskRenderers=new List<Renderer>();var priorBlocks=new List<MaterialPropertyBlock>();
            var previous=RenderTexture.active;var hidden=new List<Renderer>();
            float sourceTime=replay.Clock.Time;
            try {
                // Preserve normal apron/terminal occlusion and the full camera
                // frustum. Only selection/trajectory hints are excluded. No
                // target-based cropping or semantic visibility toggles occur.
                foreach(var renderer in replay.Content.GetComponentsInChildren<Renderer>(true))if(renderer.enabled&&VisualEvidenceCapture.IsExcluded(renderer.transform)){hidden.Add(renderer);renderer.enabled=false;}
                camera.CopyFrom(viewpoint);camera.enabled=false;camera.transform.SetPositionAndRotation(viewpoint.transform.position,viewpoint.transform.rotation);
                camera.rect=new Rect(0,0,1,1);camera.aspect=viewpoint.aspect;camera.projectionMatrix=viewpoint.projectionMatrix;
                camera.targetTexture=rgb;camera.Render();RenderTexture.active=rgb;
                image.ReadPixels(new Rect(0,0,width,height),0,0);image.Apply();
                // Both passes execute synchronously in one Unity frame, with no
                // clock advance, transform update, or physics step between them.
                camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=Color.clear;
                camera.targetTexture=depth;camera.RenderWithShader(shader,"");RenderTexture.active=depth;
                depthImage.ReadPixels(new Rect(0,0,width,height),0,0);depthImage.Apply();
                var actor=replay.Content.Find("service-vehicle");
                if(actor!=null)foreach(var renderer in actor.GetComponentsInChildren<Renderer>()){
                    var old=new MaterialPropertyBlock();renderer.GetPropertyBlock(old);priorBlocks.Add(old);maskRenderers.Add(renderer);
                    var block=new MaterialPropertyBlock();renderer.GetPropertyBlock(block);block.SetFloat("_P01ObjectId",1);renderer.SetPropertyBlock(block);
                }
                camera.targetTexture=mask;camera.RenderWithShader(maskShader,"");RenderTexture.active=mask;
                maskImage.ReadPixels(new Rect(0,0,width,height),0,0);maskImage.Apply();
                int x0=width,y0=height,x1=-1,y1=-1,count=0;var pixels=maskImage.GetPixels32();
                for(int i=0;i<pixels.Length;i++)if(pixels[i].r>127){int x=i%width,y=i/width;x0=Mathf.Min(x0,x);x1=Mathf.Max(x1,x);y0=Mathf.Min(y0,y);y1=Mathf.Max(y1,y);count++;}
                var boxes=count==0?new P01VisibleBox[0]:new[]{new P01VisibleBox{xMin=x0,yMin=y0,width=x1-x0+1,height=y1-y0+1,visiblePixels=count}};
                var rig=viewpoint.GetComponent<P01CameraRig>();var projection=new float[16];for(int i=0;i<16;i++)projection[i]=viewpoint.projectionMatrix[i];
                var values=depthImage.GetRawTextureData<float>();var floats=new float[values.Length];values.CopyTo(floats);
                var bytes=new byte[floats.Length*4];Buffer.BlockCopy(floats,0,bytes,0,bytes.Length);
                // Explicit little-endian encoding makes exports portable.
                if(!BitConverter.IsLittleEndian)for(int i=0;i<bytes.Length;i+=4)Array.Reverse(bytes,i,4);
                if(replay.Clock.Time!=sourceTime)throw new InvalidOperationException("Source clock changed during capture.");
                return new P01RgbDepthFrame {rgbPng=image.EncodeToPNG(),depthFloat32=bytes,maskPng=maskImage.EncodeToPNG(),metadata=new P01CaptureMetadata {
                    scenarioId=replay.Data.scenarioId,renderGroup=replay.Data.scenarioId+"/"+sourceTime.ToString("F3",System.Globalization.CultureInfo.InvariantCulture),visibleBoxes=boxes,sourceTime=sourceTime,width=width,height=height,unityFrame=Time.frameCount,
                    capturedUtc=DateTime.UtcNow.ToString("O"),nearClip=camera.nearClipPlane,farClip=camera.farClipPlane,
                    pose=rig!=null&&rig.OverrideCamera?rig.Pose.ToString():"viewer",
                    trackingAvailable=rig!=null&&rig.OverrideCamera?rig.TrackingAvailable:replay.Clock.Tracked,
                    lookingAway=rig!=null&&rig.OverrideCamera&&rig.Pose==P01CameraPose.LookAway,
                    cameraPositionMetres=viewpoint.transform.position,cameraRotation=viewpoint.transform.rotation,projection=projection}};
            }finally{
                for(int i=0;i<maskRenderers.Count;i++)if(maskRenderers[i]!=null)maskRenderers[i].SetPropertyBlock(priorBlocks[i]);
                foreach(var renderer in hidden)if(renderer!=null)renderer.enabled=true;
                RenderTexture.active=previous;camera.targetTexture=null;rgb.Release();depth.Release();mask.Release();
                Remove(image);Remove(depthImage);Remove(maskImage);Remove(rgb);Remove(depth);Remove(mask);Remove(host);
            }
        }
        static void Remove(UnityEngine.Object value){if(Application.isPlaying)UnityEngine.Object.Destroy(value);else UnityEngine.Object.DestroyImmediate(value);}
    }
}
