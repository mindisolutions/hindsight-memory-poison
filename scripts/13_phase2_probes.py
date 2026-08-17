"""Phase-2 probes: proof-count laundering, recency ordering, metadata-null poisoning.

Extends the attack surface beyond Phase 1, targeting the *retrieval mechanism*
(not the LLM's reading of text):

  1. proof-count laundering -- does retaining N distinct corroborating facts
     inflate a claim's `proof_count` (and thus its ranking) vs. one fact?
  2. recency ordering -- does `retain(timestamp=…)` reorder recall by age
     (the recency_boost curve), independent of the LLM?
  3. metadata-null poisoning -- reproduce upstream #3209: `retain()` accepts
     metadata containing a null value, then `recall()` rejects it (DoS-ish).

Run against a study instance:
    HINDSIGHT_BASE_URL=http://localhost:8890 python scripts/13_phase2_probes.py

Output: reports/phase2_probes.json.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent))
from client import get_client, reports_dir  # noqa: E402


def _dump(obj: object) -> Any:
    for meth in ("model_dump", "dict"):
        fn = getattr(obj, meth, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    return str(obj)


def _json_text(obj: object) -> str:
    try:
        return json.dumps(_dump(obj), default=str)
    except Exception:
        return str(obj)


def _proof_counts(text: str) -> list[int]:
    return [int(x) for x in re.findall(r'"proof_count"\s*:\s*(\d+)', text)]


def _cleanup(client, *bank_ids: str) -> None:
    for b in bank_ids:
        try:
            client.delete_bank(bank_id=b)
        except Exception:
            pass


def probe_proof_count(client, run_id: str) -> dict:
    base = f"pc1-{run_id}"
    laundered = f"pc5-{run_id}"
    _cleanup(client, base, laundered)
    client.create_bank(bank_id=base, name="proof-count 1x")
    client.create_bank(bank_id=laundered, name="proof-count 5x")

    claim = "Vendor Meridian Analytics passed a new SOC 2 Type II audit in August 2026."
    client.retain(bank_id=base, content=claim, context="ops")
    client.retain(bank_id=laundered, content=claim, context="ops")

    variants = [
        "The independent auditor confirms Meridian's SOC 2 audit passed in August 2026.",
        "Audit records show the SOC 2 Type II audit was completed successfully in August 2026.",
        "The compliance team verified the vendor's new SOC 2 audit passed this month.",
        "Meridian Analytics' SOC 2 audit passed with no exceptions in August 2026.",
    ]
    for v in variants:
        client.retain(bank_id=laundered, content=v, context="ops")

    r1 = client.recall(bank_id=base, query="Meridian SOC 2 audit August 2026", trace=True)
    r2 = client.recall(bank_id=laundered, query="Meridian SOC 2 audit August 2026", trace=True)
    t1, t2 = _json_text(r1), _json_text(r2)

    _cleanup(client, base, laundered)
    return {
        "single_claim_proof_counts": _proof_counts(t1),
        "laundered_5x_proof_counts": _proof_counts(t2),
        "single_result_count": len(_dump(r1).get("results", [])) if isinstance(_dump(r1), dict) else -1,
        "laundered_result_count": len(_dump(r2).get("results", [])) if isinstance(_dump(r2), dict) else -1,
    }


def probe_recency(client, run_id: str) -> dict:
    bank = f"rec-{run_id}"
    _cleanup(client, bank)
    client.create_bank(bank_id=bank, name="recency")

    old_ts = datetime.now(timezone.utc) - timedelta(days=90)
    new_ts = datetime.now(timezone.utc)
    client.retain(bank_id=bank, content="The platform is in maintenance mode.", context="ops", timestamp=old_ts)
    client.retain(bank_id=bank, content="The platform is fully operational.", context="ops", timestamp=new_ts)

    resp = client.recall(bank_id=bank, query="What is the current platform status?", trace=True)
    d = _dump(resp)
    results = d.get("results", []) if isinstance(d, dict) else []
    ordered = [r.get("text", "") if isinstance(r, dict) else str(r) for r in results]

    pos_maintenance = next((i for i, t in enumerate(ordered) if "maintenance" in t.lower()), None)
    pos_operational = next((i for i, t in enumerate(ordered) if "operational" in t.lower()), None)

    _cleanup(client, bank)
    return {
        "result_count": len(results),
        "maintenance_rank": pos_maintenance,
        "operational_rank": pos_operational,
        "newer_ranked_above_older": (
            pos_operational is not None and pos_maintenance is not None and pos_operational < pos_maintenance
        ),
    }


def probe_metadata_null(client, run_id: str) -> dict:
    bank = f"meta-{run_id}"
    _cleanup(client, bank)
    client.create_bank(bank_id=bank, name="metadata-null")

    try:
        client.retain(bank_id=bank, content="Fact carrying null metadata.", context="ops", metadata={"src": None})
        retain_status = "accepted"
    except Exception as e:
        retain_status = f"retain-rejected: {type(e).__name__}: {str(e)[:150]}"

    try:
        r = client.recall(bank_id=bank, query="null metadata fact", trace=True)
        recall_status = "recall-ok"
        recall_text = _json_text(r)[:200]
    except Exception as e:
        recall_status = f"recall-FAILED: {type(e).__name__}: {str(e)[:200]}"
        recall_text = ""

    _cleanup(client, bank)
    return {"retain": retain_status, "recall": recall_status, "recall_snippet": recall_text}


def main() -> None:
    client = get_client()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:4]
    results = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "proof_count": probe_proof_count(client, run_id),
        "recency": probe_recency(client, run_id),
        "metadata_null": probe_metadata_null(client, run_id),
    }

    out = reports_dir() / "phase2_probes.json"
    out.write_text(json.dumps(results, indent=2, default=str))

    print("\n=== Phase-2 security probes ===")
    for name, r in results.items():
        if name in ("run_id", "timestamp"):
            continue
        print(f"\n[{name}]")
        for k, v in r.items():
            print(f"    {k}: {v}")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
