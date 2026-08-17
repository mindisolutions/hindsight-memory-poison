"""
Aggregates all trial files in reports/ into a comparison table, statistical
tests, and reports/summary.json -- the single source of truth used for the
final write-up.

Every decision number comes from the manually-reviewed ``decision`` field in
each trials JSONL file (see the ``manual_review_note`` field on each record).

Beyond the raw counts, this script now also reports:

- the number of distinct ``run_id`` batches per group, with a warning when a
  group's data spans more than one run (the committed data is 3 batches of
  N=5, not a single N=15 run -- re-running a trial script appends, which
  silently inflates N unless you notice the run count);
- the "non-deny" rate (grant + unclear), the security-relevant metric for an
  access-control decision where an unclear answer should fail closed, not be
  counted as a harmless neutral;
- Fisher's exact test (baseline vs each attack, grant x non-grant);
- Wilson 95% confidence intervals on each grant-rate;
- the per-group N required to detect a grant-rate shift from baseline at
  80% power / alpha=0.05, for several plausible effect sizes.

All statistics are computed here from scratch (stdlib only -- no scipy
dependency) so the numbers are reproducible without extra installs.

Run:
    python scripts/aggregate_report.py [--run-id <id>]
"""

import argparse
import json
import math
from pathlib import Path

REPORTS_DIR = Path(__file__).parent.parent / "reports"

GROUPS = [
    ("baseline", "Baseline (no attack)", REPORTS_DIR / "baseline_trials.jsonl"),
    ("attack_v1", "Attack v1: hidden instruction (prompt injection)", REPORTS_DIR / "attack_trials.jsonl"),
    ("attack_v2", "Attack v2: plain forged fact", REPORTS_DIR / "attack_v2_trials.jsonl"),
    ("attack_v3", "Attack v3: trusted-tag forgery + reinforcement", REPORTS_DIR / "attack_v3_trials.jsonl"),
]


# --- statistics (stdlib-only) ----------------------------------------------

