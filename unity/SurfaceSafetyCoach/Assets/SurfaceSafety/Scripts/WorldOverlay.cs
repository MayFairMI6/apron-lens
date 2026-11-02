using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;

namespace SurfaceSafety {
    // AR-first overlay for world-scale AR (WorldArBootstrap), drawn beneath the coordinator panels:
    // - a label floating above each aircraft: aircraft and current flight, its stand and latest received report,
    //   NEW when a report for it arrived while the user looked away, highlighted when selected; tap to select;
    // - a banner for the "While you were away" notice; tap to open the details on the Now tab.
    public class WorldOverlay : MonoBehaviour {
        static readonly Color Ink = new Color(.055f, .095f, .13f, .86f);
        static readonly Color Teal = new Color(0f, .40f, .42f, .94f);
        static readonly Color Amber = new Color(.86f, .55f, .12f, .96f);
        const float LabelHeightMetres = 14f;  // above the aircraft's origin, clear of the tail

        class Tag { public string id; public RectTransform pill; public Image back; public Text title, detail; public GameObject badge; }

        StandReplay replay;
        Canvas canvas;
        RectTransform root, banner;
        Text bannerText;
        Font font;
        readonly List<Tag> tags = new List<Tag>();

        public int VisibleLabels => tags.Count(t => t.pill.gameObject.activeSelf);
        public bool BannerShown => banner != null && banner.gameObject.activeSelf;

        public void Bind(StandReplay target) {
            replay = target;
            font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var go = new GameObject("AR overlay", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            go.transform.SetParent(transform, false);
            canvas = go.GetComponent<Canvas>(); canvas.renderMode = RenderMode.ScreenSpaceOverlay; canvas.sortingOrder = -10;
            var scaler = go.GetComponent<CanvasScaler>(); scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1080, 1920); scaler.matchWidthOrHeight = .5f;
            root = go.GetComponent<RectTransform>();
            for (int i = 0; i < replay.Data.aircraft.Length; i++) tags.Add(BuildTag(i));
            banner = Box(root, "Away banner", new Vector2(.03f, .772f), new Vector2(.97f, .832f), Amber);
            bannerText = Label(banner, "", 30, TextAnchor.MiddleLeft, Color.white);
            banner.gameObject.AddComponent<Button>().onClick.AddListener(() => { replay.SetDetails(true); replay.SelectTab("now"); });
            banner.gameObject.SetActive(false);
        }

        Tag BuildTag(int index) {
            var tag = new Tag { id = replay.Data.aircraft[index].id };
            tag.pill = Box(root, "Label " + tag.id, Vector2.zero, Vector2.zero, Ink);
            tag.pill.sizeDelta = new Vector2(310, 104); tag.pill.pivot = new Vector2(.5f, 0);
            tag.back = tag.pill.GetComponent<Image>();
            tag.title = Label(tag.pill, "", 32, TextAnchor.UpperLeft, Color.white); Fit(tag.title.rectTransform, .52f, .96f);
            tag.detail = Label(tag.pill, "", 25, TextAnchor.LowerLeft, new Color(.86f, .91f, .93f)); Fit(tag.detail.rectTransform, .06f, .5f);
            tag.detail.resizeTextForBestFit=true;tag.detail.resizeTextMinSize=18;tag.detail.resizeTextMaxSize=25;
            var badge = Box(tag.pill, "New", new Vector2(.74f, .56f), new Vector2(.97f, .92f), Amber);
            Label(badge, "NEW", 22, TextAnchor.MiddleCenter, Color.white).rectTransform.offsetMin = Vector2.zero;
            tag.badge = badge.gameObject;
            tag.pill.gameObject.AddComponent<Button>().onClick.AddListener(() => replay.SelectAircraft(index));
            return tag;
        }

        void LateUpdate() { Refresh(Camera.main); }

