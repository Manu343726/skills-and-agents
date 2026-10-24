---
name: git-workflow
description: How work moves through git — branches named after the work, every commit pushed as it is made, Conventional Commits with a body that says what was measured, pull requests small enough to review, and a merge that keeps the history honest.
---

# Git workflow

## Branches

- **One branch per unit of work.** `dev/<issue-id>`, or `dev/<description>-<ids>` when one change
  serves several issues. Lowercase, hyphens, no names of people.
- **Cut from the trunk you measured**, never from another unfinished branch.
- **Push the branch as soon as it exists**, before the first file changes. A branch that lives only
  in one working tree has delivered nothing and dies with the session — and liveness can only be read
  from what the remote has.
- **Isolation is per writer, not per intention.** A worktree per branch, or one writer at a time: two
  agents in one checkout overwrite each other's index with no trace.

## Commits

- **As many as the work needs, and every one pushed when it is made.** No local pile, no `wip:`
  waiting for attention. The branch history is what a reviewer reads.
- **Conventional Commits**: `type(scope): imperative summary`, ≤ 72 characters. `feat`, `fix`,
  `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`.
- **The body carries the evidence**: what was wrong, what changed, the command and the output that
  proves it, and `Refs #N`. A commit that cannot name its measurement is a preference.
- **A commit that claims to work passes at that commit.** An exploratory commit says it is one.
- **Never commit state**: build output, dependencies, coverage, generated artefacts that the build
  regenerates, real secrets. Configuration and sources only.

## Pull requests

- **The PR is the queue.** A delivery that is only a message is a delivery nobody can find.
- **Small enough to review**: roughly ≤ 400 changed lines excluding generated code and fixtures.
  Larger is split, or it is a contract change reviewed on its own.
- **Title** follows the commit convention. **Body** carries `Refs #N` for every issue, what changed,
  what was measured (command and output), what was deliberately not done, and the rollback.
- **One logical change**, and its tests. A drive-by rename in the same diff is a review tax.

## Review and merge

- **The verdict names the sha it measured** and answers first: approved, or changes requested — then
  the evidence, in severity order.
- **A trial merge**: merge the branch onto the trunk's current tip, run every suite the diff touches
  on the result, and report both shas. A branch tested only on its own base is untested.
- **The merge keeps the authors' commits.** No squash of a reviewed history, no force push over a
  published branch.
- **After the merge**: prove it on the trunk, delete the head branch, and bring the local checkout to
  the merged commit with an autostashed rebase — a dirty tree that conflicts is a stop, not a
  `reset --hard`.

## When the platform cannot merge

A rebase needed, a conflict the platform will not resolve, an outage. Say which, in one line, before
anything else. Never resolve a conflict by dropping a test: that is a finding, and the finding is the
deliverable.

## Never

`push --force`, `push --force-with-lease`, `reset --hard` over uncommitted work, `clean -f`, deleting a
ref a review has not read, `stash clear`, rewriting published history. Each of them destroys something
that git cannot give back.
