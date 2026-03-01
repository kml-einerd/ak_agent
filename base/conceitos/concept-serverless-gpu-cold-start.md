# CONCEPT: Serverless GPU Cold Start

**DOMAIN:** deployment / ai-infrastructure
**DEFINITION:** The latency incurred when a serverless GPU worker activates from idle state and loads a model's weights from disk (or network volume) into VRAM before the first inference can execute. For a ~4GB model on RunPod serverless with a Network Volume, cold start is the VRAM-loading time (not download time) — typically 30–90 seconds.
**NOT:** Cold start is NOT the same as model download time. When model weights are stored on a persistent Network Volume (not pulled from a registry on each activation), cold start is only the disk-to-VRAM loading step, which is deterministic and bounded. It is also NOT a bug to be eliminated — it is a cost/availability tradeoff: serverless charges only for active inference time, so cold starts are the price of not paying for an always-on GPU.
**RATIONALE:** Without this distinction, engineers either over-provision (keep a GPU warm at all times, paying idle cost) or under-estimate latency (assuming cold start ≈ 0). Knowing cold start is bounded and distinct from download time enables correct SLA design: queue requests during cold start rather than treating the timeout as a failure.

---

## REFERENCED BY

- base/procedimentos/procedure-two-pass-llm-script-generation.md
- base/protocolos/protocol-graceful-degradation-external-deps.md

## SOURCE
https://akitaonrails.com/2026/02/18/servindo-ia-na-nuvem-meu-tts-pessoal-bastidores-do-the-m-akita-chronicles/
