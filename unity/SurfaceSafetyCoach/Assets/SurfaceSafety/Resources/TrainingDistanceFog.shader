// Authored visual attenuation only. No measured visibility/RVR or minima.
// A separate opaque distance pass includes unlit materials without ShadowCaster.
Shader "Hidden/SurfaceSafety/TrainingDistanceFog" {
    Properties { _MainTex ("Scene", 2D) = "white" {} }
    SubShader {
        Pass {
            Name "OpaqueDistance"
            ZWrite On ZTest LEqual Cull Back
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            struct v2f { float4 position:SV_POSITION; float3 viewPosition:TEXCOORD0; };
            v2f vert(appdata_base v) {
                v2f o; o.position=UnityObjectToClipPos(v.vertex);
                o.viewPosition=UnityObjectToViewPos(v.vertex);return o;
            }
            float4 frag(v2f i):SV_Target {return float4(length(i.viewPosition),0,0,1);}
            ENDCG
        }
        Pass {
            Name "DistanceFogComposite"
            ZWrite Off ZTest Always Cull Off
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            sampler2D _MainTex,_FogDistance;
            float4 _MainTex_TexelSize,_FogColor;
            float _ExtinctionPerMetre;
            struct v2f {float4 position:SV_POSITION;float2 uv:TEXCOORD0;float2 depthUV:TEXCOORD1;};
            v2f vert(appdata_img v){
                v2f o;o.position=UnityObjectToClipPos(v.vertex);o.uv=v.texcoord;o.depthUV=v.texcoord;
                #if UNITY_UV_STARTS_AT_TOP
                if(_MainTex_TexelSize.y<0)o.depthUV.y=1-o.depthUV.y;
                #endif
                return o;
            }
            fixed4 frag(v2f i):SV_Target {
                fixed4 scene=tex2D(_MainTex,i.uv);
                float distanceMetres=max(0,tex2D(_FogDistance,i.depthUV).r);
                float transmission=exp(-distanceMetres*_ExtinctionPerMetre);
                return fixed4(lerp(_FogColor.rgb,scene.rgb,transmission),scene.a);
            }
            ENDCG
        }
    }
    Fallback Off
}
