# PROCEDURE: LoRA Training for Code LLM

**TRIGGER:** Need to add knowledge about a new language version, framework, or private API to a local LLM that is missing from its training cutoff
**DOMAIN:** ai-workflow
**PRE-CONDITIONS:** GPU with sufficient VRAM (24GB+ for 8B models), Python with unsloth/transformers/trl installed, base model available on HuggingFace, training material gathered

---

## STEPS

1. Gather training material (documentation, release notes, code examples, cookbooks) and convert HTML to clean Markdown/text via html2text → raw_data directory with structured files (expect ~800KB+ for a single language version)
2. Create alignment prompts as JSON with "prompt"/"completion" pairs covering key questions about the new knowledge, in multiple phrasings per topic → training-prompts.json (~8KB minimum)
3. Oversample alignment prompts (100x via numpy random_choice with replace=True) to compensate for their small size relative to documentation corpus → oversampled dataset that influences model bias toward new knowledge
4. Concatenate all datasets (docs + release notes + code examples + oversampled prompts) into a combined HuggingFace dataset using concatenate_datasets → single combined_dataset
5. Tokenize the combined dataset using the base model's tokenizer with truncation=True → tokenized_dataset ready for training
6. Configure SFTConfig (num_train_epochs=5 for small datasets, learning_rate=2e-4, max_seq_length=2048, optim="adamw_8bit", bf16=True) and run SFTTrainer → LoRA adapter files saved to output directory (~3-4GB for 8B model)
7. Serve the LoRA-augmented model using vLLM (`vllm serve Qwen/Qwen3-8B --enable-lora --lora-modules ziglora=./lora-dir --max_model_len 8192`) → OpenAI-compatible API endpoint with LoRA loaded as separate model

**ON_FAILURE[step-6]:** If VRAM OOM, reduce training material size (remove largest corpus like stdlib — 15MB stdlib caused OOM on RTX 4090), reduce per_device_train_batch_size, or use a remote GPU (RunPod A40/H100 with 40-80GB VRAM)
**ON_FAILURE[step-7]:** If Ollama is the only option, note that Ollama has limited LoRA support due to proprietary model format; prefer vLLM for LoRA serving
**ON_FAILURE[step-3]:** If alignment prompts are insufficient (model generates correct "I know version X" but produces wrong code), write more diverse prompt/completion pairs manually — alignment creates response patterns, not actual understanding

---

## DONE WHEN
The LoRA-augmented model responds correctly to questions about the new knowledge (e.g., "which version of Zig do you know?" → "0.14.0") AND the knowledge is embedded in the model weights (no context injection needed per session). Note: aligned responses confirm training worked but do not guarantee code correctness — verify with actual compilation/test runs.

## EXTENSION: H100 VRAM Constraints and Chat-Token Format
[extended from: https://akitaonrails.com/2025/05/03/ultimo-tentativa-de-treinar-uma-llm-com-lora-tiro-de-canhao-mas-errando-a-mosca/]

### H100 80GB VRAM constraints for Qwen3-32B

Scaling to H100 (80GB VRAM) on RunPod: even with 1MB dataset (not the full 15MB stdlib), training consumed ~75GB of the 80GB. The stdlib corpus (15MB) caused OOM even on H100. Practical ceiling: ~1MB training data for Qwen3-32B on H100. If more training data is needed, drop to Qwen3-14B.

**Cost reference:** RunPod H100 SXM = USD 3/hour. A Qwen3-32B LoRA training run on 1MB dataset takes ~5–6 hours = ~USD 15–18 per training run.

### CRITICAL: Training Data Chat-Token Format Requirement

All training data (not just alignment prompts) MUST be formatted as chat-format conversation pairs with explicit turn delimiters matching the base model's chat template (ChatML for Qwen3):

```
<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
[question about a concept in the documentation]<|im_end|>
<|im_start|>assistant
[answer derived from the documentation]<|im_end|>
```

Failure to format training data this way causes circular generation after training — the model generates tokens indefinitely and crashes the context window. See `antipattern-lora-training-data-raw-text.md`.

### Serving: H100 + Qwen3-32B + LoRA Context Ceiling

Maximum usable context when serving Qwen3-32B with LoRA on H100 80GB:

```bash
# Max that initializes without KV cache failure
vllm serve Qwen/Qwen3-32B \
  --enable-lora \
  --lora-modules ziglora=./qwen3-zig-lora \
  --max_model_len 10000 \
  --port 8888
```

10k token context is insufficient for agentic tools (Aider needs 15k+ for system prompts alone). Qwen3-14B with LoRA is a more practical serving target.

## SOURCE
https://akitaonrails.com/2025/05/03/ensinando-zig-mais-recente-pra-sua-llm-treinando-loras-quase/
https://akitaonrails.com/2025/05/03/ultimo-tentativa-de-treinar-uma-llm-com-lora-tiro-de-canhao-mas-errando-a-mosca/
