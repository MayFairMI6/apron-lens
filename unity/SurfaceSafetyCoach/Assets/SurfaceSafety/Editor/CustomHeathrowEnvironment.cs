using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

// Custom training apron around the free FlightGear Terminal 5A asset.
// See WorldAR/Heathrow/ATTRIBUTION.txt for source, license and conversion details.
public static class CustomHeathrowEnvironment {
    const string Folder = "Assets/SurfaceSafety/WorldAR/Heathrow";
    static Material concrete, asphalt, yellow, white, metal, rubber, glass, orange;

    static Material Material(string name, Color color, float smooth = .15f) {
        var path = Folder + "/" + name + ".mat";
        var m = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (m == null) { m = new Material(Shader.Find("Standard")); AssetDatabase.CreateAsset(m, path); }
        m.color = color; m.SetFloat("_Glossiness", smooth); EditorUtility.SetDirty(m); return m;
    }

    static Material Surface(string name, bool slabs) {
        var path = Folder + "/" + name + ".png";
        if (!File.Exists(path)) {
            const int size = 512;
            var texture = new Texture2D(size, size, TextureFormat.RGB24, false);
            var pixels = new Color[size * size]; var random = new System.Random(slabs ? 71 : 92);
            for (int y = 0; y < size; y++) for (int x = 0; x < size; x++) {
                float grain = (float)random.NextDouble() * .065f;
                float wear = Mathf.PerlinNoise(x * .017f, y * .017f) * .065f;
                float value = (slabs ? .48f : .16f) + grain + wear;
                if (slabs && (x < 2 || y < 2)) value *= .48f;
                pixels[y * size + x] = new Color(value * 1.02f, value, value * .96f);
            }
            texture.SetPixels(pixels); texture.Apply(); File.WriteAllBytes(path, texture.EncodeToPNG());
            Object.DestroyImmediate(texture); AssetDatabase.ImportAsset(path);
            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            importer.wrapMode = TextureWrapMode.Repeat; importer.anisoLevel = 8; importer.SaveAndReimport();
        }
        var material = Material(name, Color.white, .08f);
        material.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>(path); return material;
    }

