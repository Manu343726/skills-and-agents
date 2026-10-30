---
name: git-workflow
description: How work moves through git — branches named after the work, every commit pushed as it is made, Conventional Commits with a body that says what was measured, a head that is green before the pull request is opened or, where CI runs on pull requests only, before its merge, pull requests small enough to review, and a merge that keeps the history honest.
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

## A green head before the PR

**A branch is not delivered until the gate has passed on its head.** Where the project's CI can run on
a branch push, the pull request is opened after the head sha is green — not before it, and not with
the fix promised in review: a red head is a tree nobody has seen work, and the queue is for work
rather than for runs still to come. Until that run exists the branch is unfinished, and so is the
task it carries.

**Where the project's CI runs on pull requests only, the pull request is opened to produce the run.**
A workflow that triggers on `pull_request` and on pushes to the trunk, and on nothing else, emits
nothing for a branch push — so there is no run to wait for before the pull request exists, and the
pull request is what causes it. There the requirement moves from *before the pull request* to *before
the merge*, because the merge is where the gate can be observed: the branch is pushed, the pull
request is opened, the run it produces is read at the head sha, and the pull request is not merged
until that run is green. **The delivery says which wiring it ran under**, in one sentence, because
the reader cannot see the workflow file: a branch whose CI can run without a pull request cites the
run that was green before the pull request was opened, and a branch whose CI cannot says `CI runs on
pull requests only:` and names the run id the pull request produced. Nothing else moves — a red head
is still fixed forward with a new commit and never by rewriting, the requirement is still on the head
sha, and a green run on another sha is not this branch's green.

- **The requirement is on the head sha, not on every commit.** *At least the last, ideally all*: a
  red intermediate commit that a later commit fixes is the honest record of a break and its repair,
  and it stays. **The history is never rewritten to make a log look clean** — no amend, no squash,
  no force-push to tidy the red away — because what the next reader needs is that the break happened
  and what fixed it.
- **A red head is fixed forward**: a new commit on the same branch, pushed as it is made, with the
  green run on the new sha in the report. Not a rewrite, not a force-push, not a branch cut again
  from the base — and not *"it was a flake"* unless a re-run of that same sha came back green and the
  run id sits beside the sentence. A flake nobody re-ran is a failure with a nicer name.
- **A gate that never ran is not a block.** The rule is about a gate that exists and fails. A
  repository with no CI — no workflow file, no runner registered — delivers on the local suite, and
  the delivery says `CI did not run:` and why, in the words `agents/verifier.md` uses — § *The CI
  result, at the sha you measure*. A branch is not held hostage to a pipeline the project never
  built, and a local green is never presented as a gate.
- **The gate is read at the sha, not at the PR.** A green run on an earlier push describes a tree
  nobody is being asked to merge; filter the runs by the branch's head sha (`list_workflow_runs` with
  `head_sha`, or `git rev-parse` of the pushed tip) and cite the run id beside the result.

This paragraph is earlier in the flow than the verdict, and the two are complementary rather than
duplicates: it stops a red branch reaching a pull request at all — or, where the pull request is what
runs the gate, reaching the merge — while `verifier` blocks a red gate at the verdict and `reviewer`
audits the merged tree after it. A branch whose run is green when its pull request arrives keeps the
queue short; a verdict is the net under what still got through.

Fixing forward is not an exception to § *Bringing a branch up to date* or § *Never*: a published
commit is a sha somebody may have measured, so it is added to, never replaced.

## Pull requests

- **The PR is the queue.** A delivery that is only a message is a delivery nobody can find.
- **Small enough to review**: roughly ≤ 400 changed lines excluding generated code and fixtures.
  Larger is split, or it is a contract change reviewed on its own.
- **Title** follows the commit convention. **Body** carries `Refs #N` for every issue, what changed,
  what was measured (command and output), what was deliberately not done, and the rollback.
- **The documentation it invalidates, or a line saying none does.** A body names the page the
  change updates — a technical page, or the product page a new capability needs — and updates it
  in the same diff; a change that invalidates no page says so once, in the body, rather than
  leaving the reader to guess.
- **One logical change**, and its tests. A drive-by rename in the same diff is a review tax.

## Review and merge

- **The verdict names the sha it measured** and answers first: approved, or changes requested — then
  the evidence, in severity order.
