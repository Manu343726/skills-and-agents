---
name: forgejo-ticketing
description: The Forgejo board for manu343726/z80-emulator — label taxonomy, the issue body template, the status lifecycle the kanban reads, and comment-don't-duplicate.
---

# Forgejo ticketing

Board: <https://git.manu343726.com/manu343726/z80-emulator/issues>. The **open** issues are the
project's pending state; the kanban columns are derived from the `status/*` labels. Reach it with
the `forgejo` MCP server, repo `manu343726/z80-emulator`.

## Read first

```
forgejo list_issues(state: "open")
forgejo search_issues(q: "<the subject>")
forgejo list_labels()
```

If an issue already carries the subject, **comment there** and move its status. A twin splits the
evidence across two threads and is deleted by the next person.

## Labels

| Namespace | Values | Meaning |
|---|---|---|
| `type/*` | `feature` `improvement` `bug` `incident` `change` `removal` `security` | what kind of event |
| `priority/*` | `critical` `high` `medium` `low` | how soon |
| `status/*` | `backlog` `todo` `in-progress` `blocked` `done` | where it is (the kanban) |
| `area/*` | `engine` `proto` `backend` `web` `toolchain` `roms` `docs` `build` | what it touches |

Exactly one `type/*`, one `priority/*`, one `status/*`; one or more `area/*` for what the change
actually touches (a `proto` change also carries `backend` and `engine`).

## Body template

```markdown
## What
The event or the proposal, one paragraph, present tense.

## Evidence
- `$ go test ./... -race` → `FAIL backend/internal/stream (0.42s)` (2026-10-24 06:12)
- `backend/internal/stream/sse.go:88` — `time.After` inside the heartbeat loop

## Expected
The smallest statement of the correct behaviour, with the test that will assert it.

## Scope
- In: `backend/internal/stream/**`
- Out: `api/openapi.yaml`, `web/**`

## Rollback
`git revert <sha>`, or the manual step that undoes it.

## Definition of done
- [ ] `TestSSE_Heartbeat` exists and passes
- [ ] `docs/api/sse.md` states the heartbeat interval
```

An incident replaces `What` with `Impact`, `Cause` and `Fix`, and carries the timestamps in the
body. The title names the event, not its date — an issue filed at the moment it happened is dated by
its creation; only a write-up after the fact puts the date in the title.

## Lifecycle

| From | To | When |
|---|---|---|
| — | `backlog` | a proposal nobody has picked up |
| `backlog` | `todo` | accepted, not started |
| `todo` | `in-progress` | **before the first command of the work** |
| `in-progress` | `blocked` | stopped; the body says what blocks it and who |
| `in-progress` | `todo` | handed back unfinished |
| `in-progress` | `done` | merged, evidenced |
| any | `backlog` | turns out not to be actionable yet |

`in-progress` left behind by an agent that stopped is the one always-wrong state: it claims
somebody is on it when nobody is. Moving it is part of stopping, not optional bookkeeping.

## Closing

- Close only with evidence in a comment: the commit SHA, the command and its output, the PR, the
  document revision.
- Never close on a subagent's word. Re-measure, then write the comment.
- `Closing is not deleting`: a closed issue that turns out to be wrong is reopened or superseded
  with a link, never removed.
- A finding that does not belong to the issue in hand gets **its own issue**, in the state it
  belongs to (`backlog` for a proposal, `todo` for something found and queued).

## Kanban

Columns follow `status/*`: Backlog, Todo, In progress, Blocked, Done. Moving a card and relabelling
the issue are the same action; the board is not a second source of truth.