# HEURISTIC: Documentation ROI with AI

**DOMAIN:** ai-workflow
**RULE:** Every hour spent documenting in CLAUDE.MD saves multiple hours of re-discovery in future AI coding sessions. With AI agents, documentation investment returns exponentially because agents actually read the entire document before every interaction.
**APPLIES WHEN:** Any AI-assisted project spanning more than one coding session. The ROI increases with project duration and complexity.
**RATIONALE:** Human developers skim documentation and rely on tribal knowledge. AI agents read the entire CLAUDE.MD in ~2 seconds before each interaction. Every hurdle documented once ("Yahoo Finance does TLS fingerprinting", "HN RSS changes format", "LLM softens opinions unless explicit") is never re-discovered. Without documentation, the agent starts from zero context each session, re-encountering the same problems. Akita's CLAUDE.MD grew to 702 lines documenting 12 common hurdles and 14 design patterns over 8 days. The equivalent of institutional knowledge that would take a human team member weeks to absorb was available to the agent instantly in every session.
**COUNTER-INDICATION:** Single-session throwaway projects don't benefit from documentation since there's no future session to leverage it. Also, documenting implementation details that change frequently (specific API responses, exact config values) creates maintenance burden without proportional benefit.

## SOURCE
https://akitaonrails.com/2026/02/20/do-zero-a-pos-producao-em-1-semana-como-usar-ia-em-projetos-de-verdade-bastidores-do-the-m-akita-chronicles/
