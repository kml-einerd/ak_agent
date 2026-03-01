# PROTOCOL: ComfyUI Workflow Failure Diagnosis

**DOMAIN:** ai-image-generation
**APPLIES TO:** ComfyUI workflow that fails to run, produces wrong output, or shows unexpected results after loading a community workflow or changing model files
**RATIONALE:**
1. Community workflows are built against specific model files that may not exist locally — errors appear as red-bordered nodes or missing file warnings in the console, not as user-facing error dialogs. [explicit]
2. Each pipeline stage (text encoder, U-Net/checkpoint, ControlNet, VAE, LoRA, upscaler) can fail independently, so diagnosis must isolate which stage is failing. [derived]
3. Model file naming inconsistencies between community workflows (which embed expected filenames) and actual downloaded files mean that compatible-but-differently-named files require manual node reconfiguration. [derived]

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Node shows red border when workflow runs | Model file required by that node is missing from its `models/<subdir>` | Identify filename from node config, download from Hugging Face or CivitAI, place in correct subdirectory, reload workflow |
| Console shows crash without UI error message | An extension (`custom_nodes/<ext>`) has a Python error, possibly Python version mismatch | Check terminal output, identify extension, remove from `custom_nodes/` or delete VENV and rebuild |
| Workflow runs but output image looks wrong (wrong style, wrong pose) | ControlNet input map (depth/canny/pose) not properly populated, or LoRA activation keyword missing from prompt | Verify ControlNet node has correct preprocessor model; check CivitAI page for the LoRA's activation trigger word and add to prompt |
| LoRA loaded but has no visible effect on output | LoRA activation keyword not present in positive prompt | Find the LoRA's documented trigger word on its CivitAI page; add it at the start of the prompt in the text node |
| LoRA is architecturally incompatible with checkpoint | LoRA was trained on a different base model (e.g., SD1.5 LoRA used with SDXL checkpoint) | Match LoRA base model to checkpoint base model — check both CivitAI pages for the "base model" field |
| Output has artifacts from background of ControlNet edge/depth map | Preprocessor captured background noise as structure | Adjust ControlNet preprocessor threshold parameters; optionally use SAM to mask the subject before preprocessing |

**TRADE-OFFS:** Systematic per-node diagnosis is thorough but time-intensive. Experienced users skip to the most likely failure (missing file vs. wrong activation keyword) based on observed symptom.

**ESCALATE WHEN:** The workflow was built for a specific ComfyUI version and uses deprecated custom nodes — requires finding an updated community fork or rebuilding the workflow from scratch with current nodes.

## SOURCE
https://akitaonrails.com/2025/04/20/entendendo-o-basico-de-comfyui-pra-gerar-imagens-com-i-a/
https://akitaonrails.com/2025/04/20/gerando-imagens-com-i-a-ate-estilo-ghibli-com-docker-e-cuda/
