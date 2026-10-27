"""Verify the final M1 APK package; does not claim an Android runtime test."""
import hashlib
import json
import os
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tools = Path(os.environ.get("UNITY_ANDROID_TOOLS", str(ROOT / "work/unity-editor/PlaybackEngines/AndroidPlayer")))
apk = ROOT / "outputs/milestone1/AirfieldCoordination-M1.apk"
env = dict(os.environ, JAVA_HOME=str(tools / "OpenJDK"))
sign = subprocess.run([str(tools / "SDK/build-tools/34.0.0/apksigner"), "verify", "--verbose", str(apk)],
                      capture_output=True, text=True, env=env, check=True)
badging = subprocess.run([str(tools / "SDK/build-tools/34.0.0/aapt"), "dump", "badging", str(apk)],
                         capture_output=True, text=True, check=True).stdout
assert "com.unity3d.player.UnityPlayerActivity" in badging
assert "sdkVersion:'29'" in badging
assert "native-code: 'arm64-v8a'" in badging
assert "android.permission.CAMERA" in badging
assert "android.permission.INTERNET" in badging
assert "versionName='1.3'" in badging and "versionCode='4'" in badging
manifest = subprocess.run([str(tools / "SDK/build-tools/34.0.0/aapt"), "dump", "xmltree", str(apk), "AndroidManifest.xml"],
                          capture_output=True, text=True, check=True).stdout
assert any("usesCleartextTraffic" in line and "0xffffffff" in line for line in manifest.splitlines())
with zipfile.ZipFile(apk) as archive:
    assert archive.testzip() is None
    assert any("vuforia" in n.lower() and n.startswith("lib/arm64-v8a/") for n in archive.namelist())
result = {
    "status": "build_and_package_checks_passed",
    "apk": apk.name,
    "bytes": apk.stat().st_size,
    "sha256": hashlib.sha256(apk.read_bytes()).hexdigest(),
    "abi": "arm64-v8a",
    "version": "1.3",
    "version_code": 4,
    "minimum_android_api": 29,
    "target_android_api": 35,
    "launch_activity": "com.unity3d.player.UnityPlayerActivity",
    "signature_verified": True,
    "zip_integrity_verified": True,
    "development_local_http_enabled": True,
    "physical_device_test": "deferred_by_user",
    "tracking_test": "pending",
}
(apk.parent / "android-build-verification.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
