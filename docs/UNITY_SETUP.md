# Unity and Android setup

The application is in `unity/SurfaceSafetyCoach`. GitHub stores the complete
editable Unity source. Android execution and AR tracking take place on a phone.

## Prerequisites

- Unity **6000.2.2f1**; open this exact project version first.
- Android Build Support, SDK/NDK and OpenJDK installed with the editor.
- Vuforia Engine **11.4.4**, obtained through its official licensed distribution.
- An ARM64 Android phone; the current build requires Android 10 / API 29 or newer.
- For model answers, a separate Mac running the local Qwen service.

The package manifest references `Packages/com.ptc.vuforia.engine-11.4.4.tgz`.
Obtain that exact package and put it there before opening Unity. The `.tgz` is
intentionally ignored and is not redistributed. Open Vuforia configuration in
Unity, create local settings as needed, and enter your own application license.
`Assets/Resources/VuforiaConfiguration.asset` and its metadata are ignored.

## Open and run

1. In GitHub Desktop choose **File → Clone repository**. Select this repository.
2. In Unity Hub choose **Add project from disk**, then the `unity/SurfaceSafetyCoach`
   folder. Allow package import to finish.
3. Open `Assets/SurfaceSafety/Scenes/DesktopReplay.unity` and press Play for the
   camera-free layout/replay view. This view is explicitly labeled preview.
4. For Android, use `Assets/SurfaceSafety/Scenes/AndroidAR.unity` in the Build
   Profile, ARM64/IL2CPP, portrait orientation and OpenGL ES 3.
5. Build and install, grant camera permission, and scan the measured print.

The [board](../outputs/milestone1/Print-AirportBoard-24x16cm.png) must be printed
at 24 × 16 cm with scaling disabled. Its image target width is 0.24 m. The scene
contains fictional paths and generic airliners, not type-accurate aircraft or
validated airport geometry.

## Build helper

On macOS, specify an editor with Android modules installed:

```sh
export UNITY_EDITOR="/path/to/Unity.app/Contents/MacOS/Unity"
bash scripts/build_milestone1.sh
```

The original machine's private editor path is used only as a fallback. A teammate
must set `UNITY_EDITOR`. The editor build helper configures SDK/NDK/JDK paths
relative to the editor; adapt those paths if your installation layout differs.
You can also build through Unity's Android Build Profile normally.

Output: `outputs/milestone1/AirfieldCoordination-M1.apk` (ignored by Git).
The checked release is version 1.3 / build 4, a development build with local
HTTP enabled. Use it only with the fictional test data on trusted connections.

## Model connection

The app's replay and **Recorded facts** view work without a model. To use Qwen:

1. Start the Mac service as described in the root README.
2. In the app open **More → Model connection**.
3. Enter the service address and local token; the token is displayed as a password.
4. Select an aircraft and replay checkpoint, then **Why → Qwen → Explain**.

USB forwarding: `adb reverse tcp:8765 tcp:8765`, using `http://127.0.0.1:8765`.
Wi-Fi: start the service with `--host 0.0.0.0` on a trusted network and use the
Mac's LAN address. Read [QWEN_CONNECTION.md](../QWEN_CONNECTION.md) for details.
Never commit the service token or a Vuforia application license.

## Verification and remaining phone work

Editor entry points:

- `MilestoneBuild.Verify`: deterministic motion, replay, receipt-time and tracking gates.
- `CoordinatorUiVerification.Run`: flight scope, source inspection and navigation.
- `ClaimClientVerification.Run`: value/source support and stale response rejection.
- `QwenIntegrationVerification.Run`: real service at checkpoints 13 and 14; omit
  `-quit` because this method exits after asynchronous requests finish.
- `S24LayoutVerification.Run`: actual Unity UI renders at 1080 × 2340. Insets
  90 px top / 72 px bottom and density 3 are explicit simulation assumptions.

The saved S24 checks passed 14 workflow checks, 86 control-instance size/bounds
checks and 155 type-size checks under those assumptions. Repeated controls
across screens count separately. They do not measure the user's One UI settings.

Physical acceptance is pending: phone launch, permissions, target acquisition,
tracking loss/recovery, real touch, keyboard avoidance, font scaling, networking,
performance and device logs. The user chose to perform this test later.

## Optional wireframe wrapper

The app itself does not use Node. To regenerate the illustrative phone outline
from existing S24 Unity screenshots, install Node.js and run:

```sh
npm install
npx playwright install chromium
npm run render:s24
```

Set `AIRFIELD_CHROMIUM` to an existing Chromium/Chrome executable if preferred.
This renderer opens only the generated local artifact with an isolated headless
browser. It does not inspect a user's browser tabs. Actual UI pixels come from
`S24LayoutVerification.Run`; the wrapper does not invent or redraw app content.
