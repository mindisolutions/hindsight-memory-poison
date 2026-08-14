# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-14

Initial stable release — a complete adversarial evaluation of Hindsight's
long-term memory (retain / recall / reflect) across four LLMs and seven attack
techniques, run against a real local Hindsight instance.

### Added

- Baseline plus seven attack scripts: v1 hidden instruction, v2 forged fact,
  v3 trusted-tag forgery, v4 repetition/amplification, v5 temporal ordering,
  v6 forged policy, v7 authority spoofing.
- Original N=15 study with the F1–F8 corrections from an adversarial review.
- Counterfactual probe (the attack scenario *without* the forged fact) to
  separate a real effect from baseline noise.
- Cross-model stress matrix (llama3.2:3b, DeepSeek v4-flash/v4-pro, and a
  nemotron-omni-30b reasoning model).
- Retrieval-internals probe (`scripts/11_retrieval_probe.py`) isolating the
  `context` trust signal, repetition/`proof_count` amplification, and
  recency-decay mechanisms.
- `scripts/aggregate_report.py` with Fisher exact tests, Wilson confidence
  intervals, N-per-group reporting, and sample-size planning.
- Statistical aggregation and reproducible reports under `reports/`.

### Changed

- `client.py` deprecated raw HTTP in favor of the `hindsight_client` SDK;
  retry handling narrowed to transient service errors.

### Fixed

- F1–F8 review corrections: citation counts, causal-language overclaims,
  multi-batch structure documentation, recall logging, non-deny/Fisher/CI
  reporting, orphaned `attacks/` relocated to `legacy_attacks/`, and retry logic.
- Pylint CI on Python 3.10/3.12, with a `.pylintrc` that ignores
  `legacy_attacks/` and CI-only dependencies.
- Corrected an over-claimed "retrieval degradation" note after the dedicated
  probe showed healthy retrieval on the same long-lived instance.

### Documentation

- README covering methodology, results, the stress matrix, retrieval-mechanism
  findings, and known limitations.
- `reports/REPORT.md` with evidence exhibits.

[1.0.0]: https://github.com/mindisolutions/hindsight-memory-poison/releases/tag/v1.0.0
