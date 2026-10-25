---
name: orchestrator-pattern
description: How one agent holds a whole task and gets it built — decompose into independent workstreams, isolate each one on its own branch, brief a fresh subagent with everything it needs, verify every claim yourself, and keep the record that outlives the session.
---

# Orchestrating work

A session that does the work itself spends most of its context re-learning what it already knows. A
session that delegates keeps the one thing no subagent can hold: everything at once — the board, the
decision, the state of the tree, and what the operator actually asked for.

The pattern only works if three things are true: **the subagent gets everything**, **the report is
checked**, and **the record is not in your head**.

## 1. Before you cut anything

Read the record: the issue, the documents that describe the area, the commits that touched it last.
Never answer from memory and never plan from a summary — open the file, the issue, the log.

Then answer three questions out loud, because they decide the cut:

- **What is the deliverable?** A merged change, a measurement, a document. Not "investigate".
- **What does it touch?** Two workstreams that write one file are one workstream.
- **What would prove it?** A command and its expected output. If you cannot name it, the task is not
  cut yet.

## 2. Cut

- **The repository is decided here, with the cut.** The issue is opened in the repository that
  owns the work, and the worktree, the branch and the pull request are cut from it — never from
  the tree the session happens to be sitting in. A finding noticed in this repository often
  belongs to another. If the owner is not certain, **stop and ask**: a Forgejo issue cannot be
  moved without deleting it, the MCP exposes no delete-issue call, and until a human moves it the
  board answers *what is pending here* with work that is not here.
- **One workstream, one branch, one writer.** Name it after the work (`dev/<issue-id>`), not after
  the agent.
- **Disjoint files.** Two agents in one file is one agent's work destroyed. If the split is not
  clean, cut differently or run them in series.
- **Every task type has a role, and `general` is never the answer.** The role table is `README.md` §
  *Contents → Agents*; a task that fits no row is a defect of the library, and the fix is the role —
  written, listed there, and cross-referenced from `agents/orchestrator.md` — not a general agent
  doing work nobody owns.
- **Parallel is for independent things.** A contract change goes first; its consumers after it.

## 3. The brief

A subagent starts with **no** context of your session. In this order:

1. **Where it works** — the repository (owner, name, base branch), the worktree, the branch, and
   the first command that proves the branch. The repository is named, never inferred from the
   directory this session is in. The worktree is named as the **working directory**, with the
   absolute path of every file the subagent writes: a subagent inherits the session's directory,
   which is the trunk, and a brief that mentions a worktree without moving the agent into it is a
   brief that writes into the trunk.
2. **The flow** — or, better, one line: *read the `git-workflow` skill first*. A brief without the
   flow produces a report nobody can merge.
3. **What is owned**, and what is explicitly not.
4. **The measured facts**, with where they came from. Not "the tests fail" — the command, the output.
5. **What to read** — the project's layout skill, the standards that apply.
6. **The deliverable** — commits, pushed branch, pull request naming the issues.
7. **The constraints** — the language, the gate, the thing it must not touch.

If the brief needs a paragraph of history to make sense, that history is yours to compress: the
subagent gets the conclusion and the evidence.

## 4. While they run

Liveness is read from **artifacts**, not from silence: the branch tip, the commit time, the newest
write, the pushed ref. A quiet workstream is not a dead one — a restart does not kill a child, and
relaunching one is how two writers end up in one tree.

Do not poll, do not duplicate, do not do the task beside it. Work on something that does not
overlap.

**A parent does not end its turn while a child of its own is still running.** The rule above is the
*orchestrator's*: the top-level session watching a workstream it launched with `background`, whose
liveness it can only read from artifacts. It is not a licence for a composed agent that starts its
own child — a head delegating to the generic roles — to end its turn the same way. Such a parent
launches every child **in the foreground**, with no flag, and stays until it reports; a `sessionID`
where a result should be means the launch went to the background by mistake, and that session is
continued until it reports. Polling is what the orchestrator must not do; a parent that ends its
turn mid-child is not avoiding a poll, it is failing to deliver, and *"the child is still running"*
is a status where a delivery was owed.

## 5. A report is a claim

Re-measure before repeating it: run the command, open the endpoint, read the diff. A subagent that
says "done" and an orchestrator that repeats it is how a wrong sentence acquires authority.

| Claim | Re-measure with |
|---|---|
| "tests pass" | the same command, fresh output |
| "the endpoint works" | the request and its response |
| "it is merged" | the platform, and the branch list |
| "the file says X" | the file |

## 6. Review and merge

Two roles, on purpose: one decides, another acts. A merge is gated on a verdict that states the sha
it measured, and the merger proves the result before it calls the local checkout synced. The
orchestrator owns the decision and the record; the merger owns the merge.

A delivery lands as a **merge commit**, always: `style: "merge"` through the platform, `git merge
--no-ff` locally, never `rebase`, `rebase-merge` or `squash`. The graph has to show the delivery as
a unit; a rebase publishes shas the verifier never measured, and a squash turns *each commit pushed
as it was made* into a claim nobody can check.
A delivery the platform cannot merge at all is the one exception: `merge-conflict-fixer` rebases the
branch and moves the trunk to it, so that landing is linear, not a merge commit —
`skills/git-workflow/SKILL.md` § *When the platform cannot merge* states the condition, and
`agents/merge-conflict-fixer.md` § *The sequence* the commands.

## 7. The record

The issue, the labels, the comment with the finding and its evidence, and the documents the change
invalidated. Written in the same change that produces them, because nothing else survives the
session:

- what you start → in progress, before the first command;
- what you finish → done, and closed;
- what you cannot → blocked, and the body says what by;
- what you found and did not fix → its own issue, with the evidence.
- the document the change invalidated → updated in the same change, by `docs-writer`, or the
  delivery says that none was. What no change noticed is `docs-auditor`'s sweep — deliberately, not
  per change.

An issue left in progress by an agent that stopped is worse than one never started: it says someone
is on it when nobody is.

**None of it is delegated.** A subagent reports and the session that holds the thread writes: the
record is what a later session reads as fact, and an account written by the agent it describes is
the claim §5 already refuses to repeat.

## Failure modes this pattern exists to prevent

- **Two writers, one tree** — the files of one workstream committed by the other.
- **A brief that narrated instead of naming the paths** — the agent writes into the trunk.
- **A verdict nobody measured** — a merged change nobody ran.
- **A task in flight that only exists in a chat** — no branch, no issue, nothing to read tomorrow.
