import datetime as dt
import unittest
from bootstrap import publication_date
from refresh import rr_blocks, journal_in, extract_deadline, job_status, find_paper_block, homepage_coverage, finance_top5_homepage_coverage, research_links, ms_author_ledger, author_eligibility, listed_homepages

class EvidenceTests(unittest.TestCase):
    def test_journal_name_spans_and_ampersand(self):
        self.assertEqual(journal_in('Revise & Resubmit, Management Scie nc e'),'MS')
        self.assertEqual(journal_in('Journal of Financial & Quantitative Analysis, R&R'),'JFQA')
    def test_ampersand_revision_and_abbreviated_journal(self):
        body='<div><a href="/paper.pdf">The Pricing of Property Tax Revenues</a><p>Revise &amp; Resubmit, JFE</p></div>'
        self.assertEqual([(r['title'],r['journal'])for r in rr_blocks(body,'https://author.example/')],[('The Pricing of Property Tax Revenues','JFE')])

    def test_heading_wins_over_coauthor_anchor(self):
        body='<article><h3>Tunneling and Hidden Profits in Health Care</h3><a href="/andrew">Andrew Olenski</a><p>Revise &amp; Resubmit, Journal of Finance</p></article>'
        rows=rr_blocks(body,'https://author.example/')
        self.assertEqual({r['title']for r in rows},{'Tunneling and Hidden Profits in Health Care'})

    def test_div_cannot_borrow_a_different_papers_status(self):
        body='<div><a href="/a.pdf">A Paper Without a Decision</a><a href="/b.pdf">A Confirmed Finance Paper</a><p>R&amp;R, JFE</p></div>'
        self.assertEqual(rr_blocks(body,'https://author.example/'),[])

    def test_ampersand_rejection_is_separate(self):
        body='<li><a href="/p.pdf">A Paper With Rejection and Resubmission</a>Reject &amp; Resubmit, Journal of Finance</li>'
        self.assertEqual(rr_blocks(body,'https://author.example/'),[])

    def test_research_content_inside_navigation_wrapper_is_not_discarded(self):
        html='<nav><h1>Alice Author</h1><p>Professor of Finance</p><ul><li><a href="/paper.pdf">A Confirmed Corporate Finance Paper</a> Revise and Resubmit, Journal of Finance</li></ul></nav>'
        self.assertEqual([(r['title'],r['journal'])for r in rr_blocks(html,'https://author.example/')],[('A Confirmed Corporate Finance Paper','JF')])

    def test_google_sites_title_and_status_in_adjacent_lists(self):
        html='<ol><li><p><a href="https://papers.ssrn.com/abstract=5025423">Where to Hire? Political Alignment and Internal Labor Allocation</a> (with Wanyi Wang)</p></li></ol><ul><li>Journal of Financial and Quantitative Analysis, Revise and Resubmit</li></ul>'
        rows=rr_blocks(html,'https://sites.google.com/view/linghang-zeng')
        self.assertEqual([(r['title'],r['journal']) for r in rows],[('Where to Hire? Political Alignment and Internal Labor Allocation','JFQA')])

    def test_adjacent_paper_status_is_not_bridged(self):
        html='<ul><li><a href="/a.pdf">An Unrelated Working Paper</a></li><li><a href="/b.pdf">A Confirmed Banking Paper</a> Revise and Resubmit, Review of Finance</li></ul>'
        self.assertEqual([r['title']for r in rr_blocks(html,'https://author.example')],['A Confirmed Banking Paper'])

    def test_school_profile_follows_explicit_external_personal_site(self):
        html='<a href="https://sites.google.com/view/linghang-zeng">Personal Website</a><a href="https://coauthor.example/research">Papers</a>'
        self.assertEqual(research_links(html,'https://www.babson.edu/faculty/linghang-zeng.php'),['https://sites.google.com/view/linghang-zeng'])

    def test_fixed_watchlist_keeps_aliases_without_admitting_new_authors(self):
        homes=[{'name':'A. Student'},{'name':'A New Author'}]
        roster=[{'name':'Alice Student','name_keys':['astudent']}]
        self.assertEqual(listed_homepages(homes,roster),[{'name':'A. Student'}])

    def test_fixed_roster_preferred_personal_site_is_added_once(self):
        homes=[{'name':'A. Student','url':'https://school.example/alice','approved':True,'eligibility':{'doi':'10.1/paper'}}]
        roster=[{'name':'Alice Student','name_keys':['astudent'],'homepage_url':'https://alice.example','alternate_urls':['https://school.example/alice']}]
        selected=listed_homepages(homes,roster)
        self.assertEqual(len(selected),2)
        self.assertEqual(listed_homepages(selected,roster),selected)

    def test_rejected_old_source_is_not_reintroduced_by_weekly_scan(self):
        homes=[{'name':'Alice Student','url':'https://index.example/alice','approved':True}]
        roster=[{'name':'Alice Student','homepage_url':'https://alice.example','alternate_urls':[]}]
        self.assertEqual([h['url']for h in listed_homepages(homes,roster)],['https://alice.example'])
        self.assertEqual(listed_homepages(homes,[{'name':'Alice Student','homepage_url':'','alternate_urls':[]}]),[])

    def test_newly_linked_fixed_author_enters_weekly_scan(self):
        roster=[{'name':'Doruk Gunaydin','name_keys':['adorukgunaydin','dorukgunaydin'],
                 'homepage_url':'https://dorukgunaydin.com/','homepage_linked_on':'2026-10-14'}]
        selected=listed_homepages([],roster)
        self.assertEqual(len(selected),1)
        self.assertTrue(selected[0]['approved'])
        self.assertEqual(selected[0]['url'],roster[0]['homepage_url'])
        self.assertEqual(listed_homepages(selected,roster),selected)
        publication={'doi':'10.1016/j.jfineco.2023.103715','published':'2023-11-01','journal':'JFE'}
        proof,_=author_eligibility(selected[0],[{'name':'A. Doruk Gunaydin','publications':[publication]}],[])
        self.assertEqual(proof,publication)

    def test_turkish_name_keeps_actual_publication_eligibility(self):
        publication={'doi':'10.1/example','published':'2023-11-01','journal':'JFE'}
        proof,_=author_eligibility({'name':'A. Doruk Gunaydın'},[{'name':'A. Doruk Gunaydin','publications':[publication]}],[])
        self.assertEqual(proof,publication)

    def test_conference_only_student_is_scanned_without_publication_doi(self):
        proof={'conference':'SFS-NA-2024','year':2024,'paper_title':'Language Frictions in Consumer Credit','program_url':'https://sfs.org/program.pdf','program_page':14}
        author={'name':'Chao Liu','conference_name_keys':['chaoliu'],'eligibility':None,'eligibility_status':'conference_verified'}
        cohort=[{'name':'Chao Liu','name_keys':['chaoliu'],'conferences':[proof]}]
        publication,conference=author_eligibility(author,[],cohort)
        self.assertIsNone(publication)
        self.assertEqual(conference['paper_title'],proof['paper_title'])

    def test_conference_name_alias_retains_program_evidence(self):
        proof={'conference':'AFA-2025','year':2025,'paper_title':'A Student Paper','program_url':'https://afajof.org/program'}
        author={'name':'A. Student','conference_name_keys':['alicebethstudent'],'eligibility_status':'conference_verified'}
        cohort=[{'name':'Alice Beth Student','name_keys':['alicebethstudent'],'conferences':[proof]}]
        publication,conference=author_eligibility(author,[],cohort)
        self.assertIsNone(publication)
        self.assertEqual(conference['conference'],'AFA-2025')

    def test_incomplete_program_row_uses_complete_paper_evidence(self):
        author={'name':'Chaojun Wang','conference_eligibility':{'conference':'SFS-AP-2025','year':2025,'paper_title':''}}
        proof={'conference':'AFA-2026','year':2026,'paper_title':'The Modern Bond Market','program_url':'https://afajof.org/program'}
        _,conference=author_eligibility(author,[],[{'name':'Chaojun Wang','conferences':[proof]}])
        self.assertEqual(conference['paper_title'],'The Modern Bond Market')

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

    def test_saved_publication_alias_is_counted_without_changing_denominator(self):
        universe=[{'name':'A. Student','publications':[{'doi':'10.1/jf','journal':'JF'}]}]
        homes=[{'name':'Alice Student','name_keys':['astudent'],'approved':True,'url':'https://alice.example','eligibility':{'doi':'10.1/jf'}}]
        corpus={'works':[{'doi':'10.1/jf','journal':'JF'}]}
        self.assertEqual(homepage_coverage(universe,homes,corpus)['linked_authors'],1)
        self.assertEqual(finance_top5_homepage_coverage(universe,homes,corpus)['author_rows'],1)

    def test_verified_finance_eligibility_is_not_replaced_by_earlier_ms_article(self):
        finance={'doi':'10.1/jf','published':'2024-01-01','journal':'JF'}
        ms={'doi':'10.1/ms','published':'2022-01-01','journal':'MS'}
        author={'name':'Alice Student','eligibility':finance}
        publication,_=author_eligibility(author,[{'name':'Alice Student','publications':[ms,finance]}],[])
        self.assertEqual(publication['doi'],'10.1/jf')

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
