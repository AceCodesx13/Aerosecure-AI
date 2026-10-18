import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from supplier_selection import (build_lead_times, candidates_for, load_reference, percentile,
                                select_supplier)
from validate_data import read


def history(supplier, category, days, condition='New', destination='REG-A'):
    return [{'supplier_id': supplier, 'part_category_id': category, 'condition': condition,
             'destination_region_id': destination, 'actual_delivery_days': d} for d in days]


def request(**overrides):
    r = dict(aircraft_part_id='AC-01-PC-02', scenario_date='2026-10-12', replacement_interval_hours=1000,
             hours_since_replacement=500, projected_daily_flight_hours=5, buffer_days=5,
             destination_region_id='REG-A', shipment_restriction_classification='Unrestricted',
             authorization_status='Not required')
    r.update(overrides)
    return r


class SupplierSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = load_reference()
        # SUP-A, SUP-B and SUP-F all sell PC-02
        cls.lead_times = build_lead_times(
            history('SUP-A', 'PC-02', [10, 12, 14, 30])
            + history('SUP-B', 'PC-02', [5, 6, 7, 8])
            + history('SUP-F', 'PC-02', [50, 60, 70, 80]))

    def test_percentile_is_conservative_and_a_real_value(self):
        self.assertEqual(percentile([10, 12, 14, 30], 90), 30)
        self.assertEqual(percentile([5, 6, 7, 8], 50), 6)

    def test_candidates_respect_condition(self):
        self.assertEqual(sorted(candidates_for('PC-02', 'New', self.reference[2])), ['SUP-A', 'SUP-B', 'SUP-F'])
        self.assertEqual(candidates_for('PC-02', 'Repaired', self.reference[2]), [])

    def test_picks_supplier_with_most_time_left(self):
        decision, chosen, candidates = select_supplier(request(), self.reference, self.lead_times)
        self.assertEqual(decision, 'Recommend')
        self.assertEqual(chosen['supplier_id'], 'SUP-B')   # fastest one
        self.assertEqual(len(candidates), 3)

    def test_need_date_and_order_date_use_starter_math(self):
        # 500 hours left at 5 hours a day is 100 days, then minus 8 lead and 5 buffer
        _, chosen, _ = select_supplier(request(), self.reference, self.lead_times)
        self.assertEqual(chosen['need_date'], '2027-01-20')
        self.assertEqual(chosen['latest_order_date'], '2027-01-07')

    def test_late_for_everyone_escalates_with_fastest_supplier(self):
        decision, chosen, _ = select_supplier(request(hours_since_replacement=990), self.reference, self.lead_times)
        self.assertEqual(decision, 'Escalate: order deadline already passed')
        self.assertEqual(chosen['supplier_id'], 'SUP-B')

    def test_blocked_destination_has_no_feasible_option(self):
        decision, chosen, candidates = select_supplier(
            request(destination_region_id='REG-C', shipment_restriction_classification='Highly Restricted',
                    authorization_status='Approved after review'), self.reference, self.lead_times)
        self.assertEqual(decision, 'Escalate: no feasible option')
        self.assertIsNone(chosen)
        self.assertTrue(all(c['result'] == 'Blocked' for c in candidates))

    def test_missing_authorization_needs_review(self):
        decision, chosen, _ = select_supplier(
            request(shipment_restriction_classification='Restricted', authorization_status='Expired'),
            self.reference, self.lead_times)
        self.assertEqual(decision, 'Escalate: human review required')
        self.assertIsNone(chosen)

    def test_unknown_part_escalates(self):
        decision, chosen, _ = select_supplier(request(aircraft_part_id='AC-99-PC-99'), self.reference, self.lead_times)
        self.assertEqual(decision, 'Escalate: unknown part')

    def test_runs_on_training_split(self):
        lead_times = build_lead_times(read(ROOT / 'data' / 'prepared' / 'train' / 'train.csv'))
        decision, chosen, _ = select_supplier(request(), self.reference, lead_times)
        self.assertEqual(decision, 'Recommend')
        self.assertEqual(chosen['lead_time_source'], 'history')


if __name__ == '__main__':
    unittest.main()
