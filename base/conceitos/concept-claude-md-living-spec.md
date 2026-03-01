# CONCEPT: CLAUDE.MD Living Spec

**DOMAIN:** ai-workflow
**DEFINITION:** A project-level document (CLAUDE.MD, CONTRIBUTING.MD, or equivalent) that serves as the persistent memory and onboarding guide for AI agents across coding sessions. It is NOT written once at project start — it evolves with the project. Every discovered hurdle, pattern, domain-specific knowledge, and architectural decision is documented in this file as it emerges. The agent reads the entire document before each interaction (in ~2 seconds), giving it the equivalent of institutional knowledge that a human team member would accumulate over weeks. Contains: architecture overview, tech stack, environment variables, directory structure, known hurdles with solutions, design patterns, pipeline descriptions, and post-implementation checklists.
**NOT:** Not a static configuration file (like .editorconfig). Not a one-time setup document written before coding starts (that's necessary but insufficient). Not a README for humans (though it can serve double duty). The key distinction is that CLAUDE.MD is a LIVING document that grows with every discovery, making the agent smarter with each session. Also not a replacement for in-code documentation — CLAUDE.MD captures project-level knowledge, not function-level documentation.
**RATIONALE:** Without a living spec, every new AI coding session starts from zero context. The agent doesn't remember that "Yahoo Finance does TLS fingerprinting" or that "HN RSS changes format periodically" or that "the LLM softens opinions unless explicitly instructed otherwise." Each rediscovery costs time. With a living CLAUDE.MD, these discoveries are recorded once and applied forever. Akita's CLAUDE.MD grew to 702 lines over 8 days and 274 commits, documenting 12 "common hurdles" and 14 design patterns. The investment in documentation returns exponentially with AI agents because they actually read the entire document before every interaction.

---

## REFERENCED BY

- base/anti-patterns/antipattern-no-architecture-rules-upfront.md
- base/protocolos/protocol-ai-pair-programming.md
- base/procedimentos/procedure-vibe-coding-project-lifecycle.md

## SOURCE
https://akitaonrails.com/2026/02/20/do-zero-a-pos-producao-em-1-semana-como-usar-ia-em-projetos-de-verdade-bastidores-do-the-m-akita-chronicles/
