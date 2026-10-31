# Decision ledger

Append-only record of decisions that shape ApronLens, so they survive context
compaction, new sessions and handoffs. Add new entries at the end with the
next number. Never rewrite an entry: if a decision changes, add a new entry
that supersedes it and mark the old one's status.

Each entry has a decision, the reason, where it lives (commit, PR or file),
and a status: **active**, **superseded by D-n**, or **done**. Earlier details
are in `docs/REVIEW_DISPOSITIONS.md`.

## Standing rules

| ID | Date | Decision | Reason | Where | Status |
|---|---|---|---|---|---|
| D-001 | 2026-10-31 | Never modify the frozen V2 sources: `backend/evidence.py`, `reasoning.py`, `decisions.py`, `server.py`, `scripts/evaluate_reasoning_v2.py`, `scripts/report_reasoning_v2.py`, `requirements-qwen.lock.txt`. | They produced the preserved V2 results. | `scripts/check_research_integrity.py --current` | active |
| D-002 | 2026-10-31 | Never read held-out answers. `data/reasoning_v2_fresh/` is not used for development (two entries, N01-Q1 and N01-Q2, were displayed once in review; unused). New held-out answers live outside the repository. | Development runs tune the method; a test set seen during tuning stops being a test. | `backend/conversation/guards.load_heldout` | active |
| D-003 | 2026-10-31 | Never commit the user's own uncommitted work (README, RESEARCH_PLAN, QWEN_*.md, docs/MODEL_WORKFLOW.md, docs/UNITY_SETUP.md, media/, output/, tmp/, scripts/build_android.sh, the staged MILESTONE_1.md → IMPLEMENTATION.md rename). Commit only explicit paths. | It is the user's work in progress. | — | active |
| D-004 | 2026-10-31 | No paid API calls, no GitHub releases, and no pushes or merges to `main` without the user's say-so. | Budget and control stay with the user. | — | active |
| D-005 | 2026-10-31 | Every backbone change bumps `backbone/VERSION` and reruns `python -m backbone.check --stamp`. | The backbone is shared with the compaction project and adopted by version. | `backbone/` | active |
| D-006 | 2026-10-31 | Third-party weights and frameworks (Qwen, transformers, Unity, Vuforia) are not the user's contribution. | Accurate attribution. | `THIRD_PARTY_NOTICES.md` | active |
| D-007 | 2026-10-31 | Development runs use development data only: inline fixtures, `visual_dev_*` scenarios, and v1 families D01–D08. Never H01–H04 or `reasoning_v2_fresh`; v1 dialogues are generated from scenario events without reading the v1 question/gold file. | Keeps every held-out set untouched. | `scripts/run_conversation_smoke.py` | active |

## Environment and scope

