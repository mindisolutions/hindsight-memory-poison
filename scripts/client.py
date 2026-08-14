"""
Thin wrapper around Hindsight for this lab.

Uses the official `hindsight_client` SDK for retain/recall/reflect and bank
management (documented, stable). All trial scripts (00-04) go through
`get_client()`.

There is no raw-HTTP fallback here anymore: bank creation is done via the
SDK's `create_bank`/`delete_bank`. The legacy memory-defense scaffold that
used a raw-HTTP `ensure_bank`/`set_memory_defense` path was moved to
`legacy_attacks/` and is unmaintained.
"""

import os

from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

BASE_URL = os.environ.get("HINDSIGHT_BASE_URL", "http://localhost:8888")
TENANT = "default"


def get_client() -> Hindsight:
    return Hindsight(base_url=BASE_URL)
