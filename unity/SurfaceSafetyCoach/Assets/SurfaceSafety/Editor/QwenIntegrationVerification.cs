using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using SurfaceSafety;

public static class QwenIntegrationVerification {
    static StandReplay replay;
    static QwenReasoningClient client;
    static int stage;
    static int accepted;
    static double started;
    static string Output => Path.GetFullPath(Path.Combine(Application.dataPath,"../../../outputs/milestone1"));
    public static void Run() {
        try {
            File.Delete(Path.Combine(Output,"qwen-integration-verification.json"));
            MilestoneBuild.Verify();CoordinatorUiVerification.Run();ClaimClientVerification.Run();
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
            var host=new GameObject("Real Qwen integration verification");var boot=host.AddComponent<SceneBootstrap>();boot.previewMode=true;boot.Initialize();
            replay=boot.Replay;client=host.GetComponent<QwenReasoningClient>();stage=0;accepted=0;started=EditorApplication.timeSinceStartup;
            client.RequestCompleted+=Completed;
            EditorApplication.update+=Watch;
            Next();
        }catch(Exception ex){Debug.LogException(ex);EditorApplication.Exit(1);}
    }
    static void Watch(){if(EditorApplication.timeSinceStartup-started>360){Debug.LogError("Qwen integration timed out");EditorApplication.Exit(1);}}
    static void Next(){
        replay.SelectAircraft(1);replay.Seek(stage==0?13:14);replay.SelectTab("why");
        Directory.CreateDirectory(Output);
        File.WriteAllBytes(Path.Combine(Output,$"qwen-scene-{(stage==0?13:14)}.png"),QwenReasoningClient.CaptureSyntheticScene(replay));
        client.Request();
        if(!client.Busy)throw new Exception("Qwen request did not start: "+client.LastError);
    }
    static void Completed(){
        try {
            var result=client.LastResponse;
            if(result==null||(result.resultStatus!="generated"&&result.resultStatus!="withheld"))throw new Exception("Qwen transport/contract failed: "+client.LastError);
            int checkpoint=stage==0?13:14;
            File.WriteAllText(Path.Combine(Output,$"qwen-response-{checkpoint}.json"),JsonUtility.ToJson(result,true));
            if(stage==0&&Array.Exists(result.evidenceIds,x=>x=="E03"))throw new Exception("Future report leaked");
            if(result.resultStatus=="generated")accepted++;
            else if(result.evidenceIds.Length!=0||result.claims.Length!=0)throw new Exception("Withheld answer must display no claims");
            if(stage==1&&result.resultStatus=="generated"&&!Array.Exists(result.evidenceIds,x=>x=="E03"))throw new Exception("Late report was not cited after receipt");
            if(stage==1&&result.resultStatus=="generated"&&(!result.answer.ToLowerInvariant().Contains("baggage")||!result.answer.Contains("12")||!result.answer.Contains("14")))
                throw new Exception("Latest report explanation omits baggage/event/receipt details");
            if(!result.insufficientEvidence||string.IsNullOrEmpty(result.contextLimit))throw new Exception("Interface must preserve the scenario's unknown readiness");
            CaptureScreen($"coordinator-qwen-{checkpoint}.png");
            if(stage++==0){Next();return;}
            // A response for second 14 must never be accepted at second 13.
            var originalRequest=client.BuildRequest();originalRequest.requestId=result.requestId;replay.Seek(13);
            if(client.ApplyResponse(originalRequest,result))throw new Exception("Stale response accepted after rewind");
            File.WriteAllText(Path.Combine(Output,"qwen-integration-verification.json"),
                "{\"status\":\"transport_and_guard_checks_passed\",\"transport\":\"UnityWebRequest to local real Qwen model\",\"checkpoints\":[13,14],\"accepted_answers\":"+accepted+",\"withheld_answers\":"+(2-accepted)+",\"stale_response_rejected\":true,\"scope\":\"Connection and fail-closed behavior only; withheld answers are not successful model reasoning\"}");
            Debug.Log("QWEN_UNITY_INTEGRATION_PASS");EditorApplication.update-=Watch;EditorApplication.Exit(0);
        }catch(Exception ex){Debug.LogException(ex);EditorApplication.Exit(1);}
    }
    public static void CaptureScreen(string name,int width=1080,int height=1920) {
        var cam=Camera.main;var oldTarget=cam.targetTexture;float oldAspect=cam.aspect;
        var rt=new RenderTexture(width,height,24);cam.targetTexture=rt;cam.aspect=(float)width/height;
        SceneBootstrap.FramePreview(cam);
        var canvases=UnityEngine.Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None);
        foreach(var canvas in canvases){canvas.renderMode=RenderMode.ScreenSpaceCamera;canvas.worldCamera=cam;canvas.planeDistance=.1f;}
        Canvas.ForceUpdateCanvases();cam.Render();var oldActive=RenderTexture.active;RenderTexture.active=rt;
        var image=new Texture2D(width,height,TextureFormat.RGB24,false);image.ReadPixels(new Rect(0,0,width,height),0,0);image.Apply();
        File.WriteAllBytes(Path.Combine(Output,name),image.EncodeToPNG());
        cam.targetTexture=oldTarget;cam.aspect=oldAspect;RenderTexture.active=oldActive;
        foreach(var canvas in canvases)canvas.renderMode=RenderMode.ScreenSpaceOverlay;
        UnityEngine.Object.DestroyImmediate(rt);UnityEngine.Object.DestroyImmediate(image);
    }
}
