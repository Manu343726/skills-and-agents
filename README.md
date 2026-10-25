# agent-skills-library

Shared OpenCode agents and skills for this machine's projects. It is a **library**, not a
project: nothing here is run directly, and nothing here knows about a particular repository.

A project references an entry by git and the `git-skills` plugin registers it for the session:

```jsonc
{
  "package": "git+ssh://git@forgejo:2222/manu343726/opencode-plugins.git#main",
  "options": {
    "plugins": ["git-skills"],
    "git-skills": {
      "agents": ["orchestrator@ssh://git@forgejo:2222/manu343726/agent-skills-library.git:main"],
      "skills": ["testing-strategy@ssh://git@forgejo:2222/manu343726/agent-skills-library.git:main"]
    }
  }
}
```

Editing a skill here changes every project on its next session. A project that needs its own
version **adopts** the entry (copy with provenance) and edits the copy; the plugin then stops
registering the remote one for that id.

## The orchestrator pattern

`agents/orchestrator.md` is the default agent of every project that uses this library. It is an
orchestrator in the strict sense:

- it holds the context of the task — the board, the documents, what the operator asked for;
- it has **no permission to act**: no edit, no shell. It reads, plans and delegates;
- **every task is a subagent launched in the background**, with its own fresh context and its own
  git worktree — never the main checkout;
- it never trusts a report it has not re-measured, and it owns the record: the issue, the
  documents and the merge.

`skills/orchestrator-pattern/SKILL.md` is the operating manual: how to cut the work, how to isolate
each workstream in its own worktree, how to brief a subagent, what stays with the orchestrator, how
it merges, and how to close.

## How work flows

1. **A workstream is cut and isolated.** The orchestrator reads the board, opens or moves the issue,
   then creates a git worktree per workstream (`opencode worktree_create <name>`), branch
   `work/<name>`. The brief names the path and the branch; no subagent works in the main checkout.
2. **A subagent delivers a pushed branch and a pull request.** Closed commits on its branch, the
   branch pushed with `git push -u origin work/<name>`, an open PR to `main` naming every issue it
   serves — and a summary (what changed, what was measured, what it did not do, the shas) with the
   Forgejo issues it touched, by number, with their `status/*` label. It never merges, never pushes
   `main`, and never closes an issue that was not its deliverable. A branch nobody pushed and a PR
   nobody opened have delivered nothing.
3. **The verifier gates the merge, the orchestrator decides when, and `merger` merges.** The
   verifier trial-merges the branch onto the base sha it measured, runs the whole suite on the
   merged result, and answers `APPROVED` or `REQUEST_CHANGES` as a review body carrying the base sha
   and the trial-merge sha. `merger` then performs `merge_pull_request` on an approval that still
   describes `main`, proves the result with the platform, and syncs the operator's checkout to the
   merged sha with an autostashed rebase.
   Nobody pushes `main`. A branch that does not build or whose tests fail is refused, and a test is
   never fixed to pass.
4. **`reviewer` audits what already landed** — the merged tree, not the branch — and answers `PASS`
   or `BLOCK` with the evidence: a hunk dropped in a conflict, a test weakened to pass, a generated
   file not regenerated, a contract changed on one side only.
5. **A regression is reverted, not fixed forward.** The revert and the reason go in the issue, and
   the branch goes back to its author in `status/todo`.

The record — the issue, its `status/*`, the documents, the merge — is the orchestrator's. It is the
only memory a session leaves behind.

## Permissions

All fifteen roles share one permission matrix, written in each `agents/*.md`, with three named
exception lines in two shapes: `orchestrator` and `ticket-manager` deny `shell` and `edit`, and
`orchestrator` alone adds `opencode_*` and `subagent`. The floor is
`{action: "*", resource: "*", effect: deny}`: every tool a role does not explicitly allow is a tool
the session does not have. The two `shell` denies are deliberate — `orchestrator` delegates every
command to a subagent, and `ticket-manager` works the board with the board's tools. `edit`
accompanies `shell`, because with a shell an `edit` scope guards nothing a role cannot already do.
Every other line is identical across the fifteen, and `execute` grants every Code Mode tool, Forgejo
included, because the harness offers no narrower scope that works.