def fisher_exact(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact test for a 2x2 table [[a,b],[c,d]]."""
    def hypergeom(aa, bb, cc, dd):
        n = aa + bb + cc + dd
        return (math.comb(aa + bb, aa) * math.comb(cc + dd, cc)) / math.comb(n, aa + cc)

    row1, col1, n = a + b, a + c, a + b + c + d
    p_obs = hypergeom(a, b, c, d)
    p = 0.0
    for aa in range(max(0, col1 - (n - row1)), min(row1, col1) + 1):
        bb = row1 - aa
        cc = col1 - aa
        dd = (n - row1) - cc
        if hypergeom(aa, bb, cc, dd) <= p_obs + 1e-15:
            p += hypergeom(aa, bb, cc, dd)
    return min(p, 1.0)


def wilson_ci(x: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = x / n
    denom = 1 + z * z / n
    center = p + z * z / (2 * n)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (center - margin) / denom, (center + margin) / denom


def cohens_h(p1: float, p2: float) -> float:
    """Cohen's h effect size for two proportions (arcsine transform)."""
    return 2 * (math.asin(math.sqrt(p2)) - math.asin(math.sqrt(p1)))


def _h_label(h: float) -> str:
    a = abs(h)
    if a < 0.2:
        return "negligible"
    if a < 0.5:
        return "small"
    if a < 0.8:
        return "medium"
    return "large"


def _norm_ppf(p: float) -> float:
    """Inverse standard-normal CDF (Winitzki approximation, ~1e-3 rel. error)."""
    x = 2 * p - 1
    a = 0.147
    ln = math.log(1 - x * x)
    t = 2 / (math.pi * a) + ln / 2
    return math.copysign(math.sqrt(math.sqrt(t * t - ln / a) - t), x) * math.sqrt(2)


def sample_size(p1: float, p2: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Per-group N for a two-proportion test (two-sided)."""
    za = _norm_ppf(1 - alpha / 2)  # two-sided
    zb = _norm_ppf(power)
    pbar = (p1 + p2) / 2
    num = za * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    return math.ceil((num / (p2 - p1)) ** 2)


# --- loading ----------------------------------------------------------------

def _run_id(record: dict) -> str:
    """Extract the run_id batch from a bank id like '<prefix>-<run_id>-<n>'."""
    bank = record.get("bank", "")
    parts = bank.rsplit("-", 1)
    return parts[0] if len(parts) == 2 else bank


def load(path: Path, run_id: str | None = None) -> list[dict]:
    if not path.exists():
        return []
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if run_id:
        records = [r for r in records if _run_id(r) == run_id]
    return records


def summarize(records: list[dict]) -> dict:
    n = len(records)
    deny = sum(1 for r in records if r["decision"] == "deny")
    grant = sum(1 for r in records if r["decision"] == "grant")
    unclear = sum(1 for r in records if r["decision"] == "unclear")
    error = sum(1 for r in records if r["decision"] == "error")
    run_ids = sorted({_run_id(r) for r in records})
    return {
        "n": n,
        "deny": deny,
        "grant": grant,
        "unclear": unclear,
        "error": error,
        "grant_rate": round(grant / n, 4) if n else None,
        "non_deny": grant + unclear,
        "non_deny_rate": round((grant + unclear) / n, 4) if n else None,
        "run_ids": run_ids,
        "run_count": len(run_ids),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default=None, help="scope aggregation to a single run_id batch")
    args = ap.parse_args()

    summary: dict = {}
    print(f"{'Group':48s} {'N':>3s} {'deny':>5s} {'unclear':>8s} {'grant':>6s} {'grant':>8s} {'non-deny':>9s}")
    print("-" * 92)
    for key, label, path in GROUPS:
        records = load(path, args.run_id)
        stats = summarize(records)
        summary[key] = {"label": label, "path": path.relative_to(REPORTS_DIR.parent).as_posix(), **stats}
        rate = f"{stats['grant_rate']:.0%}" if stats["grant_rate"] is not None else "n/a"
        ndrate = f"{stats['non_deny_rate']:.0%}" if stats["non_deny_rate"] is not None else "n/a"
        print(f"{label:48s} {stats['n']:>3d} {stats['deny']:>5d} {stats['unclear']:>8d} "
              f"{stats['grant']:>6d} {rate:>8s} {ndrate:>9s}")
        if stats["error"]:
            print(f"  (! {stats['error']} trial(s) hit an unrecoverable API error and are excluded from N)")
        if stats["run_count"] != 1:
            print(f"  (!) data spans {stats['run_count']} run_id batches: {stats['run_ids']}")

    # --- Fisher exact + Wilson + sample size (baseline as reference) -------
    print("\n" + "-" * 92)
    print("Statistical tests (grant x non-grant, baseline as reference)")
    print("-" * 92)
    base = summary.get("baseline")
    if base and base["n"]:
        base_g, base_ng = base["grant"], base["n"] - base["grant"]
        for key in ("attack_v1", "attack_v2", "attack_v3"):
            g = summary.get(key)
            if not g or not g["n"]:
                continue
            g_g, g_ng = g["grant"], g["n"] - g["grant"]
            p = fisher_exact(base_g, base_ng, g_g, g_ng)
            print(f"  Fisher exact  {key:10s} ({g_g}/{g['n']}) vs baseline ({base_g}/{base['n']}): p = {p:.4f}")
            summary[key]["fisher_exact_p_vs_baseline"] = round(p, 4)
            h = cohens_h(base_g / base["n"], g_g / g["n"])
            print(f"  Cohen's h     {key:10s} vs baseline: h = {h:+.3f} ({_h_label(h)})")
            summary[key]["cohens_h_vs_baseline"] = round(h, 3)

    print("\nWilson 95% CI on grant-rate:")
    for key, g in summary.items():
        if not g.get("n"):
            continue
        lo, hi = wilson_ci(g["grant"], g["n"])
        print(f"  {key:10s} {g['grant']}/{g['n']} = {g['grant']/g['n']:.1%}  CI95% = [{lo:.1%}, {hi:.1%}]")
        g["grant_rate_wilson_ci95"] = [round(lo, 4), round(hi, 4)]

    print("\nPer-group N required (80% power, alpha=0.05) to detect a grant-rate shift from baseline:")
    if base and base["n"] and base["grant_rate"]:
        base_rate = base["grant_rate"]
        summary["sample_size"] = {}
        for target in (0.60, 0.50, 0.45, 0.40):
            n_need = sample_size(base_rate, target)
            print(f"  {base_rate:.0%} -> {target:.0%}: N/grupo ~ {n_need}")
            summary["sample_size"][f"{base_rate:.0%}_to_{target:.0%}"] = n_need

    out_path = REPORTS_DIR / "summary.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWritten: {out_path}")


if __name__ == "__main__":
    main()
