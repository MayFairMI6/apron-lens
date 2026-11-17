// PROCEDURAL: depth-tested instance mask; full scene geometry writes depth.
Shader "Hidden/AirfieldLens/P01ObjectMask" {
    Properties { _P01ObjectId ("Instance",Float)=0 }
    SubShader { Tags { "RenderType"="Opaque" } Pass {
        ZWrite On ZTest LEqual Cull Back
        CGPROGRAM
        #pragma vertex vert
        #pragma fragment frag
        #include "UnityCG.cginc"
        float _P01ObjectId;
        struct input { float4 vertex : POSITION; };
        struct output { float4 vertex : SV_POSITION; };
        output vert(input v){output o;o.vertex=UnityObjectToClipPos(v.vertex);return o;}
        float4 frag(output i):SV_Target{return float4(_P01ObjectId,0,0,1);}
        ENDCG
    } }
    Fallback Off
}
