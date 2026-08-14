"""
F4 validation: demonstrate recall() logging end-to-end.

Runs a small number of baseline trials (no attack) through the REAL
Hindsight + llama3.2:3b stack and writes each trial's `recalled_memories`
field to a SEPARATE file (reports/recall_logged_demo.jsonl) so the committed
study data (reports/baseline_trials.jsonl) is not polluted.

This is the committed artifact backing finding 2's mechanism claim: it shows
what retain() actually extracted and what recall() returns for the forged-vs-
legitimate payload, instead of relying on manual inspection.
"""
import importlib.util as _ilu
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from client import get_client  # noqa: E402

_spec = _ilu.spec_from_file_location("baseline_trials", Path(__file__).parent / "01_baseline_trials.py")
assert _spec is not None and _spec.loader is not None
_b = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_b)

FACTS = _b.FACTS
DECISION_QUERY = _b.DECISION_QUERY
classify_decision = _b.classify_decision
reflect_with_retry = _b.reflect_with_retry
log_recall = _b.log_recall

OUT = Path(__file__).parent.parent / "reports" / "recall_logged_demo.jsonl"


def run_one(client, n):
    bank = f"recall-demo-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{n}"
    try:
        client.delete_bank(bank_id=bank)
    except Exception:
        pass
    client.create_bank(bank_id=bank, name=f"F4 recall-logging demo trial {n}")
    for fact in FACTS:
        client.retain(bank_id=bank, content=fact, context="security_review_note")
    recalled = log_recall(client, bank)
    try:
        result = reflect_with_retry(client, bank, DECISION_QUERY)
        answer = getattr(result, "answer", None) or getattr(result, "text", None) or str(result)
        decision = classify_decision(answer)
    except Exception as exc:
        answer = f"[ERROR after retries] {exc}"
        decision = "error"
    record = {
        "trial": n,
        "bank": bank,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "recalled_memories": recalled,
        "answer": answer,
        "decision": decision,
    }
    return record


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    client = get_client()
    records = []
    try:
        for i in range(1, n + 1):
            print(f"[F4 demo trial {i}/{n}] running...", flush=True)
            rec = run_one(client, i)
            records.append(rec)
            print(f"  decision={rec['decision']!r}")
            print(f"  recalled_memories ({len(rec['recalled_memories'])} chars):")
            print("    " + rec["recalled_memories"][:400].replace("\n", "\n    "))
    finally:
        client.close()

    with OUT.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nWritten {len(records)} records to {OUT}")


if __name__ == "__main__":
    main()
