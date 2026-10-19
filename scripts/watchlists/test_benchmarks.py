import json
import unittest
from benchmarks import parse_rr, parse_openpostdoc, op_in_scope, merge, rr_key, normalize_paper, stage_unverified_jobs

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

    def test_unverified_new_board_job_stays_in_review_queue(self):
        job={'id':'new','title':'Postdoc in Economics','institution':'University',
             'apply_url':'https://example.org/job','last_verified':'',
             'verification':'Reference-listed; employer verification pending',
             'reference_ids':['openpostdoc:new']}
        public,queue=stage_unverified_jobs([job],set(),[],'2026-10-19')
        self.assertEqual(public,[])
        self.assertEqual(queue[0]['reference_ids'],['openpostdoc:new'])
        self.assertEqual(queue[0]['candidate'],job)

    def test_employer_verified_new_job_is_public_and_existing_records_remain(self):
        old={'id':'old','title':'Earlier advert','last_verified':''}
        verified={'id':'new','title':'Postdoc','last_verified':'2026-10-19',
                  'verification':'Employer-published EJM advertisement'}
        public,queue=stage_unverified_jobs([old,verified],{'old'},[],'2026-10-19')
        self.assertEqual(public,[old,verified])
        self.assertEqual(queue,[])

    def test_employer_crosspost_resolves_reference_only_provenance(self):
        old={'id':'old','apply_url':'https://example.org/job','reference_ids':['op:1'],
             'source_reports':[],'verification':'Reference-listed; employer verification pending'}
        new={'id':'new','apply_url':'https://example.org/job','reference_ids':['ejm:1'],
             'source_reports':[],'source_type':'Econ Job Market employer advert',
             'source_url':'https://econjobmarket.org/positions/1',
             'deadline':'2026-11-15','status':'open','last_verified':'2026-10-19',
             'verification':'Employer-published EJM advertisement'}
        merged=merge([old],[new],'jobs')[0]
        self.assertEqual(merged['verification'],new['verification'])
        self.assertEqual(merged['source_url'],new['source_url'])

if __name__=='__main__':unittest.main()
