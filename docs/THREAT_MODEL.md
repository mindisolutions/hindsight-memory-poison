# Threat Model

## System under analysis

[Hindsight](https://github.com/vectorize-io/hindsight) — an agent memory system
with three primitives:

- `retain(bank_id, content, context, timestamp, metadata, entities, tags)` — write a fact.
- `recall(bank_id, query, …)` — retrieve facts (semantic + BM25 + graph, then
  cross-encoder rerank with recency / temporal / proof-count boosts).
- `reflect(bank_id, query, …)` — answer a query grounded in retrieved facts.

Backing store: Postgres + vector index. The `context` string is prepended to the
fact text before the cross-encoder and before the LLM sees it (`f"{context}: {text}"`).

## Assets

1. **Memory-bank contents** — facts, entities, metadata, and mental models.
2. **The decision** — the downstream action (e.g. grant/deny API access) that
   `reflect()`'s answer feeds into.
3. **Cross-tenant data** — in a multi-bank / multi-tenant deployment, other
   tenants' facts and their confidentiality.
4. **The agent's behavior** — its ability to follow instructions and call tools.

## Trust boundaries

The single most important boundary is the **`retain()` caller**: Hindsight treats
any content passed to `retain()` as legitimate memory, and does not authenticate
the provenance of `context`, `metadata`, or `entities`. A second boundary is
**bank scoping**: whether `bank_id` is an enforced isolation boundary or merely a
filter that the retrieval path can be made to ignore.

## Attackers

| ID | Attacker | Capability | Goal |
| -- | -------- | ---------- | ---- |
| A1 | **Compromised integration** (web-scraper, note-taker, email importer) | Can call `retain()` with attacker-influenced content | Flip a security decision by poisoning memory |
| A2 | **Malicious tenant** (multi-tenant deployment) | Can call `retain/recall/reflect` on *their own* bank | Read or influence *another* tenant's bank |
| A3 | **External content author** (document/email/page later ingested) | Only controls the *content* that gets retained | Inject instructions or forgeries via content |
| A4 | **Insider / misconfigured deployment** | Already has memory access | Escalate via weak provenance checks |

The v1–v7 study characterizes A1/A3. The **bank-isolation** and
**reflect-injection** probes below extend to A2 and A4.

## Attack surface (beyond the tested niche)

- **Write path:** unauthenticated `context` (trusted-tag forgery), forged
  `metadata`/`timestamp`, forged `entities`, tag-shaped labels minted as entities
  (#3276/#3277), null-metadata asymmetry (#3209).
- **Retrieval path:** adversarial embeddings, cross-encoder adversarial examples,
  `proof_count` laundering, recency-curve timing, graph-retrieval behavior.
- **Reflection path:** prompt injection via retrieved facts, tool-call hijack,
  mental-model consolidation races (#2894/#3135).
- **Isolation path:** cross-bank recall (A2), poison-pill regrind loop (#2675).

## Security properties to verify

1. **Bank isolation** — `recall(bank_id=B)` must never surface facts from bank A.
2. **Provenance authenticity** — `context`/`metadata`/`entities` must be
   authenticated or treated as untrusted advisory, never as trust evidence.
3. **Instruction/data separation** — retrieved facts must reach the LLM as
   *data*, never as *instructions*.
4. **Integrity under load** — retrieval must not degrade or leak under flooding.
