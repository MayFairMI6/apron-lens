"""Model choice contract: the evaluated default is unchanged; candidates are pinned and guarded."""
import json,re,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.engines import ROOT,DEFAULT_MODEL,candidates,check_transformers,expected_manifest,model_names
from backend.server import CandidateEngine,create_app

class NoEngine:
 manifest={'model_id':'test-double','revision':'test-only'};device='test'
 def score_labels(self,prompt,image,labels):return {'Yes':-5.,'No':-.1},10

class EngineTests(unittest.TestCase):
 def test_default_is_the_evaluated_manifest(self):
  self.assertEqual(expected_manifest(DEFAULT_MODEL),json.loads((ROOT/'config/model-manifest.json').read_text()))
  self.assertEqual(model_names()[0],DEFAULT_MODEL);self.assertNotIn(DEFAULT_MODEL,candidates())
 def test_candidates_are_pinned_and_complete(self):
  for name,entry in candidates().items():
   self.assertRegex(entry['revision'],r'^[0-9a-f]{40}$',name)
   self.assertIn(entry['dtype'],('float16','bfloat16'),name)
   self.assertRegex(entry['transformers'],r'^>=\d+\.\d+$',name)
   self.assertTrue(entry['source'].endswith(entry['model_id']),name)
   self.assertEqual(set(expected_manifest(name)),{'model_id','revision','source','license'})
 def test_unknown_and_unpinned_rejected(self):
  with self.assertRaises(ValueError):expected_manifest('not-a-model')
  unpinned={'x':dict(next(iter(candidates().values())),revision=None)}
  with patch('backend.engines.candidates',return_value=unpinned),self.assertRaises(ValueError):expected_manifest('x')
 def test_transformers_version_gate(self):
  check_transformers('gemma-4-e4b','5.5.0.dev0');check_transformers('qwen3-vl-4b','4.57.6')
  with self.assertRaises(ValueError):check_transformers('gemma-4-e4b','4.57.6')
  with self.assertRaises(ValueError):check_transformers('qwen3.5-9b','5.1.0')
 def test_wrong_download_refused_before_loading(self):
  name=next(iter(candidates()))
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'download-manifest.json').write_text(json.dumps(dict(expected_manifest(name),revision='0'*40)))
   with patch('backend.server.model_dir',return_value=Path(tmp)),self.assertRaises(ValueError):CandidateEngine(name)
 def test_workflow_offers_every_model(self):
  text=(ROOT/'.github/workflows/model-check.yml').read_text()
  options=re.search(r'model:\n(?:.*\n)*?\s+options:\n((?:\s+- .*\n)+)',text).group(1)
  self.assertEqual([o.strip()[2:] for o in options.splitlines()],model_names())
  self.assertEqual(text,(ROOT/'docs/github-actions/model-check.yml').read_text())
 def test_request_without_image(self):
  body=dict(requestId='test',scenarioId='M1-stand-coordination-01',aircraftId='A2',checkpoint=14)
  with tempfile.TemporaryDirectory() as tmp,patch('backend.server.AUDIT_PATH',Path(tmp)/'audit.jsonl'):
   with TestClient(create_app(NoEngine(),'test-token')) as client:
    r=client.post('/reason',json=body,headers={'Authorization':'Bearer test-token'})
    self.assertEqual(r.status_code,200,r.text);self.assertFalse(r.json()['imageUsedForInference'])
    self.assertEqual(client.post('/reason',json=dict(body,imageBase64=''),headers={'Authorization':'Bearer test-token'}).status_code,422)
   self.assertIsNone(json.loads((Path(tmp)/'audit.jsonl').read_text())['imageSha256'])
if __name__=='__main__':unittest.main()
