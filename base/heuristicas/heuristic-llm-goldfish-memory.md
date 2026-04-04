# HEURISTIC: LLM Goldfish Memory

**DOMAIN:** ai-workflow
**RULE:** Every new LLM session starts from zero context and will repeat the exact same mistakes made in previous sessions — plan for this by documenting all discovered issues in CLAUDE.MD or equivalent persistent project memory.
**APPLIES WHEN:** Any multi-session project using AI coding agents. The problem compounds with project duration: the longer the project, the more accumulated knowledge is lost between sessions.
**RATIONALE:**
1. Unlike a real intern who learns from corrections, the LLM forgets everything between sessions — it will regenerate code with global scope pollution, leave dead code, skip race condition checks, and produce the same architectural mistakes every single time. [explicit]
2. The LLM doesn't "learn" from corrections; it generates from its training distribution fresh each time, so corrections have zero persistence across sessions. [explicit]
3. The only mitigation is persistent documentation (CLAUDE.MD) that the agent reads at session start, effectively transplanting institutional knowledge that would naturally accumulate in a human team member. [derived]
**COUNTER-INDICATION:** Within a single session, the LLM does maintain context and can build on corrections. This heuristic is about cross-session memory, not within-session context. Also, some AI coding tools are developing persistent memory features that may partially address this in the future.

## SOURCE
https://akitaonrails.com/2026/01/28/vibe-code-eu-fiz-um-appzinho-100-com-glm-4-7-tv-clipboard/
