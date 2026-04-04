# HEURISTIC: vLLM Over Ollama for LoRA

**DOMAIN:** ai-workflow
**RULE:** When serving local LLM models with LoRA adapters, use vLLM instead of Ollama — Ollama uses a proprietary model format and has limited LoRA support, while vLLM natively loads HuggingFace .safetensors models with LoRA adapters.
**APPLIES WHEN:** Deploying a fine-tuned model locally for AI coding agents (Aider, Crush, OpenCode) or for multi-user inference serving where LoRA adapters need to be loaded alongside the base model.
**RATIONALE:**
1. Ollama wraps models in a proprietary format (not .safetensors), making LoRA attachment non-trivial and poorly documented — this creates friction for any fine-tuning workflow. [explicit]
2. vLLM serves an OpenAI-compatible API (`vllm serve Model --enable-lora --lora-modules name=./lora-dir`), supports HuggingFace model formats directly, and lists the LoRA as a separate "model" in the /v1/models endpoint — any tool that supports OpenAI API can use it transparently. [explicit]
3. For production multi-user serving, vLLM also provides continuous batching and better throughput, and AI coding agents (Aider, Crush) can connect by pointing OPENAI_API_BASE to localhost. [derived]
**COUNTER-INDICATION:** If you don't need LoRA adapters and just want to run a stock model locally with minimal setup, Ollama is simpler and sufficient — `ollama run model` requires no configuration. vLLM has heavier Python dependencies, requires explicit VRAM management (`--max_model_len`), and is more complex to set up.

## OPERATIONAL NOTE: vLLM + LoRA Startup Latency
[extended from: https://akitaonrails.com/2025/05/03/ultimo-tentativa-de-treinar-uma-llm-com-lora-tiro-de-canhao-mas-errando-a-mosca/]

Loading a Qwen3-32B model with a LoRA adapter on vLLM takes 8+ minutes for checkpoint loading — even on an H100 with 80GB VRAM. This is not caused by the LoRA adapter itself (base model without LoRA also takes ~8 minutes for Qwen3-32B). Root cause appears to be I/O-bound shard loading from network volumes. This is a known open issue in vLLM with no resolution as of May 2025.

**Implication:** vLLM + LoRA servers should be treated as slow-start, long-running processes — not daemons that can be cycled between requests. Restart cost is 8–10 minutes; plan accordingly.

**Context window constraint with LoRA:** On H100 80GB VRAM with Qwen3-32B + LoRA adapter, the maximum usable context is ~10k tokens (`--max_model_len 10000`). The default 40k context fails KV cache initialization. This makes the setup unusable with tools like Aider, which require 15k+ tokens for system prompts + code context. Qwen3-14B with LoRA may be a more practical size.

**Port mapping note for RunPod:** vLLM defaults to port 8000. When running on RunPod with only port 8888 exposed (Jupyter default), add `--port 8888` to the vllm serve command explicitly.

## SOURCE
https://akitaonrails.com/2025/05/03/ensinando-zig-mais-recente-pra-sua-llm-treinando-loras-quase/
https://akitaonrails.com/2025/05/03/ultimo-tentativa-de-treinar-uma-llm-com-lora-tiro-de-canhao-mas-errando-a-mosca/
