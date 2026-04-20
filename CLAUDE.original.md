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

You have access to an `advisor` tool backed by a stronger reviewer model. It takes NO parameters — when you call advisor(), your entire conversation history is automatically forwarded. They see the task, every tool call you've made, every result you've seen.

Call advisor BEFORE substantive work — before writing, before committing to an interpretation, before building on an assumption. If the task requires orientation first (finding files, fetching a source, seeing what's there), do that, then call advisor. Orientation is not substantive work. Writing, editing, and declaring an answer are.

Also call advisor:
- When you believe the task is complete. BEFORE this call, make your deliverable durable: write the file, save the result, commit the change. The advisor call takes time; if the session ends during it, a durable result persists and an unwritten one doesn't.
- When stuck — errors recurring, approach not converging, results that don't fit.
- When considering a change of approach.

On tasks longer than a few steps, call advisor at least once before committing to an approach and once before declaring done. On short reactive tasks where the next action is dictated by tool output you just read, you don't need to keep calling — the advisor adds most of its value on the first call, before the approach crystallizes.

Give the advice serious weight. If you follow a step and it fails empirically, or you have primary-source evidence that contradicts a specific claim (the file says X, the paper states Y), adapt. A passing self-test is not evidence the advice is wrong — it's evidence your test doesn't check what the advice is checking.

If you've already retrieved data pointing one way and the advisor points another: don't silently switch. Surface the conflict in one more advisor call — "I found X, you suggest Y, which constraint breaks the tie?" The advisor saw your evidence but may have underweighted it; a reconcile call is cheaper than committing to the wrong branch.

The advisor should respond in under 100 words and use enumerated steps, not explanations.

## Memory

Always use the plugin's `claude-mem` tools (artifacts and MCP) to manage your memories.

## Conventions

Follow python-development plugin skills for all Python patterns, testing strategies, and code style.

## Applied Learning

- Agents fail silently on wrong paths. Always verify hardcoded paths.
- Before creating a new project artifact, check if an existing one can be extended or merged.
- Plans file must alway be saved in the project scope.
