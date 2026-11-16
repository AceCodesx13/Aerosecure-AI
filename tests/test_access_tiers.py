import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from validate_data import read

TIERS = {'unrestricted': 'Unrestricted', 'restricted': 'Restricted', 'highly-restricted': 'Highly Restricted'}


class AccessTierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # run the starter script into a temp folder so we don't touch artifacts/
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        subprocess.run([sys.executable, str(ROOT / 'src' / 'create_access_tiers.py'), '--output', str(cls.out)],
                       check=True, capture_output=True, cwd=ROOT)
        cls.tiers = {t: read(cls.out / t / 'orders.csv') for t in TIERS}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_three_files_made(self):
        for t in TIERS:
            self.assertTrue((self.out / t / 'orders.csv').exists(), t)

    def test_totals_add_up_to_20000(self):
        self.assertEqual(sum(len(rows) for rows in self.tiers.values()), 20000)

    def test_each_file_only_has_its_own_label(self):
        for t, rows in self.tiers.items():
            self.assertEqual({r['data_access_classification'] for r in rows}, {TIERS[t]}, t)

    def test_no_order_lost_or_duplicated(self):
        ids = [r['order_id'] for rows in self.tiers.values() for r in rows]
        raw_ids = {r['order_id'] for r in read(ROOT / 'data' / 'raw' / 'orders.csv')}
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), raw_ids)

    def test_same_columns_as_raw(self):
        with (ROOT / 'data' / 'raw' / 'orders.csv').open(encoding='utf-8', newline='') as f:
            raw_cols = next(csv.reader(f))
        for t in TIERS:
            with (self.out / t / 'orders.csv').open(encoding='utf-8', newline='') as f:
                self.assertEqual(next(csv.reader(f)), raw_cols, t)


if __name__ == '__main__':
    unittest.main()
