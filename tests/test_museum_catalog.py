import json
import unittest
from pathlib import Path

from night_curator.daily import choose_dynamic_museum, MUSEUM_IDEAS

class MuseumCatalogTests(unittest.TestCase):
    def test_catalog_has_at_least_500_museums(self):
        self.assertGreaterEqual(len(MUSEUM_IDEAS), 500)

    def test_catalog_items_have_required_fields(self):
        required = {'museum', 'city', 'country', 'artifact'}
        for item in MUSEUM_IDEAS[:20]:
            self.assertTrue(required <= set(item))
            self.assertTrue(all(item[key] for key in required))

    def test_dynamic_selection_spreads_across_large_catalog(self):
        picks = {choose_dynamic_museum(day, seed='agent')['museum'] for day in range(60)}
        self.assertGreaterEqual(len(picks), 50)

if __name__ == '__main__':
    unittest.main()
