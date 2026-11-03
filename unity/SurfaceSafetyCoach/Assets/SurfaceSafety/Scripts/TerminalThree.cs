using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;

namespace SurfaceSafety {
    // Source meshes retain their texture coordinates and baked geographic placement.
    // Current mapped remainder footprints and the entrance canopy supplement that
    // asset. Facade divisions, structural spacing and forecourt finishes are authored.
    public sealed class TerminalThree:MonoBehaviour {
        [Serializable] public sealed class SourceMesh {
            public string name;
            public Vector3[] vertices;
            public Vector2[] uv;
            public int[] triangles;
            public Color color=Color.white;
            public bool textured;
        }
        [Serializable] public sealed class Remainder {
            public string name;
            public TaxiPoint[] points,roofPoints;
            public MapRing[] holes;
            public int[] roofTriangles;
            public float height=.010f;
        }
        [Serializable] public sealed class Model {
            public SourceMesh[] meshes;
            public Remainder[] remainders;
            public TaxiPoint[] canopyPoints;
            public Vector3[] canopyRectangle;
            public float canopyHeight=.011f;
        }

        readonly List<Mesh> ownedMeshes=new List<Mesh>();
        readonly List<Material> ownedMaterials=new List<Material>();
        readonly Dictionary<string,Material> sourceMaterials=new Dictionary<string,Material>();
        Model model;
        Font signFont;Material signTextMaterial;

        public static GameObject Build(Transform parent){
            var asset=Resources.Load<TextAsset>("HeathrowT3/model");
            if(asset==null)throw new InvalidOperationException("Terminal 3 requires Resources/HeathrowT3/model.json.");
            var data=JsonUtility.FromJson<Model>(asset.text);
            Validate(data);
            var texture=Resources.Load<Texture2D>("HeathrowT3/EGLL-t3");
            if(data.meshes.Any(m=>m.textured)&&texture==null)
                throw new InvalidOperationException("Terminal 3 source texture Resources/HeathrowT3/EGLL-t3 is missing.");
            var root=new GameObject("Terminal 3 geographic hybrid");root.transform.SetParent(parent,false);
            var renderer=root.AddComponent<TerminalThree>();renderer.model=data;
            try {renderer.BuildSource(texture);renderer.BuildRemainders();renderer.BuildCanopy();renderer.BuildEntranceSign();}
            catch {Release(root);throw;}
            return root;
        }

