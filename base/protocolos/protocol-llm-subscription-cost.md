# PROTOCOL: LLM Subscription Cost Evaluation

**DOMAIN:** ai-workflow
**APPLIES TO:** Choosing between LLM subscription plans vs per-token API access for coding sessions, especially when hitting rate limits
**RATIONALE:** Per-token API access (e.g., via OpenRouter) costs orders of magnitude more than subscription plans for sustained coding sessions. A few hours of per-token Claude Opus can exceed the entire monthly subscription cost. The impulse to "keep going" when hitting limits leads to catastrophic cost overruns. The correct response is usually to wait for limits to reset.

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Hit daily token limit on subscription plan (e.g., Claude Code Max) | Normal rate limiting — plan working as designed | Stop coding. Wait for limit reset. Use the break for rest, planning, or manual review. |
| Tempted to switch to per-token API to continue during rate limit | Cost will multiply 10-50x compared to subscription | Do NOT switch. Calculate the per-token cost first. Akita spent $100+ in 2-3 hours on OpenRouter vs $6/day effective cost on Max plan. |
| Project requires more than 1-2 days of sustained LLM usage | Need to plan total budget before starting | Estimate total days of work. Multiply by subscription daily cost. Compare with per-token estimates. Choose subscription. |

**TRADE-OFFS:** Subscription plans cap daily usage (forced breaks) but are dramatically cheaper per token. Per-token gives unlimited access but can bankrupt a project budget in hours.

**ESCALATE WHEN:** The project genuinely cannot tolerate breaks (hard deadline). In that case, set a hard dollar cap on per-token spending and monitor in real-time.

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