- **A trial merge, with `git merge --no-ff`**: merge the branch onto the trunk's current tip, run
  every suite the diff touches on the result, and report both shas. A branch tested only on its own
  base is untested.
- **The merge is a merge commit, always.** Through the platform, `merge_pull_request` with
  `style: "merge"` — never `rebase`, `rebase-merge` or `squash`; locally, `git merge --no-ff`,
  never a bare `git merge` that can fast-forward. The graph has to show the delivery as a unit — the
  branch, its commits, and the point it landed — and this process measures shas: a rebase publishes
  commits the verifier never measured, and a squash makes "commits `a`, `b`, `c`, each pushed as
  it was made" a sentence nobody can check.
- **The merge keeps the authors' commits.** No force push over a published branch, no rewrite of a
  history a review has read.
- **After the merge**: prove it on the trunk, delete the head branch **on the platform**, **remove
  its worktree (refused unless the tree is clean and its HEAD is an ancestor of the merge commit
  just proved)**, sync the local checkout **onto the delivered sha** with `git pull --rebase` under
  an autostash, and delete the branch **locally** — `git branch -d`, never `-D`, after its worktree
  is gone (it refuses a branch a worktree still has checked out) and **after the sync**, so that
  `-d`'s ancestor is `HEAD` itself and not an upstream the platform pruned. The delivery already
  landed as a merge on the platform, so the checkout has nothing to land: `--rebase` leaves
  `main` exactly on `merge_commit_sha`, `git rev-list --count origin/main..HEAD` at `0`, and the
  change usable at the sha the board names. A local merge here would leave the operator one commit
  away from the delivery, with a commit no verdict, no report and no `list_branches` names. A pull
  that conflicts — the operator's own commits on `main` colliding with what arrived — is a stop and
  a report: `git rebase --abort`, the work restored, the merge still standing. Never a
  `reset --hard`, never a force.

## Bringing a branch up to date

**A branch is never rebased.** When a `dev/*` branch needs what `main` has gained — the PR reports
conflicts, or a verdict measured a base that has since moved — the branch takes the trunk into
itself:

```sh
git fetch origin
git switch dev/<id>
git merge --no-ff origin/main   # main INTO the branch: a merge commit — what it took, and when
# resolve the conflicts, if any — in the branch, keeping both intents
git push                        # committed and pushed like any other change on the branch
```

`--no-ff` keeps the update visible when the branch happens to be only *behind*: without it, git
fast-forwards the branch onto a commit `main` already had, the graph records nothing, and the next
reader cannot tell an updated branch from one that was never touched. With it, the branch carries a
merge commit naming `origin/main`'s tip at the moment it took it in.

Then it returns to the queue: the verdict is re-measured on the new tip, and the delivery lands as a
merge commit as always. What must never happen is the other direction — this branch's commits
replayed onto `main`, by `git rebase`, by `git pull --rebase`, or by a platform style that does it on
our behalf. **That prohibition is about a work branch**: its commits are deliveries and the verdict
measured their shas. The operator's checkout is not one — it publishes nothing, and the sync above
moves it onto a sha that already landed.

The reasons are the ones this process already runs on. **It measures shas.** A verdict names the
base it measured and the tree it produced; a rebase replaces every commit on the branch with a new
one, so what lands is not what was approved, and *"commits `a`, `b`, `c`, each pushed as it was
made"* becomes a set of shas no verifier ever saw. **And the graph keeps what actually happened** —
where the branch forked, which trunk commits it took and when, which conflicts were resolved and
how. A rebase erases exactly that, and the erasure is the part no later session can reconstruct from
anywhere else.

## When the platform cannot merge

A conflict the platform will not resolve, or an outage of it. Say which, in one line, before
anything else. The landing is not different for it: `merge-conflict-fixer` merges `main` into
`dev/<id>`, resolves the conflicts there, pushes the branch, and the delivery lands as the merge
commit every other delivery lands as. `agents/merge-conflict-fixer.md` carries the sequence and what
it refuses. Never resolve a conflict by dropping a test: that is a finding, and the finding is the
deliverable.

## Never

`push --force`, `push --force-with-lease`, `reset --hard` over uncommitted work, `clean -f`, deleting a
ref a review has not read, `stash clear`, rewriting published history — and, on a `dev/*` branch,
`git rebase` and `git pull --rebase`, which rewrite it. Each of them destroys something that git
cannot give back.
