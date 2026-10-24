---
name: orchestrator-pattern
description: How to cut a task into bounded background workstreams, isolate each in its own worktree, brief each subagent with measured facts and disjoint file ownership, verify every claim, merge through the integrator, review the merged tree, and keep the record honest.
---

# The orchestrator pattern

The orchestrator holds the thread — the board, the documents, what the operator asked for — and
does none of the work. Every task goes to a subagent launched with `background: true`. This skill
is the operating manual: how to cut, how to isolate, how to brief, what to verify, how it merges,
what it writes down.

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

A workstream is **one deliverable, one owner, one file set, one worktree**. If two workstreams
would write the same file, they are sequential — never parallel. If one changes a contract
(`proto/.../engine.proto`, `api/openapi.yaml`), it goes first and the consumers go after it.

| Workstream | Agent | Typical deliverable |
|---|---|---|
| Implement in C++ | `cpp-engineer` | a target, a test, a timing fix |
| Implement in Go | `go-engineer` | a handler, a client, an SSE fix |
| Implement in the browser | `web-engineer` | a component, a store action, a test |
| Assembler / disassembler / `.rom` | `toolchain-engineer` | a subcommand, a round-trip test |
| Tests only | `test-engineer` | vectors, fuzz corpus, coverage |
| Measure | `verifier` | commands and their output |
| Documentation | `docs-writer` | a page, an ADR |
| Board | `ticket-manager` | labels, issue bodies, transitions |
| Dependencies | `conan-dependencies` | `conanfile.py`, profiles, lockfiles |
| Integrate | `integrator` | a merged tree, and the suite run on it |
| Final review | `reviewer` | `PASS` or `BLOCK` on the merged tree |

State each workstream's files in the brief and in your own notes. Two subagents editing one file
is the failure this table exists to prevent, and the worktree is what makes it structural instead
of hopeful.

## 3. The worktree

**One workstream, one worktree, one branch `work/<name>`.** Created by you, before the brief:

```
opencode worktree_create <name>      # → a directory, and branch work/<name>
```

The harness worktree tool, not a shell command, so the orchestrator's `shell` denial still holds.
If the harness has no such tool, the first thing the integrator does is
`git worktree add <dir> -b work/<name> main` and it reports the path.

- **Name it after the workstream**, not the agent: `worktree_create ddcb-result`,
  `worktree_create sse-heartbeat`, `worktree_create conan-lock-refresh`. Two agents may take turns
  on one workstream; they never share a tree.
- **One branch per workstream**, cut from the `main` you measured. Never from another unfinished
  workstream.
- **The main checkout is the operator's.** No subagent is told its path and none works there.
- **A dead workstream is removed**, not left dirty: `opencode worktree_remove <dir>`, and the
  issue says why the branch was dropped.

Why it is structural: in one checkout every agent shares an index, a stash and one `git status`, so
two parallel edits become one indistinguishable diff. In a worktree the branch *is* a directory —
the diff is that directory, and a branch that does not build cannot break the tree being read.

## 4. The brief

A subagent starts with **no** context of this session. Everything it needs is in the brief, in
this order:

```markdown
## Worktree
You work in `/tmp/opencode/<name>`, on branch `work/<name>`. Nothing outside it. Commit there.

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
`backend/`, `web/`, `toolchain/`, `proto/`, `docs/`, the issue tracker, `main`.

## Delivery
Closed commits on `work/<name>` (one logical change each, message and body in English), then the
summary: what changed, what was measured with the command and its output, what you deliberately
did not do, the branch and the shas, and the issue numbers with the `status/*` you left.
```

No brief without a *measured* fact: a command that ran, a `path:line`, a version. A conclusion
whose evidence you cannot name is the orchestrator guessing, and the subagent will build on it.
No brief with the main checkout's path in it: an agent told where `main` lives works in `main`.

## 5. Launch

Use the `subagent` tool with `background: true`. Never foreground, never inline the work in your
own turn. Launch independent workstreams in the same burst so they run at once, each in its own
worktree.

## 6. While they run

Work on something that does not overlap: read the next issue, prepare the record skeleton, read
the contract. Do **not** poll (`sleep`, re-reading, "are you done"), and do **not** redo the task
beside the agent. You are told when it finishes.

## 7. The delivery contract

A subagent delivers exactly three things, and nothing else:

1. **Closed commits** on `work/<name>` — self-contained, English subject and a body that says what
   was measured, tests passing in every commit that claims to work.
2. **A summary** — what changed; what was measured, with the command and its output; what was
   deliberately not done; the branch and the commit shas.
3. **The issues**, by number — every one it opened or updated, and the `status/*` label it left.

It does not merge, does not push `main`, and does not close an issue unless that issue *was* the
deliverable. A delivery missing the shas or the issue numbers is incomplete; ask for the missing
part, not for "a report".

## 8. When a report arrives

A report is a claim, not a measurement. Re-measure before repeating it:

| Claim | Re-measure with |
|---|---|
| "tests pass" | the same command, in this session, fresh output |
| "endpoint returns 200" | `curl -sS -o /dev/null -w '%{http_code}' <url>` |
| "no state committed" | `git status --short` in that worktree |
| "field added to the contract" | `git diff proto/ api/`, then check generated code |
| "documented" | open the document and read the paragraph |
| "3 commits on `work/<name>`" | `git log --oneline main..work/<name>` |

If it does not hold: brief a **new** subagent with the failing output and the same ownership (or
the same agent resumed, if the harness supports it). Do not re-run the same brief blind — it will
produce the same result and burn a context.

### The gate before the merge

| Check | Passes when |
|---|---|
| the branch exists and has commits | `git log --oneline main..work/<name>` lists them |
| it builds | the stack's build command exits 0 |
| its tests pass | the declared test command exits 0, run here or by `verifier` |
| the issue exists | `forgejo list_issues(state: "open")` has it, `status/in-progress` |
| the label matches reality | the issue is not `in-progress` for work that stopped |

A branch that fails the gate does not go to `integrator`. It goes back to its author with the
failing output, in the worktree it already has.

## 9. Integration

`integrator` is the only agent that merges, and the only one that pushes `main`:

```sh
git fetch origin && git switch main && git merge --ff-only origin/main
git switch work/<name> && git rebase main      # conflicts resolved here, both intents kept
git switch main && git merge --ff-only work/<name>
make test                                      # on the merged tree, not on the branch
```

It reports: what was rebased, what conflicted and how it was resolved, the exact commands and their
output, the merged sha, and the tests that pass. It **refuses** when the branch does not build, a
test fails, the tree is dirty, or a conflict can only be resolved by dropping a test — and it says
which. It does not fix a test to make a merge pass: a regression is a refusal, not an edit.

## 10. The final review

`reviewer` reviews the **merged tree**, after the merge, because that is the state the repository
is in. It runs the suite itself and looks for what integration hid: a conflict resolved by dropping
a hunk, a test weakened to pass, a generated file not regenerated, a contract changed on one side.

Its answer is `PASS` or `BLOCK`, with the evidence. Your move:

- **`PASS`** → the issue goes `status/done` and closes, with the merged sha and the suite output in
  the comment.
- **`BLOCK`** → the merge is reverted (section 11). A blocking finding is never "follow-up work",
  and nothing is fixed forward on `main`.

## 11. The revert

A merge that regresses is reverted by `integrator`, not repaired in a panic:

```sh
git revert -m 1 <merged-sha>        # or: git reset --hard <last-green-sha> before the push
git push origin main
make test                           # the tree is green again, or you are not done
```

The revert sha, the blocking finding and the reason go in the issue; the branch returns to its
author in `status/todo` with the finding quoted in it. The next attempt starts from a measured
green tree, never from the broken one.

## 12. The lifecycle

| State | Board | Git | Who acts |
|---|---|---|---|
| proposed | `backlog` | — | orchestrator |
| accepted | `todo` | — | orchestrator |
| in flight | `in-progress` | `work/<name>`, commits landing | subagent |
| delivered | `in-progress` | branch has the commits, gate passes | orchestrator verifies |
| merged | `in-progress` | `main` fast-forwarded, suite run | `integrator` |
| reviewed | `done` + closed | merge stands | `reviewer` then orchestrator |
| reverted | `todo` | revert commit on `main`, branch back | `integrator`, finding quoted |

Nothing skips a row: a merged workstream that never reached `reviewer` is not `done`, and an issue
that says `in-progress` while no worktree exists is a lie the board will keep telling.

## 13. Failure modes

- **Empty report** — the agent died or was cut. Treat as not done; relaunch with a narrower
  deliverable, in a fresh worktree from the same `main`.
- **Partial report** ("mostly done") — the deliverable is the only thing that counts. Ask for the
  remainder with the exact missing item, not "finish it".
- **A branch that does not merge** — `integrator` refuses. The author gets the conflict, in its own
  worktree; do not re-cut the work under a new worktree to dodge a rebase.
- **Conflicting edits** — two agents touched one file, which the worktrees should have made
  impossible: `git diff` both branches, keep one, brief a third to reconcile, then fix the
  ownership overlap in the next cut.
- **Touched the record** — revert the issue or commit change, and say in the issue that the
  orchestrator owns it.
- **Report contradicts the code** — the code wins. Quote the line in the next brief.
- **A workstream with no issue** — a finding, not a detail: `ticket-manager` opens it with the
  branch and the shas, so the work is not invisible.

## 14. The record

Written by you, in the same change that produces the finding:

- the issue comment: command, output, `path:line`, timestamp; what changed and the rollback;
- the `status/*` label, moved before the work starts and out of `in-progress` when it stops;
- the documents the change invalidates;
- the commit body: what, why, evidence, rollback.

The subagent's summary becomes the issue comment; the merged sha and the reviewer's verdict are
added to it. A subagent never writes the record itself: it gets a bounded workstream, not the
project's memory.

## 15. Closing

`status/done` and closed when done and reviewed; `status/blocked` with the blocker in the body;
`status/todo` when handed back unfinished or reverted; `status/backlog` when it is not actionable
yet. An issue left in `status/in-progress` by an orchestrator that stopped claims somebody is on it
when nobody is.

## Anti-patterns

- Answering "it works" from a subagent's sentence. Quote the command or do not say it.
- A brief that says "improve the engine" — no path, no deliverable, no test.
- Two agents in one file because "they will be quick"; two agents in one checkout for any reason.
- Foregrounding to "save a turn" — it defeats the pattern.
- Merging a branch that never passed the gate, or calling a merged tree `done` before the review.
- Fixing a regression forward because the revert "looks like a step back".
- Answering a question about the project from memory instead of the board and the documents.
