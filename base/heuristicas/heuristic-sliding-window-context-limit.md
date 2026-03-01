# HEURISTIC: Sliding Window Context Is Not Full Recall

**DOMAIN:** ai-workflow
**RULE:** Never assume an LLM with a 1M-token context window "reads" all 1M tokens for every response — it uses sliding window attention and only actively attends to a window of tokens at a time; content far from the current query position receives diminished or zero attention.
**APPLIES WHEN:** Deciding how much context to load into an LLM session (codebase files, documentation, conversation history) and when debugging situations where the model "forgets" earlier instructions or injected content despite it being technically within the context limit.
**RATIONALE:**
1. Full attention over 1M tokens would require O(n²) memory and compute — SDPA (Scaled Dot Product Attention) and sliding window mechanisms reduce this by computing attention only over local windows or selected positions, making large contexts computationally feasible. [explicit]
2. The practical consequence: rules defined in the system prompt at the start of a long conversation degrade in influence as the session history grows, because they fall outside or to the edge of the active attention window. [explicit]
3. Token density estimation: ~10 tokens per line of code, ~5000 tokens per 500-line file, ~100K tokens for a 20-file project — use these to estimate when a project exceeds practical attention coverage. [explicit]
**COUNTER-INDICATION:** For short sessions (<20K tokens total history), sliding window rarely causes recall degradation — the entire context fits comfortably within most models' effective attention window. Also, some models (e.g., Gemini with "infinite context" techniques) use retrieval augmentation internally to partially mitigate this.

## SOURCE
https://akitaonrails.com/2025/04/25/hello-world-de-llm-criando-seu-proprio-chat-de-i-a-que-roda-local/
