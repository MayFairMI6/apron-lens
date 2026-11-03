# AirfieldLens user manual

AirfieldLens is a conversational AR assistant for airport stand coordination. You
stand on a simulated apron, see aircraft and ground vehicles through an AR
camera, point at an aircraft and ask about it. The assistant answers from the
operational reports received so far, and every claim it shows is checked
against those reports.

Everything runs on a Mac, in Unity, as a simulated AR session (AR Foundation's
XR Simulation) on a fictional airport apron. The airport, aircraft and reports
are invented, and nothing here is for operational use.

## 1. What you need

- A Mac with Apple Silicon and about 40 GB free for the model.
- The project's Unity editor at `work/unity-editor/Unity.app`, or Unity
  6000.2.2f1 with Android build support.
- Python 3.12 (Homebrew).

## 2. One-time setup

Run these from the repository folder.

1. **Create the model environment:**
   ```bash
   /opt/homebrew/opt/python@3.12/bin/python3.12 -m venv .venv-candidates
   ```
   ```bash
   .venv-candidates/bin/python -m pip install -r requirements-candidates.txt
   ```
2. **Download the model** (Qwen3.5-9B, about 18 GB, at its pinned revision):
   ```bash
   .venv-candidates/bin/python -m backbone.download --model qwen3.5-9b
   ```
3. **Open the project** `unity/SurfaceSafetyCoach` in the Unity editor. The
   first import takes a few minutes.

## 3. Starting a session

1. **Start the assistant service** and leave it running:
   ```bash
   .venv-candidates/bin/python -m backend.conversation.server --model qwen3.5-9b --profile apronlens-v2-mps
   ```
   It serves on `127.0.0.1:8766` and writes its access token to
   `work/qwen-server-token.txt`, which the editor reads by itself.
2. **In Unity,** open the scene `Assets/SurfaceSafety/Scenes/WorldAR.unity`.
3. **In the Game view's resolution menu,** choose (or add) 1080 × 1920
   portrait, the phone layout the app is designed for.
4. **Press Play.** You start at eye height south of the taxiway, looking at
   stands A and B and the terminal. The status line reads "Simulated world AR ·
   apron in view".

The demo scenario has:
- three identical-looking aircraft: A1 on stand A, A2 on stand B, A3 taxiing;
- A2 with two rotations (flights F2-R1, then F2-R2);
- reports that arrive over two minutes of replay, some late and some
  conflicting.

## 4. Moving around

| Action | Control |
|---|---|
| Look around | Hold the right mouse button and move the mouse |
| Walk | W, A, S, D |
| Down / up | Q / E |
| Move faster | Hold Shift |

These are AR Foundation's XR Simulation defaults (Edit → Project Settings → XR
Plug-in Management → XR Simulation).

## 5. The screen

From top to bottom:

- **Header:** the status line (whether the apron is in view, and whether the
  replay is running), and one chip per aircraft showing its current flight. Tap
  a chip to select that aircraft.
- **AR view:** the apron through the camera. The selected aircraft has a ring,
  and the caption below the view names it and says what it's doing.
- **Now, Why, History:**
  - **Now:** the latest report for the selected flight, or the "While you were
    away" card.
  - **Why:** the evidence behind readiness and status.
  - **History:** every report received for the flight, oldest to newest. Tap a
    report for its source, event time and receipt time.
- **Transport:**
  - **Play / Pause** runs the replay.
  - **Restart** returns to 0 s.
  - The **timeline** jumps to any time.
  - **More** opens the session options.

Reports appear only after their receipt time, as in operations: a report about
an event at 40 s that was received at 48 s shows up at 48 s, marked **LATE**.

## 6. Pointing at an aircraft

Click an aircraft in the AR view, or tap its chip. The ring moves to it, and
questions are about that aircraft and its current flight. Pointing is how you
tell identical aircraft apart: the demo's three aircraft share one livery.

## 7. Asking a question

1. Select the aircraft.
2. Open **More → Ask a question**.
3. Type your question and choose **Ask**.

The replay pauses while the assistant answers, so the answer stays tied to that
moment. With the 9B model, answers take about 20–30 s.

What you may see:

| Status | Meaning |
|---|---|
| **CHECKED ANSWER** | Every claim shown matches a report received for that flight by this time. Each claim names its report, for example [D05]. |
| Unknowns | Things no report covers yet, listed rather than guessed. |
| Model interpretation (not checked) | The model's own reading. Shown, but not verified against reports. |
| **ANSWER WITHHELD** | A claim didn't match a received report, so nothing from the model is shown. Rephrase or ask again. |
| **CONTEXT CHANGED** | The selection or replay time changed while it was answering. Ask again. |
| **SCENE UNAVAILABLE** | The apron is out of view. Turn back to it, then ask. |
| **CONNECTION NEEDED** / **UNAVAILABLE** | The assistant service isn't reachable. Check that it's running (section 3). |

Questions to try:
- "Where is this aircraft heading?" (with the taxiing aircraft selected)
- "When does this aircraft leave?", then "I mean its next rotation."
- "Which stand is this aircraft on?" (A1 has conflicting stand reports between
  36 s and 56 s)
- "What changed while I was away?" (after looking away)

## 8. Corrections

Corrections such as "I mean its next rotation" or "no, the other aircraft"
change what the conversation is about, not the facts. The assistant remembers
the correction for your next questions, until you select a different aircraft.

## 9. Looking away

Turn the camera away from the apron while the replay runs. The status reads
"Apron out of view · it keeps running", because reports keep arriving. When you
turn back, the **While you were away** card on the Now tab lists every report
received meanwhile, across all aircraft. Tap the card to dismiss it.

If you then ask the assistant what changed, it is told when you were looking
away.

## 10. Session options (More)

- **Model connection:** the service address and token. Only needed when the
  service runs somewhere other than this Mac.
- **Copy session log path:** the session's event log (selections, questions,
  tracking changes), for checking what happened.
- **Ask a question:** opens the conversation panel.

## 11. Troubleshooting

| Problem | What to do |
|---|---|
| No aircraft visible after pressing Play | Make sure you opened `WorldAR.unity`, not another scene, and look towards the terminal (north). |
| The camera doesn't move | Hold the right mouse button while moving the mouse; click inside the Game view first. |
| Answers never arrive | Check that the service from section 3 is running in a terminal. The first answer after starting it can take longer while the model loads. |
| "Connection failed" | The service stopped or another program uses port 8766. Restart the service. |
| The layout looks squashed | Set the Game view to 1080 × 1920 portrait. |
| Something looks wrong in the scene | Re-create the apron and scene with **WorldArSetup** (see `docs/AR_SCOPE.md`). |

## 12. Limits

- The airport, aircraft and reports are fictional. The replay is a scripted
  scenario, not live data.
- AR runs in simulation; it hasn't been tested on a physical device.
- Answers come from a local model and can be wrong. Only the checked claims are
  verified, and only against the replay's reports.
