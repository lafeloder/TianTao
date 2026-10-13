import json
import unittest
from benchmarks import parse_rr, parse_openpostdoc, op_in_scope, merge, rr_key, normalize_paper

class BenchmarkTests(unittest.TestCase):
    def test_full_rr_array_and_date(self):
        row={'scholar':'Author One','title':'A Corporate Finance Paper','coauthors':[],'journal':'Journal of Finance','status':'Reject & Resubmit','url':'https://example.com/research'}
        page='Updated 2026-09-29<script>const data='+json.dumps([row])+';const esc=s=>s;</script>'
        out=parse_rr(page)
        self.assertEqual(out['source_updated'],'2026-09-29')
        self.assertEqual(len(out['rows']),1)
        self.assertEqual(out['rows'][0]['status'],'Reject & Resubmit')

    def test_reference_ids_survive_paper_deduplication(self):
        old={'title':'Same Paper','status':'Accepted','reference_ids':['first'], 'last_verified':'2026-10-12'}
        new={'title':'Same Paper','status':'R&R','reference_ids':['second'],'reference_checked_on':'2026-10-12'}
        result=merge([old],[new],'papers')
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['reference_ids'],['first','second'])
        self.assertEqual(result[0]['status'],'Accepted')

    def test_management_science_reference_joins_tracked_scope(self):
        row={'scholar':'Author One','title':'A Finance Paper','coauthors':[],
             'journal':'Management Science','status':'R&R','url':'https://example.com/research'}
        paper=normalize_paper(row,{'source_updated':'2026-10-12','checked_on':'2026-10-12'})
        self.assertEqual(paper['journal'],'MS')
        self.assertEqual(paper['source_scope'],'top5')

    def test_existing_management_science_paper_is_promoted(self):
        old={'title':'A Finance Paper','journal':'MS','source_scope':'extended','scope':'extended',
             'reference_ids':['first']}
        new={'title':'A Finance Paper','journal':'MS','source_scope':'top5','reference_ids':['second']}
        merged=merge([old],[new],'papers')[0]
        self.assertEqual((merged['source_scope'],merged['scope']),('top5','top5'))

    def test_public_rsc_data(self):
        body='1:'+json.dumps({'positions':[{'id':'job1','title':'Postdoc in Economics'}],'total':1,'pageCount':1})
        page='<script>self.__next_f.push('+json.dumps([1,body])+')</script>'
        rows,meta=parse_openpostdoc(page)
        self.assertEqual(rows[0]['id'],'job1')
        self.assertEqual(meta['total'],1)

    def test_distinct_employer_adverts_with_identical_titles_survive(self):
        common={'title':'Postdoctoral Research Assistant in Quantitative Finance',
                'institution':'University of Oxford','deadline':'2026-11-19',
                'source_type':'OpenPostdoc','source_reports':[]}
        first={**common,'id':'oxford-188851','apply_url':'https://my.corehr.com/job?p_recruitment_id=188851','reference_ids':['openpostdoc:first']}
        second={**common,'id':'oxford-188853','apply_url':'https://my.corehr.com/job?p_recruitment_id=188853','reference_ids':['openpostdoc:second']}
        result=merge([first,second],[{**second,'title':'Revised advert title'}],'jobs')
        self.assertEqual(len(result),2)
        self.assertEqual({r['id'] for r in result},{'oxford-188851','oxford-188853'})

    def test_matching_employer_url_merges_crossposts(self):
        common={'title':'Research Fellow','institution':'Oxford','deadline':'2026-11-19',
                'source_type':'OpenPostdoc','source_reports':[]}
        first={**common,'id':'first','apply_url':'https://example.org/job?b=2&a=1','reference_ids':['openpostdoc:first']}
        second={**common,'id':'second','apply_url':'https://example.org/job?a=1&b=2','reference_ids':['openpostdoc:second']}
        result=merge([first],[second],'jobs')
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['reference_ids'],['openpostdoc:first','openpostdoc:second'])

    def test_scope_does_not_inflate_with_mislabeled_engineering(self):
        self.assertFalse(op_in_scope({'region':'eu','primaryField':'Economics','title':'Mechanical design of flexure mechanisms'}))
        self.assertFalse(op_in_scope({'region':'us','primaryField':'Economics','title':'Postdoc in Economics'}))
        self.assertTrue(op_in_scope({'region':'eu','primaryField':'Economics','title':'Postdoc in Labour Economics'}))

if __name__=='__main__':unittest.main()
