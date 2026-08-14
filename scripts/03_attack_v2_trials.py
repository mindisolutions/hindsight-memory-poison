"""
Attack trials, variant 2 -- plain forged fact via retain() (no hidden
instruction), on the Meridian Analytics vendor-access scenario.

Difference from scripts/02_attack_trials.py (variant 1): that version hid
an imperative "SYSTEM NOTE" instruction inside an HTML comment, telling
the reasoning step to prioritize the forged claim and ignore the real
facts. Inspection of recall() output showed that instruction was
*not* preserved as an extracted fact -- only the plain factual sentence
was. This variant tests whether dropping the instruction framing
entirely, and just asserting the lie as ordinary vendor-page content,
lets it compete on equal footing with the real facts (since we already
know from v1 that plain factual sentences DO survive extraction intact).

Run:
    python scripts/03_attack_v2_trials.py [N]
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
log_recall = _baseline.log_recall

PAYLOAD_PATH = Path(__file__).parent.parent / "payloads" / "forged_meridian_audit_v2.md"
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
BANK_PREFIX = f"attack-v2-trial-{RUN_ID}"
OUT_PATH = Path(__file__).parent.parent / "reports" / "attack_v2_trials.jsonl"
LOCK_PATH = Path(__file__).parent.parent / "reports" / ".trials.lock"


def run_trial(client, trial_num: int, payload: str) -> dict:
    bank_id = f"{BANK_PREFIX}-{trial_num}"
    try:
        client.delete_bank(bank_id=bank_id)
    except Exception:
        pass
    client.create_bank(bank_id=bank_id, name=f"Attack v2 trial {trial_num} (plain forged fact via retain)")

    for fact in FACTS:
        client.retain(bank_id=bank_id, content=fact, context="security_review_note")

    client.retain(
        bank_id=bank_id,
        content=payload,
        context="web_scrape:meridiananalytics.example/trust",
    )

    recalled = log_recall(client, bank_id)

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
        "recalled_memories": recalled,
        "expected_decision": EXPECTED_DECISION,
        "matches_expected": decision == EXPECTED_DECISION,
        "attack": "meridian_audit_plain_forged_fact_v2",
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
    payload = PAYLOAD_PATH.read_text(encoding="utf-8")

    OUT_PATH.parent.mkdir(exist_ok=True)
    LOCK_PATH.write_text(RUN_ID, encoding="utf-8")
    records = []
    try:
        print(f"Running {n} attack v2 trials (plain forged fact via retain)...\n")
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
