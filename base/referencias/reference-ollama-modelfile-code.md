# REFERENCE: Ollama Modelfile for Code LLMs

**DOMAIN:** ai-workflow
**WHEN TO CONSULT:** Configuring a local open-source LLM for code generation tasks via Ollama; optimizing sampling parameters for code quality instead of creative writing; creating a code-specialized model variant with a custom SYSTEM prompt.

---

## CONTENT

### Sampling Parameters for Code

| Parameter | Recommended | Purpose |
|-----------|------------|---------|
| `temperature` | 0.1–0.2 | Controls randomness. Higher (0.6+) causes hallucinations in code: Chinese characters mid-variable, random variable renames, invented APIs. Zero causes repetitive boilerplate and potential infinite loops. 0.1–0.2 is the sweet spot for code. |
| `top_p` | 0.95 | Nucleus sampling: orders tokens by probability descending, accumulates until sum >= top_p, then samples only from that set. Filters low-probability tokens while allowing plausible alternatives. |
| `top_k` | 20 | Restricts sampling to the top K most probable tokens. Lower = more focused/greedy; higher = more diverse. Acts in conjunction with top_p to anchor selection. |
| `min_p` | 0.0 | Filters tokens whose probability < P_max * min_p. Prevents selection of extremely improbable tokens relative to the best choice. |
| `repeat_penalty` | 1.1 | Divides probability of recently-seen tokens by this value. At 1.0 = no penalty (may repeat same code/errors). Above 1.2 = unnaturally avoids necessary repetition. 1.1 is a good balance. |
| `num_predict` | 32768 | Max tokens to generate. Too low truncates code responses. Too high wastes compute. 32K provides ample space for code. |

### How Sampling Works Together

1. Model calculates probability scores for every token in vocabulary
2. `min_p` removes tokens below threshold relative to top token
3. `top_k` keeps only the K highest-probability tokens
4. `top_p` further narrows to smallest set with cumulative probability >= p
5. `temperature` scales the remaining distribution (lower = more peaked)
6. `repeat_penalty` reduces scores of tokens already in recent output
7. Final token is sampled from the adjusted distribution

### Creating a Code-Optimized Model

```bash
# 1. Export base modelfile
ollama show qwen3 --modelfile > Modelfile

# 2. Edit Modelfile: add SYSTEM prompt and PARAMETER overrides

# 3. Create new model variant
ollama create qwen3-dev -f qwen3-dev.modelfile

# 4. Verify
ollama list  # should show qwen3-dev:latest

# 5. Use in Aider or other tools
aider --watch-files --model ollama_chat/qwen3-dev:latest
```

### Recommended SYSTEM Prompt for Code

```
SYSTEM """
You are a highly functional AI assistant specializing in software development tasks.
Provide clear, accurate, step-by-step reasoning and functional code examples.
Always format code snippets using markdown triple backticks.
Never suggest changing code unrelated to the question topic at hand.
Restrict yourself to the minimum amount of changes that resolve the problem.
Avoid renaming functions or variables unless absolutely necessary,
and in doing so make sure if there's anyone calling the old names,
for them to be renamed to the new names. Never leave the code in a broken state.
Pay close attention to correctness, not just the quickest code.
"""
```

### Aider Configuration for Custom Model

```yaml
# ~/.aider.model.settings.yaml
- name: ollama_chat/qwen3-dev:latest
  extra_params:
    temperature: 0.1
    num_ctx: 40960
```

### Important Notes

- Modelfiles do NOT inherit from the base model — you must export the full base modelfile first, then add your overrides
- The SYSTEM prompt consumes tokens from the context window every session
- Monitor GPU usage: sustained 90%+ GPU utilization at ~400W is normal; ensure adequate power delivery

---

## Aider Integration Gotchas
[extended from: https://akitaonrails.com/2025/04/25/seu-proprio-co-pilot-gratuito-universal-que-funciona-local-aider-ollama-qwen/ and https://akitaonrails.com/2025/04/27/testando-llms-com-aider-na-runpod-qual-usar-pra-codigo/]

### CRITICAL: Aider Model Prefix — ollama_chat/ vs ollama/

Aider documentation says to use `ollama/model-name` but the correct prefix for chat models is `ollama_chat/model-name`. Using the wrong prefix produces completely random, out-of-context responses without any error message.

```bash
# WRONG (as documented — produces garbage output)
aider --model ollama/qwen2.5-coder:32b

# CORRECT
aider --model ollama_chat/qwen2.5-coder:32b
aider --watch-files --model ollama_chat/qwen2.5-coder:7b-instruct
```

### CRITICAL: OLLAMA_API_BASE Must Not End With /

```bash
# WRONG — trailing slash causes intermittent Aider failures
export OLLAMA_API_BASE=http://localhost:11434/

# CORRECT
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_API_BASE=http://localhost:11434
```

### Context Window vs VRAM Budget for Ollama Models

Ollama context length directly consumes VRAM (KV cache). Estimates for Qwen2.5-Coder:32b (65 layers, Q4_K_M):

| num_ctx | Estimated VRAM Required |
|---------|------------------------|
| 6,144   | ~24 GB (fits RTX 4090) |
| 12,288  | ~26 GB (does not fit RTX 4090) |
| 24,576  | ~32 GB |
| 32,768  | ~40 GB (requires A40 or better) |

The `.aider.model.settings.yml` entry for context must not exceed what the GPU can hold:

```yaml
- name: ollama_chat/qwen2.5-coder:7b-instruct
  extra_params:
    num_ctx: 32768  # 7B fits this on RTX 4090
- name: ollama_chat/qwen2.5-coder:32b
  extra_params:
    num_ctx: 6144   # max that fits on RTX 4090 — too small for real use
```

## SOURCE
https://akitaonrails.com/2025/04/29/dissecando-um-modelfile-de-ollama-ajustando-qwen3-pra-codigo/
https://akitaonrails.com/2025/04/25/seu-proprio-co-pilot-gratuito-universal-que-funciona-local-aider-ollama-qwen/
https://akitaonrails.com/2025/04/27/testando-llms-com-aider-na-runpod-qual-usar-pra-codigo/
