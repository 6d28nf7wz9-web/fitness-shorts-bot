import unittest
from research_sources import references_block

class PubMedReferenceTests(unittest.TestCase):
    def test_reference_has_pubmed_link_and_pmid(self):
        block=references_block([{"pmid":"12345","title":"Resistance training review","journal":"Sports Medicine","year":"2024","doi":"10.1000/test","url":"https://pubmed.ncbi.nlm.nih.gov/12345/"}])
        self.assertIn("PMID: 12345",block)
        self.assertIn("https://pubmed.ncbi.nlm.nih.gov/12345/",block)
        self.assertIn("10.1000/test",block)

    def test_empty_sources_do_not_invent_references(self):
        self.assertEqual(references_block([]),"")

if __name__ == "__main__": unittest.main()