        static bool Finite(float v)=>!float.IsNaN(v)&&!float.IsInfinity(v);
        static void Validate(Model data){
            if(data==null||data.meshes==null||data.meshes.Length==0||data.remainders==null||data.remainders.Length==0)
                throw new ArgumentException("Terminal 3 model requires source meshes and mapped remainders.");
            foreach(var mesh in data.meshes){
                ValidateMesh(mesh.vertices,mesh.triangles,"source mesh");
                if(mesh.textured&&(mesh.uv==null||mesh.uv.Length!=mesh.vertices.Length||mesh.uv.Any(v=>!Finite(v.x)||!Finite(v.y))))
                    throw new ArgumentException("Terminal 3 textured mesh requires matching finite UV coordinates.");
            }
            foreach(var part in data.remainders){
                ValidateRing(part.points);
                if(!Finite(part.height)||part.height<=0||part.height>.1f)throw new ArgumentException("Invalid Terminal 3 authored height.");
                if(part.roofPoints==null)throw new ArgumentException("Terminal 3 remainder requires a triangulated roof.");
                ValidateMesh(part.roofPoints.Select(p=>new Vector3(p.x,part.height,p.z)).ToArray(),part.roofTriangles,"remainder roof");
                foreach(var hole in part.holes??new MapRing[0])ValidateRing(hole.points);
            }
            ValidateRing(data.canopyPoints);
            if(data.canopyRectangle==null||data.canopyRectangle.Length!=4||data.canopyRectangle.Any(v=>!Finite(v.x)||!Finite(v.z)))
                throw new ArgumentException("Terminal 3 canopy requires four geographic rectangle corners.");
            if(data.canopyHeight==0)data.canopyHeight=.011f;
            if(!Finite(data.canopyHeight)||data.canopyHeight<.005f||data.canopyHeight>.025f)
                throw new ArgumentException("Invalid Terminal 3 canopy height.");
        }
        static void ValidateMesh(Vector3[] vertices,int[] triangles,string label){
            if(vertices==null||vertices.Length<3||triangles==null||triangles.Length<3||triangles.Length%3!=0||
               vertices.Any(v=>!Finite(v.x)||!Finite(v.y)||!Finite(v.z))||triangles.Any(i=>i<0||i>=vertices.Length))
                throw new ArgumentException("Invalid Terminal 3 "+label+" geometry.");
        }
        static void ValidateRing(TaxiPoint[] points){
            if(points==null||points.Length<3||points.Any(p=>p==null||!Finite(p.x)||!Finite(p.z)))
                throw new ArgumentException("Invalid Terminal 3 mapped outline.");
        }
        Material Material(string name,Color color,float smoothness=.25f,float metallic=0,bool transparent=false){
            var shader=Shader.Find("Standard");if(shader==null)throw new InvalidOperationException("Terminal 3 requires the Standard shader.");
            var material=new Material(shader){name="Terminal 3 "+name,color=color};
            material.SetFloat("_Glossiness",smoothness);material.SetFloat("_Metallic",metallic);
            if(transparent){
                material.SetFloat("_Mode",3);material.SetOverrideTag("RenderType","Transparent");
                material.SetInt("_SrcBlend",(int)BlendMode.SrcAlpha);material.SetInt("_DstBlend",(int)BlendMode.OneMinusSrcAlpha);
                material.SetInt("_ZWrite",0);material.DisableKeyword("_ALPHATEST_ON");material.EnableKeyword("_ALPHABLEND_ON");
                material.DisableKeyword("_ALPHAPREMULTIPLY_ON");material.renderQueue=(int)RenderQueue.Transparent;
            }
            ownedMaterials.Add(material);return material;
        }
        void MeshObject(string name,Vector3[] vertices,int[] triangles,Material material,Vector2[] uv=null){
            var mesh=new Mesh{name="Terminal 3 "+name};
            if(vertices.Length>65535)mesh.indexFormat=IndexFormat.UInt32;
            mesh.vertices=vertices;mesh.triangles=triangles;if(uv!=null&&uv.Length==vertices.Length)mesh.uv=uv;
            mesh.RecalculateNormals();mesh.RecalculateBounds();ownedMeshes.Add(mesh);
            var obj=new GameObject(name,typeof(MeshFilter),typeof(MeshRenderer));obj.transform.SetParent(transform,false);
            obj.GetComponent<MeshFilter>().sharedMesh=mesh;obj.GetComponent<MeshRenderer>().sharedMaterial=material;
        }
        void MeshObject(string name,Geometry geometry,Material material){
            if(geometry.vertices.Count>0)MeshObject(name,geometry.vertices.ToArray(),geometry.triangles.ToArray(),material);
        }
        void BuildSource(Texture2D texture){
            foreach(var source in model.meshes){
                string key=source.color.ToString("F5")+"/"+source.textured;
                if(!sourceMaterials.TryGetValue(key,out var material)){
                    material=Material("source "+sourceMaterials.Count,source.color,.3f);
                    if(source.textured)material.mainTexture=texture;
                    sourceMaterials.Add(key,material);
                }
                MeshObject("Source "+source.name,source.vertices,source.triangles,material,source.uv);
            }
        }
        void BuildRemainders(){
            var roof=Material("mapped hall roofs",new Color(.57f,.62f,.64f),.32f,.1f);
            var cladding=Material("light hall cladding",new Color(.70f,.73f,.73f),.27f,.12f);
            var glass=Material("facade glazing",new Color(.15f,.26f,.30f),.68f,.35f);
            var frame=Material("facade frames",new Color(.76f,.79f,.78f),.45f,.4f);
            for(int i=0;i<model.remainders.Length;i++){
                var part=model.remainders[i];string name=string.IsNullOrEmpty(part.name)?"Mapped hall "+(i+1):part.name;
                MeshObject(name+" roof",part.roofPoints.Select(p=>new Vector3(p.x,part.height,p.z)).ToArray(),part.roofTriangles,roof);
                var walls=new Geometry();var glazing=new Geometry();var frames=new Geometry();
                Facade(part.points,part.height,false,walls,glazing,frames);
                foreach(var hole in part.holes??new MapRing[0])Facade(hole.points,part.height,true,walls,glazing,frames);
                MeshObject(name+" walls",walls,cladding);MeshObject(name+" glazing",glazing,glass);MeshObject(name+" frames",frames,frame);
            }
        }
        static Vector3 Point(TaxiPoint point,float y=0)=>new Vector3(point.x,y,point.z);
        static Vector3[] Ring(TaxiPoint[] points){
            var result=new List<Vector3>();
            foreach(var point in points){var p=Point(point);if(result.Count==0||(p-result[result.Count-1]).sqrMagnitude>1e-14f)result.Add(p);}
            if(result.Count>1&&(result[0]-result[result.Count-1]).sqrMagnitude<1e-14f)result.RemoveAt(result.Count-1);
            return result.ToArray();
        }
        static float Area(Vector3[] ring){float area=0;for(int i=0;i<ring.Length;i++){var a=ring[i];var b=ring[(i+1)%ring.Length];area+=a.x*b.z-b.x*a.z;}return area/2;}
        static void Facade(TaxiPoint[] points,float height,bool courtyard,Geometry walls,Geometry glass,Geometry frames){
            var ring=Ring(points);float sign=(Area(ring)>=0?1:-1)*(courtyard?-1:1);
            for(int i=0;i<ring.Length;i++){
                var a=ring[i];var b=ring[(i+1)%ring.Length];var direction=b-a;float length=direction.magnitude;if(length<.0001f)continue;
                var normal=new Vector3(direction.z,0,-direction.x).normalized*sign;
                WallBand(walls,a,b,0,height,normal,0);
                // Bands follow each actual perimeter, including courtyard walls;
                // neither glazing nor roof strips bridge across mapped voids.
                WallBand(glass,a,b,height*.17f,height*.43f,normal,.00004f);
                WallBand(glass,a,b,height*.51f,height*.76f,normal,.00004f);
                WallBand(frames,a,b,height*.44f,height*.46f,normal,.00007f);
                WallBand(frames,a,b,height*.77f,height*.80f,normal,.00007f);
                WallBand(frames,a,b,height-.00035f,height+.00015f,normal,.00008f);
                int divisions=Mathf.Max(1,Mathf.CeilToInt(length/.0038f));var along=direction/length;
                for(int n=0;n<=divisions;n++){
                    float distance=Mathf.Clamp(length*n/divisions,.00007f,Mathf.Max(.00007f,length-.00007f));
                    var centre=a+along*distance;
                    WallBand(frames,centre-along*.000065f,centre+along*.000065f,height*.14f,height*.80f,normal,.00009f);
                }
            }
        }
        static void WallBand(Geometry geometry,Vector3 a,Vector3 b,float bottom,float top,Vector3 normal,float offset){
            a+=normal*offset;b+=normal*offset;
            geometry.Quad(a+Vector3.up*bottom,b+Vector3.up*bottom,b+Vector3.up*top,a+Vector3.up*top,normal);
        }

