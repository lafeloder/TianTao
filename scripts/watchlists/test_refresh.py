import datetime as dt
import unittest
from bootstrap import publication_date
from refresh import rr_blocks, journal_in, extract_deadline, job_status, find_paper_block, homepage_coverage, finance_top5_homepage_coverage, research_links, ms_author_ledger

class EvidenceTests(unittest.TestCase):
    def test_reject_is_not_revise(self):
        html='<li><h3><a href="/p.pdf">Corporate Debt and Financial Crises</a></h3>Reject and Resubmit, Journal of Finance</li>'
        self.assertEqual(rr_blocks(html,'https://author.example/'),[])

    def test_neighbouring_status_stays_with_its_paper(self):
        html='<h3><a href="/a.pdf">An Unrelated Working Paper</a></h3><p>No decision</p><h3><a href="/b.pdf">A Confirmed Banking Paper</a></h3><p>Revise and Resubmit, Review of Finance</p>'
        result=rr_blocks(html,'https://author.example/')
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['title'],'A Confirmed Banking Paper')
        self.assertEqual(result[0]['journal'],'RF')
        block=find_paper_block(html,'An Unrelated Working Paper',['An Unrelated Working Paper','A Confirmed Banking Paper'])
        self.assertNotIn('Revise',block)

    def test_first_journal_wins(self):
        self.assertEqual(journal_in('Revise and resubmit, Review of Finance. Publications: Journal of Financial Economics'),'RF')

    def test_management_science_is_tracked(self):
        html='<li><h3><a href="/ms.pdf">A Confirmed Management Paper</a></h3>Revise and Resubmit, Management Science</li>'
        result=rr_blocks(html,'https://author.example/')
        self.assertEqual([(p['title'],p['journal']) for p in result],[('A Confirmed Management Paper','MS')])

    def test_homepage_coverage_deduplicates_name_groups(self):
        universe=[{'name':'A. Author'},{'name':'A Author'},{'name':'B Author'}]
        homes=[{'name':'A. Author','url':'https://example.com','approved':True,
                'eligibility':{'doi':'10.1234/paper'}}]
        corpus={'works':[{'doi':'10.1234/paper'}]}
        self.assertEqual(homepage_coverage(universe,homes,corpus)['percent'],50.0)

    def test_finance_top5_coverage_excludes_ms_only_authors(self):
        universe=[{'name':'Finance Author','publications':[{'doi':'10.1/jf','journal':'JF'}]},
                  {'name':'Management Author','publications':[{'doi':'10.1/ms','journal':'MS'}]}]
        homes=[{'name':'Finance Author','url':'https://example.com/finance','approved':True,
                'eligibility':{'doi':'10.1/jf'}},
               {'name':'Management Author','url':'https://example.com/management','approved':True,
                'eligibility':{'doi':'10.1/ms'}}]
        corpus={'works':[{'doi':'10.1/jf','journal':'JF'},{'doi':'10.1/ms','journal':'MS'}]}
        result=finance_top5_homepage_coverage(universe,homes,corpus)
        self.assertEqual((result['linked_authors'],result['author_rows'],result['percent']),(1,1,100.0))

    def test_research_links_stay_on_author_site(self):
        body='<a href="/view/alice-finance/research">Research</a><a href="/view/bob-finance/research">Research</a><a href="https://other.example/research">Papers</a>'
        self.assertEqual(research_links(body,'https://sites.google.com/view/alice-finance/'),
                         ['https://sites.google.com/view/alice-finance/research'])

    def test_ms_ledger_keeps_unresolved_authors(self):
        universe=[{'name':'A. Author','publications':[{'doi':'10.1/ms','journal':'MS'}]},
                  {'name':'B Author','publications':[{'doi':'10.1/jf','journal':'JF'}]}]
        ledger,summary=ms_author_ledger(universe,[],{'ms_search_done':['aauthor'],
                                      'ms_search_checked_on':'2026-10-13'},'2026-10-13')
        self.assertEqual(summary['author_name_groups'],1)
        self.assertEqual(summary['searched_by_name'],1)
        self.assertEqual(ledger['authors'][0]['homepage_status'],'unresolved')

    def test_deadline_not_start(self):
        self.assertEqual(extract_deadline('Starts 1 November 2026. Application deadline: 21 October 2026'),'2026-10-21')
        self.assertEqual(extract_deadline('Start date: 1 November 2026'),'')
        self.assertEqual(extract_deadline('Apply now until 26.11.2026'),'2026-11-26')

    def test_unknown_date_does_not_mean_open(self):
        self.assertEqual(job_status({'source_type':'Official website'},'Postdoctoral researcher in economics','2026-10-12'),'deadline unknown')
        self.assertEqual(job_status({'deadline':'2026-10-11'},'Postdoctoral researcher','2026-10-12'),'closed')
        self.assertEqual(job_status({'deadline':'2026-11-26','source_type':'LinkedIn'},'Postdoctoral researcher','2026-10-12'),'needs official confirmation')

    def test_first_publication_not_deposit(self):
        item={'published-online':{'date-parts':[[2021,9,10]]},'published-print':{'date-parts':[[2022,1]]},'deposited':{'date-parts':[[2026,10,12]]}}
        self.assertEqual(publication_date(item),dt.date(2021,9,10))

if __name__=='__main__':unittest.main()
