---
name: release-policy
description: How a trunk becomes a version — the readiness question a project answers for itself, the level question with semver's shape and the project's own criterion, the artefact-before-tag rule and why a wrong tag cannot be withdrawn, and the finding when a project has documented no procedure at all.
---

# Release policy

A release is two judgements and one procedure. *Is a version due?* and *at which level?* are
judgements about a trunk; *how does this project release?* is a procedure the project wrote down. This
skill is the pattern behind the first two and the discipline around the third. **The release agent is
the same everywhere; the procedure is never.**

Nothing here decides a version. A project's own documentation decides it, and this page tells you what
that documentation must answer, what to do while it does not, and which mistakes cannot be undone.

## The shape

- **A trunk is released in semantic versions**, one version per release, `MAJOR.MINOR.PATCH`.
- **The level is decided by the change, not by the date.** A month without a release is not a reason
  to release; a month with one breaking commit is a reason to release at a level that says so.
- **A released version is immutable.** The tag, the artefact and the notes are published together and
  never edited, moved or re-pointed. A mistake is corrected by the next version, with the reason
  recorded — never by rewriting what a consumer may already have resolved.
- **A version with nothing to release is not a version.** An empty release is a claim that something
  changed, made to the only reader who cannot check it before downloading.

## The readiness question

Readiness is not a feeling and it is not a checklist this page can write for you: **each project
answers these four for itself**, and the answers are in that project's documentation.

1. **What is the gate?** The suites the project considers its release gate — the unit tests, the
   integration tests, the linters, the type checks, the contract checks — named, and run on the sha
   that will be tagged. A gate that "usually passes" is not a gate.
2. **What must the trunk be?** Its own branch, its own measure: which branch a release is cut from, at
   which commit, and whether anything may be sitting on it unreleased and unmerged.
3. **What artefacts must a release contain?** An image, a binary, a package, a set of headers, a
   bundle — with the identity each one carries (a digest, a version, a size) and where a consumer
   fetches it.
4. **What else travels with it?** The changelog, the release notes, a schema migration, a
   compatibility statement. If it must be published for the release to be complete, it is an artefact
   and the rule below applies to it.

A project that cannot answer these four in writing cannot release reproducibly, and the answer is
never to answer them on its behalf for one release: see *The undocumented case*.

## The level question

Semver is the shape. What fills the shape is the project's own statement of **which surface is the
promise** — a CLI's flags and output, a library's exported names, an HTTP document, an event schema, a
file format. Without that statement, "breaking" and "compatible" are the releaser's opinion, and two
releasers reach two versions.

Given the surface, the three levels mean:

| Level | What it is | What it is not |
|---|---|---|
| **major** | a change a consumer must act on to keep working — a removed or renamed export, a required field, a changed default, a narrowed input, a dropped platform | "a large diff", "a schema file touched", "a dependency bumped" |
| **minor** | a capability added without breaking: a new optional field, a new subcommand, a new endpoint, a new hook | a new default, a new required value, or a behaviour change in an existing path — those are major |
| **patch** | a fix that changes nothing else: a wrong answer corrected, a crash removed, a typo, a performance gain with the same output | an internal refactor that leaks into one observable path, which is at least a minor |

The honest caveat, because it decides more real releases than the table does: **while a project is
`0.x`, "breaking" usually bumps the minor.** That is a convention, not a rule of semver, and it is the
project's call to state — a `0.x` library that says nothing has not told you whether `0.4.0 → 0.5.0` or
`0.4.0 → 1.0.0` is the breaking release, and guessing silently makes the version mean something
different from what its own history meant. Read the page; if there is no page, the finding is the
missing page, and the level is confirmed with a person before anything is tagged.

**A major bump is a decision a person confirms.** The releaser proposes it with its evidence — the
commits, the issues, the criterion quoted — and the operator answers. The releaser is not the person
who decides that the next release breaks everyone's code.

