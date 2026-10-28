---
name: backup-and-restore
description: What must be preserved, what a backup is not, and how a restore is proven — state versus configuration, the inventory that drifts away from reality, retention and the disk it eats, and the rule that an unexercised restore is a hope with a schedule attached.
---

# Backup and restore

A backup is not a copy of something that exists. It is a claim that a specific thing can be made to
exist again, at a stated age, from a stated store, by a stated procedure. Until that claim has been
exercised, it is a hope with a schedule attached.

## What is state and what is configuration

| Kind | Example | Where it belongs |
|---|---|---|
| **Configuration** | a compose file, a unit, a route, a dashboard | the repository — rebuildable, reviewable, revertible |
| **State** | a database, an uploaded file, a user's session store, a key | nowhere in the repository; in a backup, with its restore procedure |
| **Neither** | a cache, a rendered page, a temporary index | nowhere; regenerating it is the correct recovery |

The test for a file is the same in both directions: **does this rebuild the thing, or did the thing
produce it?** A backup that carries what the repository already carries is cost without recovery value,
and a repository that carries what the backup should carry is a leak waiting for a clone.

## The inventory drifts, and the drift is the defect

The list of what must be backed up lives somewhere — a table, a role, an agent's configuration — and the
estate grows beside it. So the check is not "is the list right" but **"does the list describe reality"**,
and it is answered by comparing the two, not by reading the list:

- every store that holds state appears in the inventory;
- every entry in the inventory names something that still exists, with the volume or path it really is;
- and an entry that names a *file* where the estate has a *directory* is a defect that fails every night
  without ever proving it is broken.

Two errors are worth naming because they hide: **an orphan** (an inventory entry for a store nobody runs
anymore) still consumes a schedule and still fails, and **a gap** (a store with state and no entry) is
silent until the day it is needed. Both are found the same way, by joining the inventory to reality and
reporting the difference.

## Retention is a decision with a number in it

More is not safer: a retention that fills a disk guarantees the failure it was meant to prevent, and an
unpruned store grows until the backup job is the incident. Write it down as a number — how far back
questions can be answered, how many copies of the last day, how long an off-site copy lives.

**RPO and RTO are different promises.** *How much can be lost* sets the schedule; *how long until it is
back* sets the procedure, and a restore nobody has timed is a procedure of unknown length.

## Proving a restore

A backup job that exits zero has proven that a file was written. The restore is proven by making the
thing exist and using it:

1. pick a **real** artefact from the store — not the newest alone, and at least once an old one, because
   a rotated store is where the unreadable copy hides;
2. restore it **somewhere that is not the production path**;
3. **start the consumer** against the restored data and answer a query with it;
4. record the command, the timing, the size and what the answer was.

The record of that exercise belongs with the service's documentation, dated. A restore procedure that is
only written has never been run by the person who will need it.

## Snapshots are not backups

A snapshot is a point-in-time view of a live store, tied to the store, its filesystem or its retention. It
is excellent for a fast rollback of a mistake and it is not a copy that survives losing the machine, the
volume or the account. Both are worth having; confusing the two is how an estate has neither.

## What the report carries

What is protected with its schedule, the drift found between inventory and reality (orphans and gaps, each
with the evidence), the age and the size of the last artefact, the restore that was exercised with its
command and result, and the retention with the number of days it actually holds.
