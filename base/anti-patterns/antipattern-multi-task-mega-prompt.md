# ANTI-PATTERN: Multi-Task Mega Prompt

**DOMAIN:** ai-workflow
**APPEARS AS:** Giving the AI agent a single prompt that combines multiple different types of tasks: "update dependencies AND fix compatibility bugs AND refactor into smaller files AND make sure it still runs." Seems efficient because you describe everything at once and let the agent figure it out.
**ROOT CAUSE:** The LLM treats all tasks with equal priority and attempts to interleave them, often refactoring before fixing bugs (breaking more things), or claiming completion on partially finished work. Each task type requires different reasoning: dependency updates need documentation lookup, bug fixes need iterative test-and-fix cycles, refactoring needs structural understanding. Mixing them in one prompt overwhelms the context and produces worse results than sequential isolated prompts.
**RATIONALE:** Akita explicitly demonstrated this with his "worst prompt possible" for the Zig challenge — combining Zig 0.15 migration, llama.cpp compatibility, runtime bug fixes, and code refactoring in one prompt. Even Claude Opus, the best performer, required 2 rounds. Gemini "gave up" mid-process, falsely claiming success. The key insight: each prompt should be one type of task (fix ONE bug, refactor ONE file, update ONE dependency). The agent's enthusiasm to work on everything at once is not efficiency — it's chaos.

---

## SYMPTOMS

- Agent starts refactoring code before ensuring existing functionality compiles
- Agent claims "I fixed everything" but build still has errors
- Agent enters agentic loop: recognizes problems, generates plans, but doesn't actually execute fixes (especially in open-source models)
- Agent modifies files unrelated to the current issue, creating new bugs while fixing old ones
- Context window fills with reasoning about multiple interleaved problems, degrading quality on all of them

## CORRECTION

Use sequential, isolated prompts — one task type per prompt: (1) "Update Zig API calls for 0.15 compatibility. Run `zig build` after each change." (2) Once compiling: "Fix runtime crashes when loading the model." (3) Once running: "Refactor qwen_cli.zig into smaller files without changing behavior." Each prompt has a clear, verifiable completion criterion.

**NOT TO CONFUSE WITH:** Providing context about the overall goal while asking for a specific task. It's fine to say "I'm migrating to Zig 0.15 — start by fixing the ArrayList API changes." The anti-pattern is asking for ALL tasks to be done simultaneously.

## OPERATIONAL CONSTRAINTS
**FOR reliable AI agent task execution TO SUCCEED:**

NEVER:
- Combine multiple task types (fix + refactor + update) in a single prompt [explicit — ROOT CAUSE, RATIONALE]
- Let the agent start refactoring before ensuring existing code compiles [explicit — SYMPTOMS]
- Trust agent claims of "I fixed everything" without verifying each task independently [explicit — SYMPTOMS]

ALWAYS:
- Use sequential, isolated prompts — one task type per prompt [explicit — CORRECTION]
- Define a clear, verifiable completion criterion for each prompt [explicit — CORRECTION]
- Verify completion of current task before issuing the next [implied — CORRECTION: sequential]

GATE: Current prompt contains exactly one task type. If false, split into sequential prompts.

## SOURCE
https://akitaonrails.com/2026/01/11/ai-agents-comparando-as-principais-llm-no-desafio-de-zig/
