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
`chore/conan-lock-refresh`, `docs/connect-rpc`. Lowercase, hyphens, no names.

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

Each commit is one logical change that builds and passes on its own. "wip" and "fix tests" never
reach `main`; squash before merge if the branch is noisy.

## Pull requests

- **Size**: ≤ 400 changed lines excluding generated code and tests fixtures. A larger change is
  split, or it is a contract change reviewed on its own.
- **Title** follows the commit convention; the body carries the issue link, the evidence and the
  rollback.
- **Review**: at least one; a contract change (`proto/`, `api/`) gets a second review by the
  owner of the consumer.
- **CI must be green** on the final commit: engine build + tests, Go build + test `-race`, web
  lint + typecheck + tests + build.
- Rebase, do not merge `main` into the branch; the history stays linear.

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