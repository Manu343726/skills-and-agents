---
name: incident-response
description: How a live fault is worked — read the board and the runbook first, capture the evidence before changing any state, name the blast radius, take one least-invasive action and verify it from the side that reported it, then write the timeline with timestamps instead of a story.
---

# Incident response

An incident is not a debugging session with a clock on it. It is a decision procedure whose first
question is *what do I do right now* and whose second is *what actually happened* — in that order,
because a system that is down is not making evidence, it is making noise.

The role is `sre`. This skill is the loop it runs; `observability` is how it measures and `networking`
is where the path is.

## 1. Read before you run anything

- **The report, in its own words.** "The site is down" and "the site answers 502" are different
  incidents, and the second sentence was already a measurement somebody made for you.
- **The board.** An open issue for this fault may carry the last attempt, the rollback and why it
  failed. Retrying a documented failed attempt is the loop this skill exists to prevent.
- **The runbook**, if the project has one for this service. If it does not, that absence is a finding
  worth its own issue — an incident nobody has run before is an incident somebody runs twice.

Then state, before the first command, in one line each: what is degraded and from whose side, what
depends on it, and what the last change was.

## 2. Capture the evidence before you change the state

A restart is the cheapest action and the most destructive to evidence: it discards the process's memory,
its open sockets, its last log lines and the exit code that explains them.

Before the first state-changing command, collect what only exists now:

- the **exit code** and the restart count (a restart loop is a different fault from a stop);
- the **tail of the log**, with timestamps, for the interval before the stop;
- the **health and readiness** answers as they were, with their status codes;
- the **timestamps** of the last successful probe and the first failed one — that interval is the
  incident's window, and it bounds every query you will run afterwards;
- for a dependency: whether the dependency is reachable **from where the failing process runs**, not
  from your shell.

Write those five lines into the issue before acting. They are the part of the record that cannot be
reconstructed later.

## 3. Stop the bleeding, minimally

The action is the smallest one that restores the service, and it is chosen from a short ordered list:

1. **Restore the previous state** — the previous image, the previous config, the previous unit. A
   revert is the way back from a bad change; fixing forward trades a known bad state for an unknown
   one.
2. **Start what stopped**, or restart the single process that hung. Not the whole stack: a restart that
   takes dependencies with it is a new incident with the old one's timestamp.
3. **Take the failing part out of the path** — if the estate can serve without it, that buys the time
   to diagnose instead of guessing.
4. **Do nothing but tell a person**, when every action would destroy evidence or widen the blast radius.
   That is a legitimate step and it is written down as one.

**One attempt per action.** If the same command is worth running twice, the first run taught nothing and
the second will teach nothing either: the loop is the symptom of not knowing which layer is broken, and
the next move is a measurement, not the same command with more hope.

## 4. Verify from the side that reported it

The incident closes on the measurement that failed, repeated — the same URL, the same query, the same
probe, from the same vantage point. An internal healthcheck that answers `200` while the public name
answers `502 PROTOCOL_ERROR` says the process is alive, not that the incident is over.

Say what is still degraded even when the main symptom is gone: partial recovery is the normal state
after the bleeding stops, and hiding it turns one incident into two.

## 5. Then, and only then, diagnose

With the service back, the question is which layer failed first, not which layer is loudest. Order the
evidence: the first timestamp that moved, the series that changed shape, the log line that came before
the others, the deployment that landed in the window. Two facts that share a timestamp are correlated,
not caused.

A cause is stated with the query or the log line that shows it, or it is not stated. "The cause is
unknown, and X would decide it" is a complete and honest sentence, and it is worth more than a
confident story.

## 6. Write the timeline, and make the next one shorter

The issue's comment is the timeline: symptom, evidence captured, actions with their commands, the
measurement that proved recovery, the cause if known, and what would have caught it sooner.

Then the three findings a real incident usually leaves, each its own issue:

- a **gap in the signal** — nothing alerted, or the alert arrived after a person did;
- a **gap in the runbook** — the step nobody had written down;
- a **defect that made it worse** — the retry loop, the second resolver, the missing access path.

## What never belongs in the middle of an incident

- A refactor, an upgrade or a cleanup, "while I am here".
- A configuration change that makes a symptom disappear without naming the cause.
- A second, unrelated finding fixed on the way.
- Silence. A person waiting for a status that nobody sends will start their own investigation.
