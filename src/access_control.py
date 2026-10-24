# Role-based access for orders. Uses the data_access_classification label
# and can_read() from policy.py. Unknown roles/labels get denied.
# Usage: python src/access_control.py --role student --user jad
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

from policy import ROLE_CLEARANCE, can_read
from validate_data import read

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = ROOT / 'artifacts' / 'logs' / 'access_log.csv'
LOG_COLUMNS = ['timestamp_utc', 'user', 'role', 'requested', 'allowed', 'denied']


def filter_records(rows, role):
    allowed = []
    denied = []
    for row in rows:
        label = row.get('data_access_classification')
        if can_read(role, label):
            allowed.append(row)
        else:
            denied.append(row)
    return allowed, denied


def log_request(user, role, requested, allowed, denied, log_path=DEFAULT_LOG):
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not log_path.exists()

    with log_path.open('a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
        if new_file:
            writer.writeheader()
        writer.writerow({
            'timestamp_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'user': user,
            'role': role,
            'requested': requested,
            'allowed': allowed,
            'denied': denied,
        })


# this is what the backend should call
# denied rows are only counted, never returned
def get_records(rows, user, role, log_path=DEFAULT_LOG):
    allowed, denied = filter_records(rows, role)
    log_request(user, role, len(rows), len(allowed), len(denied), log_path)
    return allowed


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--role', required=True, help='student, mentor or administrator')
    parser.add_argument('--user', required=True)
    parser.add_argument('--data', default=ROOT / 'data' / 'raw' / 'orders.csv')
    args = parser.parse_args()

    if args.role not in ROLE_CLEARANCE:
        print(f'Warning: "{args.role}" is not a known role, everything will be denied.')

    rows = read(args.data)
    visible = get_records(rows, args.user, args.role)

    print(f'{args.user} ({args.role}) requested {len(rows)} orders')
    print(f'  allowed: {len(visible)}')
    print(f'  denied:  {len(rows) - len(visible)}')
    print(f'Logged to {DEFAULT_LOG}')
