using System;
using System.Linq;
using UnityEngine;

namespace SurfaceSafety {
    // Image capture for the planned visual-reference condition.
    //
    // QwenReasoningClient.CaptureSyntheticScene is left unchanged for the frozen
    // /reason path. This capture differs in three ways:
    //  - it leaves out the selection ring and the authored path lines, which
    //    reveal the selected aircraft and its plan;
    //  - it renders from the viewer's AR camera pose and projection, so
    //    viewpoint-relative references ("behind this one") can be tested;
    //  - it never draws the tap. The tap is returned as viewport coordinates
    //    for the request, so the referent is not painted into the pixels.
    //
    // Known limit: StandReplay still colours aircraft by index and builds two
    // aircraft. Families that test similar aircraft need a uniform livery and
    // three or more aircraft before formal visual evaluation.
    public struct VisualEvidence {
        public byte[] png;
        public Vector2 tapViewport; // 0..1, origin bottom-left; NaN when there is no tap
        public int width, height;
        public string version;
    }

    public static class VisualEvidenceCapture {
        public const string Version = "visual-capture-v1";
        const string RingName = "Selected aircraft ring";
        const string PathSuffix = " authored path";
        const int CaptureLayer = 30;

        public static bool IsExcluded(Transform node) {
            for (var t = node; t != null; t = t.parent) {
                if (t.name == RingName || t.name.EndsWith(PathSuffix, StringComparison.Ordinal)) return true;
            }
            return false;
        }

        public static VisualEvidence Capture(StandReplay target, Camera viewpoint, Vector2? tapScreen, int width = 672) {
            if (target == null) throw new ArgumentNullException(nameof(target));
            if (viewpoint == null) throw new ArgumentNullException(nameof(viewpoint));
            int height = Mathf.Clamp(Mathf.RoundToInt(width / Mathf.Max(viewpoint.aspect, 0.01f)), 64, 2048);
            var nodes = target.Content.GetComponentsInChildren<Transform>(true);
            var layers = nodes.Select(n => n.gameObject.layer).ToArray();
            var host = new GameObject("Visual evidence camera");
            var cam = host.AddComponent<Camera>();
            var rt = new RenderTexture(width, height, 24);
            var image = new Texture2D(width, height, TextureFormat.RGB24, false);
            var previous = RenderTexture.active;
            try {
                foreach (var n in nodes) if (!IsExcluded(n)) n.gameObject.layer = CaptureLayer;
                cam.cullingMask = 1 << CaptureLayer;
                cam.clearFlags = CameraClearFlags.SolidColor;
                cam.backgroundColor = new Color(.055f, .09f, .12f);
                cam.transform.SetPositionAndRotation(viewpoint.transform.position, viewpoint.transform.rotation);
                cam.nearClipPlane = viewpoint.nearClipPlane;
                cam.farClipPlane = viewpoint.farClipPlane;
                cam.fieldOfView = viewpoint.fieldOfView;
                cam.aspect = viewpoint.aspect;
                cam.projectionMatrix = viewpoint.projectionMatrix;
                cam.targetTexture = rt;
                cam.Render();
                RenderTexture.active = rt;
                image.ReadPixels(new Rect(0, 0, width, height), 0, 0);
                image.Apply();
                Vector2 tap = new Vector2(float.NaN, float.NaN);
                if (tapScreen.HasValue) tap = (Vector2)viewpoint.ScreenToViewportPoint(tapScreen.Value);
                return new VisualEvidence { png = image.EncodeToPNG(), tapViewport = tap, width = width, height = height, version = Version };
            } finally {
                for (int i = 0; i < nodes.Length; i++) nodes[i].gameObject.layer = layers[i];
                RenderTexture.active = previous;
                cam.targetTexture = null;
                Remove(image); Remove(rt); Remove(host);
            }
        }

        // Development check: the image must not change with the selected aircraft.
        // Side effects: selecting aircraft clears the current AI result and writes
        // selection events to the session log, as a normal selection would.
        public static bool SelectionInvariant(StandReplay target, Camera viewpoint) {
            int original = target.SelectedAircraftIndex;
            try {
                target.SelectAircraft(0);
                var first = Capture(target, viewpoint, null).png;
                target.SelectAircraft(1);
                var second = Capture(target, viewpoint, null).png;
                return first.SequenceEqual(second);
            } finally {
                target.SelectAircraft(original);
            }
        }

        static void Remove(UnityEngine.Object item) {
            if (Application.isPlaying) UnityEngine.Object.Destroy(item);
            else UnityEngine.Object.DestroyImmediate(item);
        }
    }
}
