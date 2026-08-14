"""
Thin wrapper around Hindsight for this lab.

Uses the official `hindsight_client` SDK for retain/recall/reflect (documented,
stable), and raw HTTP via `requests` for bank creation / memory_defense config,
since those are less consistently documented and may need adjusting against
whatever SDK version you actually install -- run `dir(client)` / check
`hindsight_client`'s installed source if a call here 404s.
"""
import os

import requests
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

BASE_URL = os.environ.get("HINDSIGHT_BASE_URL", "http://localhost:8888")
TENANT = "default"

CONTROL_BANK = "attack-lab-control"      # memory_defense disabled
DEFENDED_BANK = "attack-lab-defended"    # memory_defense enabled


def get_client() -> Hindsight:
    return Hindsight(base_url=BASE_URL)


def _v1(path: str) -> str:
    return f"{BASE_URL}/v1/{TENANT}/{path.lstrip('/')}"


def ensure_bank(bank_id: str) -> None:
    """Create the bank if it doesn't already exist. Idempotent."""
    resp = requests.put(_v1(f"banks/{bank_id}"), json={})
    if resp.status_code not in (200, 201, 409):
        raise RuntimeError(f"Failed to create bank {bank_id}: {resp.status_code} {resp.text}")


def set_memory_defense(bank_id: str, enabled: bool, rules: list[dict] | None = None) -> None:
    payload = {
        "updates": {
            "memory_defense": {
                "enabled": enabled,
                "rules": rules or [{"on": "sensitive_data", "action": "redact"}],
            }
        }
    }
    resp = requests.patch(_v1(f"banks/{bank_id}/config"), json=payload)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Failed to set memory_defense on {bank_id}: {resp.status_code} {resp.text}"
        )


def append_result(record: dict) -> None:
    import json
    from pathlib import Path

    out = Path(__file__).parent.parent / "reports" / "results.jsonl"
    out.parent.mkdir(exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
