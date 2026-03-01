# CONCEPT: ComfyUI Model File Taxonomy

**DOMAIN:** ai-image-generation
**DEFINITION:** ComfyUI organizes AI model files into strictly separate subdirectories under `models/`, where each subdirectory defines the functional role of the file — not the file extension. Files with the same extension (`.safetensors`, `.pt`, `.pth`) can be checkpoints, LoRAs, VAEs, ControlNets, embeddings, or text encoders depending only on which subdirectory they live in.
**NOT:** The file extension (`.safetensors`, `.ckpt`, `.pt`, `.pth`) does NOT indicate the model type. A `.safetensors` file may be a full checkpoint, a LoRA adapter, a VAE, a ControlNet, a text encoder, or a style model. The extension only signals which framework can open it (PyTorch), not what role it plays.
**RATIONALE:** Without this explicit definition, a practitioner moving files between directories silently corrupts their workflow — ComfyUI will fail to find or misuse the file, but the error is not obvious because all files have identical extensions. Knowing that directory = role prevents file placement errors and clarifies why the same extension appears across all model types.

---

## REFERENCED BY

- base/heuristicas/heuristic-comfyui-directory-is-role.md
- base/protocolos/protocol-comfyui-workflow-debug.md

## SOURCE
https://akitaonrails.com/2025/04/20/entendendo-o-basico-de-comfyui-pra-gerar-imagens-com-i-a/
