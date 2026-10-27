using System;
using UnityEditor.SceneManagement;
using UnityEngine;
using SurfaceSafety;

public static class ClaimClientVerification {
    public static void Run() {
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
        var host=new GameObject("Claim support regression");var boot=host.AddComponent<SceneBootstrap>();boot.previewMode=true;boot.Initialize();
        var replay=boot.Replay;var client=host.GetComponent<QwenReasoningClient>();replay.Seek(14);
        var request=client.BuildRequest();
        var response=new ReasoningResponse {requestId=request.requestId,scenarioId=request.scenarioId,aircraftId="A2",flightInstance="F2-R1",checkpoint=14,
            resultStatus="generated",answerOrigin="validated_fact_templates",answer="Baggage service: complete [E03]",evidenceIds=new[]{"E03"},
            claims=new[]{new SupportedClaim {fact_id="E03:baggage_status",value="complete",status="current",evidence_ids=new[]{"E03"}}}};
        Action<bool,string> check=(condition,message)=>{if(!condition)throw new Exception("Claim client check failed: "+message);};
        check(client.ApplyResponse(request,response),"supported atomic claim");
        response.claims[0].fact_id="E02:stand";response.claims[0].value="B";
        check(!client.ApplyResponse(request,response),"stand claim cannot borrow baggage citation");
        response.claims[0].fact_id="E03:baggage_status";response.claims[0].value="ready for departure";
        check(!client.ApplyResponse(request,response),"unsupported value blocked");
        response.claims[0].value="complete";response.answerOrigin="free_model_prose";
        check(!client.ApplyResponse(request,response),"legacy free prose contract blocked");
        response.answerOrigin="validated_fact_templates";replay.Seek(13);
        check(!client.ApplyResponse(request,response),"late answer blocked after rewind");
        Debug.Log("CLAIM_CLIENT_CHECKS_PASS: 5");
    }
}
