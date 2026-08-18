# Upstream engagement — LIVE

> Current state of the upstream engagement (`vectorize-io/hindsight`):
>
> - **#3558** — security-evaluation report (posted by @Luscaswolf) — CLOSED by
>   maintainer @nicoloboschi (scoped: each request is self-contained, no
>   server-data/tool access).
> - **#3559** — `docs(retain): document context as caller-supplied trust hint`
>   (posted by @Luscaswolf) — OPEN.
> - **#3562** — hardening proposal (the body below) — OPEN.
>
> Attribution: [@Luscaswolf](https://github.com/Luscaswolf) +
> [@handnewb](https://github.com/handnewb). The body below is the exact text of
> the hardening proposal posted to #3562.

---

**Title:** `Security evaluation: memory-poisoning attack surface + hardening suggestions`

**Label:** `enhancement`

## Summary

We ran a security evaluation of Hindsight's long-term memory against a real
local instance (Docker + Postgres) with real LLMs — not a synthetic benchmark.
Scenario: a security-review assistant deciding whether to grant a third-party
vendor API access to a production database, seeded to require **deny**.

Seven techniques via `retain()` (hidden instruction, forged fact, trusted-tag
forgery, repetition, temporal ordering, forged policy, authority spoofing)
across four models (`llama3.2:3b`, DeepSeek `v4-flash`/`v4-pro`,
`nemotron-omni-30b`).

## Key findings (honest framing — not a 0-day report)

- Attacks succeed by manipulating the model's **reading of retrieved fact
  text**, not the ranking math. Corroboration (repetition) and recency-framing
  ("supersedes earlier entries") broke all strong models at 75–100% grant
  (baseline 0% for the strong models).
- The **`context` field in `retain()` is unauthenticated**: it is prepended to
  fact text (`f"{context}: {text}"`) and read by the LLM as a trust signal, so a
  caller can forge `context="security_review_note"` for attacker content. This
  is the one concrete, actionable hardening gap.

## Hardening suggestions

1. **Authenticate/namespace `context`** — derive the trust tier from the
   authenticated caller identity, not the caller-supplied string.
2. **Deduplicate** near-identical claims (repetition floods retrieval: 5
   corroborating facts → 6 results vs 1 fact → 2 results).
3. **Provenance / trust tiering** for sources (authority spoofing relies on
   unverifiable attribution).
4. **Instruction/data separation** in the `reflect` prompt (delimit facts so
   they cannot be read as instructions).

## Also observed

- Bank isolation held up in our tests (no cross-bank leak) — good.
- Direct instruction-injection in a retrieved fact was **detected and refused**
  by the strong model, but aligned factual forgery still flipped the decision —
  guardrails catch imperative injection, not aligned forgeries.
- Attempted to reproduce #3276/#3277 (entity minting): not observed under
  default config; the entity-extraction config returned HTTP 400 on our instance.

No CVE or 0-day is claimed. Happy to collaborate on any hardening item.

Full study (methodology, per-model grant rates, statistics):
https://github.com/mindisolutions/hindsight-memory-poison
