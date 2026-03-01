# CONCEPT: Diffusion Image Generation Pipeline Stages

**DOMAIN:** ai-image-generation
**DEFINITION:** AI image generation via diffusion is a multi-stage pipeline with distinct components: (1) Text Encoder (CLIP/T5) converts the text prompt into an embedding vector; (2) U-Net (Diffusion Model / Checkpoint) performs iterative denoising of a latent starting from random noise, conditioned on the prompt embedding; (3) Scheduler controls how much noise is added/removed per step (sampler algorithms: euler, ddim, plms; scheduler types: normal, klms, dpmsolver); (4) ControlNet optionally injects structural conditions (edges, depth maps, poses) in parallel to the U-Net denoising; (5) VAE decodes the final latent space representation into visible pixels. The process starts from random noise, not a blank canvas — structure emerges through guided denoising, not construction.
**NOT:** Diffusion image generation is NOT analogous to a human drawing on a blank canvas. It is NOT a single-model lookup. The U-Net (checkpoint) is NOT the only model involved — a complete workflow requires text encoder + U-Net + scheduler + VAE, plus optional ControlNet and LoRA adapters. The U-Net does NOT "understand" your prompt directly — the text encoder mediates.
**RATIONALE:** Without naming each stage explicitly, practitioners conflate "the model" with the checkpoint alone and fail to diagnose failures: a bad output may be caused by the wrong VAE, a mismatched text encoder, or a ControlNet that was not supplied proper input — not the checkpoint itself. This concept is prerequisite for correctly selecting and combining model files in a ComfyUI workflow.

---

## REFERENCED BY

- base/conceitos/concept-comfyui-model-taxonomy.md
- base/protocolos/protocol-comfyui-workflow-debug.md

## SOURCE
https://akitaonrails.com/2025/04/20/entendendo-o-basico-de-comfyui-pra-gerar-imagens-com-i-a/
