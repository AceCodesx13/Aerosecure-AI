import sys
from functools import lru_cache
from pathlib import Path

# so we can import from src/
SRC = Path(__file__).resolve().parents[3] / "src"
sys.path.insert(0, str(SRC))

from access_control import DEFAULT_LOG, get_records
from policy import ROLE_CLEARANCE
from validate_data import read

ORDERS_FILE = SRC.parent / "data" / "raw" / "orders.csv"
LOG_PATH = DEFAULT_LOG


@lru_cache
def load_orders():
    return read(ORDERS_FILE)


def is_known_role(role: str) -> bool:
    return role in ROLE_CLEARANCE


def get_orders_for(user: str, role: str):
    return get_records(load_orders(), user, role, LOG_PATH)
