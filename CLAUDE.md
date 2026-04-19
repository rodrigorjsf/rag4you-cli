# rag4you-cli — Python CLI tool for RAG-based document querying

## Tooling

- Package manager: `uv` (use `uv add`, `uv run`; never bare `pip install`)
- Test: `uv run pytest`
- Lint/format: `uv run ruff check . && uv run ruff format .`

## Behaviour

- On loading or using any atifact (rules, skills, agents), always announce at start: "I'm using/loading the <artifact_name> <artifact_type> to <action>."
- Make sure to evaluate the creation of artefacts for this projects in order to garantee that it will self construct a solid harness to deliver and evolve project properlly. They must always be reviewed to avoid obsolete definitions and be always in sync with the actual state and expected `ROADMAP`.
- If creating any skill for this project, alway use the skill `/superpowers:writing-skills` to create it.
  - Other artifacs (as rules, subagents, hooks, etc) must use `agent-customizer` plugin skills.
- Keep the Claude Code instruction surface (`CLAUDE.md`, `.claude/rules/`) mirrored with the GitHub Copilot instruction surface (`.github/copilot-instructions.md`, `.github/instructions/`). When one side changes, update the equivalent files on the other side in the same task.
- Use the `wiki` to guide you throught documentations and project specifications.
- Before implementing a feature, consult `wiki/knowledge/index.md` for relevant research pages. When implementation changes invalidate wiki content, update the affected knowledge pages in the same task.
- YOU MUST update the `README.md` file whenever you add, remove, or significantly change project functionality, file structures, or environment variables following the `docs/templates/readme-template.md`.
- After completing any major task or PR, review README.md to ensure it reflects current project state. Reflect on "What did I learn from this task that could be relevant and helpful in future tasks?", and update the `wiki` in a "Learnings" section with the consolidated learnings and also the summary in `Applied Learning`.

## Advisor

- Double-check this with the advisor before committing.
- If you get stuck, consult the advisor.
- Before you write the code, get an advisor review.

## Memory

Always use the plugin's `claude-mem` tools (artifacts and MCP) to manage your memories.

## Conventions

Follow python-development plugin skills for all Python patterns, testing strategies, and code style.

## Applied Learning

- Agents fail silently on wrong paths. Always verify hardcoded paths.
- Before creating a new project artifact, check if an existing one can be extended or merged.
- Plans file must alway be saved in the project scope.
