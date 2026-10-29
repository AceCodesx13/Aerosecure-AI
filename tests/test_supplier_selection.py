import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from supplier_selection import (DEFAULT_MODEL, build_lead_times, candidates_for, history_estimator,
                                load_estimator, load_reference, model_estimator, percentile,
                                select_supplier)
from validate_data import read


def history(supplier, category, days, condition='New', destination='REG-A'):
    rows = []
    for d in days:
        rows.append({'supplier_id': supplier, 'part_category_id': category, 'condition': condition,
                     'destination_region_id': destination, 'actual_delivery_days': d,
                     'quantity_ordered': 4, 'stock_at_acceptance': 10, 'supplier_backlog_days': 5,
                     'quoted_lead_time_days': d})
    return rows


def request(**overrides):
    r = dict(aircraft_part_id='AC-01-PC-02', scenario_date='2026-10-12', replacement_interval_hours=1000,
             hours_since_replacement=500, projected_daily_flight_hours=5, buffer_days=5,
             destination_region_id='REG-A', shipment_restriction_classification='Unrestricted',
             authorization_status='Not required')
    r.update(overrides)
    return r


# fake model that just returns the quoted lead time, easy to check by hand
class FakePipeline:
    def __init__(self):
        self.seen = []

    def predict(self, df):
        self.seen.append(df.iloc[0].to_dict())
        return [float(df.iloc[0]['quoted_lead_time_days'])]


class SupplierSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = load_reference()
        # SUP-A, SUP-B and SUP-F all sell PC-02
        cls.rows = (history('SUP-A', 'PC-02', [10, 12, 14, 30])
                    + history('SUP-B', 'PC-02', [5, 6, 7, 8])
                    + history('SUP-F', 'PC-02', [50, 60, 70, 80]))
        cls.estimate = staticmethod(history_estimator(build_lead_times(cls.rows)))

    def test_percentile_is_conservative_and_a_real_value(self):
        self.assertEqual(percentile([10, 12, 14, 30], 90), 30)
        self.assertEqual(percentile([5, 6, 7, 8], 50), 6)

    def test_candidates_respect_condition(self):
        self.assertEqual(sorted(candidates_for('PC-02', 'New', self.reference[2])), ['SUP-A', 'SUP-B', 'SUP-F'])
        self.assertEqual(candidates_for('PC-02', 'Repaired', self.reference[2]), [])

    def test_picks_supplier_with_most_time_left(self):
        decision, chosen, candidates = select_supplier(request(), self.reference, self.estimate)
        self.assertEqual(decision, 'Recommend')
        self.assertEqual(chosen['supplier_id'], 'SUP-B')   # fastest one
        self.assertEqual(len(candidates), 3)

    def test_need_date_and_order_date_use_starter_math(self):
        # 500 hours left at 5 hours a day is 100 days, then minus 8 lead and 5 buffer
        _, chosen, _ = select_supplier(request(), self.reference, self.estimate)
        self.assertEqual(chosen['need_date'], '2027-01-20')
        self.assertEqual(chosen['latest_order_date'], '2027-01-07')

    def test_late_for_everyone_escalates_with_fastest_supplier(self):
        decision, chosen, _ = select_supplier(request(hours_since_replacement=990), self.reference, self.estimate)
        self.assertEqual(decision, 'Escalate: order deadline already passed')
        self.assertEqual(chosen['supplier_id'], 'SUP-B')

    def test_missing_authorization_needs_review(self):
        decision, chosen, _ = select_supplier(
            request(shipment_restriction_classification='Restricted', authorization_status='Expired'),
            self.reference, self.estimate)
        self.assertEqual(decision, 'Escalate: human review required')
        self.assertIsNone(chosen)

    def test_unknown_part_escalates(self):
        decision, chosen, _ = select_supplier(request(aircraft_part_id='AC-99-PC-99'), self.reference, self.estimate)
        self.assertEqual(decision, 'Escalate: unknown part')


