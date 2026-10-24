---
name: forgejo-ticketing
description: How a board carries a project's state — one issue per event, the label taxonomy the kanban reads, an issue body that keeps the finding and its evidence, status transitions that match what is actually happening, and comments instead of twins.
---

# Ticketing on Forgejo

The board is not paperwork. **The open issues are the project's pending state**, and the closed ones
are its history: whatever is not written there does not exist for the next session.

## One issue per event

An incident, a feature, an improvement, a change, a removal, a security exposure, a proposal nobody
has built yet. One issue each, filed **in the same change that produces it**, not remembered for
later.

- **The title is the event**, in the present tense and specific enough to recognise: `the loader
  accepts a banked container it cannot boot`, not `loader bug`.
- **Something found and not fixed gets its own issue**, with the evidence. Burying it in the body of
  the issue in hand is how it is lost.

## Labels

Four families, and an issue carries one of each:

| Family | Values | Reads as |
|---|---|---|
| `type/*` | `incident`, `feature`, `improvement`, `change`, `removal`, `security`, `docs`, `test` | what kind of event this is |
| `priority/*` | `high`, `medium`, `low` | needed next, should happen, eventually |
| `status/*` | `backlog`, `todo`, `in-progress`, `blocked`, `done` | where it is — the kanban column |
| `area/*` | one per stack or concern the project actually has | what it touches |

The label set is the project's, in its own taxonomy; a label that exists but nobody reads is noise.
Add one by convention, not per issue.

## The body

Ordered, so a reader can stop early:

1. **What happened / what is wanted**, in one paragraph.
2. **The measurement** — the command, the output, the file and line, the version, the date. For a
   defect, the reproduction; for a feature, the requirement it serves.
3. **Why it matters** — the consequence, not the sentiment.
4. **The fix or the shape** — what would make it right, and the alternatives if there are two.
5. **Acceptance** — the checks that would prove it done, each measurable.
6. **Rollback** — how this is undone: a revert, a restore, a documented step.

An issue whose acceptance cannot be checked is a wish.

## Status is a promise

| State | Means | When you move it |
|---|---|---|
| `backlog` | proposed, not built, not scheduled | when it is filed as a proposal |
| `todo` | actionable, not started | when it is agreed and queued |
| `in-progress` | **someone is on it right now** | **before the first command** of the work |
| `blocked` | stuck, and the body says what by | when it stops being actionable, with the reason |
| `done` | finished, and the evidence is in the issue | with the closing comment |

- **Never leave an issue in progress when you stop.** Take it out in the same breath: done, blocked,
  or back to todo. An issue in progress by an agent that stopped is worse than one never started —
  it says someone is on it when nobody is.
- **The label is the lifecycle**, and it is a lie the moment it drifts from what you are doing.

## Comments, not twins

- **Something new about an existing issue is a comment** on it, with the evidence, and a status move
  if the situation changed. Filing a second issue for the same event fragments the record.
- **A closing comment carries the proof**: the commit, the merged sha, the command and its output,
  what was deliberately left out, and the issue that carries what remains.
- **Closing is never deleting.** A decision reversed later is a new issue that links the old one.

## Working the board as an agent

1. Read the open issues **before** proposing or changing anything: `backlog` is what is proposed,
   `todo`/`in-progress` is what is in flight, `blocked` says what is stuck.
2. Move the issue in hand to `in-progress` before the first command.
3. When the work stops — whatever the reason — set the state that is true, and write the comment that
   explains it.
4. If the board does not answer, say so before doing anything else: without the board there is no
   issue, and without an issue the work has no record.
