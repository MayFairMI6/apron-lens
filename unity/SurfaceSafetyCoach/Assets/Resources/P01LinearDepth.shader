// PROCEDURAL: geometric camera-space depth, linear metres in the R float channel.
Shader "Hidden/AirfieldLens/P01LinearDepth" {
    SubShader { Tags { "RenderType"="Opaque" } Pass {
        ZWrite On ZTest LEqual Cull Back
        CGPROGRAM
        #pragma vertex vert
        #pragma fragment frag
        #include "UnityCG.cginc"
        struct input { float4 vertex : POSITION; };
        struct output { float4 vertex : SV_POSITION; float depth : TEXCOORD0; };
        output vert(input v) { output o; o.vertex=UnityObjectToClipPos(v.vertex);o.depth=-UnityObjectToViewPos(v.vertex).z;return o; }
        float4 frag(output i) : SV_Target { return float4(i.depth,0,0,1); }
        ENDCG
    } }
    Fallback Off
}
