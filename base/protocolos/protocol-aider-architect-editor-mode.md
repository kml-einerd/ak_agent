# PROTOCOL: Aider Architect-Editor Split Mode

**DOMAIN:** ai-workflow
**APPLIES TO:** AI coding sessions where a single model produces poor results — either reasoning well but generating bad code, or generating good code but failing to understand the problem.
**RATIONALE:**
1. Different LLMs have different strengths: reasoning models (o1, o4) are strong at analyzing a problem and producing a verbal plan, but weak at emitting code in the exact format Aider expects. Code models (Gemini, Claude) are strong at producing precise code when given a clear specification. [explicit]
2. Splitting the task so the "architect" model reasons and the "editor" model codes leverages each model's strength. [derived]
3. The Aider `--architect` flag was originally designed for OpenAI o1, which reasoned well but coded poorly. [explicit]
4. The cost implication is real: two models are called per turn, doubling token spend — so this mode should be reserved for genuinely complex tasks where a single model is demonstrably failing. [derived]

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Single model reasons correctly (explains what to do) but produces wrong code | Model has strong reasoning but weak code generation in Aider's diff format | Set architect = current model, set editor = strong code model (Gemini, Claude) |
| Single model produces code but misunderstands the problem or omits edge cases | Model has weak planning but strong code generation | Set architect = strong reasoning model (OpenAI o4, o1), set editor = current model |
| Model fails on complex multi-file refactor but succeeds on simple edits | Complexity overloads single model | Use architect mode for complex tasks; revert to single model for simple ones |
| Token cost spike with no quality improvement | Architect mode overhead not justified | Return to single model; redesign the prompt instead |

**TRADE-OFFS:** Better results on complex tasks / Double token cost per turn. Architect mode adds latency (two sequential API calls). Not all model combinations work — the editor model must understand Aider's SEARCH/REPLACE diff format.

**ESCALATE WHEN:** Both architect and editor models fail to produce correct code after 3+ rounds — this indicates the task requires knowledge not in the training data (new library version, undocumented API). Switch to manual coding with LLM as reviewer only.

### Commands

```bash
# Architect = GPT o4, Editor = Gemini
aider --watch-files --architect --editor-model gemini

# Architect = Claude Sonnet, Editor = Claude Sonnet (same model, both roles)
export ANTHROPIC_API_KEY=your-key
aider --sonnet --architect

# Architect = OpenAI, Editor = local Ollama model
aider --watch-files --architect --editor-model ollama_chat/qwen2.5-coder:7b-instruct
```

### Model Settings for Architect Mode (Claude Sonnet 3.7 with thinking)

```yaml
# $HOME/.aider.model.settings.yml
- name: anthropic/claude-3-7-sonnet-20250219
  edit_format: diff
  weak_model_name: anthropic/claude-3-5-haiku-20241022
  use_repo_map: true
  examples_as_sys_msg: true
  use_temperature: false
  extra_params:
    extra_headers:
      anthropic-beta: prompt-caching-2024-07-31,pdfs-2024-09-25,output-128k-2025-02-19
    max_tokens: 64000
    thinking:
      type: enabled
      budget_tokens: 32000
    cache_control: true
  editor_model_name: anthropic/claude-3-7-sonnet-20250219
  editor_edit_format: editor-diff
```

## SOURCE
https://akitaonrails.com/2025/04/25/seu-proprio-co-pilot-gratuito-universal-que-funciona-local-aider-ollama-qwen/