# all the ways we can end up with nothing to recommend
class NoOptionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.reference = load_reference()
        cls.estimate = staticmethod(history_estimator(build_lead_times(history('SUP-B', 'PC-02', [5, 6, 7, 8]))))

    def test_blocked_destination_has_no_feasible_option(self):
        decision, chosen, candidates = select_supplier(
            request(destination_region_id='REG-C', shipment_restriction_classification='Highly Restricted',
                    authorization_status='Approved after review'), self.reference, self.estimate)
        self.assertEqual(decision, 'Escalate: no feasible option')
        self.assertIsNone(chosen)
        self.assertTrue(all(c['result'] == 'Blocked' for c in candidates))

    def test_region_c_highly_restricted_never_recommended(self):
        for auth in ['Not required', 'Valid', 'Expired', 'Missing', 'Approved after review']:
            decision, chosen, _ = select_supplier(
                request(destination_region_id='REG-C', shipment_restriction_classification='Highly Restricted',
                        authorization_status=auth), self.reference, self.estimate)
            self.assertNotEqual(decision, 'Recommend')
            self.assertIsNone(chosen)

    def test_no_supplier_for_condition(self):
        # nobody sells PC-02 repaired
        decision, chosen, candidates = select_supplier(request(condition='Repaired'), self.reference, self.estimate)
        self.assertEqual(decision, 'Escalate: no supplier sells this part in that condition')
        self.assertIsNone(chosen)
        self.assertEqual(candidates, [])

    def test_no_lead_time_for_anyone(self):
        empty = history_estimator(build_lead_times([]))
        decision, chosen, candidates = select_supplier(request(), self.reference, empty)
        self.assertEqual(decision, 'Escalate: no feasible option')
        self.assertIsNone(chosen)
        self.assertTrue(all(c['result'] == 'No lead-time data' for c in candidates))

    def test_bad_request_numbers_escalate(self):
        decision, chosen, _ = select_supplier(request(projected_daily_flight_hours=0), self.reference, self.estimate)
        self.assertTrue(decision.startswith('Escalate: invalid request'))
        self.assertIsNone(chosen)

    def test_missing_field_escalates(self):
        r = request()
        del r['buffer_days']
        decision, chosen, _ = select_supplier(r, self.reference, self.estimate)
        self.assertTrue(decision.startswith('Escalate: invalid request'))
        self.assertIsNone(chosen)


class ModelEstimateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = load_reference()
        cls.rows = (history('SUP-A', 'PC-02', [10, 12, 14, 30])
                    + history('SUP-B', 'PC-02', [5, 6, 7, 8])
                    + history('SUP-F', 'PC-02', [50, 60, 70, 80]))

    def make(self, margin=3.2):
        pipe = FakePipeline()
        return pipe, model_estimator({'pipeline': pipe, 'margin': margin}, self.reference, self.rows)

    def test_uses_prediction_plus_margin_rounded_up(self):
        # SUP-B: median quote 6.5 + 3.2 margin = 9.7, rounds up to 10
        _, estimate = self.make()
        _, chosen, _ = select_supplier(request(), self.reference, estimate)
        self.assertEqual(chosen['supplier_id'], 'SUP-B')
        self.assertEqual(chosen['conservative_lead_time_days'], 10)
        self.assertEqual(chosen['lead_time_source'], 'model (typical quote)')

    def test_builds_the_same_features_the_model_was_trained_on(self):
        pipe, estimate = self.make()
        select_supplier(request(), self.reference, estimate)
        row = pipe.seen[0]
        self.assertEqual(row['aircraft_model_id'], 'AC-01')
        self.assertEqual(row['part_category_id'], 'PC-02')
        self.assertEqual(row['order_month'], 10)
        self.assertEqual(row['destination_region_id'], 'REG-A')
        # SUP-A ships from REG-A so it's the short route
        sup_a = next(r for r in pipe.seen if r['supplier_id'] == 'SUP-A')
        self.assertEqual(sup_a['origin_region_id'], 'REG-A')
        self.assertEqual(sup_a['route_transit_days'], 2)

    def test_real_supplier_quote_overrides_typical(self):
        _, estimate = self.make(margin=0)
        quotes = {'SUP-F': {'quoted_lead_time_days': 2}}
        _, chosen, _ = select_supplier(request(quotes=quotes), self.reference, estimate)
        self.assertEqual(chosen['supplier_id'], 'SUP-F')
        self.assertEqual(chosen['conservative_lead_time_days'], 2)
        self.assertEqual(chosen['lead_time_source'], 'model (supplier quote)')

    def test_prediction_never_below_one_day(self):
        _, estimate = self.make(margin=0)
        quotes = {s: {'quoted_lead_time_days': 0} for s in ['SUP-A', 'SUP-B', 'SUP-F']}
        _, chosen, _ = select_supplier(request(quotes=quotes), self.reference, estimate)
        self.assertEqual(chosen['conservative_lead_time_days'], 1)

    @unittest.skipUnless(DEFAULT_MODEL.exists(), 'no trained model yet, run src/train.py')
    def test_real_model_end_to_end(self):
        estimate, kind = load_estimator(self.reference)
        self.assertEqual(kind, 'model')
        decision, chosen, _ = select_supplier(request(), self.reference, estimate)
        self.assertEqual(decision, 'Recommend')
        self.assertEqual(chosen['lead_time_source'], 'model (typical quote)')


# honeywell's 3 maintenance scenarios
class StarterScenarioTests(unittest.TestCase):

    def test_maintenance_scenarios_match_expected(self):
        from policy_demo import recommendation
        for r in read(ROOT / 'data' / 'examples' / 'maintenance_scenarios.csv'):
            got = recommendation(r['scenario_date'], float(r['replacement_interval_hours']),
                                 float(r['hours_since_replacement']), float(r['projected_daily_flight_hours']),
                                 float(r['conservative_lead_time_days']), float(r['buffer_days']),
                                 r['policy_decision'])
            self.assertEqual(got, (r['expected_need_date'], r['expected_latest_order_date'], r['expected_result']),
                             r['scenario_id'])


if __name__ == '__main__':
    unittest.main()
