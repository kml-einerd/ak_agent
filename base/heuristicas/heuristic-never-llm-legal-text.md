# HEURISTIC: Never LLM Legal Text

**DOMAIN:** ai-workflow
**RULE:** Never let an LLM generate legal documents (licenses, terms of service, privacy policies, contracts) — always obtain these from official sources and copy verbatim.
**APPLIES WHEN:** Any project that needs a software license (MIT, GPL, AGPL), terms of service, privacy policy, or any document with legal standing.
**RATIONALE:**
1. LLMs produce summarized, incomplete, or subtly incorrect versions of legal text — a license with wrong wording or missing clauses may not provide the legal protection intended, and there is no "compiler" for laws that catches errors. [explicit]
2. The LLM treats legal prose as natural language to be generated, but legal prose is a formal specification where every word is deliberate — an AGPL-3.0 license with a paraphrased clause may not hold up legally the same as the official FSF text. [explicit]
3. Unlike code (where "close enough" often works), legal text must be exactly right — always obtain from official sources and copy verbatim. [derived]
**COUNTER-INDICATION:** LLMs can be useful for explaining what a license means in plain language, or for comparing licenses to help choose which one to adopt. The heuristic is specifically about generating the actual legal text that will be included in the project, not about using LLMs as a research aid for understanding legal concepts.

## SOURCE
https://akitaonrails.com/2026/01/28/vibe-code-eu-fiz-um-appzinho-100-com-glm-4-7-tv-clipboard/
