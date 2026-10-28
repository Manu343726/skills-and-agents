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
- it **delegates every action**: it carries the same permission block as every role, and what
  refuses the edit and the command is its contract, not the block. It reads, plans and delegates;
- **every task is a subagent launched in the background**, with its own fresh context and its own
  git worktree — a workstream never runs in the main checkout;
- it never trusts a report it has not re-measured, and it owns the record: the issue, the
  documents and the merge.

`skills/orchestrator-pattern/SKILL.md` is the operating manual: how to cut the work, how to isolate
each workstream in its own worktree, how to brief a subagent, what stays with the orchestrator, how
it merges, and how to close.

## How work flows

1. **A workstream is cut and isolated.** The orchestrator reads the board, opens or moves the issue,
   then creates a git worktree per workstream (`opencode worktree_create <name>`), branch
   `work/<name>`. The brief names the path and the branch; no subagent does its workstream in the
   main checkout.
2. **A subagent delivers a pushed branch and a pull request.** Closed commits on its branch, the
   branch pushed with `git push -u origin work/<name>`, an open PR to `main` naming every issue it
   serves — and a summary (what changed, what was measured, what it did not do, the shas) with the
   Forgejo issues it touched, by number, with their `status/*` label. A delivery never merges and
   never pushes `main` — the library's single exception is `merge-conflict-fixer`'s stated outage,
   named in its row — and never closes an issue that was not its deliverable. A branch nobody
   pushed and a PR nobody opened have delivered nothing.
3. **The verifier gates the merge, the orchestrator decides when, and `merger` merges.** The
   verifier reads the CI checks that belong to the head sha — including the finding that none
   ran — trial-merges the branch onto the base sha it measured, runs the whole suite on the merged
   result, and answers `APPROVED` or `REQUEST_CHANGES` as a review body carrying the base sha, the
   trial-merge sha and the CI result. `merger` then performs `merge_pull_request` on an approval
   that still describes `main`, proves the result with the platform, and syncs the operator's
   checkout onto the delivered sha with `git pull --rebase` under an autostash: `HEAD` equals
   `merge_commit_sha`, the sync writes no commit of its own, and nothing local is left for a later
   branch to carry. A pull that conflicts is a stop and a report — `git rebase --abort`, the
   operator's work restored, the merge still standing. Nobody pushes `main` in this flow: the
   delivery lands through the platform. The one exception is
   `merge-conflict-fixer`'s stated outage, named in its row below. A branch that does not build or
   whose tests fail is refused, and a test is never fixed to pass.
4. **`reviewer` audits what already landed** — the merged tree, not the branch — and answers `PASS`
   or `BLOCK` with the evidence: a hunk dropped in a conflict, a test weakened to pass, a generated
   file not regenerated, a contract changed on one side only.
5. **A regression is reverted, not fixed forward.** The revert and the reason go in the issue, and
   the branch goes back to its author in `status/todo`.
6. **A delivery is a trigger, not a resting point.** With the record written, the orchestrator reads
   the open issues again and starts the next workstream the pattern's four compatibility conditions
   allow — or names the blocker it is waiting on. The operator's silence is not a stop condition.

The record — the issue, its `status/*`, the documents, the merge — is the orchestrator's. It is the
only memory a session leaves behind.

## Permissions

All twenty-two roles share **one** permission matrix, written identically in each `agents/*.md`:
seventeen rules, no per-role exception. The floor is
`{action: "*", resource: "*", effect: deny}` — every tool a role does not explicitly allow is a tool
the session does not have — and `sha256` over `permissions:` through the closing `---` is one hash
in all eighteen, `39aaf93d…0fea65056a`. The five local files `manu343726/z80-emulator` puts beside
them hash to the same value, so a project that defines its own roles carries one block, not two
shapes of one. `edit`, `shell`, `opencode_*` and `subagent` are every role's; what a role does with
them is its own contract's to bound, never the block's. `#38` collapsed the last two shapes into
this one: `orchestrator` and `ticket-manager` used to deny `edit` and `shell`, and `orchestrator`
alone carried `opencode_*` and `subagent`.

