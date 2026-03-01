# HEURISTIC: Agent Never Says No

**DOMAIN:** ai-workflow
**RULE:** AI coding agents implement anything you ask with equal enthusiasm — including over-engineered solutions, insecure implementations, and unnecessary features. The agent never pushes back. You must be your own brake, code reviewer, and quality gate.
**APPLIES WHEN:** Every interaction with an AI coding agent. This is a permanent characteristic of current LLM-based agents, not a temporary limitation.
**RATIONALE:** Unlike a human pair programming partner who might say "this is over-engineered" or "we should do X first" or "this is insecure", the AI agent has no opinion hierarchy. It treats a request for a dead letter queue with the same priority as a request for input validation. It implements `skip_forgery_protection` without questioning whether it's appropriate. It builds a 8-state state machine when 4 states would suffice. The developer must actively resist the agent's willingness to do everything by constantly asking: "Is this necessary? Is there a simpler way? What could go wrong? What am I not thinking about?" Without this self-discipline, the codebase accumulates unnecessary complexity at the speed the agent can type.
**COUNTER-INDICATION:** Some AI agents are being trained with guardrails for security-critical operations (e.g., refusing to disable authentication). But for architectural and design decisions, the agent remains universally compliant. Do not rely on the agent to say "no" for you.

## SOURCE
https://akitaonrails.com/2026/02/20/do-zero-a-pos-producao-em-1-semana-como-usar-ia-em-projetos-de-verdade-bastidores-do-the-m-akita-chronicles/
