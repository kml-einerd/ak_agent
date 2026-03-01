# CONCEPT: Content-First Architecture

**DOMAIN:** architecture
**DEFINITION:** An architectural pattern where content (Markdown + YAML frontmatter) is the single source of truth, and multiple independent renderers consume the same content to produce different outputs (web, email, RSS, podcast feeds). The content format is universal and technology-agnostic. Each renderer (Hugo for web, Rails ERB for email, Hugo RSS templates for feeds) transforms the same content according to its target platform's constraints. No renderer owns the content; they all read from the same source.
**NOT:** Not the same as headless CMS (which still implies a single rendering pipeline consuming an API). Content-First Architecture has no API — renderers read files directly. Also not the same as "static site generator" — the architecture includes dynamic renderers (email) alongside static ones (blog). The key distinction is that content exists independently of any renderer.
**RATIONALE:** Without this concept, projects couple content to a specific rendering technology. Switching blog engines requires migrating content. Switching email providers requires rewriting templates AND content. With Content-First Architecture, switching any single renderer is a template change — content remains untouched. This is the Unix philosophy applied to content: each tool does one thing well, connected by a universal format (Markdown + YAML).

---

## REFERENCED BY

- base/procedimentos/procedure-dual-content-render-pipeline.md
- base/anti-patterns/antipattern-frontend-equals-framework.md

## SOURCE
https://akitaonrails.com/2026/02/19/frontend-sem-framework-bastidores-do-the-m-akita-chronicles/