`execute` grants **every** Code Mode tool, Forgejo included, and the block does not narrow the
resource. `z80-emulator#47` measured why, and it is closed history a reader should not reopen by
"fixing" the scope: the rule was committed as *"scoped to Forgejo"* and it is not — the nested tool
answers to `<server>_<tool>`, but every MCP call passes through the outer `execute` action first, so
one allow covers the `list_issues` a board read is and Proxmox's `execute_vm_command` and
Playwright's `run_code_unsafe` with it. #47 proposed the narrow form
`{action: execute, resource: forgejo_*}` and left it **unverified**: nobody measured whether the
harness matches `execute`'s `resource` against the nested tool name, so a scoped rule is an untested
rule, and if the match does not happen every board read prompts again. The issue closed on the
operator's decision once the project floor stopped granting `execute` at all; the wide rule survives
in the roles, and this paragraph is the correction that commit owed.

One rule in a resolved block belongs to no file: `opencode debug agents` appends
`browser: * → deny` after every role's block, so it is the last rule of **every** agent the harness
resolves — a library role, a project file and a built-in alike — and it is declared in neither this
repository nor the project's `opencode.jsonc`. That is why no file here names `browser`: the matrix
is complete without it, the deny is the harness's, and a reader comparing a block against that list
must not take the extra line for a rule the matrix lost. The number of agents is a property of the
checkout's configuration at the moment it is read, not of the matrix, and three things move it: the
roles this library ships, the reading project's `agents` array, and the agents the checkout inherits
from above it — `$HOME/.opencode/agents/` here, which a working directory outside `$HOME` never
reaches. Measured on 2026-10-25 with `opencode debug agents` v2.1.4: 27 in a `z80-emulator` worktree
at `f5d1e0b` read from under `$HOME`, 26 from a worktree of that same commit under `/tmp`, and 28 at
that repository's `main` (`7198d2e`), whose array names `docs-auditor` where `f5d1e0b`'s does not.
So run the command where you read this page, and never quote a number from another tree — a count
taken in one checkout is a count of that checkout. A change that wants the browser reachable has
to add the rule to the block and show it in the resolved list; it will not arrive by leaving the
block alone.

Network access is the pair of actions the V2 permission layer names — `webfetch` for a URL and
`websearch` for a query — granted to every role on `resource: "*"` with no per-role host list,
because an agent that documents has to read the documentation it cites: a role that cannot open a
URL or run a search writes its citations from memory, and memory is exactly where the sentence that
sounds true and is not comes from. In `orchestrator` the contract still forbids using it — it
delegates the fetching as it delegates everything else — and a search provider has to be
configured for the session (`websearch.provider` in `opencode.jsonc`, or a provider's API key in
the environment) before a search has anything to call.

| Role | edit | shell | execute | forgejo_* | skill | webfetch | websearch | subagent |
|---|---|---|---|---|---|---|---|---|
| `orchestrator` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `verifier` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `merger` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `cpp-engineer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `go-engineer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `web-engineer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `sre` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `platform-admin` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `observability-engineer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `network-engineer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `test-engineer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `conan-dependencies` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `merge-conflict-fixer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `reviewer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `security-reviewer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `docs-writer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `docs-auditor` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `ticket-manager` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `backlog-triager` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `release-manager` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `agent-author` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `generalist` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Every cell is ✓ because every role carries the whole block and nothing narrower: the table is the
matrix, and a role's own file is where its *use* of a grant is bounded.

## Contents

### Agents

