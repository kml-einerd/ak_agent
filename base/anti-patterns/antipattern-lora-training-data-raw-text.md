# ANTI-PATTERN: LoRA Training on Raw Unstructured Text

**DOMAIN:** ai-workflow
**APPEARS AS:** Feed the LLM raw documentation, release notes, and code examples as flat text for LoRA training — the model learns the content, which is the goal.
**ROOT CAUSE:** Chat-format models (instruction-tuned, using ChatML or similar token formats like `<|im_start|>` / `<|im_end|>`) are fine-tuned on structured conversation pairs. When trained on raw flat text without these delimiters, the model learns that "a response" can be an arbitrarily long document — it never learns where an answer ends. This causes the model to enter circular generation: it produces text indefinitely, exhausting the context window without ever returning a final answer.
**RATIONALE:**
1. After LoRA training on raw docs without `<|im_end|>` delimiters, the Qwen3-32B model entered circular thinking — it started generating tokens but never stopped, crashing due to context overflow rather than returning an answer. [explicit]
2. The model "probably thought the entire text was a response and has to respond that long." [explicit]
3. Instruction-tuned base models have a strong prior that responses are bounded by chat tokens. Overriding this prior with raw training data that lacks those tokens shifts the distribution toward unbounded generation. [derived]
4. The alignment prompts (prompt/completion pairs) help but cannot compensate if the majority of training data (documentation) lacks proper turn delimiters. [derived]

---

## SYMPTOMS

- After LoRA fine-tuning, model generates tokens continuously with `stream=true` but never returns a complete response
- Context window fills up and crashes (CUDA OOM or context overflow error) mid-generation
- Model responds correctly to simple factual questions ("what version do you know?") but fails on generative tasks ("write a program that...")
- Disabling `enable_thinking` or reducing temperature does not stop the runaway generation

## CORRECTION

Structure all training data as chat-format conversation pairs with explicit turn delimiters:

```
<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
What is [concept from the docs]?<|im_end|>
<|im_start|>assistant
[answer derived from the docs]<|im_end|>
```

Decompose documentation into small, self-contained Q&A pairs rather than loading entire documents as a single training sample. Each pair should cover one concept, one function, or one example — not a full chapter.

**NOT TO CONFUSE WITH:** Alignment prompt oversampling (the intentional 100x repetition of prompt/completion pairs). That technique compensates for small alignment prompt size relative to the corpus. The correction here is about the format of ALL training data, including the documentation corpus itself.

## SOURCE
https://akitaonrails.com/2025/05/03/ultimo-tentativa-de-treinar-uma-llm-com-lora-tiro-de-canhao-mas-errando-a-mosca/
