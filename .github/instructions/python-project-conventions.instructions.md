---
applyTo: "bench/**/*.py,rag4you/**/*.py"
---

# Python Project Conventions

- Follow the `python-development` plugin skills for Python implementation and testing; this instruction file adds only repo-specific constraints.
- Keep code, comments, docstrings, identifiers, schemas, and config keys in English.
- Route CLI user-facing text through locale files instead of hard-coding translated prose in Python modules.
- New or changed Python modules must land with tests that keep the edited Python area at or above 90% line coverage.
- Keep model names, chunk sizes, thresholds, and similar runtime knobs configurable instead of hard-coding them in Python.
- For resume, checkpoint, and persistence flows, use atomic writes or append-only updates and surface failures explicitly.