| Agent | Mode | Owns |
|---|---|---|
| `orchestrator` | primary | The thread. Delegates everything to worktrees, verifies, decides when a verified PR merges, holds the board and the record. Its permission block is every role's; its contract is what keeps it delegating. |
| `verifier` | subagent | Measures: builds, tests, endpoints, logs. Reports evidence, never edits; posts the verdict the merge is gated on. |
| `merger` | subagent | Performs the merge the orchestrator decided on: `merge_pull_request`, the proof, the head branch, and the operator's checkout synced onto the delivered sha with `git pull --rebase` under an autostash — `HEAD` equals `merge_commit_sha`, no commit of the sync's own, never pushed. |
| `cpp-engineer` | subagent | C++ sources, their build description and their unit tests, in whatever layout the project uses. |
| `go-engineer` | subagent | Go packages, their tests, the module files and the build the project uses. |
| `web-engineer` | subagent | The browser frontend: components, state, the data layer and its tests, in whatever framework the project uses. |
| `sre` | subagent | A live fault: the evidence captured before any state changes, the least invasive action that restores service, the measurement that proves it from the side that reported it, and the timeline in the issue. One attempt per action, then a report. |
| `platform-admin` | subagent | The instances the estate runs — accounts, tokens, collaborator grants and the admin CLI or API — as idempotent provisioning that can be re-run, each credential created with its revocation route, and never the decision about who is entitled to what. |
| `observability-engineer` | subagent | What the estate measures and what it tells a person: scrape and log pipelines, alert rules, dashboards, objectives and notification routing, as provisioned files; a rule is not done until it has been seen firing and resolving. |
| `network-engineer` | subagent | The path from a name to a process: zones and resolvers, ingress routes, TLS issuance and trust, port forwards and firewalls — measured from the vantage point that reported the fault, and never verified by disabling the check that failed. |
| `test-engineer` | subagent | Test suites only, and the coverage and fuzzing the project's gates ask for. |
| `conan-dependencies` | subagent | Owns a Conan 2 dependency graph — conanfile, profiles, lockfiles, presets integration and the licence audit. |
| `merge-conflict-fixer` | subagent | The exception path: a merge Forgejo's `merge_pull_request` cannot perform — it merges `main` into `dev/<id>`, resolves the conflicts there, runs the suite on the result and pushes the branch, and the platform lands the merge commit. It pushes `main` only in a stated Forgejo outage, and says why. |
| `reviewer` | subagent | Final pass over the merged tree: runs the suite, hunts what integration hid, answers `PASS` or `BLOCK`. |
| `security-reviewer` | subagent | Read-only threat review: inputs, secrets, process boundaries, supply chain. |
| `docs-writer` | subagent | The project's documentation, wherever it declares it lives — `docs/` by default, or the external system its `AGENTS.md` names — and it coordinates with `ticket-manager`, because a ticket is documentation too. |
| `docs-auditor` | subagent | Sweeps the documentation against the code, page by page — current, stale, contradicts, missing — and fixes the pages it can. Invoked as a sweep, not per change. |
| `ticket-manager` | subagent | The board of the repository named in the brief: issues, labels, status transitions, the kanban, and the comments that carry a finding. |
| `backlog-triager` | subagent | The readiness of the board — for every open issue, whether a decision exists, and for every proposal the decision that is missing. Classifies with evidence; decides nothing, labels nothing, cuts nothing. |
| `release-manager` | subagent | The readiness of a trunk for a version, and the version's level — whether `main` should be released, which level the commits justify, and the execution of the project's own documented procedure. Never invents a version, never tags an artefact that was not built and uploaded, never assumes another project's procedure. |
| `agent-author` | subagent | This library: agents, skills, the index, `AGENTS.md` and the project's `opencode.jsonc` — descriptions true to their bodies, permissions exactly as documented. |
| `generalist` | subagent | The task no other row owns: briefed only with the roles considered and rejected, delivered to the same standard as any role, and reported back when a shape arrives twice so the missing role gets written. |

**A role here is generic: it may name a tool and a convention, never a directory that belongs to one
repository.** What is particular to a project — its layout, its exact build and test commands, its
domain — belongs in that project's own skills, and a role that needs it reads them. A role that only
makes sense for one repository (this library's first `toolchain-engineer` was one: assembler,
disassembler and ROM container for a single emulator) is a local agent in that project, not an entry
here.