| Role | edit | shell | execute | forgejo_* | skill | subagent |
|---|---|---|---|---|---|---|
| `orchestrator` | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ |
| `verifier` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `merger` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `cpp-engineer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `go-engineer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `web-engineer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `test-engineer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `conan-dependencies` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `merge-conflict-fixer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `reviewer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `security-reviewer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `docs-writer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `docs-auditor` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `ticket-manager` | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ |
| `agent-author` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |

## Contents

### Agents

| Agent | Mode | Owns |
|---|---|---|
| `orchestrator` | primary | The thread. Delegates everything to worktrees, verifies, decides when a verified PR merges, holds the board and the record. No `edit`, no shell. |
| `verifier` | subagent | Measures: builds, tests, endpoints, logs. Reports evidence, never edits; posts the verdict the merge is gated on. |
| `merger` | subagent | Performs the merge the orchestrator decided on: `merge_pull_request`, the proof, the head branch, and the operator's checkout synced with an autostashed rebase. |
| `cpp-engineer` | subagent | C++ sources, their build description and their unit tests, in whatever layout the project uses. |
| `go-engineer` | subagent | Go packages, their tests, the module files and the build the project uses. |
| `web-engineer` | subagent | The browser frontend: components, state, the data layer and its tests, in whatever framework the project uses. |
| `test-engineer` | subagent | Test suites only, and the coverage and fuzzing the project's gates ask for. |
| `conan-dependencies` | subagent | Owns a Conan 2 dependency graph — conanfile, profiles, lockfiles, presets integration and the licence audit. |
| `merge-conflict-fixer` | subagent | The exception path: a merge Forgejo's `merge_pull_request` cannot perform — a rebase, conflicts, the full suite on the merged tree. It pushes `main` only in that exception, and says why. |
| `reviewer` | subagent | Final pass over the merged tree: runs the suite, hunts what integration hid, answers `PASS` or `BLOCK`. |
| `security-reviewer` | subagent | Read-only threat review: inputs, secrets, process boundaries, supply chain. |
| `docs-writer` | subagent | The project's documentation, wherever it declares it lives — `docs/` by default, or the external system its `AGENTS.md` names — and it coordinates with `ticket-manager`, because a ticket is documentation too. |
| `docs-auditor` | subagent | Sweeps the documentation against the code, page by page — current, stale, contradicts, missing — and fixes the pages it can. Invoked as a sweep, not per change. |
| `ticket-manager` | subagent | The board of the repository named in the brief: issues, labels, status transitions, the kanban, and the comments that carry a finding. |
| `agent-author` | subagent | This library: agents, skills, the index, `AGENTS.md` and the project's `opencode.jsonc` — descriptions true to their bodies, permissions exactly as documented. |

**A role here is generic: it may name a tool and a convention, never a directory that belongs to one
repository.** What is particular to a project — its layout, its exact build and test commands, its
domain — belongs in that project's own skills, and a role that needs it reads them. A role that only
makes sense for one repository (this library's first `toolchain-engineer` was one: assembler,
disassembler and ROM container for a single emulator) is a local agent in that project, not an entry
here.

### Skills

| Skill | For |
|---|---|
| `orchestrator-pattern` | Decomposing work, isolating workstreams in worktrees, briefing background subagents, verifying, merging, closing. |
| `cpp-quality` | C++20 conventions, ownership, error handling, sanitizers, CMake. |
| `go-quality` | Go conventions, context, errors, concurrency, package layout. |
| `web-quality` | React 19 + TypeScript conventions, state, accessibility, testing. |
| `documentation-standards` | Where a project's documentation lives (declared by the project; `docs/` Markdown when nothing is said), the layout, the ADR format, links, evidence beside claims, and the document-versus-ticket split. |
| `forgejo-ticketing` | Label taxonomy, issue template, board flow, PR flow. |
| `openapi-contract` | OpenAPI-first REST, generated handlers, validation, versioning. |
| `git-workflow` | Branches, worktrees, conventional commits, PR size, review, merge. |

## Layout

```
agents/<id>.md                 the agent, discovered by the plugin from agents/
skills/<id>/SKILL.md           the skill, discovered by the plugin
skills/<id>/references/*.md    long material a skill loads on demand
```

The plugin reads `agents/` before any other root, so a repository that follows this layout needs
no manifest. Adding an entry is adding a directory or a file; the tables under *Contents* are the
index and are kept in the same change.

## Licence

MIT.
