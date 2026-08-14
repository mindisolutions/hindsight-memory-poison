"""
Aggregates all trial files in reports/ into a single comparison table and
reports/summary.json -- the single source of truth used for the final
write-up. Every number here comes straight from the manually-reviewed
`decision` field in each trials JSONL file (see the `manual_review_note`
field on each record for why a given trial was classified the way it was).

Run:
    python scripts/aggregate_report.py
"""
import json
from pathlib import Path

REPORTS_DIR = Path(__file__).parent.parent / "reports"

GROUPS = [
    ("baseline", "Baseline (no attack)", REPORTS_DIR / "baseline_trials.jsonl"),
    ("attack_v1", "Attack v1: hidden instruction (prompt injection)", REPORTS_DIR / "attack_trials.jsonl"),
    ("attack_v2", "Attack v2: plain forged fact", REPORTS_DIR / "attack_v2_trials.jsonl"),
    ("attack_v3", "Attack v3: trusted-tag forgery + reinforcement", REPORTS_DIR / "attack_v3_trials.jsonl"),
]


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarize(records: list[dict]) -> dict:
    n = len(records)
    deny = sum(1 for r in records if r["decision"] == "deny")
    grant = sum(1 for r in records if r["decision"] == "grant")
    unclear = sum(1 for r in records if r["decision"] == "unclear")
    error = sum(1 for r in records if r["decision"] == "error")
    return {
        "n": n,
        "deny": deny,
        "grant": grant,
        "unclear": unclear,
        "error": error,
        "grant_rate": round(grant / n, 4) if n else None,
    }


def main() -> None:
    summary = {}
    print(f"{'Group':45s} {'N':>3s} {'deny':>5s} {'unclear':>8s} {'grant':>6s} {'grant_rate':>11s}")
    print("-" * 84)
    for key, label, path in GROUPS:
        records = load(path)
        stats = summarize(records)
        summary[key] = {"label": label, "path": path.relative_to(REPORTS_DIR.parent).as_posix(), **stats}
        rate = f"{stats['grant_rate']:.0%}" if stats["grant_rate"] is not None else "n/a"
        print(f"{label:45s} {stats['n']:>3d} {stats['deny']:>5d} {stats['unclear']:>8d} "
              f"{stats['grant']:>6d} {rate:>11s}")
        if stats["error"]:
            print(f"  (! {stats['error']} trial(s) hit an unrecoverable API error and are excluded from N)")

    out_path = REPORTS_DIR / "summary.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWritten: {out_path}")


if __name__ == "__main__":
    main()