## The artefact-before-tag rule

**A version is tagged and published only if the artefact was built and uploaded.** The order is the
rule, not a preference about tidiness:

1. the build ran, on the sha being released;
2. it succeeded;
3. its output was uploaded — the registry, the package index, the release assets;
4. the upload is verified to exist, with the identity it carries;
5. the tag is created;
6. the release is published and then read back from the outside.

**A tag and a release that point at a build which failed are worse than no release, because they are
immutable and wrong.** They cannot be corrected in place; the choices left are to move public history,
to delete a version somebody may have resolved, or to ship a later version that has to explain its
predecessor. All three cost more than the release would have, and every consumer who resolved the bad
tag has already read it. No release at all is a state a project can be in; a wrong release is a story
it has to keep telling.

Two corollaries that follow from the order and are worth stating separately:

- **a queued or in-flight build is not built.** Waiting is not a step of the procedure; a release
  performed while the build runs is a release performed on a hope.
- **a successful build of a different sha is not this release's build.** The sha the artefact was built
  from and the sha being tagged must be the same value, quoted side by side in the finding.

## The undocumented case

**If a project documents no release procedure, the finding is "this project cannot be released
reproducibly", and it is filed — not improvised.** That is not a technicality about paperwork:

- a release invented once is a release the next session cannot repeat, so the version history becomes
  a record of who ran what from memory;
- an invented tag is immutable, so the improvisation outlives the session that made it;
- an undocumented artefact is one no consumer can verify afterwards, and no maintainer can rebuild.

The finding is cheap and the improvisation is not. It names what was searched — the `AGENTS.md`, the
`docs/` page that does not exist, the build description with no release target — and the decision that
is missing: which branch, which gate, which artefacts, which surface is the promise, and how the level
is chosen. Filed as an issue, it is work somebody can pick up; improvised in a session, it is a tag
with no author and no repeat.

The same applies to half a procedure. A project with a `make release` that builds but never uploads, or
an upload job triggered by a tag it expects a human to push by hand, has a procedure with a step
missing — and the missing step is where the tag lands on nothing.

## Working through it

The order, for a release performed today:

1. **Read the project's procedure and its versioning policy**, both quoted with `path:line`. Nothing
   else in this list can run first, because step 5 is whatever that procedure says.
2. **Measure the trunk** against the project's gate, on the sha to be released, and keep the command
   and its output.
3. **Evaluate the level** from the commits since the last release, the issues they name with their
   `type/*` labels, and the project's stated criterion. Written, with the quotes.
4. **Confirm a major**, and any level the policy leaves ambiguous, with a person.
5. **Run the procedure** in its documented order.
6. **Verify the artefact** before the tag, and quote it.
7. **Tag, publish, and read the release back** — the published version, the tag, the artefact and a
   consumer's first successful command. The release is done when it can be read from the outside, not
   when the last command of the procedure returns zero.

## What to do when a release is wrong

Wrong tag, wrong artefact, wrong level — the correction is forward and it is written down:

- **Never move, re-point or delete a published tag.** A tag that moved is a version whose meaning
  changed after consumers resolved it, and the mirror of it is a build nobody can identify.
- **Publish the next version** with the fix, and record what the previous one shipped wrongly — in the
  release notes and in the issue.
- **A yanked artefact keeps its version.** The registry's yank or deprecate is a statement about a
  version; deleting it is a statement about everyone who depended on it.

An incident that reached a consumer is a ticket with the finding, its evidence and its rollback story
— the release manager's report is not the record, the board is.

## What this skill does not say

- **It does not name a command.** `git tag`, a workflow dispatch, a registry upload — each project has
  its own, and a skill that named one would be a procedure from somewhere else.
- **It does not choose a version.** It says what the choice must rest on.
- **It does not replace the project's policy**, and where the two disagree the project's policy wins,
  because the policy is what that project's consumers were promised.
