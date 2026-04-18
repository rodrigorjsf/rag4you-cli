---
applyTo: "wiki/**/*.md"
---

# Wiki Knowledge Pages

- Follow `wiki/CLAUDE.md` as the authoritative convention reference for all wiki edits.
- Every knowledge page header: `# Title`, `**Summary**:`, `**Sources**:`, `**Last updated**:`, then `---`.
- Every knowledge page footer: `## Related pages` section with `[[page-name]]` links.
- Use `[[page-name]]` double-bracket links throughout body text when referencing related wiki concepts.
- Cite factual claims with `(source: filename)` after the claim. Note contradictions between sources explicitly.
- After creating or modifying a knowledge page, update `wiki/knowledge/index.md` and append to `wiki/knowledge/log.md`.
- Use lowercase-with-hyphens filenames (e.g., `embedding-models-research.md`).
- Never modify files under `docs/`. Wiki pages summarize doc sources; the originals are immutable.
- Consult `wiki/knowledge/index.md` before creating a page to check if an existing one can be extended.
