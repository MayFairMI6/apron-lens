"""Provision the local assistant into an installed simulator preview, without bundling secrets."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--port',type=int,default=8767)
parser.add_argument('device', help='Simulator UUID')
args = parser.parse_args()
token_path = ROOT / 'work/qwen-server-token.txt'
if not token_path.exists():
    raise SystemExit('Start the local conversation service first.')
container = Path(subprocess.check_output(['xcrun', 'simctl', 'get_app_container', args.device,
    'edu.airfieldresearch.apronlens.simulator', 'data'], text=True).strip())
path = container / 'Documents/assistant-connection.json'
path.parent.mkdir(parents=True, exist_ok=True)
# Restrict permissions before writing the existing local token. Never print its value.
path.touch(mode=0o600, exist_ok=True)
path.chmod(0o600)
path.write_text(json.dumps({'endpoint': f'http://127.0.0.1:{args.port}', 'token': token_path.read_text().strip()}))
print('Local assistant configured for the simulator. No credentials added to the build.')
