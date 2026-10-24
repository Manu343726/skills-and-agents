---
name: documentation-standards
description: Where a project's documentation lives and why the project says so, the docs/ layout when it is the default, the ADR format, README requirements, link conventions, evidence beside every claim, the English-only rule, and the split between a document and a ticket.
---

# Documentation standards

The documentation is part of the change, not a follow-up. A document that no longer describes the
code is a bug with a `path:line` on each side.

## Where the documentation lives

**A project declares its documentation system in `AGENTS.md` (or, failing that, `README.md`), and
the declaration is part of the repository's contract.** The reason is that projects do not agree:
one keeps hierarchical Markdown under `docs/`, another edits pages in an external system through an
API, a third has a single README and means it.

| Declared as | What it means | Where you write |
|---|---|---|
| `docs/` (Markdown, hierarchical) | one topic per file, the tree below | the repository |
| a generated site over `docs/` | the Markdown is the source, the HTML is built | the repository |
| an external system, named | the pages live there with their own tool | **that tool**, never a Markdown copy |
| a mirror of an external system | the repository copy is generated | the external source |
| a single `README.md` | sections, not pages | the repository |

**With nothing declared, assume `docs/` with hierarchical Markdown** — it is the least surprising
default, it needs no service, and it survives the project. Then *declare it*: add the sentence to
`AGENTS.md` in the same change, so the next session reads the answer instead of inventing one.

```markdown
## Where the documentation lives

This project documents in `docs/`, hierarchical Markdown, one topic per file. Nothing is kept in
an external system, and nothing under `docs/` is generated.

<!-- or: -->
## Where the documentation lives

Machines, services and networks are documented in **Homelable**, not here; the
`homelable-docs` skill carries its conventions. This repository keeps only
`docs/adr/` and the API references, which are generated from `api/openapi.yaml`.
```

A declaration that is wrong is worse than none: a writer told "external system" who finds Markdown
edits the wrong copy. When the two disagree, the system with the read-write tool wins and the
declaration is corrected in the same change.

### Documents and tickets are one record

| | The document | The ticket |
|---|---|---|
| Answers | what the system **is**, now | what **happened**, what was measured, how to get back |
| Lives | the project's documentation system | the tracker (`type/*`, `status/*`) |
| Written | after the change, describing the result | with the change, closing when verified |
| Owner | `docs-writer` | `ticket-manager` |

A change that alters behaviour needs both, and neither substitutes for the other: a page with no
issue has no evidence, and an issue with no page leaves the system describing itself wrongly. When
they disagree, **the issue with the measurement wins** and the document is corrected. `docs-writer`
never files, closes or labels an issue; it says which issue its page belongs to and `ticket-manager`
owns the state.

## Layout (when the project documents in `docs/`)

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