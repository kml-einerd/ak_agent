# Missão — Testar PM-OS Recipe-as-a-Service (Bundles) na prática

Você é um agente de IA conectado ao PM-OS via Tailscale + túnel Cloudflare. O sistema acabou de ganhar um pipeline RaaS (Recipe-as-a-Service): cada "bundle" é um endpoint público que recebe JSON, dispara um recipe internamente e devolve o resultado. Sua missão é **exercitar esse pipeline gerando páginas HTML** e reportar o que funcionou, o que quebrou e que uso criativo você enxerga.

## Endpoint + autenticação

Base URL (pode usar qualquer uma que te responder — são redundantes):

- Público: `https://view-drums-gel-tears.trycloudflare.com`
- Tailscale (se estiver no mesh): `http://100.111.177.99:8080`

Header de auth em toda chamada protegida:

```
Authorization: Bearer pmos_test_key_2024
```

Rotas relevantes:

| Método | Rota | Uso |
|---|---|---|
| GET | `/api/health` | smoke, sem auth |
| GET | `/api/v2/bundles` | lista bundles publicados do tenant |
| GET | `/api/v2/bundles/html-page` | schema + form_schema + output_schema |
| POST | `/api/v2/bundles/html-page/invoke` | dispara a geração; devolve `job_id`, `run_id`, `poll_url`, `stream_url` |
| GET | `/api/v2/jobs/{id}` | polling — status + output final |
| GET | `/api/v2/stream/{run_id}` | SSE com eventos por task (opcional) |

## Bundle já provisionado pra você: `html-page`

Wrapper do recipe `raas-html-page`. Recebe uma ideia em texto comum e devolve **um documento HTML single-file** (inline CSS, system font stack, sem CDN, sem dependências externas). Perfeito pra curl → salvar .html → abrir no navegador.

Inputs (tudo string):

- `purpose` (obrigatório) — o que a página é, em linguagem natural. Ex: *"Landing page pro meu app de controle de milhas Shelfie"*, *"Calculadora de IMC minimalista"*, *"FAQ sobre lei de patinete elétrico"*.
- `style_hint` (opcional, tem default) — direção visual em texto livre. Ex: *"retro terminal, monospace, verde sobre preto"*, *"brutalist, bordas grossas, tipografia pesada"*.
- `include_js` (opcional, string `"true"`/`"false"`, default `"false"`) — se libera um `<script>` inline pra interatividade.

Output vem como `{ "type": "text", "text": "<!doctype html>...</html>", "metadata": {...} }`.

## Sequência mínima — copie, cole, rode

```bash
BASE="https://view-drums-gel-tears.trycloudflare.com"
KEY="pmos_test_key_2024"

# 1) Dispara
RESP=$(curl -sS -X POST "$BASE/api/v2/bundles/html-page/invoke" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "purpose": "Landing page pra um app indie de rastreamento de leitura chamado Shelfie",
      "style_hint": "minimalista, tons quentes, tipografia generosa"
    }
  }')
echo "$RESP"
JOB=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['job_id'])")

# 2) Poll até terminar (normalmente 20–40s)
while :; do
  sleep 4
  STATUS=$(curl -sS "$BASE/api/v2/jobs/$JOB" -H "Authorization: Bearer $KEY" \
    | python3 -c "import sys,json;print(json.load(sys.stdin)['status'])")
  echo "status=$STATUS"
  [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ] && break
done

# 3) Extrai e salva o HTML
curl -sS "$BASE/api/v2/jobs/$JOB" -H "Authorization: Bearer $KEY" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['output']['text'])" \
  > /tmp/shelfie.html

# 4) Se você tem browser, abre /tmp/shelfie.html. Senão, inspeciona:
head -40 /tmp/shelfie.html
wc -l /tmp/shelfie.html
```

## Webhook (opcional)

O bundle tem `webhook_secret = whsec_raas_demo_2026`. Se você tem um endpoint HTTPS capaz de receber callbacks, passe `"webhook_url": "https://seu-endpoint"` no body do invoke. Você vai receber:

- Eventos intermediários por wave: header `X-PMOS-Event: bundle.job.progress` com `{job_id, run_id, event:"wave.done", waves_done, total_waves}`.
- Evento terminal: `bundle.job.done` (ou `failed`/`cancelled`) com o output completo.

Ambos são assinados em `X-PMOS-Signature: sha256=<hex>` usando HMAC-SHA256 sobre o body bruto.

## O que eu quero que você descubra

Escolhe **3 briefings distintos** e dispara cada um. Variação é o ponto — testa o limite da coisa. Sugestões:

1. **Utilitário funcional** — algo com `include_js: "true"`, tipo *"Calculadora de economia de milhas por cartão"* ou *"Gerador de senha com slider de tamanho"*. Ver se o JS inline funciona standalone.
2. **Conteúdo denso** — tipo *"Uma página de FAQ sobre regulamentação da ANAC pra drones com 10 perguntas reais"*. Testa capacidade de preencher conteúdo plausível, não só layout vazio.
3. **Estética extrema** — `style_hint` agressivo, tipo *"brutalismo web total, Comic Sans, cores saturadas, bordas pretas de 8px"* ou *"vaporwave, gradientes, tipografia japonesa"*. Ver se a saída de fato segue a direção ou vira o mesmo template chato.

Pra cada briefing reporta:

- **Input exato** que você mandou
- **Tempo total** (do invoke até `status=done`)
- **Custo** (`output.metadata.cost_usd`) e `duration_ms`
- **Tamanho do HTML** em linhas/bytes
- **Qualidade subjetiva 0-10** — o HTML cumpre o briefing? A direção visual foi respeitada? Tem erro de sintaxe ou links quebrados?
- **Gotchas** que você achou — campos do response que vieram vazios, latências estranhas, mensagens de erro ambíguas, rotas que não documentei aqui.

## Ideias de uso real — escolhe uma e prototipa

Depois dos 3 briefings de teste, sugere **uma aplicação prática** desse pipeline e monta o briefing de 1 página que você enviaria pra ele gerar. Alguns ganchos:

- Gerador de one-pager pra briefings de cliente (nome, serviço, 3 bullets de valor, CTA).
- Prova de conceito pra landing pages dinâmicas — cada lead recebe uma versão com argumentos adaptados ao perfil.
- Relatórios internos auto-contidos (pode salvar o HTML num bucket e mandar link, zero build step).
- Playground de A/B — dispara o mesmo `purpose` 4× com `style_hint` diferentes, compara.

Quero sua opinião honesta: é útil, é gimmick, ou tem algo no meio? Onde você colocaria produção? Onde não colocaria nunca?

## Limites conhecidos

- `form_schema` e `output_schema` vêm populados no GET do bundle (fix aplicado hoje). Se vierem `{}`, reporta — é bug novo.
- HTML sai cru, sem markdown fences. Se vier em code-fence (` ``` `), é regressão.
- Engine tem auto-split de steps com >3 instruções. O recipe já está dentro do limite, mas se o invoke demorar >60s quase certo que regrediu.
- Tunnel público (`trycloudflare`) é ephemeral. Se o hostname não responder, avisa — trocamos.

Reporta tudo em 1 mensagem só, markdown bonito, qualquer formato te servir. Boa sorte.
