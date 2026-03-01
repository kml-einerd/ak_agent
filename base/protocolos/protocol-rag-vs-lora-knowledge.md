# PROTOCOL: RAG vs LoRA Knowledge Boundary

**DOMAIN:** ai-workflow
**APPLIES TO:** Any decision about how to give an LLM access to knowledge not in its training cutoff — especially when the knowledge corpus is large (50K+ tokens) and the system will be used across multiple sessions
**RATIONALE:**
1. RAG injects knowledge into the context window per session, consuming tokens that compete with the actual task prompt and degrading attention with context length [explicit]
2. LoRA embeds knowledge permanently in model weights, consuming zero context tokens at inference time, but requires GPU training time, is model-specific, and risks catastrophic forgetting [explicit]
3. The optimal strategy depends on multiple interacting factors: knowledge change frequency, corpus size, context window limits, cost model, and session count — requiring multi-criteria evaluation rather than a simple heuristic [derived]

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Knowledge changes daily or weekly (support tickets, user records, news) | Dynamic data — LoRA retraining cycle cannot keep up | Use RAG: inject relevant chunks per session |
| Knowledge is stable, corpus is large (50K+ tokens), used across many sessions | Permanent knowledge with recurring per-session cost if using RAG | Use LoRA: embed in model weights, zero inference-time token cost |
| Knowledge corpus is small (<10K tokens) and needed for a single session | Overhead of either RAG infrastructure or LoRA training is unjustified | Paste directly into the prompt — no infrastructure needed |
| Using a commercial API with prompt caching | RAG's per-session cost is reduced by caching, diminishing LoRA's advantage | RAG with cached prompts may be more cost-effective than LoRA training |
| Single-session or ad-hoc need | No recurring cost to amortize | Paste relevant excerpt into prompt directly |

**TRADE-OFFS:** LoRA requires 1+ hours GPU training on RTX 4090 for an 8B model, is specific to the exact base model (Qwen3-8B LoRA won't work on Qwen3-32B), and risks catastrophic forgetting if learning rate is too aggressive. RAG requires retrieval infrastructure (vector DB, embedding pipeline) but works with any model and adapts instantly to knowledge updates. For 200K-character documentation (~50K tokens), RAG cost recurs every session and may exceed open-source model context windows (typical 32K).

**ESCALATE WHEN:** Knowledge corpus exceeds both the model's context window (making RAG infeasible without chunking) AND is too dynamic for LoRA (changes weekly). At this point, consider: hybrid approach (LoRA for stable core + RAG for dynamic updates), larger context model, or restructuring the knowledge into smaller domain-specific modules.

## SOURCE
https://akitaonrails.com/2025/05/03/ensinando-zig-mais-recente-pra-sua-llm-treinando-loras-quase/
