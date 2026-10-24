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
- **every task is a subagent launched in the background**, with its own fresh context;
- it never trusts a report it has not re-measured, and it owns the record: the issue, the
  documents and the commit.

`skills/orchestrator-pattern/SKILL.md` is the operating manual: how to cut the work, how to brief
a subagent, what stays with the orchestrator, and how to close.

## Contents

### Agents

| Agent | Mode | Owns |
|---|---|---|
| `orchestrator` | primary | The thread. Delegates everything, verifies, writes the record. No mutating permissions. |
| `verifier` | subagent | Measures: builds, tests, endpoints, logs. Reports evidence, never edits. |
| `cpp-engineer` | subagent | C++ engine code and its CMake build and unit tests. |
| `go-engineer` | subagent | Go services: API, RPC clients, MQTT, OpenAPI-generated handlers. |
| `web-engineer` | subagent | The browser frontend: React, TypeScript, styling, frontend tests. |
| `toolchain-engineer` | subagent | Assembler, disassembler, ROM build pipeline and CLI. |
| `test-engineer` | subagent | Test suites across stacks: unit, integration, golden files, fuzzing. |
| `reviewer` | subagent | Read-only code review against the stack's rules. |
| `security-reviewer` | subagent | Read-only threat review: inputs, secrets, process boundaries, supply chain. |
| `docs-writer` | subagent | README, `docs/`, ADRs, API references. |
| `ticket-manager` | subagent | The Forgejo board: labels, issues, status transitions, milestones. |
| `conan-dependencies` | subagent | The Conan 2 graph: `conanfile`, profiles, lockfiles, licences. |

### Skills

| Skill | For |
|---|---|
| `orchestrator-pattern` | Decomposing work, briefing background subagents, verifying, closing. |
| `z80-isa` | The Z80 instruction set, flags, timing, interrupts, undocumented behaviour. |
| `cpp-quality` | C++20 conventions, ownership, error handling, sanitizers, CMake. |
| `go-quality` | Go conventions, context, errors, concurrency, package layout. |
| `web-quality` | React 19 + TypeScript conventions, state, accessibility, testing. |
| `rom-toolchain` | ROM source kinds, assembler/disassembler contract, build pipeline. |
| `testing-strategy` | What to test at which level, golden files, coverage gates, fuzzing. |
| `documentation-standards` | Document set, template, links, evidence beside claims. |
| `forgejo-ticketing` | Label taxonomy, issue template, board flow, PR flow. |
| `connect-rpc` | Protobuf contract, Connect server/client, error model, codegen. |
| `openapi-contract` | OpenAPI-first REST, generated handlers, validation, versioning. |
| `mqtt-events` | Topic taxonomy, payload schemas, QoS, retained state. |
| `git-workflow` | Branches, conventional commits, PR size, review, merge. |
| `conan-dependencies` | Conan 2: `conanfile.py`, profiles, lockfiles, binary compatibility, audit. |

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
