---
name: orchestrator-pattern
description: How to cut a task into bounded background workstreams, isolate each in its own worktree, brief each subagent with measured facts and disjoint file ownership, verify every claim, merge through the integrator, review the merged tree, and keep the record honest.
---

# The orchestrator pattern

The orchestrator holds the thread — the board, the documents, what the operator asked for — and
does none of the work. Every task goes to a subagent launched with `background: true`. This is the
operating manual: how to cut, isolate, brief, verify, merge, review, and write down.

## 1. Read before you cut

Never cut work from a description alone.

```sh
forgejo list_issues(state: "open")          # the pending state, always first
git log --oneline -10 -- <path>             # what last touched the area
git status --short                          # is the tree already dirty?
```

Read the issue that matches the request, the documents it references, and the files. No issue
matches ⇒ `ticket-manager` opens one (`status/todo`, one `type/*`, `priority/*` and `area/*`)
before the first command of the work.

## 2. Cut the work

A workstream is **one deliverable, one owner, one file set, one worktree**. If two would write the
same file, they are sequential — never parallel. If one changes a contract
(`proto/.../engine.proto`, `api/openapi.yaml`), it goes first and the consumers after it.

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

## 3. The worktree

**One workstream, one worktree, one branch `work/<name>`**, the worktree created by you before the
brief:

```
opencode worktree_create <name>      # → a directory on a detached HEAD, and no branch
```

The tool returns the directory **detached**; it does not create the branch. The branch is the
brief's step 0: the agent runs `git switch -c work/<name>` before it writes anything, and pastes
`git branch --show-current` so its first report proves the branch exists. A brief that names a
branch nobody created ends in a commit no ref reaches, and `worktree_remove` takes it with the tree.

The harness worktree tool, not a shell command, so your `shell` denial still holds; if the harness
has none, `integrator` runs `git worktree add <dir> -b work/<name> main` and reports the path. Name
it after the workstream (`ddcb-result`, `sse-heartbeat`), never after the agent. One branch per
workstream, cut from the `main` you measured; a dead workstream is `worktree_remove`d and the issue
says why.

It is structural: one checkout means one index, one stash and one `git status`, so two parallel
edits become one indistinguishable diff. A worktree's branch *is* a directory, and a branch that
does not build cannot break the tree you are reading.

## 4. The brief

A subagent starts with **no** context of this session. Everything it needs is in the brief:

