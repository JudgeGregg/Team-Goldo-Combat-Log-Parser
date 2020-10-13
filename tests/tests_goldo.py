"""Test suite for Team Goldo App."""
import csv

import unittest2
import team_goldo


class TestGoldoFunctions(unittest2.TestCase):

    def setUp(self):
        log_file = open(
            'Goldo/sample_file/combat_2012-06-06_20_33_20_sample.txt')
        self.upload = team_goldo.Upload()
        self.upload.current_date = log_file.name.split('_', 3)[2]
        self.log_file = csv.DictReader(
            log_file, fieldnames=team_goldo.CSV_HEADER, delimiter=']',
            skipinitialspace=True)

    def test_parse(self):
        self.upload.parse(self.log_file)
        self.assertEqual(len(team_goldo.Raid.raid), 6)


if __name__ == '__main__':
    unittest2.main()
