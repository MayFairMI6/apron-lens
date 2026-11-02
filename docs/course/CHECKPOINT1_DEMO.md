# Course checkpoint 1: phone demo and video plan

The checkpoint asks for the app running on a smartphone and a narrated video of
its current features. This is a demo, not an evaluation: physical tracking is
still untested as a measurement (ledger D-010). The milestone results come from
the Unity simulation and the held-out sets.

## What runs where

- **Phone (Galaxy S24):** the AR app, `work/checkpoint1/ApronLens-AR-demo.apk`,
  built by `MilestoneBuild.AndroidArDemo`. It starts on the demo scenario
  `ar_demo_01`:
  - three identical-looking aircraft: A1 on Stand A, A2 on Stand B, A3 taxiing;
  - a two-rotation aircraft (A2);
  - reports that keep arriving while the board is out of view.
- **Mac:** the conversation service with the local model, reached over USB.
- **Table:** the printed board, `outputs/milestone1/Print-AirportBoard-24x16cm.png`,
  at exactly 24.0 × 16.0 cm.

## Setup (about 15 minutes)

1. **Print the board** at 100% scale and check that it measures 24.0 × 16.0 cm.
2. **On the Mac**, start the conversation service with the best model from
   milestone 1:
   ```bash
   .venv-candidates/bin/python -m backend.conversation.server --model qwen3.5-9b --profile apronlens-v2-mps
   ```
   The first run creates the access token in `work/qwen-server-token.txt`.
3. **On the phone**, turn on Developer options and USB debugging, then connect
   it by USB.
4. **Install the app and forward the ports.** `adb` is bundled at
   `work/unity-editor/PlaybackEngines/AndroidPlayer/SDK/platform-tools/adb`.
   ```bash
   work/unity-editor/PlaybackEngines/AndroidPlayer/SDK/platform-tools/adb install -r work/checkpoint1/ApronLens-AR-demo.apk
   ```
   ```bash
   work/unity-editor/PlaybackEngines/AndroidPlayer/SDK/platform-tools/adb reverse tcp:8766 tcp:8766
   ```
   ```bash
   work/unity-editor/PlaybackEngines/AndroidPlayer/SDK/platform-tools/adb reverse tcp:8765 tcp:8765
   ```
5. **In the app**, open **More → Model connection**, enter
   `http://127.0.0.1:8765`, and paste the token from
   `work/qwen-server-token.txt`. The conversation service uses the same host on
   port 8766.
6. **Point the phone at the board.** The status changes to "Board tracked", and
   the aircraft appear on it.

Answers from the 9B model take about 20–30 s on the Mac. Cut the waits in the
edit.

## Shot list (about 3–4 minutes)

Record the phone screen (Quick Settings → Screen recorder). Put a title card
before each part, with your name on the first. Narrate, or use the title cards
alone.

| # | Title card | What to show | Say or caption |
|---|---|---|---|
| 0 | ApronLens: a conversational AR assistant for stand coordination | The printed board on the table | "An AR assistant that keeps a shared picture of the stand as reports arrive and the conversation changes." |
| 1 | The board in AR | Phone finds the board; three aircraft appear; tap **Play** | A fictional apron replay anchored on the printed board; the timeline and the aircraft chips. |
| 2 | AR pointing | Tap the taxiing aircraft (A3) on screen; **More → Ask a question**: "Where is this aircraft heading?" | The three aircraft look the same; pointing tells the assistant which one is meant. The answer cites report D03. |
| 3 | Corrections | Tap A2 and ask "When does this aircraft leave?", then "I mean its next rotation." | The correction moves the referent to the next rotation; the answer cites the target off-block time. |
| 4 | Looking away | Around 25 s, point the phone away from the board for about 20 s, then back | The status shows the board is lost, but the apron keeps running. On return, the **While you were away** card lists what arrived meanwhile. |
| 5 | What changed? | Ask "What changed while I was away?" | The assistant answers from the reports received in that gap; every claim is checked against a report, and anything unchecked is labelled. |
| 6 | Evidence and conflicts | **Why** and **History** tabs; tap a report for its source and timing | Late reports, the conflicting stand report for A1 and its later correction. |
| 7 | What we measured | A title card with the M1 results | On 40 held-out turns: AR pointing helps (the 4B model drops 15 points without it), the best model answers 60% correctly against 40% for a rule-based baseline, and tracking information given to the model didn't help, which is why the app now shows the change card itself. |
| 8 | Next | A title card | Milestone 2: the camera's own view as evidence, realistic models, and a vision detector. Milestone 3: the full evaluation. |

## After recording

- Delete the forwarded ports when you're done:
  ```bash
  work/unity-editor/PlaybackEngines/AndroidPlayer/SDK/platform-tools/adb reverse --remove-all
  ```
- Stop the conversation service with Ctrl-C.
