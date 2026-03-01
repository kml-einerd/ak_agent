# HEURISTIC: LoRA Must Match Checkpoint Base Model

**DOMAIN:** ai-image-generation
**RULE:** Always verify that a LoRA adapter was trained on the same base model architecture as the checkpoint being used — never mix a LoRA trained on SD 1.5 with an SDXL checkpoint, or a Flux LoRA with an SD 1.5 checkpoint.
**APPLIES WHEN:** Loading any LoRA file into a ComfyUI workflow alongside a base checkpoint
**RATIONALE:**
1. A LoRA is trained against the internal weight space of a specific base model — it encodes deltas relative to that model's architecture and token vocabulary. A different base model has a different internal space; the LoRA's deltas map to meaningless dimensions. [explicit]
2. Mixing incompatible LoRA and checkpoint produces output that looks like the LoRA had no effect (best case) or introduces severe artifacts (worst case) — both failures are silent at the node level, with no error raised. [derived]
3. The author uses the analogy: a model is like a "language" — a LoRA trained in German cannot be applied to a Chinese-language model, even if both are valid language models. [explicit]
**COUNTER-INDICATION:** Some LoRAs are explicitly trained for multi-base compatibility (e.g., Flux + SDXL variants released together) — check the CivitAI "base model" field on the LoRA page; if multiple bases are listed, cross-compatibility is intentional.

## SOURCE
https://akitaonrails.com/2025/04/20/entendendo-o-basico-de-comfyui-pra-gerar-imagens-com-i-a/
