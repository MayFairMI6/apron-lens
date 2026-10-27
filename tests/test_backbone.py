"""Shared-backbone contract: frozen evaluated model, pinned candidates, enforced boundary."""
import importlib,json,re,subprocess,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from fastapi.testclient import TestClient
from backbone import PRIMARY_MODEL,VLMEngine,check_transformers,expected_manifest,model_entry,model_names,pick_device,pick_dtype
from backend.server import LocalQwen,create_app
ROOT=Path(__file__).resolve().parents[1]

class NoEngine:
 manifest={'model_id':'test-double','revision':'test-only'};device='test'
 def score_labels(self,prompt,image,labels):return {'Yes':-5.,'No':-.1},10

class BackboneTests(unittest.TestCase):
 def test_primary_is_the_evaluated_manifest(self):
  # config/model-manifest.json stays the frozen V2 record; the backbone must match it exactly.
  self.assertEqual(expected_manifest(PRIMARY_MODEL),json.loads((ROOT/'config/model-manifest.json').read_text()))
  self.assertEqual(model_names()[0],PRIMARY_MODEL);self.assertEqual(model_entry(PRIMARY_MODEL)['role'],'primary')
  self.assertEqual(model_entry(PRIMARY_MODEL)['local_dir'],'Qwen2.5-VL-3B-Instruct');self.assertIs(LocalQwen,VLMEngine)
 def test_models_are_pinned_and_complete(self):
  roles=[model_entry(n)['role'] for n in model_names()]
  self.assertEqual(roles.count('primary'),1);self.assertEqual(roles.count('robustness'),1)
  for name in model_names():
   entry=model_entry(name)
   self.assertRegex(entry['revision'],r'^[0-9a-f]{40}$',name)
   self.assertIn(entry['dtype'],('float16','bfloat16'),name);self.assertIn(entry['loader'],('qwen2_5_vl','auto'),name)
   self.assertRegex(entry['transformers'],r'^>=\d+\.\d+$',name)
   self.assertTrue(entry['source'].endswith(entry['model_id']),name)
   self.assertEqual(set(expected_manifest(name)),{'model_id','revision','source','license'})
 def test_unknown_and_unpinned_rejected(self):
  with self.assertRaises(ValueError):expected_manifest('not-a-model')
  unpinned={'x':dict(model_entry(PRIMARY_MODEL),revision=None)}
  with patch('backbone.registry._models',return_value=unpinned),self.assertRaises(ValueError):expected_manifest('x')
 def test_transformers_version_gate(self):
  check_transformers('gemma-4-e4b','5.5.0.dev0');check_transformers('qwen3-vl-4b','4.57.6');check_transformers(PRIMARY_MODEL,'4.57.6')
  with self.assertRaises(ValueError):check_transformers('gemma-4-e4b','4.57.6')
  with self.assertRaises(ValueError):check_transformers('qwen3.5-9b','5.1.0')
 def test_wrong_download_refused_before_loading(self):
  for name in (PRIMARY_MODEL,'qwen3-vl-4b'):
   with tempfile.TemporaryDirectory() as tmp:
    Path(tmp,'download-manifest.json').write_text(json.dumps(dict(expected_manifest(name),revision='0'*40)))
    with patch('backbone.engine.model_dir',return_value=Path(tmp)),self.assertRaises(ValueError):VLMEngine(name)
 def test_device_and_dtype_choice(self):
  def torch(cuda,bf16=True,mps=False):
   return SimpleNamespace(float32='f32',float16='f16',bfloat16='bf16',
    cuda=SimpleNamespace(is_available=lambda:cuda,is_bf16_supported=lambda:bf16),
    backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda:mps)))
  self.assertEqual(pick_device(torch(True,mps=True)),'cuda');self.assertEqual(pick_device(torch(False,mps=True)),'mps')
  self.assertEqual(pick_device(torch(False)),'cpu')
  # The evaluated Mac path keeps float16; NVIDIA prefers bfloat16; CPU stays float32.
  self.assertEqual(pick_dtype(torch(False,mps=True),'mps'),'f16');self.assertEqual(pick_dtype(torch(True),'cuda'),'bf16')
  self.assertEqual(pick_dtype(torch(True,bf16=False),'cuda'),'f16');self.assertEqual(pick_dtype(torch(False),'cpu'),'f32')
  self.assertEqual(pick_dtype(torch(False,mps=True),'mps','bfloat16'),'bf16')
 def test_boundary_holds(self):
  run=subprocess.run([sys.executable,'-m','backbone.check','--project','backend','scripts','tests'],cwd=ROOT,capture_output=True,text=True)
  self.assertEqual(run.returncode,0,run.stdout+run.stderr)
 def test_boundary_violations_detected(self):
  check=importlib.import_module('backbone.check')  # tooling, deliberately outside the public interface
  with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
   Path(tmp,'bad.py').write_text('from backbone.registry import _models\nfrom backbone import REGISTRY_PATH\n')
   errors=check.project_errors([Path(tmp).name])
  self.assertEqual(len(errors),2,errors)
 def test_gaivi_jobs_use_class_partition(self):
  for job in ('download_models','model_check'):
   self.assertIn('#SBATCH --partition=ClsGenAI',(ROOT/f'scripts/gaivi/{job}.sbatch').read_text())
 def test_workflow_offers_every_model(self):
  text=(ROOT/'.github/workflows/model-check.yml').read_text()
  options=re.search(r'model:\n(?:.*\n)*?\s+options:\n((?:\s+- .*\n)+)',text).group(1)
  self.assertEqual([o.strip()[2:] for o in options.splitlines()],model_names())
  for name in ('model-check.yml','checks.yml'):
   self.assertEqual((ROOT/'.github/workflows'/name).read_text(),(ROOT/'docs/github-actions'/name).read_text())
 def test_request_without_image(self):
  body=dict(requestId='test',scenarioId='M1-stand-coordination-01',aircraftId='A2',checkpoint=14)
  with tempfile.TemporaryDirectory() as tmp,patch('backend.server.AUDIT_PATH',Path(tmp)/'audit.jsonl'):
   with TestClient(create_app(NoEngine(),'test-token')) as client:
    r=client.post('/reason',json=body,headers={'Authorization':'Bearer test-token'})
    self.assertEqual(r.status_code,200,r.text);self.assertFalse(r.json()['imageUsedForInference'])
    self.assertEqual(client.post('/reason',json=dict(body,imageBase64=''),headers={'Authorization':'Bearer test-token'}).status_code,422)
   self.assertIsNone(json.loads((Path(tmp)/'audit.jsonl').read_text())['imageSha256'])
if __name__=='__main__':unittest.main()
