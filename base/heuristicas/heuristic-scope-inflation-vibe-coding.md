# HEURISTIC: Scope Inflation in Vibe Coding

**DOMAIN:** ai-workflow
**RULE:** Monitor project scope actively during vibe coding sessions. The ease of adding features via LLM makes scope creep invisible until the project is 3-5x larger than originally planned.
**APPLIES WHEN:** During any AI-assisted project where features are being added incrementally, especially when the developer is in a flow state and the LLM is delivering features quickly.
**RATIONALE:**
1. In traditional coding, scope creep is self-limiting because each new feature costs visible effort and time — in LLM-assisted coding, features arrive so quickly (minutes instead of hours) that the developer doesn't feel the cost of each addition. [explicit]
2. Akita's FrankMD started as a "Notepad Web" for simple notes and ended as a full-featured Markdown editor with S3 integration, i18n, syntax highlighting, Docker deployment, and 33,000 lines of code — the original "1 day" estimate took 3 days of extreme focus. [explicit]
3. Every time estimate in vibe coding is underestimated because scope inflates invisibly — the ease of adding features removes the natural friction that limits scope in traditional development. [derived]
**COUNTER-INDICATION:** Projects with a fixed, well-defined specification (e.g., implementing an existing API spec or replicating a known product). Scope inflation is primarily a risk in exploratory/personal projects where "just one more feature" has no external check.

## OPERATIONAL CONSTRAINTS
**FOR controlled project scope during AI-assisted development TO SUCCEED:**

NEVER:
- Add features without checking against original scope definition [derived — RULE: "Monitor project scope actively"]
- Trust initial time estimates during vibe coding sessions [explicit — RATIONALE: "Every time estimate in vibe coding is underestimated"]

ALWAYS:
- Define a written scope boundary before starting the project [derived — RULE + RATIONALE]
- Review accumulated features against original scope after every 3-5 additions [derived — RULE: "Monitor project scope actively"]
- Explicitly decide (not drift into) each scope expansion [implied — RULE: "makes scope creep invisible"]

GATE: Written scope boundary exists and was reviewed within last 5 features. If false, stop adding features and review scope against original definition.

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-part-1/
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
