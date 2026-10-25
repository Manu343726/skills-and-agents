---
name: documentation-standards
description: Where a project's documentation lives when the project declares it, the shape of a page, the ADR format, link conventions, evidence beside every claim, the English-only rule, and the split between a document and a ticket.
---

# Documentation standards

## Where it lives

**The project says where its documentation is, and the answer is not negotiable per author.** Look
for it in the project's own `AGENTS.md`/`CONTRIBUTING` or its documentation skill. Two cases, and
they behave differently:

- **In the repository** (default `docs/`): hierarchical Markdown, one topic per file, nothing
  generated under it. A change that alters behaviour edits the page it invalidates **in the same
  change**.
- **In an external system** (a wiki, a documentation service): written there, by its own convention,
  and the repository holds only the pointer.

A page that is neither is a page nobody will find.

## The three kinds

A project's documentation is three things, and a writer should be able to say which one is in hand:

| Kind | What it is | Where it lives |
|---|---|---|
| **Technical** | implementation detail, design, architecture, the decisions and why | the project's `docs/`, in the shape § *Where it lives* just described |
| **Product** | what the thing does and how to use it — the manual a reader arrives at | `README.md`, and whatever else the project publishes for its users |
| **Work tracking** | what is in flight, pending, done; the bug, the suggestion, the proposal | the board — one issue per event |

**Work tracking is not this skill's.** An issue records an event and `forgejo-ticketing` is its
rulebook; the open issues are the project's pending state, not its description. This skill is about
the other two, and one change can need both: a new capability usually invalidates a technical page
and adds a product one. A page that reads as both is two pages wearing one hat — § *One page, one
topic*.

## One page, one topic

- **A file answers one question** and its title says which. Systems that mixes an architectural
  decision, a runbook and a changelog is three pages wearing one hat.
- **Start with the answer**, then the detail. A reader looking for how to run the thing should not
  have to reach paragraph six.
- **State the audience** when it is not obvious: an operator, a contributor, a future agent.
- **Dated claims carry the date**, and a number carries the command that produced it.

## Evidence beside the claim

The rule that separates documentation from opinion:

- A measurement appears with **what was run and what it printed**: the command, the value, the file
  and line, the timestamp.
- A claim nobody measured is written as a claim — or as `unsourced:`, an open question, not a fact.
- **A document that lags its code is worse than no document**: it is confidently wrong. If you
  cannot update it, mark it as outdated and file the issue in the same change.

## ADRs

One decision per file, immutable once accepted:

```markdown
# ADR-0007: The service speaks unary RPC, not a streaming variant

- Status: accepted | superseded by ADR-00XX
- Date: YYYY-MM-DD
- Deciders: …

## Context
The forces at play, in a paragraph. The measurement that made this a decision.

## Decision
What was chosen, in one sentence, then the detail.

## Consequences
What becomes easier, what becomes harder, what is now impossible, and what it costs.
```

- **A superseded ADR is not edited.** A new one supersedes it, and the old one says so in its status.
- **An ADR without consequences is an announcement.** The rejected alternative and its cost belong in
  the file.

## Links

- **Anything with identity is a link** — a repository path, a service endpoint, a component, a ticket.
  A reader opens it instead of hunting for it.
- A path that exists in the repository is linked as a path; a service is linked to its endpoint or to
  the page that documents it.
- **No bare "here"** as link text, and no link to a line that will move tomorrow.

## Language and tone

- **English**, everywhere the project is English — including comments, commit messages and issue
  bodies. Material ported from another language is translated, not pasted.
- **Active voice, present tense**, second person for instructions: "run", not "it should be run".
- No marketing adjectives. A page that says "powerful" says nothing.

## Document or ticket?

| It is a document when… | It is a ticket when… |
|---|---|
| it describes how things are, and stays true | it describes an event: something broke, changed, was decided to change |
| it is read repeatedly | it is read once, then closed |
| its history matters | its status matters |
| an ADR, a runbook, an architecture page, a README | an incident, a feature, an improvement, a proposal nobody has built |

A ticket that accumulates design belongs in a document with the ticket linking it. A document that
accumulates a to-do list has become a ticket and should be one.

## Before you save a page

- [ ] The project's declared location, and the link from wherever a reader would start.
- [ ] One topic, the answer first, the audience named.
- [ ] Every number with the command that produced it; every unverified claim marked as such.
- [ ] Every entity and path a link.
- [ ] The pages this change invalidates are updated in the same change.
- [ ] English throughout.
