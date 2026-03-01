# HEURISTIC: Match Model to Its Harness

**DOMAIN:** ai-workflow
**RULE:** Use each LLM provider's own agent tool for best results — Claude models perform best in Claude Code, GPT models perform best in Codex CLI — because models are fine-tuned for their specific harness (system prompt, patch format, tool definitions, orchestration loop).
**APPLIES WHEN:** Choosing which AI coding agent to use for a project, or when experiencing poor results from an LLM in a third-party tool.
**RATIONALE:** GPT Codex models were fine-tuned specifically for the Codex harness: the `apply_patch` diff format (not standard unified diff), `rg` (not grep), `AGENTS.md` (not CLAUDE.md), and specific tool calling conventions. Using GPT in a tool designed for Claude's conventions produces suboptimal results because the model's fine-tuning doesn't match the tool's expectations. The same applies in reverse: Claude in a GPT-optimized tool won't leverage Claude's strengths. This is analogous to the Browser Wars: each vendor optimizes for their own rendering engine, and cross-browser compatibility is always an approximation. Open-source tools (Crush, OpenCode) can approximate but never perfectly replicate proprietary harnesses.
**COUNTER-INDICATION:** For simple tasks (formatting, basic code generation, Q&A), the harness mismatch is negligible. The effect is most pronounced on complex agentic tasks requiring multi-step tool use, file editing, and iterative debugging. Also, some open-source models (Qwen, DeepSeek) don't have a dedicated harness, so any general tool works equally.

## OPERATIONAL CONSTRAINTS
**FOR optimal AI agent performance TO SUCCEED:**

NEVER:
- Use a model in a harness designed for a different provider's model for complex agentic tasks [explicit — RATIONALE: "produces suboptimal results because the model's fine-tuning doesn't match"]
- Assume cross-tool compatibility is lossless [implied — RATIONALE: "cross-browser compatibility is always an approximation"]

ALWAYS:
- Use each LLM provider's own agent tool for best results [explicit — RULE]
- When experiencing poor results, check if the model matches the harness before blaming the model [derived — APPLIES WHEN: "experiencing poor results from an LLM in a third-party tool"]

GATE: Task is complex/agentic (multi-step tool use, file editing, iterative debugging). If false, harness mismatch is negligible.

## EXTENSION: Open-Source Models Without Dedicated Harnesses
[extended from: https://akitaonrails.com/2025/04/27/testando-llms-com-aider-na-runpod-qual-usar-pra-codigo/]

Open-source models (DeepSeek-Coder, CodeGemma, CodeLlama, Codestral) fail in Aider not because of model quality but because Aider has not implemented model-specific prompt profiles for them. Aider uses SEARCH/REPLACE diff-format instructions; DeepSeek expects XML-tagged commands. If Aider sends its standard prompt format to DeepSeek, the model responds in a format Aider cannot parse — producing "responses" that contain no actionable code edits.

**Implication:** Before concluding that an open-source model is low quality, verify that your agent tool (Aider, Crush, OpenCode) has a tested prompt profile for that model. Check the tool's GitHub issues and model-settings files. If no profile exists, the model failure is a harness problem, not a model quality problem.

**Currently tested as working in Aider (as of Apr 2025):** `qwen2.5-coder:7b-instruct` via `ollama_chat/` prefix.
**Currently untested/failing in Aider:** DeepSeek-Coder-V2, CodeGemma, CodeLlama, Codestral.

**CRITICAL: Aider prefix bug:** Use `ollama_chat/model-name` (NOT `ollama/model-name` as documented). Wrong prefix produces garbage output with no error message.

## SOURCE
https://akitaonrails.com/2026/01/24/ai-agents-qual-e-o-melhor-opencode-crush-claude-code-gpt-codex-gopilot-cursor-windsurf-antigravity/
https://akitaonrails.com/2025/04/27/testando-llms-com-aider-na-runpod-qual-usar-pra-codigo/
