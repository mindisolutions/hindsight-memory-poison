# Legacy scaffold — unpublished, no results

This directory is the **original generic-scenario scaffold** for a second
research line that was **never completed or published**:

- **Memory Defense bypass** (`02_secret_exfiltration.py` + `secret_variants.py`)
  — probing Hindsight's opt-in regex redaction (45 predefined patterns) against
  a battery of obfuscation variants (base64, zero-width chars, split-across-lines,
  described-not-shown, partial truncation).
- **Trust-boundary / confused-deputy** (`03_trusted_tag_forgery.py`) — early
  exploration of the same `context`-forgery idea that the active study now tests
  properly in `scripts/04_attack_v3_trials.py`.
- **Prompt injection** (`01_prompt_injection_retain.py`) — the original
  "scraped page" injection, superseded by `scripts/02_attack_trials.py`.

**No results for this line exist in `reports/`.** It is kept only as reference
code. Do not cite it as evidence — there is no committed outcome.

## Why this is here and not in `scripts/`

The active study (`scripts/00`–`04`) is a single coherent experiment (the
Meridian vendor-access scenario, N trials per group, hand-reviewed). This
scaffold is a *different* research line (memory-defense redaction testing) that
was never run to completion. Mixing them implied results that don't exist, so
the scaffold was moved out of the active tree.

## Notes for anyone who wants to revive it

- These scripts depend on a raw-HTTP bank-management path (`ensure_bank`,
  `set_memory_defense`) and `CONTROL_BANK`/`DEFENDED_BANK` constants that were
  **removed from `scripts/client.py`**. Recover them from git history
  (`git log -p -- scripts/client.py`) if needed — the SDK's `create_bank` /
  bank-config methods are the supported replacement.
- `secret_variants.py` is a genuinely useful obfuscation test battery and is
  worth reusing in any regex-based secret/PII detection test, independent of
  this scaffold.
