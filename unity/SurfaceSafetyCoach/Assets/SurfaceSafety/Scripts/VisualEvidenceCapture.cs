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
    //    for the request, so the referent is not painted into the pixels;
    //  - it renders only the part of the view that holds the aircraft and stand
    //    markers (SceneCrop), so small props get more pixels. The crop is fitted to
    //    every aircraft, never the referent, so framing does not reveal the selection.
    //
    // Known limit: StandReplay still colours aircraft by index and builds two
    // aircraft. Families that test similar aircraft need a uniform livery and
    // three or more aircraft before formal visual evaluation.
    public struct VisualEvidence {
        public byte[] png;
        public Vector2 tapViewport; // in image coordinates, origin bottom-left; outside 0..1 when the tap falls outside the crop; NaN when there is no tap
        public Rect crop;           // the rendered part of the viewer's viewport
        public int width, height;
        public string version;
    }

    public static class VisualEvidenceCapture {
        public const string Version = "visual-capture-v2";
        const string RingName = "Selected aircraft ring";
        const string PathSuffix = " authored path";
        const int CaptureLayer = 30;

        public static bool IsExcluded(Transform node) {
            for (var t = node; t != null; t = t.parent) {
                if (t.name == RingName || t.name.EndsWith(PathSuffix, StringComparison.Ordinal)) return true;
            }
            return false;
        }

        static bool IsProp(Transform node, Transform content) {
            for (var t = node; t != null && t != content; t = t.parent) if (t.name.StartsWith("Visual prop ", StringComparison.Ordinal)) return true;
            return false;
        }

        // Viewport rectangle around every aircraft and stand marker, widened by a margin
        // (which also covers props beside their aircraft) and kept square in viewport
        // units so the image keeps the viewer's aspect. Props are left out of the fit so
        // the framing does not change when one appears or leaves.
        public static Rect SceneCrop(StandReplay target, Camera viewpoint, float margin = .15f, float minSize = .35f) {
            var parts = target.Data.aircraft.Select(a => target.Content.Find(a.id))
                .Concat(target.Content.Cast<Transform>().Where(t => t.name.StartsWith("Stand ", StringComparison.Ordinal)))
                .Where(t => t != null)
                .SelectMany(t => t.GetComponentsInChildren<Renderer>())
                .Where(r => !IsExcluded(r.transform) && !IsProp(r.transform, target.Content));
            float x0 = 1, y0 = 1, x1 = 0, y1 = 0; bool any = false;
            foreach (var r in parts) {
                var b = r.bounds;
                for (int i = 0; i < 8; i++) {
                    var corner = new Vector3((i & 1) == 0 ? b.min.x : b.max.x, (i & 2) == 0 ? b.min.y : b.max.y, (i & 4) == 0 ? b.min.z : b.max.z);
                    var v = viewpoint.WorldToViewportPoint(corner);
                    if (v.z <= 0) continue;
                    x0 = Mathf.Min(x0, v.x); x1 = Mathf.Max(x1, v.x); y0 = Mathf.Min(y0, v.y); y1 = Mathf.Max(y1, v.y); any = true;
                }
            }
            if (!any) return new Rect(0, 0, 1, 1);
            float size = Mathf.Clamp(Mathf.Max(x1 - x0, y1 - y0) * (1 + 2 * margin), minSize, 1);
            float cx = Mathf.Clamp((x0 + x1) / 2, size / 2, 1 - size / 2), cy = Mathf.Clamp((y0 + y1) / 2, size / 2, 1 - size / 2);
            return new Rect(cx - size / 2, cy - size / 2, size, size);
        }

        public static VisualEvidence Capture(StandReplay target, Camera viewpoint, Vector2? tapScreen, int width = 672) {
            if (target == null) throw new ArgumentNullException(nameof(target));
            if (viewpoint == null) throw new ArgumentNullException(nameof(viewpoint));
            int height = Mathf.Clamp(Mathf.RoundToInt(width / Mathf.Max(viewpoint.aspect, 0.01f)), 64, 2048);
            var crop = SceneCrop(target, viewpoint);
            // Clip-space scale and shift that maps the crop to the full image.
            var toCrop = Matrix4x4.identity;
            toCrop.m00 = 1 / crop.width; toCrop.m03 = -(2 * crop.center.x - 1) / crop.width;
            toCrop.m11 = 1 / crop.height; toCrop.m13 = -(2 * crop.center.y - 1) / crop.height;
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
                cam.projectionMatrix = toCrop * viewpoint.projectionMatrix;
                cam.targetTexture = rt;
                cam.Render();
                RenderTexture.active = rt;
                image.ReadPixels(new Rect(0, 0, width, height), 0, 0);
                image.Apply();
                Vector2 tap = new Vector2(float.NaN, float.NaN);
                if (tapScreen.HasValue) tap = Rect.PointToNormalized(crop, viewpoint.ScreenToViewportPoint(tapScreen.Value));
                return new VisualEvidence { png = image.EncodeToPNG(), tapViewport = tap, crop = crop, width = width, height = height, version = Version };
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
