import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from access_control import filter_records, get_records

# One record for each label, plus two bad ones
ROWS = [
    {'order_id': 'A', 'data_access_classification': 'Unrestricted'},
    {'order_id': 'B', 'data_access_classification': 'Restricted'},
    {'order_id': 'C', 'data_access_classification': 'Highly Restricted'},
    {'order_id': 'D', 'data_access_classification': 'Secret'},
    {'order_id': 'E'},
]


def ids(rows):
    return [r['order_id'] for r in rows]


class AccessControlTests(unittest.TestCase):

    def test_student_only_sees_unrestricted(self):
        allowed, denied = filter_records(ROWS, 'student')
        self.assertEqual(ids(allowed), ['A'])
        self.assertEqual(len(denied), 4)

    def test_mentor_sees_unrestricted_and_restricted(self):
        allowed, _ = filter_records(ROWS, 'mentor')
        self.assertEqual(ids(allowed), ['A', 'B'])

    def test_administrator_sees_all_valid_labels(self):
        allowed, _ = filter_records(ROWS, 'administrator')
        self.assertEqual(ids(allowed), ['A', 'B', 'C'])

    def test_bad_or_missing_labels_are_denied_for_everyone(self):
        for role in ['student', 'mentor', 'administrator']:
            allowed, _ = filter_records(ROWS, role)
            self.assertNotIn('D', ids(allowed))
            self.assertNotIn('E', ids(allowed))

    def test_unknown_role_gets_nothing(self):
        allowed, denied = filter_records(ROWS, 'hacker')
        self.assertEqual(allowed, [])
        self.assertEqual(len(denied), len(ROWS))

    def test_request_is_logged(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / 'access_log.csv'
            get_records(ROWS, 'jad', 'student', log_path)
            get_records(ROWS, 'aaron', 'administrator', log_path)

            with log_path.open(encoding='utf-8', newline='') as f:
                lines = list(csv.DictReader(f))

            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[0]['user'], 'jad')
            self.assertEqual(lines[0]['allowed'], '1')
            self.assertEqual(lines[0]['denied'], '4')
            self.assertEqual(lines[1]['allowed'], '3')

    def test_real_dataset_totals_add_up(self):
        from validate_data import read
        rows = read(ROOT / 'data' / 'raw' / 'orders.csv')
        for role in ['student', 'mentor', 'administrator']:
            allowed, denied = filter_records(rows, role)
            self.assertEqual(len(allowed) + len(denied), len(rows))


if __name__ == '__main__':
    unittest.main()
