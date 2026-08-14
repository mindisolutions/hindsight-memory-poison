# Contributing

Thank you for your interest in contributing. This is a security-research
repository, so we value **reproducibility and honest reporting** above cleverness:
every result committed here must be backed by real trial data, and findings that
do not hold up to testing are corrected rather than defended.

## Getting started

### Prerequisites

- **Python 3.10 or 3.12** (the code uses PEP 604/585 syntax — `str | None`,
  `list[...]` — so 3.8/3.9 will not run).
- A running **Hindsight** instance with its API reachable. See
  [`docker-compose.yml`](docker-compose.yml) for the Postgres backend this lab
  uses. The `hindsight_client` SDK is pulled in via `requirements.txt`.
- An LLM backend. The original study used a local `llama3.2:3b` via Ollama;
  the stress-test matrix additionally used DeepSeek and OpenRouter. See
  [`.env.example`](.env.example) for the connection variables.

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in HINDSIGHT_BASE_URL, provider keys, etc.
```

## Running the experiments

The study is organized as a numbered sequence of trial scripts:

| Script | Purpose |
| ------ | ------- |
| `scripts/01_baseline_trials.py` | Baseline (no attack) — measures the model's natural error rate |
| `scripts/02_attack_trials.py` … `scripts/10_attack_v7_authority.py` | Attack techniques v1–v7 |
| `scripts/11_retrieval_probe.py` | Probes Hindsight's retrieval internals (no reflect) |
| `scripts/aggregate_report.py` | Regenerates the summary tables/statistics from raw trial files |
| `scripts/client.py` | Shared SDK wrapper (use this, not raw HTTP) |

Run a single group, for example:

```bash
python scripts/01_baseline_trials.py
```

Then regenerate the aggregate report:

```bash
python scripts/aggregate_report.py
```

### Important notes

- **Do not run trial scripts concurrently** — they race on the LLM backend and,
  if bank IDs collide, on the same bank. A lock file (`reports/.trials.lock`)
  enforces this, but do not bypass it.
- `legacy_attacks/` is **reference-only** and intentionally does not import
  cleanly (it depends on symbols removed from `client.py`). Do not "fix" it.
- Every result must be manually reviewed; see the Methodology section in the
  [README](README.md). The automated decision classifier is a first-pass triage,
  not ground truth.

## Linting and CI

```bash
pylint scripts/ --rcfile=.pylintrc
```

CI runs Pylint on Python 3.10 and 3.12 (`.github/workflows/pylint.yml`). Keep it
green.

## Pull requests

1. Open an issue first for anything non-trivial, so the direction can be agreed.
2. Create a feature branch and keep commits focused.
3. Run the linter and, where your change touches experiment logic, re-run the
   relevant script to confirm it still produces data.
4. Fill in the pull-request template and reference the issue.

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).
