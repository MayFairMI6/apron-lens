"""PROCEDURAL: provision a local replay connection inside a debug Android app."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ADB = ROOT / "work/unity-editor/PlaybackEngines/AndroidPlayer/SDK/platform-tools/adb"
PACKAGE = "edu.airfieldresearch.apronlens.replay"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("serial", help="Android target shown in adb devices")
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--adb", type=Path, default=Path(os.environ.get("ADB", ADB)))
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535")

    token = (ROOT / "work/qwen-server-token.txt").read_text().strip()
    if not token:
        raise SystemExit("Start the local replay service first.")

    adb = [str(args.adb), "-s", args.serial]
    subprocess.run([*adb, "shell", "run-as", PACKAGE, "true"], check=True)
    port = f"tcp:{args.port}"
    subprocess.run([*adb, "reverse", port, port], check=True)

    settings = json.dumps({"endpoint": f"http://127.0.0.1:{args.port}", "token": token})
    subprocess.run(
        [*adb, "shell", "-T", f"run-as {PACKAGE} sh -c 'umask 077; mkdir -p files && "
         "cat > files/assistant-connection.json.tmp && "
         "mv files/assistant-connection.json.tmp files/assistant-connection.json'"],
        input=settings, text=True, check=True,
    )
    print("Android replay configured through the private app directory and USB port forwarding.")


if __name__ == "__main__":
    main()
