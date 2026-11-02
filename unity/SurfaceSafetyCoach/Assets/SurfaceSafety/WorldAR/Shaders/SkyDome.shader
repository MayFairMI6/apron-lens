// Gradient sky for the simulated apron. XR Simulation renders the environment as the AR camera feed with its own
// camera, which doesn't draw a skybox, so the environment carries its sky as an inward-facing dome.
Shader "SurfaceSafety/SkyDome" {
    Properties {
        _Top ("Zenith", Color) = (0.33, 0.48, 0.70, 1)
        _Horizon ("Horizon", Color) = (0.78, 0.86, 0.94, 1)
    }
    SubShader {
        Tags { "Queue" = "Background" "RenderType" = "Background" }
        Cull Front ZWrite Off
        Pass {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            fixed4 _Top, _Horizon;
            struct appdata { float4 vertex : POSITION; };
            struct v2f { float4 pos : SV_POSITION; float3 dir : TEXCOORD0; };
            v2f vert (appdata v) { v2f o; o.pos = UnityObjectToClipPos(v.vertex); o.dir = normalize(v.vertex.xyz); return o; }
            fixed4 frag (v2f i) : SV_Target { return lerp(_Horizon, _Top, saturate(i.dir.y * 2.5)); }
            ENDCG
        }
    }
}
