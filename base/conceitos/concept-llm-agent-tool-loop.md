# CONCEPT: LLM Agent Tool Loop

**DOMAIN:** ai-workflow
**DEFINITION:** An LLM agent tool loop is a pattern where: (1) the system prompt declares available "pseudo-commands" (e.g., `[LOAD_FILE path]`, `[FETCH_URL url]`) with trigger conditions; (2) the LLM emits these commands as literal text in its response when the trigger conditions are met; (3) an external parser (regex or grammar-based) detects the commands in the LLM output; (4) external scripts execute the real operation and inject the result back into the conversation history as a system/user message; (5) the LLM continues the response with access to the injected content. The model never directly executes anything — it only outputs text that signals intent; execution is entirely in the surrounding program.
**NOT:**
- Not a "function calling" API feature (though OpenAI/Anthropic function calling implements the same pattern at the API level with structured JSON instead of freeform text commands)
- Not RAG (Retrieval-Augmented Generation) — RAG retrieves context before generation; the tool loop retrieves context triggered by the model's own output during generation
- Not fine-tuning — the model's weights are unchanged; all behavior is shaped by the system prompt rules
- Not persistent — the injected tool results exist only for the duration of the session history; nothing is written to model weights

**RATIONALE:** Without naming this pattern, engineers either (a) think LLMs have "direct access" to external systems (they don't — the model only generates text), or (b) believe building agents requires proprietary frameworks (it doesn't — any regex + subprocess call is sufficient for a proof of concept). Naming it also clarifies why the system prompt must repeat tool definitions at every session start: the model has no memory of previous sessions, so the "contract" for tool behavior must be re-established each time.

---

## REFERENCED BY

- base/protocolos/protocol-llm-sampling-agent-loops.md

## SOURCE
https://akitaonrails.com/2025/04/25/hello-world-de-llm-criando-seu-proprio-chat-de-i-a-que-roda-local/
