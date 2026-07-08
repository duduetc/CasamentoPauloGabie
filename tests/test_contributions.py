import os
import tempfile
import unittest

from app import database


class ContributionRemovalTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.original_db_path = database.DB_PATH
        database.DB_PATH = os.path.join(self.tmpdir.name, "test_wedding.db")
        database.init_db()

    def tearDown(self):
        database.DB_PATH = self.original_db_path
        self.tmpdir.cleanup()

    def test_remove_contribution_reduces_total_and_persists(self):
        database.add_contribution(1, "Presente", "Maria", 50.0)
        database.add_contribution(1, "Presente", "João", 25.0)

        removed = database.remove_contribution(1, 40.0)

        self.assertTrue(removed)
        self.assertEqual(database.get_all_contributions_totals()[1], 35.0)


class RsvpSearchTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.original_db_path = database.DB_PATH
        database.DB_PATH = os.path.join(self.tmpdir.name, "test_wedding.db")
        database.init_db()

    def tearDown(self):
        database.DB_PATH = self.original_db_path
        self.tmpdir.cleanup()

    def test_search_groups_matches_guest_names_and_marks_the_matched_guest(self):
        database.add_group("Cláudio da Silva e família", 4, guest_names=["João", "Maria"])

        results = database.search_groups("João")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Cláudio da Silva e família")
        self.assertEqual(results[0]["matched_guest_name"], "João")

    def test_search_groups_matches_main_name_and_guest_name_together(self):
        database.add_group("Cláudio da Silva e família", 4, guest_names=["João", "Maria"])

        results = database.search_groups("Cláudio e João")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Cláudio da Silva e família")
        self.assertEqual(results[0]["matched_guest_name"], "João")


if __name__ == "__main__":
    unittest.main()
