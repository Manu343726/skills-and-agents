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
- it has **no permission to act**: no edit, no shell, no network. It reads, plans, and delegates;
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
2. **A subagent delivers three things.** Closed commits on its branch, a summary (what changed,
   what was measured, what it did not do, the shas), and the Forgejo issues it touched, by number,
   with their `status/*` label. It never merges, never pushes `main`, and never closes an issue
   that was not its deliverable.
3. **`integrator` merges.** It rebases the branch onto `main`, resolves conflicts keeping both
   intents, runs the whole suite on the merged tree, and reports the commands and their output. It
   refuses a branch that does not build or whose tests fail, and it never fixes a test to pass.
4. **`reviewer` makes the final pass over the merged tree** — not the branch — and answers `PASS`
   or `BLOCK` with the evidence: a hunk dropped in a conflict, a test weakened to pass, a generated
   file not regenerated, a contract changed on one side only.
5. **A regression is reverted, not fixed forward.** The revert and the reason go in the issue, and
   the branch goes back to its author in `status/todo`.

The record — the issue, its `status/*`, the documents, the merge — is the orchestrator's. It is the
only memory a session leaves behind.

## Contents

### Agents

| Agent | Mode | Owns |
|---|---|---|
| `orchestrator` | primary | The thread. Delegates everything to worktrees, verifies, merges through `integrator`, writes the record. No mutating permissions. |
| `verifier` | subagent | Measures: builds, tests, endpoints, logs. Reports evidence, never edits. |
| `cpp-engineer` | subagent | C++ engine code and its CMake build and unit tests. |
| `go-engineer` | subagent | Go services: API, RPC clients, MQTT, OpenAPI-generated handlers. |
| `web-engineer` | subagent | The browser frontend: React, TypeScript, styling, frontend tests. |
| `toolchain-engineer` | subagent | Assembler, disassembler, ROM build pipeline and CLI. |
| `test-engineer` | subagent | Test suites across stacks: unit, integration, golden files, fuzzing. |
| `integrator` | subagent | Merges a branch onto `main`: rebase, conflicts, the full suite on the merged tree. The only agent that pushes `main`. |
| `reviewer` | subagent | Final pass over the merged tree: runs the suite, hunts what integration hid, answers `PASS` or `BLOCK`. |
| `security-reviewer` | subagent | Read-only threat review: inputs, secrets, process boundaries, supply chain. |
| `docs-writer` | subagent | The project's documentation, wherever it declares it lives — `docs/` by default, or the external system its `AGENTS.md` names — and it coordinates with `ticket-manager`, because a ticket is documentation too. |
| `ticket-manager` | subagent | The Forgejo board: labels, issues, status transitions, milestones. |
| `conan-dependencies` | subagent | The Conan 2 graph: `conanfile`, profiles, lockfiles, licences. |

### Skills

| Skill | For |
|---|---|
| `orchestrator-pattern` | Decomposing work, isolating workstreams in worktrees, briefing background subagents, verifying, merging, closing. |
| `z80-isa` | The Z80 instruction set, flags, timing, interrupts, undocumented behaviour. |
| `cpp-quality` | C++20 conventions, ownership, error handling, sanitizers, CMake. |
| `go-quality` | Go conventions, context, errors, concurrency, package layout. |
| `web-quality` | React 19 + TypeScript conventions, state, accessibility, testing. |
| `rom-toolchain` | ROM source kinds, assembler/disassembler contract, build pipeline. |
| `testing-strategy` | What to test at which level, golden files, coverage gates, fuzzing. |
| `documentation-standards` | Where a project's documentation lives (declared by the project; `docs/` Markdown when nothing is said), the layout, the ADR format, links, evidence beside claims, and the document-versus-ticket split. |
| `forgejo-ticketing` | Label taxonomy, issue template, board flow, PR flow. |
| `connect-rpc` | Protobuf contract, Connect server/client, error model, codegen. |
| `openapi-contract` | OpenAPI-first REST, generated handlers, validation, versioning. |
| `mqtt-events` | Topic taxonomy, payload schemas, QoS, retained state. |
| `git-workflow` | Branches, worktrees, conventional commits, PR size, review, merge. |
| `conan-dependencies` | Conan 2: the compiler, cmake and ninja from Conan, `conanfile.py`, profiles, lockfiles, audit. |
| `parallel-execution` | Where the cores go, the delta barrier that keeps it reproducible, the atomics and padding rules, and how a parallel change is measured. |

## Layout

```
agents/<id>.md                 the agent, discovered by the plugin from agents/
skills/<id>/SKILL.md           the skill, discovered by the plugin
skills/<id>/references/*.md    long material a skill loads on demand
```

The plugin reads `agents/` before any other root, so a repository that follows this layout needs
no manifest. Adding an entry is adding a directory or a file; the table above is the index and is
kept in the same change.

## Licence

MIT.