        public void Refresh(Camera camera) {
            if (replay == null || camera == null || replay.Clock == null) return;
            if(replay.TrainingPresentation){canvas.enabled=false;return;}
            var uiCamera = canvas.renderMode == RenderMode.ScreenSpaceOverlay ? null : canvas.worldCamera;
            var away = replay.AwayNotice != null ? new HashSet<string>(replay.AwayAircraft) : new HashSet<string>();
            var known = replay.Data.KnownAt(replay.Clock.Time);
            for (int i = 0; i < tags.Count; i++) {
                var tag = tags[i]; var aircraft = replay.Content.Find(tag.id);
                var screen = aircraft == null ? Vector3.back : camera.WorldToScreenPoint(aircraft.position + Vector3.up * LabelHeightMetres);
                bool show = replay.Clock.Tracked && screen.z > 0 && screen.x >= 0 && screen.x <= camera.pixelWidth && screen.y >= 0 && screen.y <= camera.pixelHeight;
                tag.pill.gameObject.SetActive(show);
                if (!show) continue;
                RectTransformUtility.ScreenPointToLocalPointInRectangle(root, screen, uiCamera, out var local);
                // Keep the complete label inside the view and below the header/away banner.
                float half = tag.pill.sizeDelta.x * .5f;
                local.x = Mathf.Clamp(local.x, root.rect.xMin + half + 12, root.rect.xMax - half - 12);
                float top = root.rect.yMin + root.rect.height * (replay.AwayNotice != null ? .765f : .835f);
                local.y = Mathf.Min(local.y, top - tag.pill.sizeDelta.y);
                tag.pill.anchoredPosition = local; tag.pill.anchorMin = tag.pill.anchorMax = new Vector2(.5f, .5f);
                var plan = replay.Data.aircraft[i]; var flight = plan.FlightAt(replay.Clock.Time);
                var reports = known.Where(e => e.flightInstance == flight).ToArray();
                var stand = reports.Where(e => e.facts != null).SelectMany(e => e.facts).LastOrDefault(f => f.property == "stand");
                var latest = reports.LastOrDefault(e => e.facts == null || e.facts.All(f => f.property != "stand"));
                tag.title.text = $"{tag.id}  ·  {flight}";
                tag.detail.text = (stand != null ? "Stand " + stand.value : "No stand report") + (latest != null ? "  ·  " + CompactReport(latest) : "");
                tag.back.color = i == replay.SelectedAircraftIndex ? Teal : Ink;
                tag.badge.SetActive(away.Contains(tag.id));
            }
            bool bannerOn = replay.Clock.Tracked && replay.AwayNotice != null && !replay.DetailsOpen;
            banner.gameObject.SetActive(bannerOn);
            if (bannerOn) {
                int count = replay.AwayNotice.Length == 1 && replay.AwayNotice[0].StartsWith("Nothing") ? 0 : replay.AwayNotice.Length;
                bannerText.text = $"While you were away ({replay.AwayNoticeSpan}): " + (count == 0 ? "nothing new" : count + (count == 1 ? " new report" : " new reports")) + "  ›";
            }
        }

        string CompactReport(ScenarioEvent report){
            if(!replay.LiveTraffic || report.facts==null || report.facts.Length==0)return replay.ShortReport(report);
            var fact=report.facts[0];
            switch(fact.property){
                case "movement_status":return char.ToUpper(fact.value[0])+fact.value.Substring(1);
                case "baggage_status":return fact.value=="in progress"?"Bags loading":"Bags "+fact.value;
                case "fuel_status":return fact.value=="in progress"?"Fuelling":"Fuel "+fact.value;
                case "movement_condition":return fact.value.StartsWith("hold")?"On hold":"Hold released";
                case "tobt":return "Time revised";
                default:return replay.ShortReport(report);
            }
        }

        RectTransform Box(Transform parent, string name, Vector2 min, Vector2 max, Color color) {
            var g = new GameObject(name, typeof(RectTransform), typeof(Image)); g.transform.SetParent(parent, false);
            var r = g.GetComponent<RectTransform>(); r.anchorMin = min; r.anchorMax = max; r.offsetMin = r.offsetMax = Vector2.zero;
            g.GetComponent<Image>().color = color; return r;
        }

        Text Label(Transform parent, string value, int size, TextAnchor align, Color color) {
            var g = new GameObject("Text", typeof(RectTransform), typeof(Text)); g.transform.SetParent(parent, false);
            var r = g.GetComponent<RectTransform>(); r.anchorMin = Vector2.zero; r.anchorMax = Vector2.one; r.offsetMin = new Vector2(20, 0); r.offsetMax = new Vector2(-16, 0);
            var t = g.GetComponent<Text>(); t.font = font; t.fontSize = size; t.color = color; t.alignment = align; t.text = value;
            t.horizontalOverflow = HorizontalWrapMode.Wrap; t.verticalOverflow = VerticalWrapMode.Truncate; t.raycastTarget = false; return t;
        }

        static void Fit(RectTransform r, float bottom, float top) { r.anchorMin = new Vector2(0, bottom); r.anchorMax = new Vector2(1, top); }
    }
}
