import json,unittest
from experiments.typed_review_lora.build_data import cases
from experiments.typed_review_lora.evaluate import score
from scripts.report_typed_lora import audit

class LoraReportTests(unittest.TestCase):
    def fixture(self):
        row=next(cases('stand_occupancy',0));raw=json.dumps(row['target'])
        records=[dict(id=row['id'],family=row['family'],kind=row['kind'],arm=arm,raw=raw,score=score(raw,row),elapsed=1,input_tokens=10,output_tokens=20,stop_reason='eos',error=None) for arm in ('base','adapter')]
        return [row],records
    def test_complete_paired_records(self):
        data,records=self.fixture();r=audit(data,records)
        self.assertEqual(r['base']['confusion'],{'met -> met':3})
    def test_partial_and_duplicate_results_rejected(self):
        data,records=self.fixture()
        for bad in [records[:1],records+records[:1]]:
            with self.assertRaises(ValueError):audit(data,bad)
    def test_changed_score_rejected(self):
        data,records=self.fixture();records[0]['score']['exact']=False
        with self.assertRaises(ValueError):audit(data,records)
