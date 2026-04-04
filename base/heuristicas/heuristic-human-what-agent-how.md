# HEURISTIC: Human What Agent How

**DOMAIN:** ai-workflow
**RULE:** The human decides WHAT to build and WHY. The AI agent decides HOW to implement it. Inverting this division (agent chooses what, human types code) always produces worse results.
**APPLIES WHEN:** Any AI-assisted coding session where the developer is making architectural, design, or prioritization decisions alongside an AI coding agent.
**RATIONALE:**
1. The agent excels at the HOW (writing boilerplate, scaffolding, tests, refactoring, researching APIs) but has no judgment about WHAT matters — it executes any request with equal enthusiasm, never says "this is a waste of time", and doesn't understand business context or domain constraints. [explicit]
2. When the human provides the WHAT (direction, priorities, constraints) and the agent provides the HOW (implementation, patterns, code), the combination is multiplicative — implementations are frequently better than what the developer would write manually. [explicit]
3. Over-piloting (human dictates exact code) wastes the agent's implementation strength; under-navigating (agent chooses what to build) leads to over-engineering and solving the wrong problems. [derived]
**COUNTER-INDICATION:** When the developer has very specific implementation requirements (e.g., "use exactly this algorithm because of this constraint"), dictating the HOW is appropriate. The heuristic applies to the default mode of interaction, not to every individual instruction.

## SOURCE
https://akitaonrails.com/2026/02/20/do-zero-a-pos-producao-em-1-semana-como-usar-ia-em-projetos-de-verdade-bastidores-do-the-m-akita-chronicles/
