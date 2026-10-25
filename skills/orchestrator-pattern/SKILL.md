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

- **One workstream, one branch, one writer.** Name it after the work (`dev/<issue-id>`), not after
  the agent.
- **Disjoint files.** Two agents in one file is one agent's work destroyed. If the split is not
  clean, cut differently or run them in series.
- **Every task type has a role.** A task that fits no role is a defect of the workflow: write the
  role, or say plainly that nobody owns it.
- **Parallel is for independent things.** A contract change goes first; its consumers after it.

## 3. The brief

A subagent starts with **no** context of your session. In this order:

1. **Where it works** — the worktree, the branch, and the first command that proves the branch.
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

## 7. The record

The issue, the labels, the comment with the finding and its evidence, the document the change
invalidated. Written in the same change that produces them, because nothing else survives the
session:

- what you start → in progress, before the first command;
- what you finish → done, and closed;
- what you cannot → blocked, and the body says what by;
- what you found and did not fix → its own issue, with the evidence.

An issue left in progress by an agent that stopped is worse than one never started: it says someone
is on it when nobody is.

## Failure modes this pattern exists to prevent

- **Two writers, one tree** — the files of one workstream committed by the other.
- **A brief that narrated instead of naming the paths** — the agent writes into the trunk.
- **A verdict nobody measured** — a merged change nobody ran.
- **A task in flight that only exists in a chat** — no branch, no issue, nothing to read tomorrow.
