import copy
import unittest
from scripts.compare_typed_runs import paired_summary

class PairedComparisonTests(unittest.TestCase):
    def rows(self):
        rows=[]
        for i in range(24):
            status='met' if i<12 else 'missing'
            payload=dict(episodeId='e',checkpointId='c',cutoff=10,learnerResponse='The route is blocked.',
                reports=[dict(id='r',episodeId='e',receiptTime=1)],
                criteria=[dict(id='point',evidenceIds=['r'])])
            point=dict(criterionId='point',status=status,comment='Review.',evidenceIds=['r'],
                       learnerQuote=payload['learnerResponse'] if status=='met' else '')
            review=dict(episodeId='e',checkpointId='c',verdict='supported' if status=='met' else 'needs_review',
                        explanation='Review.',points=[point])
            rows.append(dict(index=i,payload=payload,expected={'point':status},review=review,exact=False))
        return rows
    def test_recomputes_from_reviews_not_saved_exact(self):
        rows=self.rows()
        self.assertTrue(paired_summary(rows,rows)['semanticGatePassed'])
    def test_same_total_can_hide_new_failure(self):
        c,b=self.rows(),self.rows()
        c[0]['review']=None;b[1]['review']=None
        result=paired_summary(c,b)
        self.assertEqual(result['newlyFailing'],[0])
        self.assertFalse(result['semanticGatePassed'])
    def test_false_credit_blocks_even_when_valid_pass(self):
        c,b=self.rows(),self.rows();c[20]['review']['points'][0].update(status='met',learnerQuote='The route is blocked.');c[20]['review']['verdict']='supported'
        self.assertFalse(paired_summary(c,b)['gates']['zeroFalseCredit'])
    def test_mismatched_labels_inputs_or_duplicate_refused(self):
        for mode in ('expected','payload','duplicate'):
            c,b=self.rows(),self.rows()
            if mode=='duplicate':c[1]['index']=0
            else:c[0][mode]={'changed':True}
            with self.assertRaises(ValueError):paired_summary(c,b)
    def test_duplicate_points_are_rejected(self):
        c,b=self.rows(),self.rows()
        c[0]['review']['points'].append(copy.deepcopy(c[0]['review']['points'][0]))
        with self.assertRaises(ValueError):paired_summary(c,b)
    def test_invalid_quote_list_is_rejected(self):
        c,b=self.rows(),self.rows()
        c[0]['review']['points'][0]['learnerQuotes']=['The route','The route']
        with self.assertRaises(ValueError):paired_summary(c,b)
    def test_declared_multi_quote_requires_list(self):
        rows=self.rows()
        with self.assertRaises(ValueError):paired_summary(rows,rows,candidate_multi_quote=True)
        candidate=copy.deepcopy(rows)
        for row in candidate:
            point=row['review']['points'][0]
            point['learnerQuotes']=[point['learnerQuote']] if point['learnerQuote'] else []
        self.assertTrue(paired_summary(candidate,rows,candidate_multi_quote=True)['semanticGatePassed'])
