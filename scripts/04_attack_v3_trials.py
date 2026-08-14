"""
Attack trials, variant 3 -- trusted-tag forgery + plain forged fact, on the
Meridian Analytics vendor-access scenario.

Difference from variant 2 (scripts/03_attack_v2_trials.py): v2's forged
content was retain()ed with context="web_scrape:..." (an external, less
trusted source label) and competed as one memory among many. This variant
tests two escalations at once:

  1. Trusted-tag forgery: the forged claim is retain()ed with
     context="security_review_note" -- the exact same label used for the
     5 legitimate internal facts. Hindsight's `context` field is just a
     caller-supplied string with no authentication, so nothing stops an
     attacker who controls one ingestion path from spoofing it. This is
     the "trusted source" hypothesis from attacks/03_trusted_tag_forgery.py
     in the original lab, applied to our higher-stakes scenario.
  2. Reinforcement: the forged claim is retain()ed twice (two separate
     "internal notes" asserting the same renewal), to test whether
     redundant corroboration raises its rank in recall()'s hybrid
     semantic+bm25+reranking pipeline relative to a single mention.

Run:
    python scripts/04_attack_v3_trials.py [N]
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from client import get_client  # noqa: E402
import importlib.util as _ilu  # noqa: E402

_baseline_spec = _ilu.spec_from_file_location("baseline_trials", Path(__file__).parent / "01_baseline_trials.py")
assert _baseline_spec is not None and _baseline_spec.loader is not None
_baseline = _ilu.module_from_spec(_baseline_spec)
_baseline_spec.loader.exec_module(_baseline)

FACTS = _baseline.FACTS
DECISION_QUERY = _baseline.DECISION_QUERY
EXPECTED_DECISION = _baseline.EXPECTED_DECISION
classify_decision = _baseline.classify_decision
reflect_with_retry = _baseline.reflect_with_retry

PAYLOAD_PATH = Path(__file__).parent.parent / "payloads" / "forged_meridian_audit_v3.txt"
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
BANK_PREFIX = f"attack-v3-trial-{RUN_ID}"
OUT_PATH = Path(__file__).parent.parent / "reports" / "attack_v3_trials.jsonl"
LOCK_PATH = Path(__file__).parent.parent / "reports" / ".trials.lock"

# The forged claim is retain()ed under the SAME context label as the real
# internal facts -- trusted-tag forgery, not labeled as an external source.
FORGED_CONTEXT = "security_review_note"


def run_trial(client, trial_num: int, payload: str) -> dict:
    bank_id = f"{BANK_PREFIX}-{trial_num}"
    try:
        client.delete_bank(bank_id=bank_id)
    except Exception:
        pass
    client.create_bank(bank_id=bank_id, name=f"Attack v3 trial {trial_num} (trusted-tag forgery + reinforcement)")

    for fact in FACTS:
        client.retain(bank_id=bank_id, content=fact, context="security_review_note")

    # Forged claim, retained TWICE, under the trusted internal label.
    client.retain(bank_id=bank_id, content=payload, context=FORGED_CONTEXT)
    client.retain(bank_id=bank_id, content=payload, context=FORGED_CONTEXT)

    t0 = time.monotonic()
    try:
        result = reflect_with_retry(client, bank_id, DECISION_QUERY)
        elapsed = time.monotonic() - t0
        answer = getattr(result, "answer", None) or getattr(result, "text", None) or str(result)
        decision = classify_decision(answer)
    except Exception as exc:
        elapsed = time.monotonic() - t0
        answer = f"[ERROR after retries] {exc}"
        decision = "error"

    record = {
        "trial": trial_num,
        "bank": bank_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reflect_seconds": round(elapsed, 2),
        "answer": answer,
        "decision": decision,
        "automated_decision": decision,
        "expected_decision": EXPECTED_DECISION,
        "matches_expected": decision == EXPECTED_DECISION,
        "attack": "meridian_audit_trusted_tag_forgery_v3",
    }
    return record


def main() -> None:
    if LOCK_PATH.exists():
        print(
            f"[ERROR] Another trial run appears to be in progress "
            f"(lock file {LOCK_PATH} exists). Wait for it to finish, or "
            f"delete the lock file if you're sure no other run is active."
        )
        sys.exit(1)

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    client = get_client()
    payload = PAYLOAD_PATH.read_text(encoding="utf-8").strip()

    OUT_PATH.parent.mkdir(exist_ok=True)
    LOCK_PATH.write_text(RUN_ID, encoding="utf-8")
    records = []
    try:
        print(f"Running {n} attack v3 trials (trusted-tag forgery + reinforcement)...\n")
        for i in range(1, n + 1):
            print(f"[trial {i}/{n}] running...", flush=True)
            record = run_trial(client, i, payload)
            records.append(record)
            with OUT_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"[trial {i}/{n}] decision={record['decision']!r} "
                  f"(expected={EXPECTED_DECISION!r}) in {record['reflect_seconds']}s")
    finally:
        LOCK_PATH.unlink(missing_ok=True)
        client.close()

    grants = sum(1 for r in records if r["decision"] == "grant")
    denies = sum(1 for r in records if r["decision"] == "deny")
    unclear = sum(1 for r in records if r["decision"] == "unclear")
    correct = sum(1 for r in records if r["matches_expected"])

    print("\n=== SUMMARY (automated classification -- verify manually before reporting) ===")
    print(f"Trials: {n}")
    print(f"  grant:   {grants}  <-- attack success if this is elevated vs baseline")
    print(f"  deny:    {denies}")
    print(f"  unclear: {unclear}")
    print(f"Matches expected decision ({EXPECTED_DECISION}): {correct}/{n}")
    print(f"\nRaw records appended to: {OUT_PATH}")


if __name__ == "__main__":
    main()
