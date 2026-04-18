## Summary

<!-- Describe what this PR does and why. Reference the PRD or design document when applicable. -->

<!--
BEFORE SUBMITTING: Read every word of this template. PRs that leave
sections blank, contain multiple unrelated changes, or show no evidence
of human involvement will be closed without review.
-->

## What problem are you trying to solve?
<!-- Describe the specific problem you encountered. If this was a session
     issue, include: what you were doing, what went wrong, the model's
     exact failure mode, and ideally a transcript or session log.

     "Improving" something is not a problem statement. What broke? What
     failed? What was the user experience that motivated this? -->

## What does this PR change?
<!-- 1-3 sentences. What, not why — the "why" belongs above. -->

## Is this change appropriate for the core library?
<!-- agent-engineering-toolkit contains general-purpose plugins and infrastructure
     that benefit all users. Ask yourself:

     - Would this be useful to someone working on a completely different
       kind of project than yours?
     - Is this project-specific, team-specific, or tool-specific?
     - Does this integrate or promote a third-party service?

     If your change is a new skill for a specific domain, workflow tool,
     or third-party integration, it belongs in its own plugin — not here.
     See the plugin development docs for how to publish it separately. -->

## What alternatives did you consider?
<!-- What other approaches did you try or evaluate before landing on this
     one? Why were they worse? If you didn't consider alternatives, say so
     — but know that's a red flag. -->

## Does this PR contain multiple unrelated changes?
<!-- If yes: stop. Split it into separate PRs. Bundled PRs will be closed.
     If you believe the changes are related, explain the dependency. -->

## Existing PRs
- [ ] I have reviewed all open AND closed PRs for duplicates or prior art
- Related PRs: <!-- #number, #number, or "none found" -->

<!-- If a related closed PR exists, explain what's different about your
     approach and why it should succeed where the other didn't. -->

## Environment tested

| Harness (e.g. Claude Code, Cursor) | Harness version | Model | Model version/ID |
|-------------------------------------|-----------------|-------|------------------|
|                                     |                 |       |                  |

## Evaluation
- What was the initial prompt you (or your human partner) used to start
  the session that led to this change?
- How many eval sessions did you run AFTER making the change?
- How did outcomes change compared to before the change?

<!-- "It works" is not evaluation. Describe the before/after difference
     you observed across multiple sessions. -->

## Rigor

- [ ] If this is a skills change: I verified skill behavior with adversarial
      pressure testing and completed at least 3 eval sessions (paste results below)
- [ ] This change was tested adversarially, not just on the happy path
- [ ] I did not modify carefully-tuned content (Red Flags table,
      rationalizations, "human partner" language) without extensive evals
      showing the change is an improvement

<!-- If you changed wording in skills that shape agent behavior, show your
     eval methodology and results. These are not prose — they are code. -->

## Human review
- [ ] A human has reviewed the COMPLETE proposed diff before submission

<!--
STOP. If the checkbox above is not checked, do not submit this PR.

PRs will be closed without review if they:
- Show no evidence of human involvement
- Contain multiple unrelated changes
- Promote or integrate third-party services or tools
- Submit project-specific or personal configuration as core changes
- Leave required sections blank or use placeholder text
- Modify behavior-shaping content without eval evidence
-->

## Changes

<!-- List changes by area. Remove sections that don't apply. -->

**Plugin Skills** (`plugins/agents-initializer/skills/`)
-

**Standalone Skills** (`skills/`)
-

**Agent Definitions** (`plugins/agents-initializer/agents/`)
-

**Rules** (`.claude/rules/`)
-

**Documentation** (`docs/`)
-

**Configuration** (`CLAUDE.md`, `.claude-plugin`, `DESIGN-GUIDELINES.md`)
-

**Meta-Skills / Dev Tooling** (`.claude/skills/`)
-

## Convention Compliance

- [ ] No file exceeds 200 lines (references, rules, templates, CLAUDE.md)
- [ ] SKILL.md files: name ≤64 chars, description ≤1024 chars, body <500 lines
- [ ] Shared references updated in ALL copies across both distributions
- [ ] Plugin skills delegate to agents; standalone skills use inline analysis — patterns not mixed
- [ ] Agent definitions use model: sonnet (except for `pr-comment-resolver` agent), read-only tools, maxTurns 15-20
- [ ] New guidelines in DESIGN-GUIDELINES.md have source citation and "Implemented in" traceability
- [ ] Root CLAUDE.md stays within 15-40 line target
- [ ] Commits are atomic — one logical change per commit

## Evidence & Quality

- [ ] New instructions pass the test: "Would removing this cause the agent to make mistakes?"
- [ ] Reference files have source attribution
- [ ] No stale file paths or commands introduced
- [ ] No content agents can infer from the codebase (standard conventions, directory listings)

## Related Issues / PRD

<!-- Link related issues or PRD documents -->
<!-- Ex: Implements Phase 3 from PRD docs/plans/2026-03-22-agents-initializer-plugin-design.md -->
<!-- Ex: Closes #42 -->