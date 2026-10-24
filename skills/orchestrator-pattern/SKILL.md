---
name: orchestrator-pattern
description: How to cut a task into bounded background workstreams, isolate each in its own worktree, brief each subagent with measured facts and disjoint file ownership, verify every claim, gate the merge on a verifier's verdict at a recorded base sha, merge only an approval that still describes main, audit what already landed, and keep the record honest.
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
| Measure, merge gate | `verifier` | output; `APPROVED` or `REQUEST_CHANGES` on a PR |
| Documentation | `docs-writer` | a page, an ADR |
| Board | `ticket-manager` | labels, issue bodies, transitions |
| Dependencies | `conan-dependencies` | `conanfile.py`, profiles, lockfiles |
| Integrate, as an exception | `integrator` | a merge Forgejo cannot perform |
| Audit | `reviewer` | `PASS` or `BLOCK`, on what already landed |

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
Commits on `work/<name>`, the branch pushed with `git push -u origin work/<name>`, an open PR to
`main` naming every issue it serves, and the report with the shas and the PR number — section 6.
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
2. **The branch pushed** — `git push -u origin work/<name>`, with the output pasted.
3. **An open pull request** to `main` — `create_pull_request`, head `work/<name>`, base `main`,
   and a body that names every issue it serves by number. The report carries the PR number.

The report also carries the summary: what changed, what was measured with the command and its
output, what was deliberately not done, the branch and the commit shas. A branch is not a delivery
on its own: a report is a message in a session and dies with it, while an open PR is listed by
`list_repo_pull_requests` from any session.

It does not merge, does not review its own PR, does not push `main`, and does not close an issue
unless that issue *was* the deliverable. A delivery missing the PR number, the shas or the issue
numbers is incomplete.

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

The gate is `verifier` on the pull request, not your reading of the branch. The verifier records
the base sha (`main` at handoff), fetches the branch, creates a trial merge onto that sha in its
own worktree, runs every suite the diff touches on the merged result, and answers `APPROVED` or
`REQUEST_CHANGES` as a formal Forgejo review. It states the base sha and the trial-merge sha.

| Check | Passes when |
|---|---|
| the PR is open to `main` | `get_pull_request_by_index` returns it, head `work/<name>` |
| the branch has commits | `git log --oneline main..work/<name>` lists them |
| the trial merge applies | the verifier's merge onto the recorded base sha exits 0 |
| the suites pass on the merge | the verifier pasted every command and its exit 0 |
| the approval still holds | `main` is still the base sha the verifier measured |
| the issue exists | open, `status/in-progress`, per `forgejo list_issues(state: "open")` |
| the label matches reality | it is not `in-progress` for work that has stopped |

A PR that fails the gate is never merged: it goes back to its author with the failing output, in
the worktree it already has.

## 8. The merge

On `APPROVED`, you merge the PR through Forgejo — `merge_pull_request` — with a real message, not
by pushing `main`. A direct push to `main` is a defect, not a shortcut: it skips the trial merge
and leaves no PR to point at.

Merge only on an approval that still holds. The verifier measured a base sha; if `main` has moved
past it, the approval is stale — re-verify, do not merge a measurement that no longer describes the
tree.

`integrator` is the exception path: a merge Forgejo cannot perform (a conflict only a human can
arbitrate, an outage). It says why in its report, and the normal path stays the PR.

**One verifier and one merge at a time, across the whole board.** Two trial merges can each pass
alone and conflict together; a merge moves `main` under another verifier's measurement. That is
yours to enforce, not the verifier's to detect.

The PR closed or sent back without merging goes to its author in `status/todo` with the finding
quoted, in the worktree it already has.

## 9. The review, and the revert

The review is inside the verifier's pass on the PR: that is the gate a merge passes. `reviewer`
stays for periodic audits of what already landed — the merged tree, read for what a trial merge
did not show: a hunk dropped in a conflict, a test weakened to pass, a generated file not
regenerated, a contract changed on one side.

A merge that regresses is reverted, not repaired in a panic:

```sh
git revert -m 1 <merged-sha>         # the PR's merge commit keeps its first parent
git push origin main && make test    # green again, or you are not done
```

The revert sha, the finding and the reason go in the issue; the branch returns to its author in
`status/todo` with the finding quoted, and the next attempt starts from a measured green tree.

## 10. The lifecycle

| State | Board | Git | Who acts |
|---|---|---|---|
| proposed | `backlog` | — | orchestrator |
| accepted | `todo` | — | orchestrator |
| in flight | `in-progress` | `work/<name>`, commits landing | subagent |
| delivered | `in-progress` | branch pushed, PR open | subagent, then orchestrator verifies |
| verified | `in-progress` | `APPROVED` at a recorded base sha | `verifier`, serialized |
| merged | `done` + closed | PR merged on `main` by `merge_pull_request` | orchestrator |
| reverted | `todo` | revert commit on `main`, PR closed | orchestrator, finding quoted |

A workstream with no open PR has not delivered. A merge stands on an `APPROVED` that still matches
`main`; anything else is re-verified before it lands.

## 11. Failure modes

- **Empty or partial report** — the agent died, was cut, or answered "mostly". Not done; relaunch
  narrower in a fresh worktree from the same `main`, and ask for the exact missing item.
- **A PR that does not merge** — the verifier returns `REQUEST_CHANGES` with the file and the line;
  the author gets it in its own worktree and pushes to the same branch. Do not re-cut the work to
  dodge a rebase.
- **Conflicting edits** — the worktrees should have made this impossible: diff both branches, keep
  one, brief a third to reconcile, and fix the ownership overlap in the next cut.
- **Touched the record** — revert it, and say in the issue that the orchestrator owns it.
- **Report contradicts the code** — the code wins. Quote the line in the next brief.
- **A workstream with no issue** — a finding: `ticket-manager` opens it with the branch and shas.

## 12. The record, and closing

The record is written by you, in the same change that produces the finding: the issue comment
(command, output, `path:line`, timestamp, what changed and the rollback), the `status/*` moved
before the work starts and out of `in-progress` when it stops, the documents the change
invalidates, and the commit body. The subagent's summary becomes the issue comment, and the PR
number, the merged sha and the verdict are added to it.

`status/done` and closed when done and merged on an `APPROVED`; `status/blocked` with the blocker in
the body; `status/todo` when handed back unfinished or reverted; `status/backlog` when not
actionable.

## Anti-patterns

- Answering "it works" from a subagent's sentence. Quote the command or do not say it.
- A brief that says "improve the engine" — no path, no deliverable, no test.
- Two agents in one file because "they will be quick"; two agents in one checkout, ever.
- Foregrounding to "save a turn".
- Merging a PR without an `APPROVED` for the base sha `main` is on now, or two verifiers at once.
- Pushing `main` directly, or treating an open branch as delivered when no PR exists.
- Fixing a regression forward because the revert "looks like a step back".