```markdown
## Worktree
`/tmp/opencode/<name>`, on a detached HEAD. Step 0: `git switch -c work/<name>`, then paste
`git branch --show-current`. Nothing outside it; commit there.

## Ownership
You own `engine/src/**` and `engine/tests/**`, nothing else. C++20, no allocation or exception in
`step()`, T-states unchanged. Read `engine/src/cpu.cpp` and `engine/tests/cb_test.cpp`.

## Measured facts (do not re-derive)
- `ctest --preset conan-release` → 412/412 passed, measured 2026-10-24 06:12.
- `engine/src/cpu.cpp:214` writes `regs.b` for every DDCB op; reproduces with
  `z80_tests --gtest_filter=CB.DDCB_ResultToRegister` → expected 0x42, got 0x00.

## Deliverable
Fix the DDCB result-to-register write, with the regression test in
`engine/tests/cb_test.cpp::TEST(CB, DDCB_ResultToRegister)`.

## Do not touch
`backend/`, `web/`, `toolchain/`, `proto/`, `docs/`, the issue tracker, `main`.

## Delivery
Commits on `work/<name>`, the summary, the issue numbers — section 6.
```

No brief without a *measured* fact: a command that ran, a `path:line`, a version. No brief with
the main checkout's path in it: an agent told where `main` lives works in `main`.

## 5. Launch, and while they run

`subagent`, `background: true`, always — never foreground. Launch independent workstreams in one
burst, each in its own worktree, then work on something that does not overlap (the next issue, the
record skeleton). Do not poll, and do not redo the task beside the agent.

## 6. The delivery contract

A subagent delivers exactly three things, and nothing else:

1. **Closed commits** on `work/<name>` — self-contained, English subject and a body that says what
   was measured, tests passing in every commit that claims to work.
2. **A summary** — what changed; what was measured, with the command and its output; what was
   deliberately not done; the branch and the commit shas.
3. **The issues**, by number — every one it opened or updated, and the `status/*` label it left.

It does not merge, does not push `main`, and does not close an issue unless that issue *was* the
deliverable. A delivery missing the shas or the issue numbers is incomplete.

## 7. When a report arrives

A report is a claim, not a measurement. Re-measure before repeating it:

| Claim | Re-measure with |
|---|---|
| "tests pass" | the same command, in this session, fresh output |
| "no state committed" | `git status --short` in that worktree |
| "field added to the contract" | `git diff proto/ api/`, then check generated code |
| "3 commits on `work/<name>`" | `git log --oneline main..work/<name>` |

If it does not hold, brief a **new** subagent with the failing output and the same ownership.

### The gate before the merge

| Check | Passes when |
|---|---|
| the branch has commits | `git log --oneline main..work/<name>` lists them |
| it builds | the stack's build command exits 0 |
| its tests pass | the declared test command exits 0, run here or by `verifier` |
| the issue exists | open, `status/in-progress`, per `forgejo list_issues(state: "open")` |
| the label matches reality | it is not `in-progress` for work that has stopped |

A branch that fails the gate never reaches `integrator`: it goes back to its author with the
failing output, in the worktree it already has.

## 8. Integration

`integrator` is the only agent that merges and the only one that pushes `main`:

```sh
git fetch origin && git switch main && git merge --ff-only origin/main
git switch work/<name> && git rebase main      # conflicts resolved here, both intents kept
git switch main && git merge --ff-only work/<name>
make test                                      # on the merged tree, not on the branch
```

It reports what was rebased, what conflicted and how it was resolved, the commands and their
output, the merged sha, and the tests that pass. It **refuses** when the branch does not build, a
test fails, the tree is dirty, or a conflict can only be resolved by dropping a test — and says
which. It never fixes a test to make a merge pass: a regression is a refusal, not an edit.

## 9. The final review, and the revert

`reviewer` reviews the **merged tree**, after the merge, because that is the state the repository
is in. It runs the suite itself and looks for what integration hid: a conflict resolved by dropping
a hunk, a test weakened to pass, a generated file not regenerated, a contract changed on one side.

`PASS` sends the issue to `status/done`, with the merged sha and the suite output in the comment.
`BLOCK` reverts the merge — never repairs it in a panic:

```sh
git revert -m 1 <merged-sha>        # a fast-forward merge: git revert <merged-sha>
git push origin main && make test   # green again, or you are not done
```

The revert sha, the finding and the reason go in the issue; the branch returns to its author in
`status/todo` with the finding quoted, and the next attempt starts from a measured green tree.

## 10. The lifecycle

| State | Board | Git | Who acts |
|---|---|---|---|
| proposed | `backlog` | — | orchestrator |
| accepted | `todo` | — | orchestrator |
| in flight | `in-progress` | `work/<name>`, commits landing | subagent |
| delivered | `in-progress` | commits on the branch, gate passes | orchestrator verifies |
| merged | `in-progress` | `main` fast-forwarded, suite run | `integrator` |
| reviewed | `done` + closed | merge stands | `reviewer`, then orchestrator |
| reverted | `todo` | revert commit on `main`, branch back | `integrator`, finding quoted |

A merged workstream that never reached `reviewer` is not `done`.

## 11. Failure modes

- **Empty or partial report** — the agent died, was cut, or answered "mostly". Not done; relaunch
  narrower in a fresh worktree from the same `main`, and ask for the exact missing item.
- **A branch that does not merge** — `integrator` refuses; the author gets the conflict in its own
  worktree. Do not re-cut the work to dodge a rebase.
- **Conflicting edits** — the worktrees should have made this impossible: diff both branches, keep
  one, brief a third to reconcile, and fix the ownership overlap in the next cut.
- **Touched the record** — revert it, and say in the issue that the orchestrator owns it.
- **Report contradicts the code** — the code wins. Quote the line in the next brief.
- **A workstream with no issue** — a finding: `ticket-manager` opens it with the branch and shas.

## 12. The record, and closing

The record is written by you, in the same change that produces the finding: the issue comment
(command, output, `path:line`, timestamp, what changed and the rollback), the `status/*` moved
before the work starts and out of `in-progress` when it stops, the documents the change
invalidates, and the commit body. The subagent's summary becomes the issue comment, and the merged
sha and the verdict are added to it.

`status/done` and closed when done and reviewed; `status/blocked` with the blocker in the body;
`status/todo` when handed back unfinished or reverted; `status/backlog` when not actionable.

## Anti-patterns

- Answering "it works" from a subagent's sentence. Quote the command or do not say it.
- A brief that says "improve the engine" — no path, no deliverable, no test.
- Two agents in one file because "they will be quick"; two agents in one checkout, ever.
- Foregrounding to "save a turn".
- Merging a branch that never passed the gate, or calling a merged tree `done` before the review.
- Fixing a regression forward because the revert "looks like a step back".
