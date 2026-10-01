"""
AeroSecure AI - Synthetic Supply Chain Data Generator

Placeholder data standing in for the parts/inventory dataset Honeywell has not
yet delivered. Covers the supply chain side only. Sensor/degradation data comes
from NASA C-MAPSS (Turbofan Engine Degradation Simulation, dataset #6).

Link between the two: unit_number in this file matches the engine unit number
in C-MAPSS. So when the model flags engine 47, we look up part AER-0047 here to
get its inventory and lead time.

Usage:
    python generate_parts_data.py
    python generate_parts_data.py --parts 100 --seed 42
"""

import argparse
import csv
import random
from datetime import date, timedelta

# Component types found on a turbofan engine.
COMPONENT_TYPES = [
    "High Pressure Compressor",
    "Low Pressure Compressor",
    "High Pressure Turbine",
    "Low Pressure Turbine",
    "Combustor",
    "Fan Module",
    "Fuel Control Unit",
    "Bleed Air Valve",
    "Oil Pump Assembly",
    "Ignition Exciter",
]

# Made-up supplier names. Not real companies.
SUPPLIERS = [
    "Meridian Aerospace Components",
    "Talon Precision Systems",
    "Northgate Turbine Supply",
    "Vantage Aero Parts",
    "Sierra Industrial Group",
]

CRITICALITY = ["Critical", "Essential", "Routine"]

# Data restriction labels from the project brief.
RESTRICTION_LABELS = ["Restricted", "Authorized Access Required", "Unrestricted"]


def make_part(unit_number, rng, today):
    """Build one part record tied to a C-MAPSS engine unit."""
    component = rng.choice(COMPONENT_TYPES)
    criticality = rng.choices(CRITICALITY, weights=[2, 3, 5])[0]

    # Critical parts are rarer, pricier and slower to source.
    if criticality == "Critical":
        lead_time = rng.randint(84, 168)      # 12-24 weeks
        inventory = rng.randint(0, 4)
        unit_cost = rng.randint(18000, 95000)
    elif criticality == "Essential":
        lead_time = rng.randint(42, 112)      # 6-16 weeks
        inventory = rng.randint(1, 12)
        unit_cost = rng.randint(4000, 22000)
    else:
        lead_time = rng.randint(7, 56)        # 1-8 weeks
        inventory = rng.randint(3, 40)
        unit_cost = rng.randint(200, 5000)

    monthly_usage = max(1, round(rng.gauss(inventory * 0.8 + 3, 3)))
    flight_cycles = rng.randint(180, 3200)
    days_since_maint = rng.randint(5, 420)
    last_maintenance = today - timedelta(days=days_since_maint)

    # Restriction label leans on criticality, but not rigidly.
    if criticality == "Critical":
        restriction = rng.choices(RESTRICTION_LABELS, weights=[5, 4, 1])[0]
    elif criticality == "Essential":
        restriction = rng.choices(RESTRICTION_LABELS, weights=[1, 5, 4])[0]
    else:
        restriction = rng.choices(RESTRICTION_LABELS, weights=[1, 2, 7])[0]

    return {
        "part_number": f"AER-{unit_number:04d}",
        "unit_number": unit_number,
        "component_type": component,
        "criticality": criticality,
        "current_inventory": inventory,
        "monthly_usage": monthly_usage,
        "lead_time_days": lead_time,
        "unit_cost_usd": unit_cost,
        "supplier": rng.choice(SUPPLIERS),
        "flight_cycles": flight_cycles,
        "last_maintenance_date": last_maintenance.isoformat(),
        "restriction_label": restriction,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate placeholder parts/inventory data for AeroSecure AI."
    )
    parser.add_argument("--parts", type=int, default=100,
                        help="Number of parts to generate (default 100, "
                             "matching the 100 engines in C-MAPSS FD001).")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed, so everyone gets the same file.")
    parser.add_argument("--output", default="parts_inventory.csv",
                        help="Output CSV filename.")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    today = date.today()

    rows = [make_part(i, rng, today) for i in range(1, args.parts + 1)]

    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} parts to {args.output}")
    print(f"Seed {args.seed} - rerunning with the same seed gives the same file.")

    crit_counts = {}
    for r in rows:
        crit_counts[r["criticality"]] = crit_counts.get(r["criticality"], 0) + 1
    print("Criticality split:", crit_counts)

    at_risk = [r for r in rows if r["current_inventory"] <= 1]
    print(f"Parts with 0-1 in stock: {len(at_risk)}")


if __name__ == "__main__":
    main()
