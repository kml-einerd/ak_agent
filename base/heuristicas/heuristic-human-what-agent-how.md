# HEURISTIC: Human What Agent How

**DOMAIN:** ai-workflow
**RULE:** The human decides WHAT to build and WHY. The AI agent decides HOW to implement it. Inverting this division (agent chooses what, human types code) always produces worse results.
**APPLIES WHEN:** Any AI-assisted coding session where the developer is making architectural, design, or prioritization decisions alongside an AI coding agent.
**RATIONALE:** The agent excels at the HOW: writing boilerplate, scaffolding, tests, refactoring, researching APIs. It produces implementations that are frequently better than what the developer would write manually. But the agent has no judgment about WHAT matters: it executes any request with equal enthusiasm, never says "this is a waste of time" or "do X before Y", and doesn't understand business context, user needs, or domain-specific constraints. When the human provides the WHAT (direction, priorities, constraints) and the agent provides the HOW (implementation, patterns, code), the combination is multiplicative. When the human tries to dictate exact code (over-piloting), the agent's strength in finding better implementations is wasted. When the agent chooses what to build (under-navigating), it over-engineers and solves the wrong problems.
**COUNTER-INDICATION:** When the developer has very specific implementation requirements (e.g., "use exactly this algorithm because of this constraint"), dictating the HOW is appropriate. The heuristic applies to the default mode of interaction, not to every individual instruction.

## SOURCE
https://akitaonrails.com/2026/02/20/do-zero-a-pos-producao-em-1-semana-como-usar-ia-em-projetos-de-verdade-bastidores-do-the-m-akita-chronicles/
