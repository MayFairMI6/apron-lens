using System;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

// One click to the simulated AR demo (see docs/USER_MANUAL.md): ApronLens -> Play simulated AR demo opens
// Scenes/WorldAR.unity, sets the Game view to 1080 x 1920 portrait and enters Play mode. Creating the file
// work/start-ar-demo.flag makes the editor do this once on its next script reload (the flag is then deleted).
[InitializeOnLoad]
public static class DemoLauncher {
    const string ScenePath = "Assets/SurfaceSafety/Scenes/WorldAR.unity";
    static string FlagPath => Path.GetFullPath(Path.Combine(Application.dataPath, "../../../work/start-ar-demo.flag"));

    static DemoLauncher() {
        EditorApplication.delayCall += () => {
            if (!File.Exists(FlagPath) || EditorApplication.isPlayingOrWillChangePlaymode) return;
            File.Delete(FlagPath);
            Play();
        };
    }

    [MenuItem("ApronLens/Play simulated AR demo")]
    public static void Play() {
        if (EditorApplication.isPlaying || !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
        EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        try { UsePortraitGameView(1080, 1920); }
        catch (Exception e) { Debug.LogWarning("Set the Game view to 1080 x 1920 by hand: " + e.Message); }
        EditorApplication.EnterPlaymode();
        Debug.Log("AR_DEMO_STARTED");
    }

    // The Game view's size list is internal to the editor; select (adding if needed) a fixed portrait size.
    static void UsePortraitGameView(int width, int height) {
        var editor = typeof(Editor).Assembly;
        var sizesType = editor.GetType("UnityEditor.GameViewSizes");
        var sizes = typeof(ScriptableSingleton<>).MakeGenericType(sizesType).GetProperty("instance").GetValue(null);
        var groupType = sizesType.GetProperty("currentGroupType").GetValue(sizes);
        var group = sizesType.GetMethod("GetGroup").Invoke(sizes, new[] { groupType });
        var g = group.GetType();
        int count = (int)g.GetMethod("GetTotalCount").Invoke(group, null), index = -1;
        for (int i = 0; i < count && index < 0; i++) {
            var size = g.GetMethod("GetGameViewSize").Invoke(group, new object[] { i });
            var t = size.GetType();
            if ((int)t.GetProperty("width").GetValue(size) == width && (int)t.GetProperty("height").GetValue(size) == height) index = i;
        }
        if (index < 0) {
            var sizeType = editor.GetType("UnityEditor.GameViewSize");
            var kind = editor.GetType("UnityEditor.GameViewSizeType");
            var created = sizeType.GetConstructor(new[] { kind, typeof(int), typeof(int), typeof(string) })
                .Invoke(new object[] { Enum.Parse(kind, "FixedResolution"), width, height, "ApronLens phone" });
            g.GetMethod("AddCustomSize").Invoke(group, new[] { created });
            index = count;
        }
        var gameView = EditorWindow.GetWindow(editor.GetType("UnityEditor.GameView"));
        gameView.GetType().GetProperty("selectedSizeIndex", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
            .SetValue(gameView, index);
    }
}
