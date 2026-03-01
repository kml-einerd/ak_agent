# ANTI-PATTERN: Cloud API for Professional Image Generation

**DOMAIN:** ai-image-generation
**APPEARS AS:** Using ChatGPT, DALL-E, or similar closed API image generators for professional or production image work — "it generates images, so it's a generation tool like any other"
**ROOT CAUSE:** Closed-API generators apply unpredictable, non-configurable content moderation that can silently refuse generation mid-workflow with no override path. The practitioner has zero control over the diffusion pipeline stages, model selection, ControlNet conditions, LoRA adapters, upscale models, or sampling parameters — all decisions are black-boxed behind the API.
**RATIONALE:**
1. Content moderation on closed APIs refuses generation non-deterministically — the same prompt and image may be accepted one day and refused the next, citing copyright, privacy, or safety policies that cannot be appealed or configured. [explicit]
2. Professional use requires reproducibility: a workflow that produces a result today must produce a comparable result tomorrow. Non-deterministic refusals break reproducibility at the production level. [derived]
3. Closed APIs expose no pipeline controls (no ControlNet, no custom LoRA, no KSampler configuration, no VAE swap) — maximum output quality is permanently capped at the API provider's defaults. [derived]

---

## SYMPTOMS

- Workflow fails intermittently when uploading photos of real people, fictional characters, drawings, or proprietary assets
- Output style cannot be tuned — same prompt yields inconsistent aesthetic across runs
- Generation of specific subjects (faces, logos, distinctive styles) is refused without actionable error

## CORRECTION

Deploy a local ComfyUI workflow via Docker with CUDA, giving full pipeline control: choose checkpoint, LoRA, ControlNet, VAE, sampler, and all conditioning inputs. Models from Hugging Face and CivitAI replace closed API calls. See: `base/procedimentos/procedure-comfyui-docker-setup.md`

**NOT TO CONFUSE WITH:** Using closed APIs for rapid prototyping or exploration where reproducibility and content control are not required — for casual use the tradeoff is acceptable.

## SOURCE
https://akitaonrails.com/2025/04/20/gerando-imagens-com-i-a-ate-estilo-ghibli-com-docker-e-cuda/
