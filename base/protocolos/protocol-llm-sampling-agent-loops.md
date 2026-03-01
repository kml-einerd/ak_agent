# PROTOCOL: LLM Sampling for Agent Loops

**DOMAIN:** ai-workflow
**APPLIES TO:** Any open-source LLM (Qwen, GPT-OSS, DeepSeek) entering an agentic loop — repeatedly claiming success without fixing issues, or generating identical reasoning text across turns
**RATIONALE:**
1. Open-source LLMs have less RLHF tuning for "knowing when to stop" compared to commercial models, making them prone to loops where high confidence on a wrong answer overwhelms alternatives [explicit]
2. When a model sees its own previous reasoning in context, it re-generates the same text (semantic recursion), creating a positive feedback loop that default sampling parameters cannot break [explicit]
3. Adjusting sampling parameters (temperature, min-p, repeat penalty) introduces controlled randomness that disrupts the loop while maintaining output quality — but parameters must be tuned per model family [explicit]

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Model repeats "I fixed it" but build still fails | High confidence on wrong answer — model is 98%+ certain the fix is correct | Increase temperature to 0.8-1.0 to introduce variety; increase min-p to 0.08-0.10 |
| Model generates identical reasoning text across consecutive turns | Semantic recursion — model sees its own output and re-generates it | Apply repeat penalty 1.1-1.2 (never above 1.2 — produces broken output) |
| Context fills with error traces after many failed attempts | Context window pollution — model can't find productive path | Clear context: start new session with summary of what was done |
| Adjusted sampling parameters don't break the loop | Task exceeds model capability or context is irrecoverable | Reduce task scope, provide the answer yourself, or switch models |

### Model-Specific Settings

| Model | Recommended Settings |
|-------|---------------------|
| Qwen3-Coder | Min-P 0.1, repeat penalty 1.1-1.2 (min-p more effective than top-p) |
| GPT-OSS | Temperature near 1.0, Top-K at 0 (trained to self-manage probability space) |
| GLM 4.7 / MiniMax | Monitor context length — very long reasoning chains may exceed context before useful output |
| DeepSeek | Check tool-calling format compatibility — may be incompatible with non-OpenAI format agents |

**TRADE-OFFS:** Higher temperature and repeat penalty introduce variety but may reduce output coherence. The effective range is narrow (repeat penalty 1.1-1.2; above 1.2 produces broken output). Top-P is less effective for loops because it includes all high-probability tokens, which in a loop are the wrong ones. Min-P is more adaptive because it adjusts dynamically based on model confidence.

**ESCALATE WHEN:** Sampling adjustments fail after 2-3 attempts. At that point: (1) clear context and start fresh with a summary, (2) break the task into a smaller sub-task, (3) provide the answer directly, or (4) switch to a different model for this specific sub-task.

## SOURCE
https://akitaonrails.com/2026/01/11/ai-agents-comparando-as-principais-llm-no-desafio-de-zig/
