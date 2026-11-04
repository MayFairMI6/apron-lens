"""Development score reuse cannot cross into held-out evaluation or source IDs."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from scripts.relation_development_cache import DevelopmentCache, ALLOWED_FIXTURES

class CacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.module=SimpleNamespace(MODEL_ID='test/model',MODEL_REVISION='rev',LABELS=('contradiction','entailment','neutral'),THRESHOLD=.8)
        snapshot=self.root/'.cache/huggingface/hub/models--test--model/snapshots/rev';snapshot.mkdir(parents=True)
        for f in ('model.safetensors','tokenizer.json','config.json'):(snapshot/f).write_text('{}')
        self.path=self.root/'records.jsonl'
        self.row=dict(premise='P',hypothesis='H',probabilities=[.01,.98,.01],modelId='test/model',modelRevision='rev',labelOrder=self.module.LABELS,reportIds=['OLD'])
        self.path.write_text(json.dumps(dict(error=None,pairs=[self.row]))+'\n')
        (self.root/'lock.json').write_text(json.dumps(dict(model='test/model',revision='rev',fixtureSHA256=next(iter(ALLOWED_FIXTURES)))))
        (self.root/'startup.json').write_text(json.dumps(dict(torch='test',device='cpu')))
        self.engine=SimpleNamespace(max_length=512,batch_size=8,tokenizer=lambda *args,**kwargs:{'input_ids':[1,2]},records=[])
        self.sha=next(iter(ALLOWED_FIXTURES))
    def tearDown(self):self.tmp.cleanup()
    def build(self,sha=None):
        with patch('pathlib.Path.home',return_value=self.root),patch('importlib.metadata.version',return_value='test'):
            return DevelopmentCache(self.engine,self.module,[self.path],sha or self.sha)
    def test_reserved_fixture_forbidden(self):
        with self.assertRaisesRegex(ValueError,'prohibited'):self.build('reserved-fixture')
        lock=json.loads((self.root/'lock.json').read_text());lock['fixtureSHA256']='reserved'
        (self.root/'lock.json').write_text(json.dumps(lock))
        with self.assertRaisesRegex(ValueError,'source is not exposed'):self.build()
    def test_only_probabilities_reused_and_provenance_frozen(self):
        cache=self.build()
        rows=cache.score([dict(premise='P',hypothesis='H',reportIds=['CURRENT'],criterionId='new')],100)
        self.assertEqual(rows[0]['reportIds'],['CURRENT']);self.assertEqual(rows[0]['criterionId'],'new')
        self.assertEqual(rows[0]['probabilities'],self.row['probabilities'])
        self.assertIsNone(rows[0]['elapsedSeconds']);self.assertEqual(cache.verify()['actualPairs'],0)
        self.path.write_text('changed')
        with self.assertRaisesRegex(ValueError,'changed'):cache.verify()
    def test_current_token_bound_and_conflicting_label_force_recompute(self):
        cache=self.build();self.engine.tokenizer=lambda *a,**kw:{'input_ids':list(range(513))}
        with self.assertRaisesRegex(ValueError,'token bound'):cache.score([dict(premise='P',hypothesis='H')],100)
        self.engine.tokenizer=lambda *a,**kw:{'input_ids':[1]}
        second=dict(self.row,probabilities=[.98,.01,.01])
        self.path.write_text(json.dumps(dict(error=None,pairs=[self.row,second]))+'\n')
        cache=self.build();seen=[]
        def score(pairs,deadline):
            seen.extend(pairs);return [dict(**p,probabilities=[.1,.8,.1]) for p in pairs]
        self.engine.score=score
        rows=cache.score([dict(premise='P',hypothesis='H')],100)
        self.assertEqual(len(seen),1);self.assertIsNone(rows[0]['scoreReuse']);self.assertEqual(cache.hits,0)
