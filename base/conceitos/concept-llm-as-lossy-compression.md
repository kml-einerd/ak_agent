# CONCEPT: LLM as Lossy Compression

**DOMAIN:** ai-workflow
**DEFINITION:** A large language model is a lossy compression of human-generated text — analogous to a JPEG (lossy image compression) or a ZIP file applied to a corpus. It encodes statistical patterns from training data into weights; a query is a retrieval operation over that compressed representation. No reasoning, cognition, or consciousness is involved: the model reconstructs plausible next tokens based on compressed pattern proximity. The "answer" is a decompression artifact, not a product of deliberation.
**NOT:**
- Not a reasoning engine that deliberates over problems and arrives at logical conclusions
- Not a database with factual records that can be retrieved with guaranteed accuracy
- Not an agent with beliefs, desires, or intentions
- Not evidence that the entity "understands" the domain — it has compressed representations of what humans wrote about the domain
**RATIONALE:** Without this definition, practitioners (and users) conflate statistical token prediction with reasoning, leading to: over-trusting outputs in domains requiring logical precision; attributing intentionality to hallucinations; misinterpreting personality-layer behavioral outputs as evidence of sentience. This definition establishes the correct mental model that governs when to trust, verify, or distrust LLM outputs.

---

## REFERENCED BY

- base/anti-patterns/antipattern-llm-anthropomorphized-defaults.md
- base/heuristicas/heuristic-preflight-structural-validation.md
- base/anti-patterns/antipattern-vibe-coding-without-expertise.md

## SOURCE
https://akitaonrails.com/2025/04/28/destruindo-a-personalidade-do-chatgpt-4o/
