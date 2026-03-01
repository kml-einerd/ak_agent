# REFERENCE: Claude Code Permission Config

**DOMAIN:** ai-workflow
**WHEN TO CONSULT:** Setting up Claude Code for the first time, after installing a new agent, or when balancing security vs convenience in AI agent permissions.

---

## CONTENT

### Permission Tiers (settings.json)

| Tier | Purpose | Examples |
|------|---------|----------|
| **allow** | Safe, read-only, or standard dev operations | `git status`, `ls`, `grep`, `cat`, `npm test`, `cargo build`, `WebSearch` |
| **deny** | Destructive or irreversible operations | `rm -rf`, `sudo`, `chmod 777`, `git push --force`, `git reset --hard`, `docker rm` |
| **ask** | Moderate-risk operations requiring human review | `git push`, `git rebase`, `rm` (single file), `docker run`, `kamal deploy` |

### Recommended Allow List (Akita's config)

- **Git read**: `git status`, `git diff`, `git log`, `git branch`, `git show`, `git rev-parse`, `git ls-files`
- **Git write (safe)**: `git add`, `git commit`, `git fetch`, `git pull`, `git merge`, `git stash`, `git tag`
- **File inspection**: `ls`, `find`, `grep`, `wc`, `cat`, `head`, `tail`, `file`, `which`, `pwd`
- **Build tools**: `npm`, `npx`, `yarn`, `pnpm`, `bun`, `node`, `cargo`, `rustc`, `go`, `python`, `ruby`, `bundle`, `rails`, `rake`, `make`
- **Utility**: `curl`, `jq`, `sed`, `awk`, `sort`, `uniq`, `diff`, `gh`, `docker compose`, `docker ps/logs/images`
- **Web**: `WebSearch`, `WebFetch`
- **Version checks**: `* --version`, `* --help`

### Recommended Deny List

```
rm -rf, rm -r, sudo, chmod 777,
git reset --hard, git clean, git push --force, git push -f,
docker rm, docker rmi, docker system prune
```

### Recommended Ask List

```
git push, git rebase, git branch -D/-d,
rm (single file), kamal deploy,
docker run, docker exec, docker stop
```

### Key Setting

```json
"defaultMode": "acceptEdits"
```

This allows the agent to edit files without asking but requires approval for shell commands not in the allow list.

## SOURCE
https://akitaonrails.com/2026/01/10/ai-agents-garantindo-a-protecao-do-seu-sistema/
