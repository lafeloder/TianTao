import unittest
from benchmarks import job_from_ejm

class RecruiterStatusTests(unittest.TestCase):
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