        void BuildEntranceSign(){
            // Authored placard on the mapped NE entrance-wing wall (OSM outer
            // edge 274), clear of the canopy. This is not a surveyed sign location.
            var expectedA=new Vector3(.2518446864f,0,.0609793820f);
            var expectedB=new Vector3(.2761778744f,0,.0243739616f);
            Vector3 a=Vector3.zero,b=Vector3.zero,normal=Vector3.zero;float wallHeight=0;
            foreach(var part in model.remainders){
                var ring=Ring(part.points);
                for(int i=0;i<ring.Length;i++){
                    var p=ring[i];var q=ring[(i+1)%ring.Length];
                    if(!((p-expectedA).sqrMagnitude<1e-10f&&(q-expectedB).sqrMagnitude<1e-10f)&&
                       !((p-expectedB).sqrMagnitude<1e-10f&&(q-expectedA).sqrMagnitude<1e-10f))continue;
                    a=p;b=q;wallHeight=part.height;
                    normal=new Vector3(b.z-a.z,0,a.x-b.x).normalized*(Area(ring)>=0?1:-1);
                }
            }
            if(normal.sqrMagnitude<.9f||wallHeight<.0095f)throw new ArgumentException("Terminal 3 sign requires its mapped entrance-wing wall.");
            const float width=.020f,height=.0016f;var centre=(a+b)*.5f+Vector3.up*.0087f;
            var along=(b-a).normalized;var border=new Geometry();
            // A twelve-centimetre-deep panel is backed by the wall itself. The
            // inset face and lettering remain parallel to it, never billboarded.
            border.Beam(centre-along*width*.5f+normal*.00006f,centre+along*width*.5f+normal*.00006f,.00012f,height);
            MeshObject("Terminal 3 attached sign border",border,Material("sign recess",new Color(.12f,.15f,.16f),.2f,.1f));
            var right=Vector3.Cross(Vector3.up,-normal).normalized;var face=new Geometry();var faceCentre=centre+normal*.000125f;
            face.Quad(faceCentre-right*(width*.5f-.0001f)-Vector3.up*(height*.5f-.00008f),
                faceCentre+right*(width*.5f-.0001f)-Vector3.up*(height*.5f-.00008f),
                faceCentre+right*(width*.5f-.0001f)+Vector3.up*(height*.5f-.00008f),
                faceCentre-right*(width*.5f-.0001f)+Vector3.up*(height*.5f-.00008f),normal);
            MeshObject("Terminal 3 flush sign face",face,Material("sign face",new Color(.76f,.78f,.74f),.17f));
            var letters=new GameObject("Terminal 3 facade lettering",typeof(TextMesh));letters.transform.SetParent(transform,false);
            letters.transform.localPosition=centre+normal*.00013f;
            // TextMesh reads from local -Z; positive scale keeps the lettering
            // unmirrored while that front faces the exterior wall normal.
            letters.transform.localRotation=Quaternion.LookRotation(-normal,Vector3.up);
            var text=letters.GetComponent<TextMesh>();signFont=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            text.font=signFont;text.fontSize=96;text.fontStyle=FontStyle.Bold;text.characterSize=.001f;
            text.anchor=TextAnchor.MiddleCenter;text.alignment=TextAlignment.Center;text.color=new Color(.045f,.065f,.07f);text.text="TERMINAL 3";
            signFont.RequestCharactersInTexture(text.text,text.fontSize,text.fontStyle);
            // The retained sprite shader uses the font atlas with normal scene
            // depth testing, so letters cannot show through the terminal's roof.
            signTextMaterial=new Material(signFont.material){name="Terminal 3 engraved lettering",shader=Shader.Find("Sprites/Default")};
            signTextMaterial.mainTexture=signFont.material.mainTexture;ownedMaterials.Add(signTextMaterial);
            var textRenderer=letters.GetComponent<MeshRenderer>();textRenderer.sharedMaterial=signTextMaterial;
            var bounds=textRenderer.localBounds;
            if(bounds.size.x<=0||bounds.size.y<=0)throw new InvalidOperationException("Terminal 3 sign font did not generate readable glyph bounds.");
            float textScale=Mathf.Min(.018f/bounds.size.x,.0013f/bounds.size.y);
            letters.transform.localScale=Vector3.one*textScale;
            letters.transform.localPosition=centre+normal*.00013f-letters.transform.localRotation*(bounds.center*textScale);
            Font.textureRebuilt+=RefreshSignAtlas;
        }
        void RefreshSignAtlas(Font changed){if(changed==signFont&&signTextMaterial!=null)signTextMaterial.mainTexture=signFont.material.mainTexture;}

