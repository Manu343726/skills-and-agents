---
name: orchestrator-pattern
description: How to cut a task into bounded background workstreams, brief each subagent with measured facts and disjoint file ownership, verify every claim, and keep the record honest.
---

# The orchestrator pattern

The orchestrator holds the thread — the board, the documents, what the operator asked for — and
does none of the work. Every task goes to a subagent launched with `background: true`. This skill
is the operating manual: how to cut, how to brief, what to verify, what to write down.

## 1. Read before you cut

Never cut work from a description alone.

```sh
forgejo list_issues(state: "open")          # the pending state, always first
git log --oneline -10 -- <path>             # what last touched the area
git status --short                          # is the tree already dirty?
```

Read the issue that matches the request, the documents it references, and the files. If no issue
matches, have `ticket-manager` open one (`status/todo`, one `type/*`, one `priority/*`, the
`area/*` it touches) before the first command of the work.

## 2. Cut the work

A workstream is **one deliverable, one owner, one file set**. If two workstreams would write the
same file, they are sequential — never parallel. If one changes a contract
(`proto/.../engine.proto`, `api/openapi.yaml`), it goes first and the consumers go after it.

| Workstream | Agent | Typical deliverable |
|---|---|---|
| Implement in C++ | `cpp-engineer` | a target, a test, a timing fix |
| Implement in Go | `go-engineer` | a handler, a client, an SSE fix |
| Implement in the browser | `web-engineer` | a component, a store action, a test |
| Assembler / disassembler / `.rom` | `toolchain-engineer` | a subcommand, a round-trip test |
| Tests only | `test-engineer` | vectors, fuzz corpus, coverage |
| Measure | `verifier` | commands and their output |
| Review | `reviewer`, `security-reviewer` | findings with `path:line` |
| Documentation | `docs-writer` | a page, an ADR |
| Board | `ticket-manager` | labels, issue bodies, transitions |
| Dependencies | `conan-dependencies` | `conanfile.py`, profiles, lockfiles |

State each workstream's files in the brief and in your own notes. Two subagents editing one file
is the failure this table exists to prevent.

## 3. The brief

A subagent starts with **no** context of this session. Everything it needs is in the brief, in
this order:

```markdown
## Ownership
You own `engine/src/**` and `engine/tests/**`. Do not touch anything else.

## Read first
- `engine/src/cpu.cpp`, `engine/tests/cb_test.cpp`
- `docs/adr/0004-decoder-tables.md`

## Measured facts (do not re-derive)
- `ctest --preset conan-release` → 412/412 passed, measured 2026-10-24 06:12.
- `engine/src/cpu.cpp:214` writes `regs.b` for every DDCB op; the bug reproduces with
  `z80_tests --gtest_filter=CB.DDCB_ResultToRegister` → expected 0x42, got 0x00.
- gcc 16.2.1, cmake 4.4.3, ninja 1.13.2 on the host; Conan 2 at `~/.local/bin/conan`.

## Deliverable
Fix the DDCB result-to-register write and add the regression test in
`engine/tests/cb_test.cpp::TEST(CB, DDCB_ResultToRegister)`.

## Constraints
C++20; no allocation or exception in `step()`; T-states unchanged; `-Wall -Wextra -Wpedantic
-Wconversion -Wshadow` clean; sanitizer build passes.

## Do not touch
`backend/`, `web/`, `toolchain/`, `proto/`, `docs/`, the issue tracker, git.

## Report
Files changed with paths; every command you ran with its real output; what you could not do.
```

No brief without a *measured* fact: a command that ran, a `path:line`, a version. A conclusion
whose evidence you cannot name is the orchestrator guessing, and the subagent will build on it.

## 4. Launch

Use the `subagent` tool with `background: true`. Never foreground, never inline the work in your
own turn. Launch independent workstreams in the same burst so they run at once.

## 5. While they run

Work on something that does not overlap: read the next issue, prepare the record skeleton, read
the contract. Do **not** poll (`sleep`, re-reading, "are you done"), and do **not** redo the task
beside the agent. You are told when it finishes.

## 6. When a report arrives

A report is a claim, not a measurement. Re-measure before repeating it:

| Claim | Re-measure with |
|---|---|
| "tests pass" | the same command, in this session, fresh output |
| "endpoint returns 200" | `curl -sS -o /dev/null -w '%{http_code}' <url>` |
| "no state committed" | `git status --short` |
| "field added to the contract" | `git diff proto/ api/`, then check generated code |
| "documented" | open the document and read the paragraph |

If it does not hold: brief a **new** subagent with the failing output and the same ownership (or
the same agent resumed, if the harness supports it). Do not re-run the same brief blind — it will
produce the same result and burn a context.

## 7. Failure modes

- **Empty report** — the agent died or was cut. Treat as not done; relaunch with a narrower
  deliverable.
- **Partial report** ("mostly done") — the deliverable is the only thing that counts. Ask for the
  remainder with the exact missing item, not "finish it".
- **Conflicting edits** — two agents touched one file. `git diff` to find both, keep one, brief a
  third to reconcile; then never repeat the ownership overlap.
- **Touched the record** — revert the issue/commit change, and say in the issue that the
  orchestrator owns it.
- **Report contradicts the code** — the code wins. Quote the line in the next brief.

## 8. The record

Written by you, in the same change that produces the finding:

- the issue comment: command, output, `path:line`, timestamp; what changed and the rollback;
- the `status/*` label, moved before the work starts and out of `in-progress` when it stops;
- the documents the change invalidates;
- the commit body: what, why, evidence, rollback.

A subagent never writes these. It gets a bounded workstream, not the homelab's memory.

## 9. Closing

`status/done` and closed when done; `status/blocked` with the blocker in the body; `status/todo`
when handed back unfinished; `status/backlog` when it is not actionable yet. An issue left in
`status/in-progress` by an orchestrator that stopped claims somebody is on it when nobody is.

## Anti-patterns

- Answering "it works" from a subagent's sentence. Quote the command or do not say it.
- A brief that says "improve the engine" — no path, no deliverable, no test.
- Two agents in one file because "they will be quick".
- Foregrounding to "save a turn" — it defeats the pattern.
- Answering a question about the project from memory instead of the board and the documents.