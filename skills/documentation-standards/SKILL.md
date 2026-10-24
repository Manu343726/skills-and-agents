---
name: documentation-standards
description: The docs/ layout, the ADR format, README requirements, link conventions for every file and entity, evidence beside every claim, and the English-only rule.
---

# Documentation standards

The documentation is part of the change, not a follow-up. A document that no longer describes the
code is a bug with a `path:line` on each side.

## Layout

```
docs/architecture.md            the shape of the system and why it is that shape
docs/adr/NNNN-<slug>.md         one decision per file, immutable once accepted
docs/api/connect.md             the engine contract as a reference
docs/api/rest.md                the REST surface from api/openapi.yaml
docs/api/mqtt.md                topic taxonomy and payload envelope
docs/api/sse.md                 the state stream
docs/runbooks/<task>.md         repeatable operational procedures
README.md                       what it is, how to build, how to run
AGENTS.md                       the contract of the repository for agents
```

One topic per file. A page that needs a table of contents is two pages.

## ADR

```markdown
# ADR-0007: The engine speaks Connect unary, not gRPC

- Status: accepted
- Date: 2026-10-24
- Deciders: manu343726
- Issue: https://git.manu343726.com/manu343726/z80-emulator/issues/12

## Context
What forces the decision. Measured facts, not adjectives: the versions, the constraint, the
command that produced the number.

## Decision
The choice in the present tense, and what it rules out.

## Consequences
What becomes easy, what becomes hard, what must be revisited and when.
```

An accepted ADR is never edited. A later decision adds `Superseded by ADR-NNNN` at the top and a
new file. Nothing is deleted, ever.

## Every entity and file is a link

- A repository path: ``[`engine/src/cpu.cpp`](../engine/src/cpu.cpp)``.
- A service: `[engine](http://localhost:8080)` or its documented endpoint.
- The board: `<https://git.manu343726.com/manu343726/z80-emulator/issues/12>`.
- A skill: `` `z80-isa` `` (by id), and a document: ``[ADR-0007](adr/0007-connect-unary.md)``.

A bare path in prose is a defect: the reader cannot open it.

## Evidence beside the claim

| Wrong | Right |
|---|---|
| "coverage is good" | `go test ./... -coverprofile` → 81.2 % on 2026-10-24 |
| "fast" | `perf stat ./build/z80_tests` → 1.2 G instr/s, measured 2026-10-24 |
| "we use React 19" | `web/package.json:24` → `"react": "19.0.0"` |
| "the endpoint works" | `curl …` → `HTTP 200`, body `{"status":"ok"}` |

A number carries how it was obtained. A version carries the file and line. A behaviour carries the
test that asserts it.

## README

Required, in order: one paragraph saying what the project is; a directory table; how to build and
test each stack (the four commands); how to run it (engine, backend, web); where the documentation
lives; licence. A reader with no context must reach a running emulator from this page alone.

## Rules

1. **English only**, including comments inside quoted code and commit messages.
2. **Quoted code is real.** Open the file, copy the lines. A paraphrased API is a wrong API.
3. **Present tense, no history.** Git has the history; the document describes what is.
4. **No TODO without an issue link.** `grep -rn 'TODO\|FIXME' docs/` must return only lines with a
   URL.
5. **Prerequisites of a runbook name the machine and the check**: `ssh Homelab`, `gcc 16.2.1`
   (`gcc --version`), not "a recent compiler".
6. **Update in the same change** as the code, with the commit body naming the document.

## Before reporting

```sh
git diff --stat -- docs/ README.md AGENTS.md
grep -rn 'TODO\|FIXME' docs/ README.md AGENTS.md
grep -rnE '\[[^]]+\]\(\.\./' docs/ | head -40     # spot-check relative links
```

Open every link you added. A 404 in a document is a broken change.