        void BuildCanopy(){
            var outline=Ring(model.canopyPoints);var points=outline.Select(p=>new TaxiPoint{x=p.x,z=p.z}).ToArray();
            var triangles=TrainingGeography.Triangulate(points);float height=model.canopyHeight;
            var rectangle=model.canopyRectangle;var centre=rectangle.Aggregate(Vector3.zero,(v,p)=>v+p)/4;centre.y=0;
            var edgeA=rectangle[1]-rectangle[0];var edgeB=rectangle[3]-rectangle[0];edgeA.y=edgeB.y=0;
            var longitudinal=(edgeA.sqrMagnitude>=edgeB.sqrMagnitude?edgeA:edgeB).normalized;
            var transverse=(edgeA.sqrMagnitude>=edgeB.sqrMagnitude?edgeB:edgeA).normalized;
            if(longitudinal.sqrMagnitude<.9f||transverse.sqrMagnitude<.9f||Mathf.Abs(Vector3.Dot(longitudinal,transverse))>.01f)
                throw new ArgumentException("Terminal 3 canopy rectangle is degenerate or not rectangular.");
            var paving=Material("bounded entrance paving",new Color(.48f,.50f,.48f),.18f);
            var pavingJoints=Material("paving joints",new Color(.40f,.43f,.42f),.15f);
            var steel=Material("canopy steel",new Color(.37f,.43f,.44f),.43f,.45f);
            var etfe=Material("translucent ETFE approximation",new Color(.80f,.89f,.90f,.62f),.56f,.05f,true);
            var ground=new Geometry();ground.Surface(outline.Select(p=>p+Vector3.up*.00012f).ToArray(),triangles,false);
            float sign=Area(outline)>=0?1:-1;
            for(int i=0;i<outline.Length;i++){
                var a=outline[i]+Vector3.up*.00012f;var b=outline[(i+1)%outline.Length]+Vector3.up*.00012f;
                var outward=new Vector3(b.z-a.z,0,a.x-b.x).normalized*sign*.002f;
                ground.Quad(a,b,b+outward,a+outward,Vector3.up);
            }
            MeshObject("Entrance forecourt within canopy and two metre border",ground,paving);
            var membrane=new Geometry();membrane.Surface(outline.Select(p=>p+Vector3.up*height).ToArray(),triangles,true);
            MeshObject("Mapped ETFE canopy with visible underside",membrane,etfe);
            var structure=new Geometry();var joints=new Geometry();
            float min=outline.Min(p=>Vector3.Dot(p-centre,longitudinal)),max=outline.Max(p=>Vector3.Dot(p-centre,longitudinal));
            int ribs=Mathf.Max(1,Mathf.CeilToInt((max-min)/.0038f));
            for(int i=0;i<=ribs;i++){
                float station=Mathf.Lerp(min+.00012f,max-.00012f,(float)i/ribs);
                foreach(var span in Spans(outline,centre,longitudinal,transverse,station)){
                    structure.Beam(span[0]+Vector3.up*(height-.00022f),span[1]+Vector3.up*(height-.00022f),.00014f,.00038f);
                    joints.Beam(span[0]+Vector3.up*.00014f,span[1]+Vector3.up*.00014f,.000045f,.000015f);
                }
            }
            // Two longitudinal girders and slender edge supports keep the entrance
            // open. Their exact stations are illustrative, not surveyed positions.
            float acrossMin=outline.Min(p=>Vector3.Dot(p-centre,transverse)),acrossMax=outline.Max(p=>Vector3.Dot(p-centre,transverse));
            foreach(float cross in new[]{acrossMin+.0012f,acrossMax-.0012f}){
                foreach(var span in Spans(outline,centre,transverse,longitudinal,cross)){
                    structure.Beam(span[0]+Vector3.up*(height-.00062f),span[1]+Vector3.up*(height-.00062f),.00032f,.00065f);
                    float length=(span[1]-span[0]).magnitude;int bays=Mathf.Max(1,Mathf.CeilToInt(length/.011f));
                    for(int i=0;i<=bays;i++){
                        var at=Vector3.Lerp(span[0],span[1],Mathf.Lerp(.012f,.988f,(float)i/bays));
                        if(!InsideBuilding(at))structure.Column(at+Vector3.up*.00015f,height-.0008f,.00034f,12);
                    }
                }
            }
            for(int i=0;i<outline.Length;i++)structure.Beam(outline[i]+Vector3.up*(height-.0002f),outline[(i+1)%outline.Length]+Vector3.up*(height-.0002f),.00018f,.0004f);
            MeshObject("Canopy parallel ribs girders and slender supports",structure,steel);MeshObject("Forecourt paving joints",joints,pavingJoints);
        }
        bool InsideBuilding(Vector3 point)=>model.remainders.Any(p=>Inside(point,p.points)&&!(p.holes??new MapRing[0]).Any(h=>Inside(point,h.points)));
        static bool Inside(Vector3 p,TaxiPoint[] points){
            bool inside=false;
            for(int i=0,j=points.Length-1;i<points.Length;j=i++){
                var a=points[i];var b=points[j];
                if((a.z>p.z)!=(b.z>p.z)&&p.x<(b.x-a.x)*(p.z-a.z)/(b.z-a.z)+a.x)inside=!inside;
            }return inside;
        }
        static IEnumerable<Vector3[]> Spans(Vector3[] outline,Vector3 centre,Vector3 axis,Vector3 across,float station){
            var cuts=new List<float>();
            for(int i=0;i<outline.Length;i++){
                var a=outline[i]-centre;var b=outline[(i+1)%outline.Length]-centre;
                float ta=Vector3.Dot(a,axis),tb=Vector3.Dot(b,axis);
                if((ta>station)==(tb>station))continue;
                cuts.Add(Mathf.Lerp(Vector3.Dot(a,across),Vector3.Dot(b,across),(station-ta)/(tb-ta)));
            }
            cuts.Sort();for(int i=0;i+1<cuts.Count;i+=2)if(cuts[i+1]-cuts[i]>.0001f)
                yield return new[]{centre+axis*station+across*cuts[i],centre+axis*station+across*cuts[i+1]};
        }
        sealed class Geometry {
            public readonly List<Vector3> vertices=new List<Vector3>();
            public readonly List<int> triangles=new List<int>();
            public void Quad(Vector3 a,Vector3 b,Vector3 c,Vector3 d,Vector3 outward){
                int k=vertices.Count;vertices.AddRange(new[]{a,b,c,d});
                triangles.AddRange(Vector3.Dot(Vector3.Cross(b-a,c-a),outward)>=0?new[]{k,k+1,k+2,k,k+2,k+3}:new[]{k,k+2,k+1,k,k+3,k+2});
            }
            public void Surface(Vector3[] points,int[] indices,bool underside){
                int k=vertices.Count;vertices.AddRange(points);triangles.AddRange(indices.Select(i=>i+k));
                if(!underside)return;k=vertices.Count;vertices.AddRange(points);
                for(int i=0;i<indices.Length;i+=3)triangles.AddRange(new[]{k+indices[i],k+indices[i+2],k+indices[i+1]});
            }
            public void Beam(Vector3 a,Vector3 b,float width,float depth){
                var along=b-a;if(along.sqrMagnitude<1e-12f)return;
                var right=Vector3.Cross(Vector3.up,along).normalized*width*.5f;var up=Vector3.up*depth*.5f;
                Quad(a-right-up,b-right-up,b+right-up,a+right-up,Vector3.down);
                Quad(a-right+up,a+right+up,b+right+up,b-right+up,Vector3.up);
                Quad(a-right-up,a-right+up,b-right+up,b-right-up,-right);
                Quad(a+right-up,b+right-up,b+right+up,a+right+up,right);
                Quad(a-right-up,a+right-up,a+right+up,a-right+up,-along);
                Quad(b-right-up,b-right+up,b+right+up,b+right-up,along);
            }
            public void Column(Vector3 bottom,float height,float diameter,int sides){
                for(int i=0;i<sides;i++){
                    float a=i*Mathf.PI*2/sides,b=(i+1)*Mathf.PI*2/sides;
                    var p=new Vector3(Mathf.Cos(a),0,Mathf.Sin(a))*diameter*.5f;var q=new Vector3(Mathf.Cos(b),0,Mathf.Sin(b))*diameter*.5f;
                    Quad(bottom+p,bottom+q,bottom+q+Vector3.up*height,bottom+p+Vector3.up*height,p+q);
                }
            }
        }
        static void Release(UnityEngine.Object obj){if(Application.isPlaying)Destroy(obj);else DestroyImmediate(obj);}
        void OnDestroy(){Font.textureRebuilt-=RefreshSignAtlas;foreach(var mesh in ownedMeshes)if(mesh!=null)Release(mesh);foreach(var material in ownedMaterials)if(material!=null)Release(material);}
    }
}
