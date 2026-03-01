# ANTI-PATTERN: Aider Auto-Commit on AI Changes

**DOMAIN:** ai-workflow
**APPEARS AS:** Aider commits every LLM change automatically — marketed as a convenience so the developer can review history and roll back. Seems like a safety net.
**ROOT CAUSE:** Auto-commit bypasses the mandatory human review gate. The LLM can commit broken code, incorrect refactors, or regressions before the developer has verified the result. Because the commit message says "refactor X," the developer trusts it was done correctly — but the model commits even when it made an error.
**RATIONALE:**
1. LLMs claim to have done what was asked but frequently break adjacent code while fixing the target. Without a manual review gate, bad changes enter git history with plausible commit messages. [explicit]
2. Rolling back requires identifying which commit introduced the regression — which is harder than just doing `git checkout` before committing. [derived]
3. The auto-commit feature optimizes for amateurs who don't organize commits anyway, but for professional developers it inverts the verification order: commit first, discover error later. [derived]

---

## SYMPTOMS

- Git log contains Aider-authored commits with messages like "refactor X" or "add tests for Y" that contain broken or incomplete changes
- Linter or test errors appear after an Aider session but the developer doesn't know which commit introduced them
- Developer discovers the model committed a change that added whitespace or cosmetic noise instead of the requested refactor
- Model makes a commit, developer asks it to fix an error, model makes another commit — history becomes a series of incremental mistake-correction commits

## CORRECTION

Disable auto-commit immediately after installing Aider. In `$HOME/.aider.conf.yml`:

```yaml
auto-commits: false
```

With auto-commit disabled: Aider proposes changes, developer reviews the diff in the editor, then manually stages and commits with a meaningful message. If the result is wrong, `git checkout` or undo restores the file before any history is created.

**NOT TO CONFUSE WITH:** Aider's `--dry-run` mode, which shows what would be done without writing any files. The anti-pattern is specifically the default auto-commit behavior, not the dry-run preview.

## SOURCE
https://akitaonrails.com/2025/04/25/seu-proprio-co-pilot-gratuito-universal-que-funciona-local-aider-ollama-qwen/
