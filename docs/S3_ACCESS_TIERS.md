# S3 access tiers

The 20,000 orders are split into 3 files by their data access label, so restricted data can be kept in its own place.

## Making the files

```
python src/create_access_tiers.py
```

This writes 3 files to `artifacts/access-tiers/` (not committed):

| Tier | Orders |
|---|---|
| unrestricted | 6,637 |
| restricted | 6,740 |
| highly-restricted | 6,623 |
| **total** | **20,000** |

`tests/test_access_tiers.py` checks the totals add up, each file only has its own label, no order is lost or duplicated, and the columns match the original file.

## Where they are in S3

Aaron set these up in `asu-capstone-data-bucket` on Oct 20:

- `raw/unrestricted/orders.csv`
- `raw/restricted/orders.csv`
- `raw/highly-restricted/orders.csv` (plus `audit/` and `combined/`)

Our team's training data is separate, under `capstone/v1/team-01/` (`full/` and `smoke/`).

## Who can read what

Right now our AWS student role can open all 3 tiers.
For the app itself, access is enforced in our code:

- `src/access_control.py` and `/orders` only return the orders a role is allowed to see (student: unrestricted, mentor: + restricted, administrator: everything)
- unknown roles or labels are denied, and every request is logged
- Jesus's login (Sprint 5) makes the role come from logging in instead of a header

## For a real deployment

The app's users would never log in to AWS. The backend would read the data from S3 with its own role, and the restricted folders would be locked so only the right roles (or the backend) can open them. That way going around the app doesn't get you the restricted data.
