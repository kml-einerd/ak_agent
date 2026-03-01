# PROCEDURE: AI Agent Filesystem Sandbox

**TRIGGER:** Running any AI coding agent (Claude Code, Cursor, Crush, OpenCode, Codex) that has shell access to execute arbitrary commands on your system
**DOMAIN:** security
**PRE-CONDITIONS:** Linux with bubblewrap (bwrap) installed, or Docker available; project code is in a git repository (for recovery if something goes wrong)

---

## STEPS

1. Install bubblewrap (`apt install bubblewrap` or equivalent) → sandbox tooling available
2. Create a sandbox script that mounts system directories read-only (`--ro-bind /usr /usr`, `/bin`, `/lib`, `/etc`) and the project directory read-write (`--bind $(pwd) $(pwd)`) → agent can read system tools but only write to the project
3. Mount $HOME as tmpfs (empty temporary filesystem) to hide all personal files → agent cannot access .gnupg, .aws, .docker, browser profiles, password managers
4. Selectively mount only agent-required dotdirs as read-write (.claude, .crush, .codex, .config) and sensitive config subdirs as tmpfs overrides (BraveSoftware, Bitwarden) → agent has its own config but no access to secrets
5. Unshare namespaces (--unshare-user --unshare-pid --unshare-uts --unshare-ipc) but keep network (--share-net) → agent is isolated from host processes but can access APIs and web
6. Run the AI agent inside the sandbox (`ai-jail crush`, `ai-jail claude`) → all agent actions are constrained to the sandbox
7. For tools with built-in permission systems (Claude Code settings.json), additionally configure allow/deny/ask tiers: allow safe read operations (ls, grep, git status), deny destructive operations (rm -rf, sudo, git push --force), ask for moderate-risk operations (git push, rm, docker run) → defense in depth

**ON_FAILURE[step-2]:** If bwrap is not available (macOS, Windows), use Docker with volume mounts restricted to the project directory as an alternative
**ON_FAILURE[step-4]:** If agent fails to start due to missing config, add the required dotdir to the read-write mount list

---

## DONE WHEN
AI agent runs inside the sandbox and can: (a) read and write project files, (b) run build tools and tests, (c) access the web for documentation, but CANNOT: (d) read files outside the project and allowed dotdirs, (e) write to any system directory, (f) access sensitive credentials or browser profiles.

## SOURCE
https://akitaonrails.com/2026/01/10/ai-agents-garantindo-a-protecao-do-seu-sistema/
