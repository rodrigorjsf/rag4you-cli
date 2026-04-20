# rag4you-cli — Python CLI tool for RAG-based document querying

## Tooling

- Package manager: `uv` (use `uv add`, `uv run`; never bare `pip install`)
- Test: `uv run pytest`
- Lint/format: `uv run ruff check . && uv run ruff format .`

## Behaviour

- Loading/using artifact (rules, skills, agents): announce at start: "I'm using/loading the <artifact_name> <artifact_type> to <action>."
- Evaluate artifact creation for project. Must build solid harness to deliver + evolve. Review always — no obsolete definitions. Stay in sync with `ROADMAP`.
- Creating skill: use `/superpowers:writing-skills`.
  - Other artifacts (rules, subagents, hooks, etc): use `agent-customizer` plugin skills.
- Mirror Claude Code instruction surface (`CLAUDE.md`, `.claude/rules/`) with GitHub Copilot surface (`.github/copilot-instructions.md`, `.github/instructions/`). One side changes → update other side same task.
- Use `wiki` for docs and project specs.
- Before implementing feature: consult `wiki/knowledge/index.md` for research pages. Implementation invalidates wiki content → update affected knowledge pages same task.
- MUST update `README.md` on any add/remove/significant change to functionality, file structures, or env vars. Follow `docs/templates/readme-template.md`.
- After major task or PR: review README.md for current state. Reflect on learnings → update `wiki` "Learnings" section + `Applied Learning` summary.

## Advisor

`advisor` tool backed by stronger reviewer. No params — full conversation history auto-forwarded.

Call advisor BEFORE substantive work — before writing, committing to interpretation, building on assumption. Orientation first (finding files, fetching source) is OK; then call advisor. Writing, editing, declaring answer = substantive.

Also call advisor:
- Task complete. Make deliverable durable first (write file, save result, commit). Advisor call takes time; durable result persists if session ends.
- Stuck — errors recurring, approach not converging, results don't fit.
- Considering approach change.

Longer tasks: call advisor once before committing to approach, once before declaring done. Short reactive tasks: skip — advisor adds most value on first call before approach crystallizes.

Weight advice seriously. Step fails empirically or primary source contradicts claim → adapt. Passing self-test ≠ advice wrong — test doesn't check what advice checks.

Data points one way, advisor points another: don't silently switch. Surface conflict in another advisor call — "I found X, you suggest Y, which breaks the tie?" Reconcile call cheaper than wrong branch.

Advisor: respond under 100 words, enumerated steps, no explanations.

## Memory

Use plugin's `claude-mem` tools (artifacts and MCP) for all memory management.

## Conventions

Follow python-development plugin skills for Python patterns, testing strategies, code style.

## Applied Learning

- Agents fail silently on wrong paths. Always verify hardcoded paths.
- Before new project artifact: check if existing one can be extended or merged.
- Plans file must always save in project scope.