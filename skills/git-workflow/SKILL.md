---
name: git-workflow
description: Trunk-based development for the emulator monorepo — short branches, Conventional Commits with a real body, PR size and review, no state committed, English only.
---

# Git workflow

## Branches

Trunk-based: `main` is the only long-lived branch and it is always green. A branch lives hours,
not weeks, and merges within a day.

```sh
git switch -c fix/ddcb-result-to-register main
# work
git fetch origin && git rebase origin/main
git push -u origin fix/ddcb-result-to-register
```

Branch names: `<type>/<slug>` — `feat/rom-catalog`, `fix/ddcb-result-to-register`,
`chore/conan-lock-refresh`, `docs/connect-rpc`. Lowercase, hyphens, no names. An agent workstream
uses `work/<slug>` instead; see *Worktrees*.

## Worktrees

**One workstream, one worktree, one branch, one directory.** The orchestrator creates it before
briefing and names both in the brief; the subagent works nowhere else.

```sh
git worktree add ../wt-ddcb-result -b work/ddcb-result main   # or: opencode worktree_create ddcb-result
git worktree list
cd ../wt-ddcb-result && git status --short                    # its own index, its own tree
```

- **Naming**: branch `work/<workstream>`, directory named after the same workstream. Not after the
  agent — two agents may take turns on one workstream and must never share a tree.
- **Where they live**: outside the main checkout (`../wt-<name>` beside it, or the harness's own
  directory). Never nested inside the repository, where it would show up in its own `git status`.
- **One branch per workstream**, cut from the `main` that was measured. Never from another
  unfinished workstream.
- **The main checkout stays the operator's.** Nobody writes there, and no brief names its path.
- **The workstream pushes its own branch and opens the pull request.** That is the delivery:
  `git push -u origin work/<name>` and `create_pull_request` against `main`. A branch nobody pushed
  has delivered nothing, and a worktree that is removed takes an unpushed branch with it.
- **Rebase before opening the pull request, never merge `main` into the branch**:
  `git fetch origin && git rebase origin/main`. A merge commit in the branch is rewritten by the
  rebase anyway.
- **No force-push, and nobody pushes `main`, ever.** `git push --force` is a rewrite of somebody
  else's reference. `main` moves only through `merge_pull_request`; `merge-conflict-fixer` is the
  exception path for a merge the platform cannot perform, not the normal way work lands.
- **A finished workstream is removed**: `git worktree remove <dir>` after the merge, or
  `opencode worktree_remove <dir>`. Its branch stays until the merge lands, then it is deleted.
  Before removing the tree, `git status --porcelain` must be empty: uncommitted work is committed
  first, and a `wip:` commit is cheaper than a lost afternoon.

The worktree is what makes parallel work possible: one `git status`, one index and one stash per
agent, so a branch that does not build cannot break the tree somebody else is reading.

## Conventional Commits

```
<type>(<scope>): <subject>

<body>

<footer>
```

| Type | Use |
|---|---|
| `feat` | a new behaviour |
| `fix` | a defect |
| `refactor` | no behaviour change |
| `perf` | a measurable speed or size win |
| `test` | tests only |
| `docs` | documentation only |
| `build` | CMake, Conan, Go modules, npm |
| `ci` | pipelines |
| `chore` | everything else |

`<scope>` is the directory: `engine`, `backend`, `web`, `toolchain`, `roms`, `proto`, `api`,
`docs`, `deps`. Subject in the imperative, lower case, no trailing period, ≤ 72 chars.

The **body** is required for anything that is not trivial, and it carries:

- **Why**, not what — the diff says what.
- **Evidence**: the command and the number, e.g. `ctest --preset conan-release` → 412/412.
- **Rollback**: `git revert` is the default; a manual step is named when a revert is not enough.
- **The issue**: `Refs: #12` or `Closes: #12` in the footer.

```
fix(engine): write the DDCB result to r[z], not only to (IX+d)

The CB table handler wrote the shifted value to memory unconditionally
and left the register form untouched, so DD CB d 06 shifted (IX+d) but
never loaded B. The handler now takes the operation and the destination
separately.

`ctest --preset conan-release` → 416/416 passed (was 414/416).

Refs: #12
```

Each commit is one logical change that builds and passes on its own, and its body says what was
measured. "wip" and "fix tests" never reach `main`: tidy the branch by squashing your own noise
before you open the pull request. The merge itself does not squash — the authors' commits are kept.

## Pull requests

The pull request is the queue: it is what a later session can enumerate
(`list_repo_pull_requests state: "open"`), so a delivery that is only a message in a session is a
delivery nobody can find.

- **Every workstream opens one**, with `create_pull_request`: base `main`, head `work/<name>`.
- **Size**: ≤ 400 changed lines excluding generated code and tests fixtures. A larger change is
  split, or it is a contract change reviewed on its own.
- **Title** follows the commit convention. The **body** carries `Refs #N` for every issue the
  change serves, what changed, what was measured (the command and its output), what was
  deliberately not done, and the rollback.
- **The `verifier` reviews the pull request**, not the trunk: it reads the diff
  (`get_pull_request_by_index`, `get_pull_request_diff`, `list_pull_request_files`), records the
  base sha it measured, trial-merges the branch onto that `main` in its own worktree, and runs the
  suites the diff touches — all of them when it touches `proto/`, `api/`, a shared header or a build
  input. It answers `APPROVED` with the evidence, or `REQUEST_CHANGES` naming the file and the line
  that decides it. A contract change (`proto/`, `api/`) also gets a read by the owner of the
  consumer.
- **The `orchestrator` merges** with `merge_pull_request`, and nobody pushes `main`. An approval is
  stale the moment `main` moves past the base sha it measured: re-verify, do not merge. One verifier
  and one merge in flight at a time, across the whole board.
- **The suites are green on the final commit** — engine build + tests, Go build + test `-race`,
  web lint + typecheck + tests + build — because there is no CI runner to run them for you.
- **The gate is a protocol, not branch protection.** No Actions runner is registered, so status
  checks could never pass, and whether Forgejo counts a self-review as an approval is unmeasured.
  The agents enforce the rule; the platform does not refuse a bad merge.
- No squash: the authors' commits are kept, and the merge message follows
  `Integrate work/<name>: <what it does>`.
- **The branch and its worktree are removed after the merge**, together with the local ref:
  `git worktree remove <dir>` and `git branch -d work/<name>`.

## What never gets committed

`build/`, `node_modules/`, `dist/`, coverage output, `*.test`, `.conan2/`, Lockfiles are the
exception: `engine/locks/*.lock`, `go.sum`, `package-lock.json` **are** committed — they pin
resolutions. `.env` files are ignored; `.env.example` carries the keys only. ROM build output
(`build/roms/`) is not a source.

Check before committing:

```sh
git status --short
git diff --cached --stat
git diff --cached | grep -nEi 'password|secret|token|api[_-]?key|BEGIN .*PRIVATE'
```

## English only

Commit messages, bodies, branch names, comments, code, documentation — English. A commit body in
another language is a change that gets rewritten.

## Before pushing

```sh
git fetch origin && git rebase origin/main
git log --oneline origin/main..HEAD      # every commit is scoped and conventional
git diff --stat origin/main...HEAD       # the size is reviewable
```