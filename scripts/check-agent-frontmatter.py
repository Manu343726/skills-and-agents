#!/usr/bin/env python3
"""Check that every agent's YAML frontmatter parses, and that it declares a usable `mode`.

Why this exists
---------------
An agent's frontmatter is an executable contract, not documentation. One unquoted `: ` inside
`description` splits the scalar into a nested mapping, the whole block stops parsing, and OpenCode
treats the role as `primary` — the `mode: subagent` three lines below never counts, because the
parser never reaches it. The session then answers, at launch:

    Agent <id> cannot run as a subagent

Measured in manu343726/agent-skills-library#44, after #43 rewrote `merger`'s description: `merger`
was dead for every project that loads this library, and two reviews had read the sentence and
compared its *meaning* to the new rule without ever parsing it as YAML. A grep cannot catch this
class of defect and a reader keeps missing it, so the parse is a program.

Requires PyYAML (`import yaml`), which this machine's system `python3` does not ship:

    python3 -m venv /tmp/opencode/venv-frontmatter
    /tmp/opencode/venv-frontmatter/bin/pip install pyyaml
    /tmp/opencode/venv-frontmatter/bin/python scripts/check-agent-frontmatter.py

Usage
-----
    python3 scripts/check-agent-frontmatter.py            # every agents/*.md in this repository
    python3 scripts/check-agent-frontmatter.py FILE ...   # only the files named

Exit status: 0 every file parsed and declared a valid `mode`; 1 at least one file failed;
2 nothing was checked, or PyYAML is missing.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # the dependency is the point, not an afterthought
    sys.stderr.write(
        "check-agent-frontmatter: PyYAML is not importable by this interpreter.\n"
        "The check needs a real YAML parser — a hand-rolled one would miss exactly the\n"
        "unquoted-colon defect it exists to catch. Install it and run it with that python:\n"
        "\n"
        "    python3 -m venv /tmp/opencode/venv-frontmatter\n"
        "    /tmp/opencode/venv-frontmatter/bin/pip install pyyaml\n"
        "    /tmp/opencode/venv-frontmatter/bin/python scripts/check-agent-frontmatter.py\n"
        "\n"
        "See manu343726/agent-skills-library#44 for why this is a program and not a paragraph.\n"
    )
    raise SystemExit(2)

# The modes OpenCode resolves. `all` is a role reachable both as a primary and as a subagent.
VALID_MODES = {"primary", "subagent", "all"}

REPO_ROOT = Path(__file__).resolve().parent.parent


def split_frontmatter(text: str) -> str | None:
    """Return the text between the opening `---` line and the next one, or None."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:index]) + "\n"
    return None


def check(path: Path) -> list[str]:
    """Check one file. Returns a list of problems; empty means it passed."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        return [f"cannot be read: {error}"]

    block = split_frontmatter(text)
    if block is None:
        return ["has no frontmatter block (expected `---` on the first line and a closing `---`)"]

    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as error:
        # MarkedYAMLError carries the line and column of the offending scalar, and quoting it is
        # what turns "does not parse" into "quote line 2".
        mark = getattr(error, "problem_mark", None)
        where = f" at frontmatter line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        problem = getattr(error, "problem", None) or str(error).splitlines()[0]
        return [f"frontmatter is not valid YAML{where}: {problem}"]

    if not isinstance(data, dict):
        return [f"frontmatter parsed as {type(data).__name__}, not a mapping of keys"]

    problems: list[str] = []

    if "mode" not in data:
        problems.append("declares no `mode` (a role without one is treated as `primary`)")
    elif data["mode"] not in VALID_MODES:
        problems.append(
            f"declares mode {data['mode']!r}, which is not one of {sorted(VALID_MODES)}"
        )

    description = data.get("description")
    if description is None:
        problems.append("declares no `description`")
    elif not isinstance(description, str):
        problems.append(
            f"`description` parsed as {type(description).__name__}, not a string — most often an "
            "unquoted `: ` inside the text"
        )
    elif not description.strip():
        problems.append("`description` is empty")

    return problems


def main(argv: list[str]) -> int:
    only = [Path(name) for name in argv[1:]]
    if only:
        paths = only
    else:
        agents_dir = REPO_ROOT / "agents"
        if not agents_dir.is_dir():
            sys.stderr.write(f"check-agent-frontmatter: no agents directory at {agents_dir}\n")
            return 2
        paths = sorted(agents_dir.glob("*.md"))

    if not paths:
        sys.stderr.write("check-agent-frontmatter: no agent files to check\n")
        return 2

    failed = 0
    for path in paths:
        problems = check(path)
        if problems:
            failed += 1
            print(f"FAIL {path.stem}")
            for problem in problems:
                print(f"     {problem}")
            continue
        mode = yaml.safe_load(split_frontmatter(path.read_text(encoding="utf-8")))["mode"]
        print(f"ok   {path.stem:<22} mode={mode}")

    print(f"\n{len(paths)} file(s): {len(paths) - failed} ok, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
