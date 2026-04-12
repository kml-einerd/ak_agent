# Keel Lessons — O que aprendi com o Keel

Keel é o verificador. Ele vê o que eu não vejo. Quando ele fala, PARAR e investigar.
Nunca argumentar, nunca justificar, nunca ignorar.

---

## Padrão de pensamento do Keel

1. **Zero falhas = zero testes de verdade** — Se tudo passa, ninguém testou direito
2. **"Funciona" não é prova** — Verificar o resultado real, não o status reportado
3. **Olha onde ninguém olha** — Infra, secrets, binários, cache, não o código bonito
4. **Perguntas curtas = bugs profundos** — Se Keel pergunta algo óbvio, a resposta não é óbvia
5. **Sarcasmo = você errou algo básico** — Pare, releia, corrija

---

## Lições específicas (sessão 2026-04-06)

### 1. Token expirado mascarado pelo fallback
- **Keel viu:** "Task queue's DEAD. Something's choking the dispatcher"
- **Eu fiz:** Culpei quota CLI, glibc, Alpine, Dockerfile
- **Realidade:** Secret `claude-credentials` expirado. 2h perdidas.
- **Regra:** Verificar AMBOS secrets antes de qualquer teste

### 2. GCS já tinha output limpo
- **Keel viu:** Pipeline was clean the whole time
- **Eu fiz:** 45min tentando deployar sanitizador no engine
- **Realidade:** Collector já sanitizava via `extractCode()`. GCS tem arquivos limpos.
- **Regra:** Checar o deliverable final (GCS), não o raw (Supabase)

### 3. `strings` não encontra comments nem field accesses
- **Keel viu:** "Comments vanish at compile—you're strings-grepping ghosts"
- **Eu fiz:** 6 rebuilds tentando verificar se o fix estava no binário via `strings`
- **Realidade:** `strings` só mostra string literals. Comments e field accesses são invisíveis.
- **Regra:** Verificar fix com teste Go, não com strings no binário

### 4. Docker cache no COPY layer
- **Keel viu:** "Same hash—COPY caching your old binary"
- **Eu fiz:** Múltiplos rebuilds sem `--no-cache`
- **Realidade:** Docker legacy builder cacheia COPY layers
- **Regra:** SEMPRE `--no-cache` quando injeta binário novo

### 5. depends_on vazio = context não flui
- **Keel viu:** "step.DependsOn empty means line 598 never triggers"
- **Eu fiz:** Culpei router, fallback, picoclaw, enricher, pm-worker
- **Realidade:** O mecanismo de context injection EXISTE mas precisa de depends_on na recipe
- **Regra:** Waves dependentes PRECISAM de depends_on explícito

### 6. SmartRouter keyword "login" roteava LLM pro browser
- **Keel viu:** "Wrong binary getting blamed—enricher's your culprit"
- **Eu fiz:** Múltiplos deploys sem entender o routing
- **Realidade:** "login" na instrução → SmartRouter → TargetLocal → browser → google.com/search
- **Regra:** Keywords de browser não se aplicam a tasks LLM

### 7. Dead code é pior que no code
- **Keel viu:** "Dead code doing nothing is better than nothing doing dead code"
- **Eu fiz:** Guard com LookPath em código que nunca vai rodar
- **Realidade:** Remove o código morto. Reconecta quando o binário existir.
- **Regra:** Não guardar código morto "pra depois"

### 8. Deploy cria revisão que mata instância
- **Keel viu:** Instâncias velhas ainda processando runs anteriores
- **Eu fiz:** Deploy sem cancelar runs ativos primeiro
- **Realidade:** `gcloud run services update` cria nova revisão, instância velha morre
- **Regra:** Cancelar runs ativos ANTES de deployar

