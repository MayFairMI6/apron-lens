"""PROCEDURAL: run genuine frozen 9B responses on Checkpoint 2 development cues."""
import argparse
import json
from pathlib import Path
from uuid import uuid4

from backend.bluebird_inbound import BLUEBIRD_787
from backend.conversation.state import SessionState
from backend.fleet_incident_variations import FLEET_VARIATIONS
from backend.fleet_scenarios import FLEET_DEMONSTRATIONS
from backend.surface_queue_variations import SURFACE_VARIATIONS
from backend.training_session import TrainingSession
from backend.training_turn import run_turn
from backend.turnaround_variations import TURNAROUND_VARIATIONS
from modelaccess.contract import Settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--cues", choices=("first", "rest", "all"), default="first",
                        help="first: the original run's selection; rest: every cue it left out; all: every cue")
    parser.add_argument("--candidate", action="store_true", help="use the v9 unknown-names prompt candidate")
    parser.add_argument("--only", nargs="*", help="limit to these exercise names")
    args = parser.parse_args()
    if args.candidate:
        from experiments.unknown_names.candidate import UnknownNamesCandidate as TrainingAdapter
    else:
        from backend.training_adapter import TrainingAdapter
    adapter = TrainingAdapter("qwen3.5-9b", profile="apronlens-v2-mps",
                              prompt_audit_path=args.output.with_suffix(".prompts.jsonl"))
    adapter.load()
    settings = Settings(adapter.served_model, 768, image_max_side=672)
    cases = (BLUEBIRD_787,) + FLEET_DEMONSTRATIONS + FLEET_VARIATIONS + SURFACE_VARIATIONS + TURNAROUND_VARIATIONS
    with args.output.open("x") as stream:
        for exercise in [c for c in cases if not args.only or c in args.only]:
            world = TrainingSession(17, exercise, "demo").scenario
            session = SessionState(uuid4().hex)
            cues = world["demoQuestions"]
            original = cues if exercise in (BLUEBIRD_787, "fleet_b787_priority_landing") else cues[:1]
            # Each case keeps one session, so later cues see the memory of earlier ones as in the app.
            selected = original if args.cues == "first" else cues
            skip = len(original) if args.cues == "rest" else 0
            for cue in selected:
                aid = cue.get("aircraftId", "A1")
                flight = next(a["flightInstance"] for a in world["aircraft"] if a["id"] == aid)
                turn = dict(requestId=uuid4().hex, turnId=cue["id"], expectedRevision=session.revision,
                            aircraftId=aid, flightInstance=flight, cutoff=cue["at"], question=cue["assistantQuestion"])
                try:
                    output = run_turn(session, world, turn, adapter, settings)
                except (ValueError, RuntimeError, KeyError) as exc:
                    output = dict(errors=[str(exc)])
                if selected.index(cue) < skip and args.cues == "rest":
                    recorded = False  # asked again only to rebuild memory; the original record stands
                else:
                    recorded = True
                stream.write(json.dumps(dict(exercise=exercise, cue=cue["id"], turn=turn, output=output,
                                             memoryOnly=not recorded)) + "\n")
                stream.flush()
                print(exercise, cue["id"], output.get("errors"), flush=True)


if __name__ == "__main__":
    main()
