import unittest
from author_identity import identity_key,name_variants,personal_site_links,author_profile_links,search_alias_names

class AuthorIdentityTests(unittest.TestCase):
    def test_turkish_dotless_i_is_transliterated_not_deleted(self):
        self.assertEqual(identity_key('A. Doruk Gunaydın'),identity_key('A. Doruk Gunaydin'))

    def test_leading_initial_keeps_searchable_full_given_name(self):
        self.assertIn(identity_key('Doruk Gunaydin'),name_variants('A. Doruk Gunaydin'))

    def test_german_domain_spelling_is_preserved_as_a_variant(self):
        self.assertIn(identity_key('Florian Muenkel'),name_variants('Florian Münkel'))

    def test_initial_only_given_names_do_not_reduce_to_surname(self):
        self.assertNotIn('wong',name_variants('T. J. Wong'))
        self.assertNotIn('vandijk',name_variants('C. N. Van Dijk'))

    def test_explicit_parenthetical_professional_name_is_searchable(self):
        self.assertIn('janegu',name_variants('Zheyin (Jane) Gu'))

    def test_explicit_quoted_professional_name_is_searchable(self):
        self.assertIn('elifreeman',name_variants('Charlton “Eli” Freeman'))

    def test_nickname_expansion_is_a_search_hint_not_an_identity_merge(self):
        self.assertIn('william McEvily',search_alias_names('Bill McEvily'))
        self.assertNotIn('williammcevily',name_variants('Bill McEvily'))

    def test_official_profile_website_button_is_followed(self):
        html='<p><a href="https://author.example">Website</a></p><footer><a href="https://university.example">Website</a></footer>'
        self.assertEqual(personal_site_links(html,'https://school.example/person'),['https://author.example'])

    def test_directory_name_link_is_a_candidate_for_that_author(self):
        html='<h1>Faculty</h1><a href="/bio/berk-sensoy">Berk A. Sensoy</a><a href="/bio/other-author">Other Author</a>'
        self.assertEqual(author_profile_links(html,'https://school.example/faculty','Berk Sensoy'),['https://school.example/bio/berk-sensoy'])

    def test_profile_button_stays_with_its_named_card(self):
        html='<article><h3>Alice Student</h3><a href="/profile/123">View Profile</a></article><article><h3>Other Author</h3><a href="/profile/456">View Profile</a></article>'
        self.assertEqual(author_profile_links(html,'https://school.example/faculty','Alice Student'),['https://school.example/profile/123'])

    def test_student_contact_does_not_inherit_supervisor_website(self):
        html='<div><article><h3>Yuantao Shi</h3><a href="/contact-us">Contact</a></article><article><h3>Steve Roberts</h3><a href="https://supervisor.example">Visit Personal Website</a></article></div>'
        self.assertEqual(author_profile_links(html,'https://school.example/people','Yuantao Shi'),[])

    def test_moved_site_with_url_anchor_is_followed(self):
        body='<h1>A. Doruk Gunaydın</h1><p>Personal Website: <a href="https://dorukgunaydin.com/">https://dorukgunaydin.com/</a></p><footer><a href="https://sabanciuniv.edu">Sabanci University</a></footer>'
        self.assertEqual(personal_site_links(body,'https://myweb.sabanciuniv.edu/dorukgunaydin/'),['https://dorukgunaydin.com/'])

    def test_unrelated_url_anchor_is_not_a_personal_site(self):
        self.assertEqual(personal_site_links('<p>Coauthors: <a href="https://other.example">Someone Else</a></p>','https://author.example'),[])

if __name__=='__main__':unittest.main()
