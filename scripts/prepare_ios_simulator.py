"""Create a disposable Unity project for iOS Simulator UI/replay checks.

The source project and its Android settings are preserved. Vuforia is omitted
because this player uses an explicitly simulated scene, not camera tracking.
"""
import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    destination = args.destination.resolve()
    if destination.exists():
        raise SystemExit("Destination exists; choose a fresh directory.")
    source = ROOT / "unity/SurfaceSafetyCoach"
    for directory in ("Assets", "Packages", "ProjectSettings"):
        shutil.copytree(source / directory, destination / directory,
                        ignore=shutil.ignore_patterns("*.tgz", "VuforiaConfiguration.asset*", "QwenConnection.local.json*"))
    manifest = destination / "Packages/manifest.json"
    data = json.loads(manifest.read_text())
    data["dependencies"].pop("com.ptc.vuforia.engine", None)
    manifest.write_text(json.dumps(data, indent=2) + "\n")
    lock = destination / "Packages/packages-lock.json"
    if lock.exists():
        data = json.loads(lock.read_text())
        data["dependencies"].pop("com.ptc.vuforia.engine", None)
        lock.write_text(json.dumps(data, indent=2) + "\n")
    with (destination / "Assets/csc.rsp").open("a") as stream:
        stream.write("\n-define:APRONLENS_SIMULATOR\n")
    print(destination)

if __name__ == "__main__":
    main()
