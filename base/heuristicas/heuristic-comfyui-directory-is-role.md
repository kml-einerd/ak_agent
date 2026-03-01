# HEURISTIC: ComfyUI Directory Defines Model Role

**DOMAIN:** ai-image-generation
**RULE:** In a ComfyUI installation, always determine a model file's role by the subdirectory it belongs to, never by its file extension — and always place downloaded model files into the correct subdirectory before starting the workflow.
**APPLIES WHEN:** Downloading any AI model file (checkpoint, LoRA, VAE, ControlNet, text encoder, upscaler, SAM, style model, embedding) for use in ComfyUI
**RATIONALE:**
1. All model file types share the same extensions (`.safetensors`, `.pt`, `.pth`) — the extension encodes only the serialization format, not the functional role. [explicit]
2. ComfyUI nodes enumerate files only from their designated subdirectory — a LoRA file placed in `checkpoints/` will not appear in the "Load LoRA" node selector, causing silent failure with no obvious error message. [explicit]
3. Because failure is silent (node just shows an empty selector), misplaced files lead to wasted GPU runs and hours of debugging before the root cause is identified. [derived]
**COUNTER-INDICATION:** Does not apply when using external tools (Automatic1111, InvokeAI) that may have different directory conventions — always verify the target tool's own folder structure before placing files.

## SOURCE
https://akitaonrails.com/2025/04/20/entendendo-o-basico-de-comfyui-pra-gerar-imagens-com-i-a/
