"""PROCEDURAL: run the locked B06 exposed controls through local Ollama."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from experiments.typed_qwen_frames import claims_v6_control as control

MODEL = "qwen3.5:27b"
PROMPT_SHA256 = "da73694d3c3caeeb08fc43039f64f7edfcd93dfdee32a5e7ad355ea90153b0b1"
INPUT_SHA256 = "0a57f37b255371bc6bab0fa7584fea545e73d4de7a3a5d232223d3ab9cad7df4"
FIXTURE = Path("docs/course/TYPED_QWEN_INITIAL_INPUTS_V1.json")
DEADLINE_SECONDS = 55
OPTIONS = {"num_predict": 1000, "num_ctx": 4096, "temperature": 0, "seed": 17}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def local_api(path, payload=None, timeout=5):
    headers = {} if payload is None else {"Content-Type": "application/json"}
    body = None if payload is None else json.dumps(payload).encode()
    request = Request("http://127.0.0.1:11434/api/" + path, body, headers)
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def generate(messages):
    started = time.monotonic()
    response, error = None, None
    try:
        response = local_api("chat", {
            "model": MODEL, "messages": messages, "stream": False,
            "think": False, "options": OPTIONS,
        }, DEADLINE_SECONDS)
        if (response["model"] != MODEL or response.get("done_reason") != "stop"
                or not response.get("done")):
            error = "unexpected_returned_model_or_non_stop_generation"
    except (URLError, OSError, ValueError, KeyError) as exc:
        error = f"{type(exc).__name__}: {exc}"
    elapsed = time.monotonic() - started
    if elapsed > DEADLINE_SECONDS:
        error = "deadline_exceeded"
    return {"raw": response, "elapsedSeconds": elapsed, "error": error}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    fixture = FIXTURE.read_bytes()
    if digest(Path(control.__file__).read_bytes()) != PROMPT_SHA256 or digest(fixture) != INPUT_SHA256:
        raise RuntimeError("Frozen prompt or learner-only fixture changed")
    model = next(item for item in local_api("tags")["models"] if item["name"] == MODEL)
    args.output.mkdir(parents=True, exist_ok=False)
    lock = {
        "installedModel": model,
        "runtime": local_api("version"),
        "fixtureSHA256": INPUT_SHA256, "controlSHA256": PROMPT_SHA256,
        "deadlineSeconds": DEADLINE_SECONDS, "options": OPTIONS, "thinking": False,
    }
    (args.output / "lock.json").write_text(json.dumps(lock, indent=2) + "\n")
    preflight = generate([{"role": "user", "content": "Reply with the single word ready."}])
    (args.output / "preflight.json").write_text(json.dumps(preflight, indent=2) + "\n")
    if preflight["error"]:
        raise SystemExit("B06 preflight failed. See preflight.json.")
    for case in json.loads(fixture)["cases"]:
        learner = case["learnerResponse"]
        prompt = control.prompt_for(learner)
        row = generate([{"role": "user", "content": prompt}])
        row.update(id=case["id"], promptSHA256=digest(prompt.encode()), parsed=None)
        if row["error"] is None:
            try:
                row["parsed"] = control.parse_frames(row["raw"]["message"]["content"], learner)
            except (ValueError, TypeError, KeyError) as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
        with (args.output / "controls.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        print(case["id"], row["error"] or "valid output", flush=True)
    print("Independent meaning review required before frozen contrasts.", flush=True)


if __name__ == "__main__":
    main()
