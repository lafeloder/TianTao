import unittest
from unittest.mock import patch
from benchmarks import job_from_ejm,merge

class RecruiterStatusTests(unittest.TestCase):
    def test_conflicting_old_listing_date_does_not_prematurely_close_employer_call(self):
        old={'id':'one','title':'Role','apply_url':'https://example.org/role','source_reports':[],'deadline':'2026-11-27','deadline_authority':'official_employer','last_verified':'2026-11-09','verification':'Individually reviewed','status':'open'}
        new={**old,'source_type':'Econ Job Market employer advert','deadline':'2026-11-20','last_verified':'2026-11-23','status':'closed','recruitment_status':'Accepting applications'}
        with patch('benchmarks.TODAY','2026-11-23'):
            self.assertEqual(merge([dict(old)],[new],'jobs')[0]['status'],'open')
            new['recruitment_status']='Reviewing applications'
            self.assertEqual(merge([dict(old)],[new],'jobs')[0]['status'],'closed')
    def test_conflicting_listing_cannot_replace_reviewed_official_deadline(self):
        old={'id':'one','title':'Role','apply_url':'https://example.org/role','source_reports':[],'deadline':'2026-11-27','deadline_authority':'official_employer','last_verified':'2026-11-09','verification':'Individually reviewed'}
        new={**old,'source_type':'Econ Job Market employer advert','deadline':'2026-11-20','last_verified':'2026-11-16','status':'open'}
        result=merge([old],[new],'jobs')[0]
        self.assertEqual(result['deadline'],'2026-11-27')
        self.assertEqual(result['last_verified'],'2026-11-09')
        self.assertEqual(result['deadline_conflict']['listing_deadline'],'2026-11-20')
    def row(self,**changes):
        return dict({'id':'fixture','title':'Economics postdoc','columns':['Economics postdoc','University','Postdoctoral Scholar','1 Oct 2026 1 Nov 2026 1 Dec 2026'],'facts':{'Location of job':'Ireland'},'url':'https://econjobmarket.org/positions/fixture'},**changes)
    def test_display_dates_never_supply_application_deadline(self):
        self.assertEqual(job_from_ejm(self.row(),{'checked_on':'2026-10-26'})['deadline'],'')
    def test_reviewing_without_header_label_is_not_accepting(self):
        row=self.row(deadline='2099-12-01',recruitmentStatus='Reviewing applications')
        self.assertEqual(job_from_ejm(row,{'checked_on':'2026-10-26'})['status'],'closed')
    def test_structured_accepting_status_is_used(self):
        row=self.row(deadline='2099-12-01',recruitmentStatus='Accepting applications')
        self.assertEqual(job_from_ejm(row,{'checked_on':'2026-10-26'})['status'],'open')