**`generalist` is the row that exists so no task is homeless, and it is meant to keep losing work.**
It is briefed only when no other row's `Owns` clause covers the task, and its brief names the roles
the orchestrator considered and why each was rejected — without that list the role refuses the task
and reports the gap, and that refusal is what keeps `general` (the harness's own agent, with no
contract behind it) from ever being the answer. It is measured in briefs, not in roles: the first
time a shape arrives it delivers and names the role that should have owned it; the second time the
report says the library is missing a role, and the role gets written. A `generalist` that keeps
taking one kind of task is not being useful — it is the library failing quietly, which is why its
report carries a section for exactly that.

### Skills

| Skill | For |
|---|---|
| `orchestrator-pattern` | Decomposing work, isolating workstreams in worktrees, briefing background subagents, verifying, merging, closing, and sweeping the board for the next compatible workstream when one lands. |
| `cpp-quality` | C++20 conventions, ownership, error handling, sanitizers, CMake. |
| `go-quality` | Go conventions, context, errors, concurrency, package layout. |
| `web-quality` | React 19 + TypeScript conventions, state, accessibility, testing. |
| `incident-response` | Working a live fault: read first, capture the evidence before changing state, name the blast radius, one least-invasive action verified from the reporting side, then the timeline — and the findings a real incident leaves. |
| `observability` | Reading metrics, logs and traces; the four alert shapes that cannot fire or fire twice; windows sized against the signal's own cadence; provisioned dashboards and cardinality. |
| `networking` | The vantage point as part of the measurement; one resolver and why a second is a wrong answer; split-horizon; TLS expiry versus chain versus clock; ingress, forwards and leases; the lookup-in-a-loop trap. |
| `backup-and-restore` | State versus configuration, the inventory that drifts away from reality, retention as a decision with a number, snapshots against backups, and how a restore is proven by using it. |
| `documentation-standards` | Where a project's documentation lives (declared by the project; `docs/` Markdown when nothing is said), the layout, the ADR format, links, evidence beside claims, and the document-versus-ticket split. |
| `forgejo-ticketing` | Label taxonomy, issue template, board flow, PR flow. |
| `release-policy` | Readiness, the level question against the project's own criterion, the artefact-before-tag rule, and the finding when a project documents no procedure. |
| `openapi-contract` | OpenAPI-first REST, generated handlers, validation, versioning. |
| `git-workflow` | Branches, worktrees, conventional commits, PR size, review, merge. |

## Layout

```
agents/<id>.md                 the agent, discovered by the plugin from agents/
skills/<id>/SKILL.md           the skill, discovered by the plugin
skills/<id>/references/*.md    long material a skill loads on demand
scripts/check-agent-frontmatter.py   parses every agents/*.md frontmatter as YAML
```

The plugin reads `agents/` before any other root, so a repository that follows this layout needs
no manifest. Adding an entry is adding a directory or a file; the tables under *Contents* are the
index and are kept in the same change.

**Every frontmatter is machine-checked before it is believed.** `#44` is the reason: `#43` rewrote
`merger`'s `description` with an unquoted `: ` in it — the colon after *an autostash* — which YAML
reads as a nested mapping inside a plain scalar. The block stopped parsing, OpenCode fell
back to treating the role as `primary`, and `mode: subagent` three lines below never counted — so
every session that tried to launch it was answered `Agent merger cannot run as a subagent`, and the
role was dead for every project loading this library. Two verifications read the sentence and none
parsed it. The check is therefore a program, and it prints each role beside the mode it resolves to:

```sh
python3 -m venv /tmp/opencode/venv-frontmatter          # once — the system python3 has no PyYAML
/tmp/opencode/venv-frontmatter/bin/pip install pyyaml
/tmp/opencode/venv-frontmatter/bin/python scripts/check-agent-frontmatter.py
```

It exits non-zero when a frontmatter does not parse, when it parses to something that is not a
mapping, when `mode` is missing or is not one of `primary`/`subagent`/`all`, or when `description`
is missing or did not come out a string. It exits `2` and says how to fix it when PyYAML is absent,
because a weaker hand-rolled parser would miss exactly the defect it exists to catch. A description
whose YAML spelling changes is not a description whose text changes: quoting it is the fix, and the
value must stay word for word what it was.

## Licence

MIT.
