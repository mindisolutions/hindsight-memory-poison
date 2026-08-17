# Research Expansion Plan

> How to take this project beyond the already-tested niche (baseline + v1–v7
> techniques against four models) into new attack surface, harder evidence, and
> concrete hardening contributions to Hindsight.

## 1. Related work (anchor, cite, and differentiate)

| Study | Source | Relevance |
| ----- | ------ | --------- |
| Memory Poisoning Attack and Defense on Memory-Based LLM-Agents | [arXiv:2601.05504](https://arxiv.org/abs/2601.05504) (Jan 2026) | Closest sibling: has both attack **and** defense. Basis for `DEFENSES.md`. |
| From Untrusted Input to Trusted Memory (systematic study) | [arXiv:2606.04329](https://arxiv.org/html/2606.04329) (Jun 2026) | Covers the **self-improvement loop** — injected steps synthesized into persistent skills. Validates the self-propagating attack below. |
| PoisonedRAG: Knowledge Corruption Attacks to RAG | USENIX Security 2025 ([repo](https://github.com/sleeepeer/PoisonedRAG)) | Foundational corpus-poisoning work; our extension is the same principle applied to a **persistent agent memory**, not a document index. |
| Memory poisoning via deceptive semantic reasoning | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0952197626002496) (Jan 2026) | Adjacent to v5 (deceptive "latest-wins" framing). |
| Agent Memory Poisoning — The Attack That Waits | [Medium](https://medium.com/@michael.hannecke/agent-memory-poisoning-the-attack-that-waits-9400f806fbd7) (Jan 2026) | **In-the-wild evidence**: honeypots captured ~91k attack sessions, ~80k enumeration requests across 73+ model endpoints. Confirms this is an active threat, not theory. |
| Indirect prompt injection (foundational) | Greshake et al.; [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/); [arXiv:2608.08795](https://arxiv.org/abs/2608.08795) | v1 is the classic case; our novelty is the **persistent-memory** vector that survives across sessions. |
| BiRD: Bidirectional Ranking Defense for RAG | [arXiv:2605.20123](https://arxiv.org/html/2605.20123) | Ranking-side defense; useful for the mitigation section. |

**Our differentiator:** most prior art uses synthetic benchmarks (AgentDojo etc.).
We run against a **real Hindsight instance with real LLMs on a concrete
access-control decision (grant/deny)**. That is the asset to preserve and extend.

## 2. New methods to test (beyond v1–v7)

### A. Memory vectors not yet explored
1. **Entity/graph poisoning** — forge tag-shaped labels to hijack entity-scoped
   retrieval. *Directly validated by open upstream bugs #3276 / #3277.*
2. **Metadata poisoning** — exploit the `retain`-accepts / `recall`-rejects
   asymmetry (upstream #3209, null values) and forge provenance fields.
3. **Mental-model poisoning** — attack `reflect` consolidation (upstream #2894,
   #3135 race conditions).
4. **Bank isolation** — can `recall(bank_id=A)` read facts from bank B?
   (*access-control 0-day candidate*)
5. **Self-propagating poisoning** — a fact that, when reflected on, causes the
   agent to retain *new* poisoned facts (agentic amplification).

### B. Attacking the retrieval mechanism (not the LLM)
6. Adversarial embedding / semantic hijack.
7. Adversarial examples against the cross-encoder (MS MARCO reranker).
8. Proof-count laundering (flood weak proofs to inflate `proof_count_boost`).
9. Recency-curve exploitation (measure decay half-life, time injections to peak weight).
10. Graph-retrieval activation (confirm whether `graph_count=0` is expected or a silent no-op).

### C. Reflection/prompt vectors
11. **Reflect prompt injection** — a retrieved fact that injects *instructions*
    into `reflect()` (not just influencing the decision). (*injection 0-day candidate*)
12. Tool-call injection via retrieved memory.
13. Multi-turn poisoning (spread across turns, not a single `retain`).

### D. Models and context
14. Broaden the model matrix (GPT, Claude, Gemini, Llama 3.3 70B, Qwen).
15. Hindsight Cloud (hosted product) — distinct threat model.

### E. Robustness / DoS
16. Poison-pill regrind loop (upstream #2675).
17. Memory flooding / eviction of legitimate facts.

## 3. Repository additions

1. Config-driven **benchmark harness** with standardized metrics + CI matrix.
2. **`DEFENSES.md`** (mitigations, evaluated) — the missing "defense" half.
3. **`docs/THREAT_MODEL.md`** (formal attacker/capabilities/trust boundaries).
4. New attack scripts (one per family in §2).
5. **Mitigation POC** — e.g. a `context` namespacing patch to test upstream.
6. Stronger statistics (Bayesian analysis, per-model CIs, Cohen's *h* effect size).
7. Multi-provider config + `Makefile` for one-command runs.
8. Telemetry/honeypot module (log real-world attack patterns).
9. "Related work" section in the README.

## 4. Related vulnerabilities and possible 0-days

**Confirmed — hardening gap (not a 0-day):** unauthenticated `context` field.

**Genuine 0-day candidates (absent from upstream issues → likely unreported):**
- Bank-isolation bypass (cross-bank recall = access-control flaw).
- Reflect prompt injection via retrieved facts (instruction hijack / data exfil).

**Known upstream bugs (not 0-day — "N-day"; we can validate and quantify):**
- #3276 / #3277 — entity minting at intake (open).
- #3209 — `retain`/`recall` null-metadata asymmetry (open).
- #2675 — poison-pill regrind loop (closed).
- #2894 / #3135 — mental-model overwrite races (open).

## 5. Next actions (prioritized by impact × novelty)

**Phase 1 — immediate, high impact (real novelty):**
1. Bank-isolation test (access-control 0-day candidate).
2. Reflect-injection test (injection 0-day candidate).
3. Entity-poisoning repro of upstream #3276/#3277 (collaborative contribution).

**Phase 2 — widen the surface:**
4. Broadened model matrix.
5. Retrieval-mechanism attacks (embedding, cross-encoder, proof-count, recency curve).
6. Self-propagating poisoning.

**Phase 3 — defense + publication:**
7. `DEFENSES.md` + `context` namespacing POC.
8. Benchmark harness + multi-model CI.
9. Upstream engagement (collaborative public issue + entity findings).
