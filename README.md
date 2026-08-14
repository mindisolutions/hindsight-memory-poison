# Hindsight Memory Poisoning

Security research project against [Hindsight](https://github.com/vectorize-io/hindsight) (Vectorize),
an open-source agent memory system (retain / recall / reflect). This runs against a **real, local
Hindsight instance** (Docker, Postgres-backed) reasoning with a real local LLM (Ollama, `llama3.2:3b`)
— nothing here is mocked or simulated.

## Result, in short

60 trials (4 groups × N=15, all hand-reviewed) testing whether forged content injected via
`retain()` can flip a security decision. **No technique clearly beat this local model's own 27%
baseline error rate in aggregate** — but in 4 individual trials the model's wrong decision
**explicitly quoted the forged fact by name** as its reason. See [Results](#results-n15-per-group-manually-reviewed)
below for the full table, and [`reports/REPORT.md`](reports/REPORT.md) for the write-up with
evidence exhibits.

## Case study: does memory poisoning change a real access-control decision?

Rather than testing abstract prompt-injection tricks, every script in this repo runs the same
concrete scenario: a security-review assistant deciding whether to grant a third-party vendor
("Meridian Analytics") API access to a production customer database that contains PII. The
scenario is seeded with facts that should produce one correct decision — **deny** — because the
vendor's SOC 2 Type II audit has expired and they have a documented prior data-leak incident.

We then test whether an attacker who can get content into the bank via `retain()` (e.g. a
compromised web-scraping tool, or a note-taking integration) can flip that decision, across three
escalating techniques:

| Group | Script | Technique |
|---|---|---|
| Baseline | `scripts/01_baseline_trials.py` | No attack. Measures the model's own natural error rate on this decision. |
| Attack v1 | `scripts/02_attack_trials.py` | Hidden imperative instruction inside an HTML comment in "scraped" content (classic prompt injection). |
| Attack v2 | `scripts/03_attack_v2_trials.py` | Same forged claim, but with no instruction framing — just written as ordinary page content. |
| Attack v3 | `scripts/04_attack_v3_trials.py` | The forged claim retained twice, under the **same `context` label used for legitimate internal facts** (trusted-tag forgery) instead of a "web scrape" label. |

### Methodology

- Each group runs **N=15 independent trials**, each in its own freshly-created, isolated bank
  (no state leaks between trials).
- `reflect()`'s free-text answer is auto-classified (`grant`/`deny`/`unclear`) by a regex heuristic
  in `01_baseline_trials.py::classify_decision`, **then every single trial is manually re-read**
  and corrected where the heuristic misfired (it reliably struggles with hedging language and
  headings that contain the word "grant"/"granting" out of context). The `manual_review_note`
  field on every record in `reports/*.jsonl` documents why. Treat `automated_decision` as a
  first-pass triage, not ground truth.
- Concurrent trial runs corrupt results (they'd race on Ollama and, if bank IDs collided, on the
  same bank). A lock file (`reports/.trials.lock`) prevents two trial scripts from running at once.
- `reflect_with_retry` (in `01_baseline_trials.py`) retries `reflect()` up to 4 times on failure —
  the local `llama3.2:3b` intermittently emits a malformed internal tool-call and Hindsight
  surfaces that as a 500 instead of retrying itself. This is a real robustness limitation of the
  local-LLM setup, not a bug in this lab's scripts.

### Results (N=15 per group, manually reviewed)

Run `python scripts/aggregate_report.py` to regenerate this table from the raw trial files.

| Group | deny | unclear | grant | grant rate |
|---|---|---|---|---|
| Baseline (no attack) | 8 | 3 | 4 | 27% |
| Attack v1 (hidden instruction) | 12 | 2 | 1 | 7% |
| Attack v2 (plain forged fact) | 8 | 5 | 2 | 13% |
| Attack v3 (trusted-tag forgery) | 8 | 3 | 4 | 27% |

Key findings:

1. **The model has substantial baseline noise.** Even with zero attack, this local LLM
   recommends granting access ~1 in 4 times, purely from its own reasoning errors. At N=15, none
   of the three attack variants' aggregate grant rate is convincingly distinguishable from that
   27% noise floor — v1 and v2 actually landed *below* it, and v3 landed exactly on it. **Do not
   report "grant rate" alone as evidence an attack works** — see finding 3 below for why the
   aggregate rate understates what's actually happening.
2. **Instruction-based injection (v1) was largely neutralized at the data layer.** Hindsight's
   `retain()` extraction step preserves plain factual sentences but tends to drop imperative
   "obey this" framing — the hidden instruction never survived as a retrievable memory, only the
   underlying false claim did.
3. **The forged claim demonstrably enters the reasoning chain and can flip individual decisions
   — the aggregate rate just doesn't prove it statistically at this sample size.** In several
   attack v1 and v3 trials, the model's `grant` recommendation **explicitly cited the forged audit
   claim by name and date** as its justification (e.g. "they have also passed a SOC 2 Type II
   audit in August 2026" — a fact that only exists because we injected it). See the
   `manual_review_note` field on individual records in `reports/attack_trials.jsonl` and
   `reports/attack_v3_trials.jsonl` for exact quotes. This is real, causal, per-trial evidence of
   memory poisoning — it just doesn't clear the noise floor in aggregate at N=15. A pilot run of
   attack v3 (first 5 trials only) showed a 60% grant rate; the full N=15 run regressed to 27%,
   which is itself a useful methodological lesson: **small pilot samples overstate effect size**,
   and any claim from a small N needs a larger confirmatory run before being trusted.
4. **Next step to actually pin down effect size:** a much larger N (order of 50+ per group) or a
   stronger, less noisy LLM backend would be needed to statistically separate a real attack effect
   from this model's own ~27% baseline error rate. That is out of scope for this local/free setup
   but is the right next experiment.

## Setup

1. Docker Desktop running, Ollama running locally with `llama3.2:3b` pulled
   (`ollama pull llama3.2:3b`). `.env` is already configured to point at Ollama by default — see
   `.env.example` if you want to use a paid API (OpenAI/Anthropic) instead.
2. Start Hindsight: `docker compose up -d` (exposes the API on `http://localhost:8888`).
3. Install Python deps: `pip install -r requirements.txt`.
4. Reproduce a trial sweep, e.g.:

   ```bash
   python scripts/01_baseline_trials.py 15   # control group
   python scripts/02_attack_trials.py 15     # attack v1
   python scripts/03_attack_v2_trials.py 15  # attack v2
   python scripts/04_attack_v3_trials.py 15  # attack v3
   python scripts/aggregate_report.py        # comparison table + reports/summary.json
   ```

   Run these **one at a time** — the lock file will refuse a second concurrent run. VS Code launch
   configs for all of the above are in `.vscode/launch.json`.
5. Every trial answer is manually spot-checked before being trusted (see Methodology above) — do
   not report `automated_decision` numbers without reading the underlying `answer` text.

## Layout

```
hindsight-memory-poison/
  docker-compose.yml            # local Hindsight + Postgres
  .env.example / .env
  requirements.txt
  scripts/
    client.py                   # thin wrapper around hindsight_client
    setup_banks.py               # legacy: creates control + defended banks (Memory Defense demo)
    00_baseline_demo.py         # single-run walkthrough of retain/recall/reflect (teaching aid)
    01_baseline_trials.py       # N-trial control group + shared classify_decision/reflect_with_retry
    02_attack_trials.py         # N-trial attack v1 (hidden instruction)
    03_attack_v2_trials.py      # N-trial attack v2 (plain forged fact)
    04_attack_v3_trials.py      # N-trial attack v3 (trusted-tag forgery)
    aggregate_report.py         # reports/*.jsonl -> comparison table + summary.json
  payloads/
    forged_meridian_audit.md    # attack v1 payload (hidden instruction)
    forged_meridian_audit_v2.md # attack v2 payload (plain forged fact)
    forged_meridian_audit_v3.txt # attack v3 payload (retained under a forged trusted tag)
  attacks/                      # original generic-scenario scaffold (superseded by scripts/ above,
                                 # kept for reference -- see git history / original README scope)
  reports/
    baseline_trials.jsonl       # one JSON record per trial, manually reviewed
    attack_trials.jsonl
    attack_v2_trials.jsonl
    attack_v3_trials.jsonl
    summary.json                # generated by aggregate_report.py
```

## Known limitations

- N=15 per group is enough to see a clear signal for attack v3, but is thin for precise
  statistics on v1/v2 (their grant rates are within baseline noise range). More trials would
  tighten the confidence interval.
- `llama3.2:3b` is a weak model chosen for local/free reproducibility. A stronger model would
  likely show a lower baseline error rate and could react differently to the same payloads —
  results here characterize *this* model + Hindsight combination, not "LLMs in general."
- The automated decision classifier is a heuristic (see Methodology). All numbers reported here
  were corrected by manual review; do not trust `automated_decision` alone.
