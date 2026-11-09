# Picks the best supplier when a part needs replacing.
# Uses the model's conservative delivery days, or past deliveries if there's no model yet.
# Run: python src/supplier_selection.py
import math
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import median

from policy import shipment_decision
from policy_demo import recommendation
from schema import FEATURES
from validate_data import read

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / 'artifacts' / 'model' / 'model.joblib'
QUOTE_FIELDS = ['quantity_ordered', 'stock_at_acceptance', 'supplier_backlog_days', 'quoted_lead_time_days']


def load_reference(root=ROOT):
    ref = root / 'data' / 'reference'
    parts = {r['aircraft_part_id']: r for r in read(ref / 'aircraft_parts.csv')}
    suppliers = {r['supplier_id']: r for r in read(ref / 'suppliers.csv')}
    eligibility = read(ref / 'supplier_eligibility.csv')
    policy_matrix = {}
    for r in read(ref / 'shipment_policy.csv'):
        policy_matrix[(r['shipment_restriction_classification'], r['destination_region_id'])] = r['destination_eligible'] == 'True'
    return parts, suppliers, eligibility, policy_matrix


def load_routes(root=ROOT):
    routes = {}
    for r in read(root / 'data' / 'reference' / 'routes.csv'):
        routes[(r['origin_region_id'], r['destination_region_id'])] = r
    return routes


# ---- old way: 90th percentile of past deliveries ----

def percentile(values, pct):
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[rank - 1]


def build_lead_times(train_rows, pct=90):
    detailed = defaultdict(list)
    coarse = defaultdict(list)
    for r in train_rows:
        days = float(r['actual_delivery_days'])
        detailed[(r['supplier_id'], r['part_category_id'], r['condition'], r['destination_region_id'])].append(days)
        coarse[(r['supplier_id'], r['part_category_id'])].append(days)
    detailed = {k: percentile(v, pct) for k, v in detailed.items()}
    coarse = {k: percentile(v, pct) for k, v in coarse.items()}
    return detailed, coarse


def history_estimator(lead_times):
    detailed, coarse = lead_times

    def estimate(supplier_id, part, condition, destination, request):
        cat = part['part_category_id']
        if (supplier_id, cat, condition, destination) in detailed:
            return detailed[(supplier_id, cat, condition, destination)], 'history'
        if (supplier_id, cat) in coarse:
            return coarse[(supplier_id, cat)], 'history (supplier + part only)'
        return None, 'no history'
    return estimate


# ---- new way: ask the model ----

def typical_quotes(train_rows):
    # we don't have a real quote before ordering, so use the usual values for that supplier + part
    values = defaultdict(lambda: defaultdict(list))
    for r in train_rows:
        for f in QUOTE_FIELDS:
            values[(r['supplier_id'], r['part_category_id'])][f].append(float(r[f]))
            values['all'][f].append(float(r[f]))
    return {k: {f: median(v) for f, v in fields.items()} for k, fields in values.items()}


def model_estimator(bundle, reference, train_rows, routes=None):
    import pandas as pd
    suppliers = reference[1]
    routes = routes or load_routes()
    typical = typical_quotes(train_rows)

    def estimate(supplier_id, part, condition, destination, request):
        origin = suppliers[supplier_id]['origin_region_id']
        route = routes.get((origin, destination))
        if route is None:
            return None, 'no route'

        quote = dict(typical.get((supplier_id, part['part_category_id']), typical['all']))
        real_quote = request.get('quotes', {}).get(supplier_id, {})
        for f in QUOTE_FIELDS:
            if f in real_quote:
                quote[f] = float(real_quote[f])
        if 'quantity' in request:
            quote['quantity_ordered'] = float(request['quantity'])

        row = {
            'aircraft_model_id': part['aircraft_model_id'],
            'part_category_id': part['part_category_id'],
            'supplier_id': supplier_id,
            'condition': condition,
            'origin_region_id': origin,
            'destination_region_id': destination,
            'route_transit_days': float(route['route_transit_days']),
            'route_customs_days': float(route['route_customs_days']),
            'order_month': date.fromisoformat(request['scenario_date']).month,
        }
        row.update(quote)

        # same conservative number predict.py gives
        predicted = max(1.0, float(bundle['pipeline'].predict(pd.DataFrame([row])[FEATURES])[0]))
        days = math.ceil(predicted + float(bundle['margin']))
        source = 'model (supplier quote)' if real_quote else 'model (typical quote)'
        return days, source
    return estimate


