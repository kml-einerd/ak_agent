# AKITA VAULT — INDEX
> First file read by akita-agent. Always load this file before any other.
> Load only element files relevant to the current request — not everything.

**Vault root:** `C:\Users\dis\Downloads\KML_mkt\Vídeos e audios CDV\Akita Vault\`
**Knowledge base:** `[vault root]\base\`

---

## HOW TO USE THIS INDEX

1. Read this file completely
2. Identify which domains and types match the current request
3. Load only the relevant element files — do not load elements outside the request scope
4. If uncertain which domain applies, check the DOMAINS section below
5. Never respond before completing the relevant reads

---

## ELEMENTS BY TYPE

### PROCEDURES
| Name | Domain | Trigger | Path |
|------|--------|---------|------|
| Inverted Thinking Orchestration Debug | ai-workflow / architecture | System de orquestração IA falha — tasks, credentials, deploys, outputs | base/procedimentos/procedure-inverted-thinking-orchestration-debug.md |
| Vibe Coding Project Lifecycle | ai-workflow | Starting a new AI-assisted project from scratch | base/procedimentos/procedure-vibe-coding-project-lifecycle.md |
| Error Report for LLM Debugging | ai-workflow | Something breaks during AI-assisted coding session | base/procedimentos/procedure-error-report-llm-debugging.md |
| HSL Color Palette Design | frontend / design-system | Creating a harmonious multi-color palette with light/dark themes | base/procedimentos/procedure-hsl-color-palette-design.md |
| Dual Content Render Pipeline | architecture / content-publishing | Same content needs publishing to both website and email | base/procedimentos/procedure-dual-content-render-pipeline.md |
| Atomic Email Delivery | backend / email | Sending emails to multiple recipients surviving failures and restarts | base/procedimentos/procedure-atomic-email-delivery.md |
| SQLite Atomic Backup | deployment / database | Backing up an active SQLite database without corruption | base/procedimentos/procedure-sqlite-atomic-backup.md |
| Security Audit AI Code | security | AI agent has generated or modified application code | base/procedimentos/procedure-security-audit-ai-code.md |
| File Upload Sanitization Pipeline | security | Application accepts file uploads from users | base/procedimentos/procedure-file-upload-sanitization.md |
| Benchmark-Driven Model Selection | ai-workflow | Choosing an LLM model for a production pipeline processing large volumes | base/procedimentos/procedure-benchmark-driven-model-selection.md |
| Cascading JSON Parse for LLM | ai-workflow | Parsing structured JSON output from an LLM response | base/procedimentos/procedure-cascading-json-parse-llm.md |
| AI Agent Filesystem Sandbox | security | Running any AI coding agent with shell access on your system | base/procedimentos/procedure-ai-agent-sandbox.md |
| LoRA Training for Code LLM | ai-workflow | Adding new language/framework knowledge to a local LLM | base/procedimentos/procedure-lora-training-code-llm.md |
| Two-Pass LLM Script Generation | ai-workflow / content-publishing | Structured content needs transformation into natural TTS-ready spoken script | base/procedimentos/procedure-two-pass-llm-script-generation.md |
| iSCSI Block Device Linux Setup | deployment / infrastructure | Need to mount NAS storage as block device for high-churn workloads | base/procedimentos/procedure-iscsi-block-device-setup.md |
| Cloudflare Tunnel Home Server | security / deployment / self-hosting | Exposing home server services without opening router ports | base/procedimentos/procedure-cloudflare-tunnel-home-server.md |
| Arr Stack Personal Media Server | deployment / self-hosting / media | Building self-hosted automated media acquisition and streaming stack | base/procedimentos/procedure-arr-stack-personal-media-server.md |
| ComfyUI Docker CUDA Setup | ai-image-generation / deployment | Setting up local ComfyUI image generation with NVIDIA GPU | base/procedimentos/procedure-comfyui-docker-setup.md |

### PROTOCOLS
| Name | Domain | Applies To | Path |
|------|--------|------------|------|
| LLM Loop Detection | ai-workflow | LLM stuck in trial-and-error during a coding session | base/protocolos/protocol-llm-loop-detection.md |
| Code Growth Quality Gate | ai-workflow | AI-assisted session with incremental feature additions | base/protocolos/protocol-code-growth-quality-gate.md |
| LLM Subscription Cost Evaluation | ai-workflow | Choosing between LLM subscription plans vs per-token API access | base/protocolos/protocol-llm-subscription-cost.md |
| Email HTML Compatibility | frontend / email | Building HTML emails for cross-client rendering and spam avoidance | base/protocolos/protocol-email-html-compatibility.md |
| Resilient Async Jobs | backend / architecture | Background job system processing important operations | base/protocolos/protocol-resilient-async-jobs.md |
| SQLite vs PostgreSQL Decision | architecture / database | Choosing a database for a new web application | base/protocolos/protocol-sqlite-vs-postgresql.md |
| AI Pair Programming | ai-workflow | Sustained coding session for production-quality software | base/protocolos/protocol-ai-pair-programming.md |
| Layered Rate Limiting | security | Web application with public-facing endpoints | base/protocolos/protocol-layered-rate-limiting.md |
| Graceful Degradation External Dependencies | architecture | Applications depending on optional external systems | base/protocolos/protocol-graceful-degradation-external-deps.md |
| Integration Testing Hierarchy | testing | Multi-service projects sharing data via filesystem or APIs | base/protocolos/protocol-integration-testing-hierarchy.md |
| LLM Sampling for Agent Loops | ai-workflow | Open-source LLM entering an agentic loop | base/protocolos/protocol-llm-sampling-agent-loops.md |
| RAG vs LoRA Knowledge Boundary | ai-workflow | Giving LLM access to knowledge not in its training cutoff | base/protocolos/protocol-rag-vs-lora-knowledge.md |
| Sender Reputation Infrastructure | backend / email | Any app sending programmatic emails via SES or similar | base/protocolos/protocol-sender-reputation-infrastructure.md |
| SES Bounce Complaint Reconciliation | backend / email | App using SES with per-recipient delivery state tracking | base/protocolos/protocol-ses-bounce-complaint-reconciliation.md |
| Zero Trust Access Layer | security / self-hosting | Internal service exposed via public URL needs auth gate | base/protocolos/protocol-zero-trust-access-layer.md |
| ComfyUI Workflow Failure Diagnosis | ai-image-generation | ComfyUI workflow fails or produces wrong output | base/protocolos/protocol-comfyui-workflow-debug.md |
| Aider Architect-Editor Split Mode | ai-workflow | Single LLM producing poor results — reasoning vs coding split | base/protocolos/protocol-aider-architect-editor-mode.md |

### ANTI-PATTERNS
| Name | Domain | Appears As | Path |
|------|--------|------------|------|
| LLM Unsupervised Coding | ai-workflow | "I can watch YouTube while the LLM works" | base/anti-patterns/antipattern-llm-unsupervised-coding.md |
| No Architecture Rules Upfront | ai-workflow | Starting vibe coding without CLAUDE.MD or equivalent | base/anti-patterns/antipattern-no-architecture-rules-upfront.md |
| Reinventing Wheel with LLM | ai-workflow | "LLM can build anything, no need for libraries" | base/anti-patterns/antipattern-reinventing-wheel-llm.md |
| "Funciona Ja" Accumulation | ai-workflow | Add feature, test, works, next — repeat 50 times without refactoring | base/anti-patterns/antipattern-funciona-ja-accumulation.md |
| Vibe Coding Without Expertise | ai-workflow | "AI codes for me, I don't need programming knowledge" | base/anti-patterns/antipattern-vibe-coding-without-expertise.md |
| Frontend Equals Framework | frontend / architecture | "We need React for the frontend" as default assumption | base/anti-patterns/antipattern-frontend-equals-framework.md |
| Catch-All Error Retry | backend / async-jobs | retry_on StandardError with short wait and fixed attempts | base/anti-patterns/antipattern-catch-all-error-retry.md |
| One-Shot Prompt | ai-workflow | "Write a detailed spec, give to AI, get complete system" | base/anti-patterns/antipattern-one-shot-prompt.md |
| Multi-Task Mega Prompt | ai-workflow | Combining fix + refactor + update in a single prompt | base/anti-patterns/antipattern-multi-task-mega-prompt.md |
| NFS/SMB for High-Churn Block Storage | deployment / infrastructure | Redirecting Docker data-root or DB to NFS/SMB share | base/anti-patterns/antipattern-nfs-smb-high-churn-storage.md |
| LLM Anthropomorphized Defaults | ai-workflow | LLM using verbose, emotionally inflected response style in technical context | base/anti-patterns/antipattern-llm-anthropomorphized-defaults.md |
| Cloud API for Professional Image Generation | ai-image-generation | Using ChatGPT/DALL-E for professional reproducible image work | base/anti-patterns/antipattern-chatgpt-image-professional-use.md |
| Aider Auto-Commit on AI Changes | ai-workflow | Aider committing LLM changes automatically without developer review | base/anti-patterns/antipattern-aider-auto-commit.md |
| LoRA Training on Raw Unstructured Text | ai-workflow | Fine-tuning chat-format LLM with raw text training data | base/anti-patterns/antipattern-lora-training-data-raw-text.md |

### CONCEPTS
| Name | Domain | Definition Summary | Path |
|------|--------|--------------------|------|
| Funciona Ja | ai-workflow | Code that "just works" visually but lacks quality and production-readiness | base/conceitos/concept-funciona-ja.md |
| Content-First Architecture | architecture | Design system around content structure, not framework capabilities | base/conceitos/concept-content-first-architecture.md |
| CLAUDE.MD Living Spec | ai-workflow | Persistent project specification that AI agents read at session start | base/conceitos/concept-claude-md-living-spec.md |
| Cooperative Cancellation | architecture | Shared AtomicBool checked at multiple processing points for bounded latency | base/conceitos/concept-cooperative-cancellation.md |
| Pareto 90/10 in Software | ai-workflow | 10% effort produces "working" prototype, 90% makes it production-ready | base/conceitos/concept-pareto-90-10-software.md |
| DevCache for LLM API | ai-workflow | File-based cache for LLM API calls keyed by namespace+hash with TTL | base/conceitos/concept-dev-cache-llm-api.md |
| Implicit Convention LLM Friction | ai-workflow | Implicit conventions (Rails magic) hinder LLM reasoning | base/conceitos/concept-implicit-convention-llm-friction.md |
| Serverless GPU Cold Start | deployment / ai-infrastructure | Designing latency SLAs for serverless GPU inference workers | base/conceitos/concept-serverless-gpu-cold-start.md |
| Block-Level vs File-Level Protocol | deployment / infrastructure | Choosing storage protocol or debugging I/O latency on network storage | base/conceitos/concept-block-vs-file-protocol.md |
| LLM Agent Tool Loop | ai-workflow | Building or debugging LLM agents and tool-calling systems | base/conceitos/concept-llm-agent-tool-loop.md |
| LLM as Lossy Compression | ai-workflow | Establishing correct mental model of what an LLM is | base/conceitos/concept-llm-as-lossy-compression.md |
| Arr Stack Architecture | deployment / self-hosting | Understanding the composable self-hosted media server pattern | base/conceitos/concept-arr-stack-architecture.md |
| ComfyUI Model File Taxonomy | ai-image-generation | Placing or searching for model files in ComfyUI | base/conceitos/concept-comfyui-model-taxonomy.md |
| Diffusion Image Generation Pipeline Stages | ai-image-generation | Understanding diffusion pipeline stages for failure diagnosis | base/conceitos/concept-diffusion-pipeline-stages.md |

### HEURISTICS
| Name | Domain | Rule Summary | Path |
|------|--------|--------------|------|
| Dead Code After Refactoring | ai-workflow | After LLM refactoring, always scan for orphaned dead code | base/heuristicas/heuristic-dead-code-after-refactoring.md |
| I18n Delegated to LLM | ai-workflow | Always delegate internationalization to LLMs | base/heuristicas/heuristic-i18n-delegated-to-llm.md |
| LLMs Default to Worst Performance | ai-workflow | LLMs default to conservative/slow implementations unless told otherwise | base/heuristicas/heuristic-llm-default-worst-performance.md |
| Scope Inflation in Vibe Coding | ai-workflow | Monitor scope — ease of adding features makes creep invisible | base/heuristicas/heuristic-scope-inflation-vibe-coding.md |
| Cron as Safety Net | backend / async-jobs | Always have a cron fallback for critical jobs | base/heuristicas/heuristic-cron-safety-net.md |
| Ambiguous State Never Auto-Retry | backend / email / async-jobs | Never auto-retry operations in ambiguous state | base/heuristicas/heuristic-ambiguous-state-no-retry.md |
| Never Raw-Copy Active SQLite | database / deployment | Use VACUUM INTO, never cp/tar on active SQLite | base/heuristicas/heuristic-never-raw-copy-active-sqlite.md |
| Human What Agent How | ai-workflow | Human decides WHAT, agent decides HOW | base/heuristicas/heuristic-human-what-agent-how.md |
| Agent Never Says No | ai-workflow | Agents implement anything with equal enthusiasm — be your own brake | base/heuristicas/heuristic-agent-never-says-no.md |
| Documentation ROI with AI | ai-workflow | Every hour documenting in CLAUDE.MD saves hours in future sessions | base/heuristicas/heuristic-documentation-roi-with-ai.md |
| TOCTOU Use Atomic Operations | backend | Use atomic SQL, never read-modify-write for concurrent state | base/heuristicas/heuristic-toctou-atomic-operations.md |
| Fail-Fast Production Config | deployment | Crash on missing config — never use fallback defaults for secrets | base/heuristicas/heuristic-fail-fast-production-config.md |
| Bigger Newer Model Not Better | ai-workflow | Don't assume bigger/newer LLM outperforms — benchmark first | base/heuristicas/heuristic-bigger-newer-not-better.md |
| LLM Goldfish Memory | ai-workflow | LLM forgets everything between sessions, repeats same mistakes | base/heuristicas/heuristic-llm-goldfish-memory.md |
| Never LLM Legal Text | ai-workflow | Never let LLM generate legal documents — use official sources | base/heuristicas/heuristic-never-llm-legal-text.md |
| Preflight Structural Validation | testing | Validate LLM output structure before consuming it | base/heuristicas/heuristic-preflight-structural-validation.md |
| LLM Billing as Engineering Metric | ai-workflow | Track LLM API costs per run — 3x cost increase is a performance bug | base/heuristicas/heuristic-llm-billing-as-engineering-metric.md |
| Agent Skills Token Cost | ai-workflow | Each installed skill adds 80-250 tokens to system prompt per session | base/heuristicas/heuristic-agent-skills-token-cost.md |
| Match Model to Its Harness | ai-workflow | Use provider's own agent tool for best results | base/heuristicas/heuristic-match-model-to-harness.md |
| Oversample Alignment Prompts | ai-workflow | Repeat alignment prompts 50-100x when small vs training corpus | base/heuristicas/heuristic-oversample-alignment-prompts.md |
| vLLM Over Ollama for LoRA | ai-workflow | Use vLLM for LoRA adapter serving, not Ollama | base/heuristicas/heuristic-vllm-over-ollama-lora.md |
| Email Prefers At-Most-Once Delivery | backend / email | Designing email delivery state machines with ambiguous outcomes | base/heuristicas/heuristic-email-prefer-at-most-once.md |
| Input Quality Dominates AI Output | ai-workflow | AI pipeline with unsatisfactory output — fix input before swapping model | base/heuristicas/heuristic-input-quality-dominates-ai-output.md |
| Specialized Model Over Generalist | ai-workflow | Selecting a model for single-domain production task | base/heuristicas/heuristic-specialized-model-over-generalist.md |
| Sliding Window Context Is Not Full Recall | ai-workflow | Loading large codebases into LLM context or debugging "forgetting" | base/heuristicas/heuristic-sliding-window-context-limit.md |
| No Open Ports — Tunnel First | security / self-hosting | Exposing home server services to internet | base/heuristicas/heuristic-no-open-ports-tunnel-first.md |
| Disable LLM Persona in Technical Work | ai-workflow | Starting any engineering session with commercial LLM | base/heuristicas/heuristic-disable-llm-persona-technical.md |
| ComfyUI Directory Defines Model Role | ai-image-generation | Downloading any model file for ComfyUI | base/heuristicas/heuristic-comfyui-directory-is-role.md |
| LoRA Must Match Checkpoint Base Model | ai-image-generation | Loading LoRA into ComfyUI workflow alongside a checkpoint | base/heuristicas/heuristic-lora-base-model-compatibility.md |
| Isolate Project Name from Training Corpus | ai-workflow | Starting new AI-assisted project with LLM code generation | base/heuristicas/heuristic-llm-project-namespace-isolation.md |

### REFERENCES
| Name | Domain | When To Consult | Path |
|------|--------|-----------------|------|
| Claude Code Permission Config | ai-workflow | Setting up Claude Code permissions (allow/deny/ask tiers) | base/referencias/reference-claude-code-permissions.md |
| Ollama Modelfile for Code LLMs | ai-workflow | Configuring local LLM for code generation with optimized sampling | base/referencias/reference-ollama-modelfile-code.md |

---

## ELEMENTS BY DOMAIN
> Quick lookup: if request is about domain X, check these files.

### ai-workflow
- **Procedures:** vibe-coding-project-lifecycle, error-report-llm-debugging, benchmark-driven-model-selection, cascading-json-parse-llm, lora-training-code-llm, two-pass-llm-script-generation
- **Protocols:** llm-loop-detection, code-growth-quality-gate, llm-subscription-cost, ai-pair-programming, llm-sampling-agent-loops, rag-vs-lora-knowledge, aider-architect-editor-mode
- **Anti-Patterns:** llm-unsupervised-coding, no-architecture-rules-upfront, reinventing-wheel-llm, funciona-ja-accumulation, vibe-coding-without-expertise, one-shot-prompt, multi-task-mega-prompt, llm-anthropomorphized-defaults, aider-auto-commit, lora-training-data-raw-text
- **Concepts:** funciona-ja, claude-md-living-spec, pareto-90-10-software, dev-cache-llm-api, implicit-convention-llm-friction, llm-agent-tool-loop, llm-as-lossy-compression
- **Heuristics:** dead-code-after-refactoring, i18n-delegated-to-llm, llm-default-worst-performance, scope-inflation-vibe-coding, human-what-agent-how, agent-never-says-no, documentation-roi-with-ai, bigger-newer-not-better, llm-goldfish-memory, never-llm-legal-text, llm-billing-as-engineering-metric, agent-skills-token-cost, match-model-to-harness, oversample-alignment-prompts, vllm-over-ollama-lora, input-quality-dominates-ai-output, specialized-model-over-generalist, sliding-window-context-limit, disable-llm-persona-technical, llm-project-namespace-isolation
- **References:** claude-code-permissions, ollama-modelfile-code

### security
- **Procedures:** security-audit-ai-code, file-upload-sanitization, ai-agent-sandbox, cloudflare-tunnel-home-server
- **Protocols:** layered-rate-limiting, zero-trust-access-layer
- **Heuristics:** no-open-ports-tunnel-first

### frontend
- **Procedures:** hsl-color-palette-design
- **Protocols:** email-html-compatibility
- **Anti-Patterns:** frontend-equals-framework

### backend
- **Procedures:** atomic-email-delivery
- **Protocols:** resilient-async-jobs, sender-reputation-infrastructure, ses-bounce-complaint-reconciliation
- **Anti-Patterns:** catch-all-error-retry
- **Heuristics:** toctou-atomic-operations, cron-safety-net, ambiguous-state-no-retry, email-prefer-at-most-once

### architecture
- **Procedures:** dual-content-render-pipeline
- **Protocols:** sqlite-vs-postgresql, graceful-degradation-external-deps
- **Concepts:** content-first-architecture, cooperative-cancellation

### database / deployment
- **Procedures:** sqlite-atomic-backup, iscsi-block-device-setup
- **Anti-Patterns:** nfs-smb-high-churn-storage
- **Concepts:** block-vs-file-protocol, serverless-gpu-cold-start
- **Heuristics:** never-raw-copy-active-sqlite, fail-fast-production-config

### self-hosting
- **Procedures:** cloudflare-tunnel-home-server, arr-stack-personal-media-server
- **Protocols:** zero-trust-access-layer
- **Concepts:** arr-stack-architecture
- **Heuristics:** no-open-ports-tunnel-first

### ai-image-generation
- **Procedures:** comfyui-docker-setup
- **Protocols:** comfyui-workflow-debug
- **Anti-Patterns:** chatgpt-image-professional-use
- **Concepts:** comfyui-model-taxonomy, diffusion-pipeline-stages
- **Heuristics:** comfyui-directory-is-role, lora-base-model-compatibility

### testing
- **Protocols:** integration-testing-hierarchy
- **Heuristics:** preflight-structural-validation

---

## ENRICHMENT STATUS

Last enrichment pass: 2026-02-28
Elements enriched: 18 (14 constraint, 2 rationale, 2 reclassification)
Enrichment log: `base\ENRICHMENT-LOG.md`

---

## EXTRACTION HISTORY

| Date | Source | Elements Created |
|------|--------|-----------------|
| 2026-02-28 | source-blog.md (17 articles from akitaonrails.com) | 63 elements (12 procedures, 12 protocols, 9 anti-patterns, 7 concepts, 21 heuristics, 2 references) |
| 2026-03-01 | links.md (13 articles from akitaonrails.com) | 31 new + 4 extended = 94 total (17 procedures, 17 protocols, 14 anti-patterns, 14 concepts, 30 heuristics, 2 references) |