| ID | Date | Decision | Reason | Where | Status |
|---|---|---|---|---|---|
| D-010 | 2026-10-31 | Physical phone and printed-board tracking tests are dropped. All validation stays inside Unity simulation: editor batch checks, rendered scenarios and the simulated S24 layout. | User decision. Simulation covers the remaining work without a device. | — | active. README, IMPLEMENTATION and RESEARCH_PLAN still say "pending" (user's uncommitted files). |
| D-011 | 2026-10-31 | Unity runs only on the user's Mac. Not in Claude cloud sessions (license sign-in, multi-GB install, Vuforia git-ignored) and not on GAIVI (USF VPN, no sudo, compute nodes may lack internet, no display). | Unity needs a licensed editor and the private Vuforia package. | — | active |
| D-012 | 2026-10-31 | GAIVI is for model runs only (larger Qwen/Gemma on CUDA). | Its documented purpose; see `docs/GAIVI.md`. | `docs/GAIVI.md` | active |
| D-013 | 2026-10-31 | No fine-tuning (OpenAI or other) for now. If evaluation later shows a repeated failure that context and prompting cannot fix, consider a LoRA adapter on local Qwen, trained on separate families and reported as its own condition. | Fine-tuning would mix model change with the context-design question, and training on the author's own generator would inflate held-out scores. | — | active |
| D-014 | 2026-10-31 | No Android emulator or iOS build for testing. | Vuforia does not run on emulators or the simulator; editor simulation covers the rest. | — | active |

## Repository history (31 October)

| ID | Decision | Reason | Where | Status |
|---|---|---|---|---|
| D-020 | Sync `.github/workflows/` on `backbone/explicit-runtime` from `docs/github-actions/`. The `gh` token gained the `workflow` scope to push it. | The remote session could not write workflow files. | `4be62ff` | done |
| D-021 | Merge `review/api-plan-fixes-2026-10-31`, then `backbone/explicit-runtime`, into `main` (fast-forward). Delete `claude/charming-maxwell-msnzgq`, which closed PR #1 unmerged. | Order from the handoff; backbone 1.1.0 supersedes 1.0.0. | `main` at `4be62ff` | done |
| D-022 | Keep `main` linear: rebase-merge single-commit PRs, squash-merge PRs whose branch holds a merge commit. Delete branches once their content is verified in `main`. | A readable history, one entry per change. | — | active |
| D-023 | Merges that would touch the user's staged index run in a temporary worktree, never in the main checkout. | Git refuses a merge over a staged rename, and the user's index must not change (D-003). | — | active |

## Visual reference design

| ID | Decision | Reason | Where | Status |
|---|---|---|---|---|
| D-030 | The evidence image is cropped to the region holding every aircraft and stand marker (`SceneCrop`), never centred on the referent. The tap is returned in crop coordinates. The format is now `visual-capture-v2`. | A referent-centred crop would reveal the selection. The scene crop gives about 2× zoom without leaking it. | PR #2, `fd8cfb1` | done |
| D-031 | Props are dark grey (one neutral colour, no text) and the hatch is 1.5× larger. `RunObservations` fails if a prop drops below 0.15% of the frame. | Props covered only 0.06% and 0.02% of the frame (not the estimated 1%) and were near-white on white aircraft. Now 0.26% and 0.23%. | PR #2, `fd8cfb1` | done |
| D-032 | Scenarios may declare 2–4 aircraft and `"livery": "uniform"`. Milestone 1 keeps two indexed aircraft, its layout and its authored baseline text; other scenarios get baseline text built from their own reports. `visual_dev_02` has three same-livery aircraft. | Reference tasks need similar aircraft told apart only by position, motion and props. | PR #3, `f8d5df2` | done |
| D-033 | A tracked Milestone 1 output regenerated by a check with only rounding-level differences is restored, not recommitted. | Preserved outputs change only for real differences. | `outputs/milestone1/s24/layout-verification.json` | active |
| D-034 | Open: occlusion families (where "cannot see" is correct) are not yet authored. | — | — | open |

## Conversation path

| ID | Decision | Reason | Where | Status |
|---|---|---|---|---|
| D-040 | `/conversation` is a new server (`backend/conversation/server.py`, port 8766), separate from the frozen `/reason`. It shares the `/reason` token, which is checked before the body. Sessions are in memory. | `/reason` is frozen (D-001); one secret for the app. | PR #4, `138c532` | done |
| D-041 | Referent rule: the app sends its selected aircraft on every turn. Selecting another aircraft resets the referent; the same aircraft keeps an accepted correction. Memory comes only from the user's selection or a validated `memoryUpdate`, never from the model's rationale. | Corrections such as "its next rotation" must persist, but the model must not write memory freely. | `backend/conversation/turns.py` | active |
| D-042 | A session is bound to the scenario and mode it started with; changing either gets 409. | Scenarios reuse aircraft and flight IDs, so memory could carry across (review finding on PR #4). | PR #4 | done |
| D-043 | Follow-up prompts carry `changedSincePreviousAnswer` from the validator's own `changed_facts`. | Without it, the required answer could not be read from the prompt (review finding on PR #4). | prompt v2, PR #4 | done |
| D-044 | `conversation-prompt-v3`: allowed status values listed, every key required, real capture time in the example, "next rotation" defined. | The 3B model copied v2's placeholder `"exact fact status"`. | branch `conversation/prompt-v3` | pending PR |
| D-045 | Development finding, not evidence: Qwen 2.5-VL-3B under v3 accepts 12/22 turns. First questions 9/9; change follow-ups 0/7; a next-rotation correction accepted with the wrong referent; image turns 0/2. Treat these as model limits rather than tuning the prompt further toward them. | Every rule it breaks is stated in the prompt, and the needed data is computed for it. | `docs/REVIEW_DISPOSITIONS.md` | active |
| D-046 | The validator does not check whether the referent is the one the user meant. Referent correctness is scored only at evaluation time, against labels kept off the request path. | Keeps gold labels away from the system under test. | `backend/conversation/validate.py` | active |
| D-047 | v1 D02 is excluded from conversation runs. | Its `F2-R0` report has no declared rotation, and the conversation path refuses to guess. | `scripts/run_conversation_smoke.py` | active |

## Open items (31 October)

- Next model comparison on the same 22 development turns: Qwen3-VL-8B locally (about 17 GB download) or on GAIVI, then one low-cost hosted probe (about $10–15 budget, D-004).
- Unity client for `/conversation` (send `flightInstance` and conversation turns); hosted adapters.
- Scenario families: occlusion; dialogue families with rotations; a development pilot, then a held-out set written outside the repository (D-002).
- Freeze the prompt, referent rule, validator and scoring before any formal run.
- Verify and write a related-work section. Suggested, not yet verified: Clark & Wilkes-Gibbs 1986, Clark & Brennan 1991, RefCOCO, Visual Dialog, SIMMC 2.0, MultiWOZ, SituatedQA, Longpre et al. 2021, Lost in the Middle, MemGPT, Endsley 1995, EUROCONTROL A-CDM.
- Adopt backbone 1.1.0 in the compaction repository with the `compaction-gaivi-cuda` profile, as an explicit change there.
- The user decides whether to commit their own uncommitted work, including the plan PDF and its generator.