def load_estimator(reference, model_path=DEFAULT_MODEL, root=ROOT):
    train_rows = read(root / 'data' / 'prepared' / 'train' / 'train.csv')
    if Path(model_path).exists():
        import joblib
        return model_estimator(joblib.load(model_path), reference, train_rows, load_routes(root)), 'model'
    return history_estimator(build_lead_times(train_rows)), 'history'


# ---- picking the supplier ----

def candidates_for(category_id, condition, eligibility):
    return [r['supplier_id'] for r in eligibility
            if r['part_category_id'] == category_id and condition in r['allowed_conditions'].split(';')]


def select_supplier(request, reference, estimate):
    # returns (decision, chosen supplier or None, every supplier we checked)
    parts, suppliers, eligibility, policy_matrix = reference
    part = parts.get(request.get('aircraft_part_id'))
    if part is None:
        return 'Escalate: unknown part', None, []

    condition = request.get('condition', 'New')
    classification = request.get('shipment_restriction_classification')
    destination = request.get('destination_region_id')
    eligible_destination = policy_matrix.get((classification, destination))

    supplier_ids = candidates_for(part['part_category_id'], condition, eligibility)
    if not supplier_ids:
        return 'Escalate: no supplier sells this part in that condition', None, []

    candidates = []
    for supplier_id in supplier_ids:
        policy, reason = shipment_decision(classification, eligible_destination, request.get('authorization_status'))
        lead, source = estimate(supplier_id, part, condition, destination, request)
        row = {
            'supplier_id': supplier_id,
            'supplier_name': suppliers[supplier_id]['name'],
            'policy_decision': policy,
            'policy_reason': reason,
            'conservative_lead_time_days': lead,
            'lead_time_source': source,
            'need_date': None,
            'latest_order_date': None,
        }
        if policy == 'Blocked':
            row['result'] = 'Blocked'
        elif lead is None:
            row['result'] = 'No lead-time data'
        else:
            try:
                need, latest, result = recommendation(
                    request['scenario_date'],
                    float(request['replacement_interval_hours']),
                    float(request['hours_since_replacement']),
                    float(request['projected_daily_flight_hours']),
                    lead,
                    float(request['buffer_days']),
                    policy,
                )
            except (KeyError, ValueError) as e:
                return f'Escalate: invalid request ({e})', None, []
            row.update(need_date=need, latest_order_date=latest, result=result)
        candidates.append(row)

    # pick the one that gives us the most time to order
    recommended = [c for c in candidates if c['result'] == 'Recommend']
    if recommended:
        best = max(recommended, key=lambda c: (c['latest_order_date'], -c['conservative_lead_time_days']))
        return 'Recommend', best, candidates

    # too late for everyone, escalate but point to the fastest one
    late = [c for c in candidates if c['result'] == 'Escalate']
    if late:
        best = min(late, key=lambda c: c['conservative_lead_time_days'])
        return 'Escalate: order deadline already passed', best, candidates

    if any(c['result'] == 'Review required' for c in candidates):
        return 'Escalate: human review required', None, candidates

    # everyone is blocked or has no estimate, policy guide says escalate
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
    estimate, kind = load_estimator(reference)
    for name, request in DEMO_REQUESTS:
        print_result(name, *select_supplier(request, reference, estimate))
    if kind == 'model':
        print("\nLead times are the model's conservative delivery days.")
    else:
        print('\nNo model found (run src/train.py first), using the 90th percentile of past deliveries.')
