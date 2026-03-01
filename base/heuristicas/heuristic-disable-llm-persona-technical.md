# HEURISTIC: Disable LLM Persona in Technical Work

**DOMAIN:** ai-workflow
**RULE:** When using a commercial LLM for engineering work, always configure the system prompt or customization settings to suppress the default personality layer before beginning any technical session.
**APPLIES WHEN:** Any technical use of a commercial LLM (ChatGPT, Claude, Gemini) — code review, debugging, architecture discussion, writing documentation. Applied at session start or permanently via provider customization settings.
**RATIONALE:**
1. The default personality layer adds token overhead (affirmations, hedging, emotional framing) that is zero-value in engineering contexts — it consumes context window space and increases latency without adding information. [explicit]
2. Verbose hedging and unsolicited disclaimers obscure whether the model actually produced a correct answer or deflected. A direct instruction ("answer with minimum words, maximum precision") forces the model to commit to a position, making failures more visible and easier to debug. [derived]
3. Establishing this baseline once in provider customization (not in every prompt) is a one-time cost that compounds — every future session benefits without requiring the user to repeat the instruction. [derived]
**COUNTER-INDICATION:** Do not apply when building user-facing products where the persona is a product feature (e.g. a customer support bot or educational assistant where warmth is a deliberate design choice).

## SOURCE
https://akitaonrails.com/2025/04/28/destruindo-a-personalidade-do-chatgpt-4o/
