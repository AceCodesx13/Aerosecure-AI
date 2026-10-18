"""Picks the best supplier for a maintenance need.

policy_demo.py only checks one supplier at a time, so this goes through all the
suppliers that can sell the part and picks one. If none of them work we escalate,
like the policy guide says.

For the lead time we use the 90th percentile of past deliveries from the training
data only (not validation or test). We can swap this for the model later.

Run from the main folder: python src/supplier_selection.py
"""
import math
from collections import defaultdict
from pathlib import Path

from policy import shipment_decision
from policy_demo import recommendation
from validate_data import read

ROOT = Path(__file__).resolve().parents[1]
PERCENTILE = 90


def load_reference(root=ROOT):
    ref = root / 'data' / 'reference'
    parts = {r['aircraft_part_id']: r for r in read(ref / 'aircraft_parts.csv')}
    suppliers = {r['supplier_id']: r for r in read(ref / 'suppliers.csv')}
    eligibility = read(ref / 'supplier_eligibility.csv')
    policy_matrix = {
        (r['shipment_restriction_classification'], r['destination_region_id']): r['destination_eligible'] == 'True'
        for r in read(ref / 'shipment_policy.csv')
    }
    return parts, suppliers, eligibility, policy_matrix


def percentile(values, pct):
    # nearest rank so we always get an actual value from the list
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[rank - 1]


def build_lead_times(train_rows, pct=PERCENTILE):
    # lead time for each supplier/part/condition/destination combo,
    # plus a simpler supplier/part one in case a combo isn't in the data
    detailed = defaultdict(list)
    coarse = defaultdict(list)
    for r in train_rows:
        days = float(r['actual_delivery_days'])
        detailed[(r['supplier_id'], r['part_category_id'], r['condition'], r['destination_region_id'])].append(days)
        coarse[(r['supplier_id'], r['part_category_id'])].append(days)
    return (
        {k: percentile(v, pct) for k, v in detailed.items()},
        {k: percentile(v, pct) for k, v in coarse.items()},
    )


def lead_time_for(lead_times, supplier_id, category_id, condition, destination):
    detailed, coarse = lead_times
    key = (supplier_id, category_id, condition, destination)
    if key in detailed:
        return detailed[key], 'history'
    if (supplier_id, category_id) in coarse:
        return coarse[(supplier_id, category_id)], 'history (supplier + part only)'
    return None, 'no history'


def candidates_for(category_id, condition, eligibility):
    return [r['supplier_id'] for r in eligibility
            if r['part_category_id'] == category_id and condition in r['allowed_conditions'].split(';')]


def select_supplier(request, reference, lead_times):
    # returns the decision, the chosen supplier (or None) and every supplier we checked
    parts, suppliers, eligibility, policy_matrix = reference
    part = parts.get(request['aircraft_part_id'])
    if part is None:
        return 'Escalate: unknown part', None, []

    condition = request.get('condition', 'New')
    classification = request['shipment_restriction_classification']
    destination = request['destination_region_id']
    # the policy only depends on the label and destination, but we still
    # show it for each supplier so the output is easier to read
    eligible_destination = policy_matrix.get((classification, destination))

    candidates = []
    for supplier_id in candidates_for(part['part_category_id'], condition, eligibility):
        policy, reason = shipment_decision(classification, eligible_destination, request['authorization_status'])
        lead, source = lead_time_for(lead_times, supplier_id, part['part_category_id'], condition, destination)
        row = {
            'supplier_id': supplier_id,
            'supplier_name': suppliers[supplier_id]['name'],
            'policy_decision': policy,
            'policy_reason': reason,
            'conservative_lead_time_days': lead,
            'lead_time_source': source,
        }
        if lead is None:
            row.update(need_date=None, latest_order_date=None, result='No lead-time data')
        else:
            need, latest, result = recommendation(
                request['scenario_date'],
                float(request['replacement_interval_hours']),
                float(request['hours_since_replacement']),
                float(request['projected_daily_flight_hours']),
                lead,
                float(request['buffer_days']),
                policy,
            )
            row.update(need_date=need, latest_order_date=latest, result=result)
        candidates.append(row)

    # best one is the supplier that gives us the most time to order
    recommended = [c for c in candidates if c['result'] == 'Recommend']
    if recommended:
        best = max(recommended, key=lambda c: (c['latest_order_date'], -c['conservative_lead_time_days']))
        return 'Recommend', best, candidates

    # allowed but already too late, so escalate and point to the fastest supplier
    late = [c for c in candidates if c['result'] == 'Escalate']
    if late:
        best = min(late, key=lambda c: c['conservative_lead_time_days'])
        return 'Escalate: order deadline already passed', best, candidates

    if any(c['result'] == 'Review required' for c in candidates):
        return 'Escalate: human review required', None, candidates

    return 'Escalate: no feasible option', None, candidates


def print_result(name, decision, chosen, candidates):
    print(f'\n{name}: {decision}')
    if chosen:
        print(f"  Choice: {chosen['supplier_id']} ({chosen['supplier_name']}), "
              f"order by {chosen['latest_order_date']}, need date {chosen['need_date']}")
    for c in candidates:
        lead = '-' if c['conservative_lead_time_days'] is None else f"{c['conservative_lead_time_days']:g}d"
        print(f"  {c['supplier_id']:<6} lead {lead:<5} order by {c['latest_order_date'] or '-':<11} "
              f"{c['policy_decision']:<16} {c['result']}")


# a few example requests to show the different outcomes
DEMO_REQUESTS = [
    ('Plenty of time', dict(aircraft_part_id='AC-01-PC-02', scenario_date='2026-10-12',
                            replacement_interval_hours=1000, hours_since_replacement=500,
                            projected_daily_flight_hours=5, buffer_days=5, destination_region_id='REG-A',
                            shipment_restriction_classification='Unrestricted', authorization_status='Not required')),
    ('Part almost due', dict(aircraft_part_id='AC-02-PC-03', scenario_date='2026-10-12',
                             replacement_interval_hours=1000, hours_since_replacement=990,
                             projected_daily_flight_hours=5, buffer_days=5, destination_region_id='REG-A',
                             shipment_restriction_classification='Unrestricted', authorization_status='Not required')),
    ('Blocked destination', dict(aircraft_part_id='AC-01-PC-02', scenario_date='2026-10-12',
                                 replacement_interval_hours=1000, hours_since_replacement=500,
                                 projected_daily_flight_hours=5, buffer_days=5, destination_region_id='REG-C',
                                 shipment_restriction_classification='Highly Restricted',
                                 authorization_status='Approved after review')),
]


if __name__ == '__main__':
    reference = load_reference()
    lead_times = build_lead_times(read(ROOT / 'data' / 'prepared' / 'train' / 'train.csv'))
    for name, request in DEMO_REQUESTS:
        print_result(name, *select_supplier(request, reference, lead_times))
    print('\nLead times are the 90th percentile from the training data.')
