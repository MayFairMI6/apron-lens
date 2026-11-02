# Course checkpoint 1: simulated AR demo and video plan

Everything runs on the Mac, in Unity, with no printed board and no physical
device (ledger D-090). The app runs as an AR app in AR Foundation's XR
Simulation:
- the simulated camera sees a full-scale fictional apron, and you walk and look
  around it at eye height;
- the replay's aircraft, reports and the assistant are drawn on that apron.

## What runs where

- **Unity editor:** the project's editor at `work/unity-editor/Unity.app`, with
  the project `unity/SurfaceSafetyCoach`, scene `Assets/SurfaceSafety/Scenes/WorldAR.unity`.
- **Demo scenario** `ar_demo_01`:
  - three identical-looking aircraft: A1 on stand A, A2 on stand B, A3 taxiing;
  - a two-rotation aircraft (A2);
  - reports that keep arriving while you look away.
- **Conversation service:** on the same Mac, reached at `127.0.0.1:8766`. The
  editor reads the token from `work/qwen-server-token.txt` itself, so there's
  nothing to configure.

## Setup (about 5 minutes)

1. Start the conversation service with the best model from milestone 1:
   ```bash
   .venv-candidates/bin/python -m backend.conversation.server --model qwen3.5-9b --profile apronlens-v2-mps
   ```
2. Open the project in the Unity editor and open the scene
   `Assets/SurfaceSafety/Scenes/WorldAR.unity`.
3. In the **Game** view's resolution menu, add and choose a portrait size of
   1080 × 1920, the phone layout the app is designed for.
4. Press **Play**. The view starts at eye height south of the taxiway, looking
   at the two stands and the terminal. The status reads "Simulated world AR ·
   apron in view".
5. **Moving around:** hold the right mouse button to look around, use W, A, S
   and D to walk and Q or E to go down or up, and hold Shift to move faster. These are XR Simulation's default
   controls; Unity lists them under Edit → Project Settings → XR Plug-in
   Management → XR Simulation.

Answers from the 9B model take about 20–30 s. Cut the waits in the edit.

## Recording

Use the Mac's screen recording (Cmd-Shift-5, "Record selected portion") over
the Game view. Narrate as you record, or add title cards in the edit.

## Shot list (about 3–4 minutes)

| # | Title card | What to show | Say or caption |
|---|---|---|---|
| 0 | ApronLens: a conversational AR assistant for stand coordination | The apron at eye height | "An AR assistant that keeps a shared picture of the stand as reports arrive and the conversation changes." |
| 1 | AR on the apron | Look around slowly, then press **Play** | A simulated AR session on a fictional apron; the replay's aircraft sit on the real stands and taxiway. |
| 2 | AR pointing | Click the taxiing aircraft (A3) in the view; **More → Ask a question**: "Where is this aircraft heading?" | The three aircraft look the same; pointing tells the assistant which one is meant. The answer cites report D03. |
| 3 | Corrections | Click A2 and ask "When does this aircraft leave?", then "I mean its next rotation." | The correction moves the referent to the next rotation; the answer cites the target off-block time. |
| 4 | Looking away | Around 25 s, turn round, away from the apron, for about 20 s, then turn back | The status says the apron is out of view and still running. On return, the **While you were away** card lists what arrived meanwhile. |
| 5 | What changed? | Ask "What changed while I was away?" | The assistant answers from the reports received in that gap; every claim is checked against a report, and anything unchecked is labelled. |
| 6 | Evidence and conflicts | **Why** and **History** tabs; tap a report for its source and timing | Late reports, the conflicting stand report for A1 and its later correction. |
| 7 | What we measured | A title card with the M1 results | On 40 held-out turns: AR pointing helps (the 4B model drops 15 points without it), the best model answers 60% correctly against 40% for a rule-based baseline, and tracking information given to the model didn't help, which is why the app now shows the change card itself. |
| 8 | Next | A title card | Milestone 2: the camera's own view as evidence, realistic models, a vision detector. Milestone 3: the full evaluation. |

## After recording

Stop Play mode, and stop the conversation service with Ctrl-C.
