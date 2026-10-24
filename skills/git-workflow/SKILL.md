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
- **Rebase before integration, never merge `main` into the branch**:
  `git fetch origin && git rebase origin/main`. The integration is a fast-forward of `main`; a merge
  commit in the branch is rewritten by the rebase anyway.
- **No force-push, and no `main` push but the integrator's.** `git push --force` is a rewrite of
  somebody else's reference; the integrator fast-forwards `main` and is the only one who does.
- **A finished workstream is removed**: `git worktree remove <dir>` after the merge, or
  `opencode worktree_remove <dir>`. Its branch stays until the merge lands, then it is deleted.

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
measured. "wip" and "fix tests" never reach `main`; squash before merge if the branch is noisy.

## Pull requests

- **Size**: ≤ 400 changed lines excluding generated code and tests fixtures. A larger change is
  split, or it is a contract change reviewed on its own.
- **Title** follows the commit convention; the body carries the issue link, the evidence and the
  rollback.
- **Review**: `reviewer` makes the final pass on the **merged tree**, after integration — its
  `BLOCK` is a revert, not a follow-up. A contract change (`proto/`, `api/`) also gets a read by
  the owner of the consumer before it is merged.
- **CI must be green** on the final commit: engine build + tests, Go build + test `-race`, web
  lint + typecheck + tests + build.
- Rebase, do not merge `main` into the branch; the history stays linear.
- **The integrator lands it**: `git switch main && git merge --ff-only work/<name>`. Nobody else
  pushes `main`, and the worktree is removed once the merge lands.

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