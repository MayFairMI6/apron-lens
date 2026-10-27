# Milestone 1: ApronLens

The full Unity application and Python service are maintained in the private
GitHub repository `MayFairMI6/apron-lens`. See README.md for setup.

## Intended airfield use

The target role is a turnaround coordinator or ramp supervisor inspecting a
stand's changing operational context. The proposed use is a stationary review of
which aircraft/flight a report concerns, what changed, and which information was
available at the time. Existing mobile coordination products establish a
plausible device/workflow precedent; see the sourced motivation in
RESEARCH_PLAN.md. AR's added value requires comparison with an ordinary screen.

Milestone one implements a simulated, printed-board surrogate. It does not
identify actual aircraft, localize at a real stand, consume operational A-CDM
feeds, issue movement instructions, or provide validated collision protection.

The Unity product name, Android launcher label and in-app title are **ApronLens**.
The current Android package is `ApronLens-M1.apk`, version 1.4 / build 5.

## Local project

Open `unity/SurfaceSafetyCoach` in Unity 6000.2.2f1. Vuforia 11.4.4 is reused
from the user's earlier assignment installation; the old project is unchanged.
Local license configuration is excluded from source-control rules.

- `Assets/SurfaceSafety/Scenes/DesktopReplay.unity`: camera-free desktop view.
- `Assets/SurfaceSafety/Scenes/AndroidAR.unity`: Vuforia image-target AR.
- `Assets/Resources/milestone1.json`: original fictional scenario, identities,
  timestamped waypoints, and reports with event and receipt times.
- `outputs/milestone1/Print-AirportBoard-24x16cm.png`: print at **24.0 x 16.0 cm**.
  The runtime target width is **0.24 m**. Disable print scaling and measure it.

## Implemented

Two aircraft, two stands, one shared path region, original diagram artwork,
play/pause/restart, timeline seek, elapsed clock, receipt-time-filtered report
history, and local JSONL session logs. A2 remains at its stand until authored
service completion; its subsequent path is a scripted simulation.

AR content is parented to the image target. Loss or limited tracking pauses
playback and hides content. Reacquisition requires the user to press Play.
Application interruption also pauses playback. Desktop preview is explicitly
labeled as simulation and does not exercise tracking.

The Log path button copies the session log location; logs are already written
locally as controls/tracking change. It does not upload or share anything.

## Coordinator UI and Qwen integration

The Astra UI pass adds aircraft selection and **Now / Why / History** views.
Now separates authored scene position, received reports, and unknown A-CDM
readiness. History defaults to the selected flight; report details show both
event and receipt times and can jump to the receipt checkpoint. The Why view
separates the deterministic evidence summary from Qwen-selected, validated atomic
claims rendered with templates.
A larger spatial view, concise latest-update card, progressive source details,
pinned replay controls and safe-area-aware layout support the portrait phone
workflow. Aircraft are original generic 3D airliners with tapered fuselages,
swept wings, engines, windows and tail livery; their dimensions are illustrative.

Qwen runs on the Mac and selects from the flight's time-eligible reports. The
service also accepts a synthetic Unity render for audit; production evidence
decisions use text, since the scene has no service-state evidence. Connection setup, tests, and limitations are in
QWEN_CONNECTION.md. No real camera imagery is sent. Changing time or aircraft
invalidates an old answer. TOBT/TSAT and overall readiness remain unconfirmed;
this prototype does not consume an A-CDM feed.

## Verified so far

- Unity C# compilation and scene-generation pass.
- Thirteen deterministic replay/event checks pass, including playback gating,
  pause, restart, backward seek, end-of-scenario stop, known waypoint positions,
  target width, and late-report availability.
- Sixteen coordinator UI checks cover selected-flight filtering, evidence inspection,
  navigation, backward replay, receipt-time jumps, and tracking gates.
- Thirty-one backend tests cover field-level claim support, citation regression,
  supersession, expiry, conflicts, identity, authentication, and request validation.
- Five Unity client checks reject borrowed citations, unsupported values, old
  free-prose responses, and stale checkpoints. Two real Qwen calls run through Unity HTTP at 13 and 14 seconds.
  The final production run accepted both supported answers (2/2); stale answers
  after rewind remain rejected. These are development smoke cases, separate
  from the frozen 32-question fresh evaluation.
- An original event at 12 seconds, received at 14 seconds, is hidden at 13 and
  available at 14.
- A rendered desktop scene is saved for layout review. This is generated from
  the project, not evidence of phone tracking.

Verification output: `outputs/milestone1/verification.json`.
The Android ARM64 development build has succeeded. Package integrity and its
debug signature are checked separately in
`outputs/milestone1/android-build-verification.json`. Minimum Android version is
10 (API 29); target API is 35. The build uses OpenGL ES 3 and Unity's conventional
Activity entry point. Phone compatibility and tracking still require testing.

The SDK/NDK/JDK/CMake toolchain was installed alongside a private, user-owned
editor copy in `work/unity-editor`. Rebuild with `bash scripts/build_milestone1.sh`.
Alternatively set `UNITY_EDITOR` to a Unity 6000.2.2f1 executable with Android
support. Local paths for external tools are set by the build script inside Unity;
adapt that configuration when building on a teammate's machine.

## Galaxy S24 layout simulation

The base S24 viewport is 1080 × 2340 portrait. Actual Unity screens are rendered
inside an illustrative phone wireframe in `outputs/milestone1/s24/`. The test
uses assumed gesture-navigation insets (90 px top, 72 px bottom) and density 3,
not measured settings from the user's phone. Important labels, touch regions
and connection fields were enlarged after checking phone-scale readability.
The saved verification records workflow, control bounds, touch dimensions and
text-size measurements. Screens cover Now, Qwen, the separate baseline,
History, source detail, connection setup, moving aircraft and tracking loss.
Physical touches, keyboard behavior, OS font scaling and camera tracking are
outside this desktop simulation. The Qwen screen replays a genuine saved
response; its source hash and timestamp are recorded.

## Phone acceptance check

On the Android phone: launch the app, grant camera access, point at the measured
print, acquire the board, and press Play. Confirm the scene follows the board as
the phone moves; pause stops clock and aircraft; restart reproduces the path;
covering/removing the board pauses and hides the scene; reacquisition requires
Play. Check the late report before and after second 14. Record device model,
Android version, target dimensions, lighting, tracking behavior, and any failure.

The user chose to perform the phone test later. Physical validation is pending
until a phone is connected and these checks run.
Milestone one is fully accepted only after the phone checks pass.