    static GameObject Box(Transform parent, string name, Vector3 position, Vector3 size, Material material) {
        var o = GameObject.CreatePrimitive(PrimitiveType.Cube); o.name = name; o.transform.SetParent(parent, false);
        o.transform.localPosition = position; o.transform.localScale = size;
        o.GetComponent<Renderer>().sharedMaterial = material; o.isStatic = true; return o;
    }
    static void Mark(Transform p, string name, float x, float z, float width, float length, Material material) {
        var o = Box(p, name, new Vector3(x, .035f, z), new Vector3(width, .012f, length), material);
        o.GetComponent<Renderer>().shadowCastingMode = ShadowCastingMode.Off;
        Object.DestroyImmediate(o.GetComponent<Collider>());
    }
    static void Ground(Transform p, string name, Vector3 position, Vector2 size, Material source, float repeat) {
        var material = Material(name, Color.white, .08f); material.mainTexture = source.mainTexture;
        material.mainTextureScale = size / repeat;
        var o = GameObject.CreatePrimitive(PrimitiveType.Plane); o.name = name; o.transform.SetParent(p, false);
        o.transform.localPosition = position; o.transform.localScale = new Vector3(size.x / 10, 1, size.y / 10);
        o.GetComponent<Renderer>().sharedMaterial = material; o.isStatic = true;
    }
    static void Cylinder(Transform p, string name, Vector3 position, Vector3 size, Material material, Quaternion rotation) {
        var o = GameObject.CreatePrimitive(PrimitiveType.Cylinder); o.name = name; o.transform.SetParent(p, false);
        o.transform.localPosition = position; o.transform.localScale = size; o.transform.localRotation = rotation;
        o.GetComponent<Renderer>().sharedMaterial = material; o.isStatic = true;
    }
    static void Wheels(Transform p, float halfWidth, float front, float rear, float radius) {
        foreach (float x in new[] {-halfWidth, halfWidth}) foreach (float z in new[] {front, rear})
            Cylinder(p, "Rubber tire", new Vector3(x, radius, z), new Vector3(radius * 2, .15f, radius * 2), rubber, Quaternion.Euler(0,0,90));
    }
    static void Tug(Transform root, Vector3 position) {
        var p = new GameObject("Electric ground tug").transform; p.SetParent(root, false); p.localPosition = position;
        Box(p,"Chassis",new Vector3(0,.65f,0),new Vector3(2.1f,.65f,4),white);
        Box(p,"Cab",new Vector3(0,1.35f,-.6f),new Vector3(1.8f,1.3f,1.7f),white);
        Box(p,"Front windscreen",new Vector3(0,1.58f,-1.46f),new Vector3(1.55f,.65f,.03f),glass);
        Box(p,"Tow hook",new Vector3(0,.4f,2.3f),new Vector3(.16f,.16f,1),metal);
        Wheels(p,1.05f,-1.2f,1.2f,.37f);
        foreach(float x in new[]{-.75f,.75f}) Box(p,"Headlamp",new Vector3(x,.83f,-2.02f),new Vector3(.26f,.18f,.04f),yellow);
        Cylinder(p,"Amber beacon",new Vector3(0,2.1f,-.5f),new Vector3(.17f,.1f,.17f),orange,Quaternion.identity);
    }
    static void Cart(Transform root, Vector3 position) {
        var p = new GameObject("Baggage container dolly").transform; p.SetParent(root,false); p.localPosition=position;
        Box(p,"Dolly frame",new Vector3(0,.45f,0),new Vector3(1.8f,.2f,2.8f),metal);
        Box(p,"Container",new Vector3(0,1.23f,0),new Vector3(1.65f,1.35f,2.4f),white);
        Box(p,"Door",new Vector3(0,1.23f,-1.21f),new Vector3(1.4f,1.13f,.025f),metal);
        Wheels(p,.9f,-.85f,.85f,.25f);
    }
    static void Bridge(Transform root, float x) {
        var p = new GameObject("Passenger boarding bridge").transform; p.SetParent(root,false);
        p.localPosition = new Vector3(x - 13, 0, 75);
        Box(p,"Enclosed walkway",new Vector3(0,4.4f,8),new Vector3(3.1f,2.8f,24),white);
        Box(p,"Window band",new Vector3(-1.56f,4.7f,8),new Vector3(.03f,1.1f,22),glass);
        Box(p,"Window band",new Vector3(1.56f,4.7f,8),new Vector3(.03f,1.1f,22),glass);
        for (float z=-2;z<19;z+=1.8f) foreach(float side in new[]{-1.59f,1.59f})
            Box(p,"Window mullion",new Vector3(side,4.7f,z),new Vector3(.05f,1.2f,.055f),metal);
        Cylinder(p,"Support column",new Vector3(0,1.8f,0),new Vector3(.6f,1.8f,.6f),metal,Quaternion.identity);
        Box(p,"Flexible cab",new Vector3(0,4,-5),new Vector3(3.5f,3,2),rubber);
        Box(p,"Cab face",new Vector3(0,4,-6.05f),new Vector3(2.7f,2.3f,.12f),glass);
    }
    public static void Decorate(GameObject root) {
        foreach (var child in root.transform.Cast<Transform>().ToArray())
            if (child.name != "Sky dome" && child.name != "Sun") Object.DestroyImmediate(child.gameObject);
        concrete=Surface("Weathered concrete",true); asphalt=Surface("Fine asphalt",false);
        yellow=Material("Worn safety yellow",new Color(.82f,.61f,.13f)); white=Material("Off white paint",new Color(.79f,.80f,.78f));
        metal=Material("Galvanised steel",new Color(.36f,.4f,.43f),.4f); rubber=Material("Rubber",new Color(.035f,.04f,.045f));
        glass=Material("Blue grey glass",new Color(.12f,.22f,.28f),.72f); orange=Material("Beacon amber",new Color(1,.38f,.03f));
        Ground(root.transform,"Apron concrete",new Vector3(0,0,20),new Vector2(700,650),concrete,6);
        Ground(root.transform,"Taxi lane",new Vector3(0,.012f,-25),new Vector2(700,32),asphalt,8);
        Ground(root.transform,"Service road",new Vector3(0,.014f,67),new Vector2(650,8),asphalt,8);
        Mark(root.transform,"Taxi centreline",0,-25,700,.22f,yellow);
        foreach(float z in new[]{-41f,-9f,63f,71f}) Mark(root.transform,"Lane boundary",0,z,650,.14f,white);
        for(float x=-300;x<300;x+=7) Mark(root.transform,"Service road dash",x,67,3,.12f,white);
        foreach(var stand in new[]{("A",-45f),("B",35f),("C",115f)}) {
            float x=stand.Item2;
            Mark(root.transform,"Stand lead in",x,15,.23f,78,yellow);
            Mark(root.transform,"Stop line",x,49,8,.27f,yellow);
            foreach(float side in new[]{-23f,23f}) Mark(root.transform,"Equipment clearance",x+side,32,.15f,50,white);
            for(int i=0;i<8;i++) Mark(root.transform,"Equipment bay hatch",x+27+i*.6f,52,.2f,8,yellow);
            var label = new GameObject("Training stand "+stand.Item1,typeof(TextMesh));label.transform.SetParent(root.transform,false);
            label.transform.localPosition=new Vector3(x+4,.055f,20);label.transform.localRotation=Quaternion.Euler(90,0,0);
            var text=label.GetComponent<TextMesh>();text.text=stand.Item1;text.fontSize=64;text.characterSize=2;text.anchor=TextAnchor.MiddleCenter;text.color=yellow.color;
            text.font=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");label.GetComponent<MeshRenderer>().sharedMaterial=text.font.material;
            Bridge(root.transform,x);Tug(root.transform,new Vector3(x+24,0,45));
            for(int i=0;i<3;i++)Cart(root.transform,new Vector3(x+31,0,35+i*4));
        }
        var model=AssetDatabase.LoadAssetAtPath<GameObject>(Folder+"/HeathrowT5.obj");
        if(model==null)throw new System.Exception("Heathrow T5 source asset is missing.");
        var terminal=(GameObject)PrefabUtility.InstantiatePrefab(model);terminal.name="Heathrow Terminal 5A";terminal.transform.SetParent(root.transform,false);
        terminal.transform.localPosition=new Vector3(0,.65f,182);
        var facade=Material("Terminal photographic facade",new Color(.88f,.88f,.88f),.25f);
        facade.mainTexture=AssetDatabase.LoadAssetAtPath<Texture2D>(Folder+"/EGLL-T5.png");
        foreach(var r in terminal.GetComponentsInChildren<Renderer>())r.sharedMaterials=r.sharedMaterials.Select(_=>facade).ToArray();
        foreach(float x in new[]{-140f,-75f,5f,85f,160f}) {
            Cylinder(root.transform,"Apron light mast",new Vector3(x,12,61),new Vector3(.28f,12,.28f),metal,Quaternion.identity);
            Box(root.transform,"Floodlight crossbar",new Vector3(x,24,61),new Vector3(3,.18f,.22f),metal);
            foreach(float dx in new[]{-1f,0f,1f})Box(root.transform,"Floodlight",new Vector3(x+dx,24,60.8f),new Vector3(.7f,.55f,.2f),white);
        }
        var sun=root.transform.Find("Sun").GetComponent<Light>();sun.intensity=1.05f;sun.color=new Color(1,.96f,.88f);
        sun.shadows=LightShadows.Soft;sun.shadowStrength=.6f;sun.transform.rotation=Quaternion.Euler(32,-35,0);
        RenderSettings.ambientLight=new Color(.60f,.65f,.71f);
        QualitySettings.shadowDistance=250; QualitySettings.shadows=ShadowQuality.All; QualitySettings.shadowResolution=ShadowResolution.High;
        AssetDatabase.SaveAssets();
    }
}
