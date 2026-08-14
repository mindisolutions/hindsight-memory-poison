# Security Policy

## Scope

This repository is a **security-research harness**, not a production application.
Its purpose is to measure the memory-poisoning and prompt-injection attack
surface of [Hindsight](https://github.com/vectorize-io/hindsight) (an open-source
agent memory system) by running controlled experiments against a real, local
instance. The "attacks" documented here are deliberate, contained experiments —
they are not vulnerabilities in this codebase.

## Reporting a vulnerability

If you discover a security issue **in this repository** (the harness itself —
e.g. credential leakage, unsafe input handling, an error in how results are
aggregated or reported), please report it privately so it can be fixed before
disclosure:

1. Open a **private vulnerability report** via
   [GitHub Security Advisories](https://github.com/mindisolutions/hindsight-memory-poison/security/advisories/new),
   or email the maintainers directly if you prefer.
2. Include: affected component/script, steps to reproduce, and the impact you
   believe it has.
3. You will receive an acknowledgement within a few business days and a
   proposed resolution timeline.

Please **do not** open a public issue for a suspected vulnerability before it is
triaged.

## Findings about Hindsight itself

This project evaluates Hindsight but is **not affiliated with Vectorize**.
If your work surfaces a concrete defect or hardening gap in Hindsight, report it
to the upstream project at
[`vectorize-io/hindsight`](https://github.com/vectorize-io/hindsight) (following
their own reporting process). We are happy to coordinate if a finding originated
from this harness.

## Supported versions

| Version | Supported |
| ------- | --------- |
| 1.0.0   | ✅        |

Only the latest tagged release receives security fixes.
