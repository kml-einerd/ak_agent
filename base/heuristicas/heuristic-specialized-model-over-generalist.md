# HEURISTIC: Specialized Model Over Generalist

**DOMAIN:** ai-workflow
**RULE:** When a task fits a defined domain (code generation, a specific programming language, image analysis, medical text), always prefer a smaller specialized model over a larger generalist model as the starting candidate — only escalate to generalist if the specialized model demonstrably fails.
**APPLIES WHEN:** Selecting a local or API-hosted LLM for a single-domain production task (coding assistant, code review, language-specific generation, domain-specific Q&A). Especially relevant when running models locally with constrained VRAM.
**RATIONALE:**
1. Specialized models are trained on higher-density domain data relative to their parameter count — a 14B coding model trained on curated code has more "code knowledge per parameter" than a 70B generalist where code is diluted by general text. [explicit]
2. A smaller specialized model fits in less VRAM, enabling faster inference with lower latency and lower cost — a model that does not fit in VRAM must page between RAM and VRAM, causing severe performance degradation that erases any quality advantage. [explicit]
3. Empirically confirmed: Qwen2.5-Coder:7b-instruct dramatically outperformed Qwen2.5-Coder:32b on identical refactor + unit test tasks in Aider — it was faster, made fewer errors, and required fewer correction rounds. A larger model has more parameters encoding more relationships, which means more potential paths to "hallucinate" from memorized patterns rather than reasoning from provided context. [explicit]
4. Generalist models optimized for instruction-following may apply "safety alignment" corrections that degrade task-specific output quality (hedging, refusing to generate raw code, adding disclaimers) — specialized models trained without those constraints produce cleaner domain output. [derived]
**COUNTER-INDICATION:** When the task requires multi-domain reasoning (e.g., writing code that implements a legal contract clause), no specialized model covers all domains — use a large generalist or a multi-LLM pipeline. Also does not apply when ground truth is unavailable and instruction-following quality matters more than domain depth. For commercial APIs (Claude, Gemini, GPT) the situation differs — their Sonnet/Flash tiers are already highly optimized for code.

## SOURCE
https://akitaonrails.com/2025/04/25/hello-world-de-llm-criando-seu-proprio-chat-de-i-a-que-roda-local/
https://akitaonrails.com/2025/04/27/testando-llms-com-aider-na-runpod-qual-usar-pra-codigo/
