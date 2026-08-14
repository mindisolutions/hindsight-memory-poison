# Hindsight Memory Poisoning — Report

**Date:** {{date}}
**Target:** Hindsight (self-hosted, `{{version_or_commit}}`)
**Scope:** Local instance, own data, self-authorized research. No third-party
system or data was involved.

## Summary

{{one paragraph: what was tested, what stood out}}

## Attack 1 — Prompt injection via retained content

- **Vector:** {{how the payload entered the system}}
- **Payload:** `payloads/fake_scraped_page.md`
- **Result:** {{did reflect() follow the injected instruction? quote the answer}}
- **Mitigation:** {{sanitize before retain / strip hidden text/comments /
  provenance tagging + trust-aware retrieval / output filtering}}

## Attack 2 — Secret/PII exfiltration vs Memory Defense

- **Vector:** {{which variants leaked, on which bank}}
- **Payload:** `payloads/secret_variants.py`
- **Result:** {{table or summary of leaked=True rows from results.jsonl}}
- **Mitigation:** {{what a defense-in-depth layer would need to add — e.g.
  entropy-based detection for obfuscated secrets, since regex alone misses
  base64/zero-width/split variants}}

## Attack 3 — Trust boundary / confused-deputy via forged metadata

- **Vector:** {{what metadata/context field was forged}}
- **Result:** {{verdict from results.jsonl}}
- **Mitigation:** {{provenance verification tied to the actual caller/API key,
  not a self-declared context string}}

## Overall assessment

{{how much of this is "Hindsight is missing a documented control" vs "the
marketing claims outpace the current documented feature set" -- keep those
two categories separate, it's the difference between a bug report and a
gap analysis}}
