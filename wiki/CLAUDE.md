# LLM Wiki

A personal knowledge base maintained by LLM Agents.
Based on Andrej Karpathy's LLM Wiki pattern.

## Purpose

This wiki is a structured, interlinked knowledge base for getting structured and organized code base docs.
Claude maintains the wiki. The human curates sources, asks questions, and guides the analysis.

## Folder structure

```text
docs/                   -- source documents (immutable -- never modify these)
wiki/                   -- root wiki folder
wiki/knowledge          -- markdown pages maintained by Claude
wiki/knowledge/index.md -- table of contents for the entire wiki
wiki/knowledge/log.md   -- append-only record of all operations
```

## Ingest workflow

When the user adds a new source to `docs/` and asks you to ingest it:

1. Read the full source document
2. Discuss key takeaways with the user before writing anything
3. Create a summary page in `wiki/knowledge` named after the source
4. Create or update concept pages for each major idea or entity
5. Add knowledge-links ([[page-name]]) to connect related pages
6. Update `wiki/knowledge/index.md` with new pages and one-line descriptions
7. Append an entry to `wiki/knowledge/log.md` with the date, source name, and what changed

A single source may touch 10-15 wiki pages. That is normal.

## Page format

Every wiki knowledge page should follow this structure:

```markdown
# Page Title

**Summary**: One to two sentences describing this page.
**Sources**: List of raw source files this page draws from.
**Last updated**: Date of most recent update.
---

Main content goes here. Use clear headings and short paragraphs.

Link to related concepts using [[knowledge-links]] throughout the text.

## Related pages

- [[related-concept-1]]
- [[related-concept-2]]
```

## Citation rules

- Every factual claim should reference its source file
- Use the format (source: filename.pdf) after the claim
- If two sources disagree, note the contradiction explicitly
- If a claim has no source, mark it as needing verification

## Question answering

When the user asks a question:

1. Read `wiki/knowledge/index.md` first to find relevant pages
2. Read those pages and synthesize an answer
3. Cite specific wiki knowledge pages in your response
4. If the answer is not in the wiki knowledge, say so clearly
5. If the answer is valuable, offer to save it as a new wiki knowledge page

Good answers should be filed back into the wiki knowledge so they compound over time.

## Lint

When the user asks you to lint or audit the wiki:

- Check for contradictions between pages
- Find orphan pages (no inbound links from other pages)
- Identify concepts mentioned in pages that lack their own page
- Flag claims that may be outdated based on newer sources
- Check that all pages follow the page format above
- Report findings as a numbered list with suggested fixes

## Rules

- Never modify anything in the `docs/` folder
- Always update `wiki/knowledge/index.md` and `wiki/knowledge/log.md` after changes
- Keep page names lowercase with hyphens (e.g. `machine-learning.md`)
- Write in clear, plain language
- When uncertain about how to categorize something, ask the user
