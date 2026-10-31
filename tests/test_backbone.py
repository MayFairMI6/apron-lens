"""Shared-backbone contract: frozen evaluated model, pinned candidates, explicit runtime, enforced boundary."""
import hashlib,importlib,json,re,subprocess,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from backbone import (PRIMARY_MODEL,VLMEngine,check_transformers,expected_manifest,load_engine,model_entry,model_names,
                      pick_device,pick_dtype,resolve_runtime,runtime_profile,runtime_profiles)
ROOT=Path(__file__).resolve().parents[1]

def fake_torch(cuda,bf16=True,mps=False):
 return SimpleNamespace(float32='f32',float16='f16',bfloat16='bf16',
  cuda=SimpleNamespace(is_available=lambda:cuda,is_bf16_supported=lambda:bf16),
  backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda:mps)))

class BackboneTests(unittest.TestCase):
 def test_primary_is_the_evaluated_manifest(self):
  # config/model-manifest.json stays the frozen V2 record; the backbone must match it exactly.
  self.assertEqual(expected_manifest(PRIMARY_MODEL),json.loads((ROOT/'config/model-manifest.json').read_text()))
  self.assertEqual(model_names()[0],PRIMARY_MODEL);self.assertEqual(model_entry(PRIMARY_MODEL)['role'],'primary')
  self.assertEqual(model_entry(PRIMARY_MODEL)['local_dir'],'Qwen2.5-VL-3B-Instruct')
 def test_frozen_server_is_untouched_and_independent(self):
  # The V2 evaluation's server must equal its frozen source snapshot and never import the backbone.
  protocol=json.loads((ROOT/'outputs/reasoning_v2/protocol.json').read_text())
  source=(ROOT/'backend/server.py').read_bytes()
  self.assertEqual(hashlib.sha256(source).hexdigest(),protocol['sources']['backend/server.py'])
  self.assertNotIn(b'backbone',source)
 def test_apronlens_profile_matches_frozen_server(self):
  source=(ROOT/'backend/server.py').read_text()
  self.assertIn("attn_implementation='eager'",source);self.assertIn("torch.float16 if self.device == 'mps'",source)
  self.assertEqual(runtime_profile('apronlens-v2-mps'),dict(device='mps',dtype='float16',attn_implementation='eager'))
 def test_runtime_profiles_are_complete(self):
  for name in runtime_profiles():
   profile=runtime_profile(name)
   self.assertIn(profile['device'],('mps','cuda','cpu'),name);self.assertIn(profile['dtype'],('float16','bfloat16','float32'),name)
   self.assertIn(profile['attn_implementation'],('eager','sdpa'),name)
  self.assertEqual(runtime_profile('compaction-gaivi-cuda'),dict(device='cuda',dtype='float16',attn_implementation='sdpa'))
  with self.assertRaises(ValueError):runtime_profile('auto')
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
    with patch('backbone.engine.model_dir',return_value=Path(tmp)),self.assertRaises(ValueError):
     VLMEngine(name,**runtime_profile('cpu-float32'))
 def test_engine_requires_an_explicit_runtime(self):
  with self.assertRaises(TypeError):VLMEngine(PRIMARY_MODEL)
  with self.assertRaises(ValueError):load_engine(PRIMARY_MODEL)
  with self.assertRaises(ValueError):load_engine(PRIMARY_MODEL,device='mps')
  with self.assertRaises(ValueError):load_engine(PRIMARY_MODEL,profile='apronlens-v2-mps',device='cpu')
 def test_runtime_is_validated_without_fallback(self):
  self.assertEqual(resolve_runtime(fake_torch(False,mps=True),'mps','float16','eager'),('mps','f16','eager'))
  self.assertEqual(resolve_runtime(fake_torch(True),'cuda','float16','sdpa'),('cuda','f16','sdpa'))
  with self.assertRaises(RuntimeError):resolve_runtime(fake_torch(False,mps=False),'mps','float16','eager')
  with self.assertRaises(RuntimeError):resolve_runtime(fake_torch(False,mps=True),'cuda','float16','eager')
  with self.assertRaises(RuntimeError):resolve_runtime(fake_torch(True,bf16=False),'cuda','bfloat16','eager')
  for bad in (('auto','float16','eager'),('mps','half','eager'),('mps','float16','flash')):
   with self.assertRaises(ValueError):resolve_runtime(fake_torch(False,mps=True),*bad)
 def test_device_and_dtype_suggestions(self):
  # Suggestions for interactive use only; engines never call them.
  self.assertEqual(pick_device(fake_torch(True,mps=True)),'cuda');self.assertEqual(pick_device(fake_torch(False,mps=True)),'mps')
  self.assertEqual(pick_device(fake_torch(False)),'cpu')
  self.assertEqual(pick_dtype(fake_torch(False,mps=True),'mps'),'f16');self.assertEqual(pick_dtype(fake_torch(True),'cuda'),'bf16')
  self.assertEqual(pick_dtype(fake_torch(True,bf16=False),'cuda'),'f16');self.assertEqual(pick_dtype(fake_torch(False),'cpu'),'f32')
  self.assertEqual(pick_dtype(fake_torch(False,mps=True),'mps','bfloat16'),'bf16')
  engine_source=(ROOT/'backbone/engine.py').read_text()
  self.assertNotIn('pick_device',engine_source);self.assertNotIn('pick_dtype',engine_source)
 def test_boundary_holds(self):
  run=subprocess.run([sys.executable,'-m','backbone.check','--project','backend','scripts','tests','modelaccess'],cwd=ROOT,capture_output=True,text=True)
  self.assertEqual(run.returncode,0,run.stdout+run.stderr)
 def test_boundary_violations_detected(self):
  check=importlib.import_module('backbone.check')  # tooling, deliberately outside the public interface
  with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
   Path(tmp,'bad.py').write_text('from backbone.registry import _models\nfrom backbone import REGISTRY_PATH\n')
   errors=check.project_errors([Path(tmp).name])
  self.assertEqual(len(errors),2,errors)
 def test_gaivi_jobs_use_class_partition_and_require_runtime(self):
  for job in ('download_models','model_check'):
   self.assertIn('#SBATCH --partition=ClsGenAI',(ROOT/f'scripts/gaivi/{job}.sbatch').read_text())
  self.assertIn('RUNTIME="${RUNTIME:?',(ROOT/'scripts/gaivi/model_check.sbatch').read_text())
 def test_workflow_offers_every_model_and_a_runtime(self):
  text=(ROOT/'.github/workflows/model-check.yml').read_text()
  options=re.search(r'model:\n(?:.*\n)*?\s+options:\n((?:\s+- .*\n)+)',text).group(1)
  self.assertEqual([o.strip()[2:] for o in options.splitlines()],model_names())
  runtimes=re.search(r'runtime:\n(?:.*\n)*?\s+options:\n((?:\s+- .*\n)+)',text).group(1)
  self.assertTrue(set(o.strip()[2:] for o in runtimes.splitlines())<=set(runtime_profiles()))
  self.assertIn('--runtime "$AIRFIELD_CHECK_RUNTIME"',text)
  for name in ('model-check.yml','checks.yml'):
   self.assertEqual((ROOT/'.github/workflows'/name).read_text(),(ROOT/'docs/github-actions'/name).read_text())
if __name__=='__main__':unittest.main()
