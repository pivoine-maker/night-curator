import unittest
from night_curator.daily import choose_dynamic_museum, MUSEUMS

class DynamicMuseumTests(unittest.TestCase):
    def test_dynamic_museum_is_stable_for_same_day(self):
        first = choose_dynamic_museum(10, seed='agent')
        second = choose_dynamic_museum(10, seed='agent')
        self.assertEqual(first['museum'], second['museum'])
        self.assertIn('artifact', first)

    def test_dynamic_museum_changes_across_days(self):
        picks = [choose_dynamic_museum(day, seed='agent')['museum'] for day in range(8)]
        self.assertGreaterEqual(len(set(picks)), 6)

    def test_dynamic_museum_is_not_limited_to_route_table(self):
        route_names = {m['museum'] for m in MUSEUMS}
        picks = {choose_dynamic_museum(day, seed='agent')['museum'] for day in range(20)}
        self.assertTrue(picks - route_names)

if __name__ == '__main__':
    unittest.main()
