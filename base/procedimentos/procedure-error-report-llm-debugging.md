# PROCEDURE: Error Report for LLM Debugging

**TRIGGER:** Something breaks during an AI-assisted coding session and needs to be reported to the LLM for fixing
**DOMAIN:** ai-workflow
**PRE-CONDITIONS:** An observable error or regression has been detected (visual, functional, or in logs)

---

## STEPS

1. Identify WHAT specifically stopped working → "element X disappeared" not "it broke"
2. Determine SCOPE of the failure → full app crash vs single element vs visual glitch vs data loss
3. Check for error messages in browser console, server logs, or terminal output → copy exact error text
4. Identify WHAT CHANGED since the last working state → which commits, which files, which prompt
5. Attempt to reproduce the error → document exact steps to trigger it
6. Construct the next prompt including: (a) specific description of what broke, (b) exact error messages, (c) relevant log lines, (d) reproduction steps, (e) what changed since last working state

**ON_FAILURE[step-4]:** If you don't know which commit broke it, ask the LLM to perform a manual git bisect: test commits one by one to isolate when the regression was introduced
**ON_FAILURE[step-6]:** If the LLM starts doing trial-and-error without progress after 2-3 attempts, stop and investigate the root cause yourself — the LLM may be missing critical context

---

## DONE WHEN
- The prompt contains all four elements: specific error description, exact error messages/logs, reproduction steps, and change history since last working state
- The LLM receives enough information to diagnose without guessing (verified by checking that the LLM's first response addresses the root cause rather than asking for more context)

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
