using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

namespace SurfaceSafety {
    // Drag the simulated scene to look around; UI taps never rotate the view.
    public class SimulatorLook : MonoBehaviour {
        bool dragging;
        Vector2 last;
        float yaw, pitch;
        readonly List<RaycastResult> hits = new List<RaycastResult>();
        void Start() { yaw = transform.eulerAngles.y; pitch = transform.eulerAngles.x; }
        bool OverUI(Vector2 position) {
            if (EventSystem.current == null) return false;
            hits.Clear();
            EventSystem.current.RaycastAll(new PointerEventData(EventSystem.current) { position = position }, hits);
            return hits.Count > 0;
        }
        void Update() {
            Vector2 position;
            bool began, ended, held;
            if (Input.touchCount > 0) {
                var touch = Input.GetTouch(0); position = touch.position;
                began = touch.phase == TouchPhase.Began;
                ended = touch.phase == TouchPhase.Ended || touch.phase == TouchPhase.Canceled;
                held = !ended;
            } else {
                position = Input.mousePosition;
                began = Input.GetMouseButtonDown(0); ended = Input.GetMouseButtonUp(0); held = Input.GetMouseButton(0);
            }
            if (began) { dragging = !OverUI(position); last = position; }
            if (ended || !held) { dragging = false; return; }
            if (!dragging) return;
            var delta = position - last; last = position;
            var sensitivity = 120f / Mathf.Max(1, Screen.width);
            yaw += delta.x * sensitivity;
            pitch = Mathf.Clamp(pitch - delta.y * sensitivity, -45, 60);
            transform.rotation = Quaternion.Euler(pitch, yaw, 0);
        }
    }
}