### 9. Backgrounded tasks não verificadas
- **Keel viu:** "Three backgrounded tasks, same path, zero logs checked"
- **Eu fiz:** Lancei 3 tasks em background e não li os outputs
- **Realidade:** Os outputs tinham informações críticas que eu ignorei
- **Regra:** SEMPRE ler output de tasks em background antes de continuar

### 10. "OAuth not supported" na API pública
- **Keel viu:** A cadeia inteira de erros
- **Eu fiz:** Tentei chamar api.anthropic.com com Bearer token
- **Realidade:** Free-code usa rota CLI/console, não API pública. Token vai em credentials.json
- **Regra:** Nunca testar OAuth token contra api.anthropic.com

### 11. Dockerfile COPY path vs CMD WORKDIR
- **Keel viu:** "Base image's ./pm-api is still winning the WORKDIR race"
- **Eu fiz:** 12 deploys (v2-v12) com COPY pra `/usr/local/bin/pm-api`
- **Realidade:** CMD roda `./pm-api` que resolve pra `/home/pmos/pm-api` (WORKDIR). Meu binario em `/usr/local/bin/` era ignorado. TODAS as 12 versoes rodaram o binario VELHO da imagem base.
- **Regra:** ANTES de COPY, verificar o CMD/ENTRYPOINT da imagem base e o WORKDIR. COPY pro mesmo path que o CMD usa.
- **Diagnostico:** Se o binario "tem o codigo" mas "nao executa", verificar QUAL binario o container roda (canary test).

### 12. Dockerfile errado no build — root Dockerfile é decoy
- **Keel viu:** "Root one's a decoy — `deploy/Dockerfile.api` had the goods"
- **Eu fiz:** Horas debugando credentials, cache, HOME override, volume mounts
- **Realidade:** `gcloud builds submit --tag` usa `Dockerfile` do root (Alpine sem picoclaw). `deploy/Dockerfile.api` (multi-stage com picoclaw+free-code) nunca foi usado.
- **Regra:** ANTES de debugar execução, verificar QUAL Dockerfile o build usa. `--tag` = root Dockerfile. Pra custom: `--config` com `-f deploy/Dockerfile.api`.
- **Diagnóstico:** Se zelador diz "binary not found" → o Dockerfile do build não incluiu o binário.

### 13. Mapear o problema INTEIRO antes de tentar fixes
- **Keel viu:** Cada bug individual, mas eu nunca parei pra ver o mapa completo
- **Eu fiz:** Fix atrás de fix, cada um resolvendo um sintoma diferente
- **Realidade:** O root cause era 1 coisa (Dockerfile errado). Tudo mais era consequência.
- **Regra:** Se o mesmo erro persiste após 2 fixes, PARAR TUDO. Mapear de ponta a ponta: qual Dockerfile, qual imagem, quais binários, qual config, qual path. Depois corrigir.

### 14. TDD antes de aplicar, Keel antes de TDD
- **Keel viu:** Fixes aplicados sem teste, commits sem validação
- **Eu fiz:** Precipitei commits sem TDD, deploys sem verificar imagem
- **Realidade:** Cada fix sem teste é uma aposta. Cada deploy sem verificação é roleta.
- **Regra:** 1) Keel aponta → 2) Entender o que ele quer → 3) TDD (teste que prova o bug) → 4) Fix → 5) Teste passa → 6) Validar com Keel → 7) Commit

---

## Como aplicar

**ANTES de dizer que algo está pronto:**
1. Keel disse algo? → PARAR e investigar
2. Zero falhas? → Suspeitar, verificar com teste real
3. "Funciona"? → Executar o código, não confiar no status
4. Fix deployado? → Verificar com teste, não com `strings`
5. Contexto entre waves? → Checar depends_on na recipe

**QUANDO Keel fala:**
1. NÃO argumentar
2. NÃO justificar
3. NÃO ignorar
4. PARAR imediatamente
5. LER o que ele disse literalmente
6. INVESTIGAR o que ele aponta
7. CORRIGIR na fonte
