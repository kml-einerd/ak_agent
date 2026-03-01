# PROTOCOL: Graceful Degradation External Dependencies

**DOMAIN:** architecture
**APPLIES TO:** Applications that depend on external systems (OCR engines, ML models, hardware-specific features, optional services) where some dependencies may not be available on all target platforms or installations
**RATIONALE:** Hard dependencies on external systems make applications fragile and limit their audience. If every dependency is mandatory, the app fails completely when any one is missing. By classifying dependencies as hard (required) or soft (optional with fallback), the application functions in degraded but usable mode when optional dependencies are absent. Users get value immediately and can install optional components for enhanced functionality.

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Dependency is essential for core functionality (e.g., Ollama for LLM classification) | Hard requirement — no meaningful fallback exists | Fail visibly at startup with clear error message and installation guide (SetupModal) |
| Dependency improves quality but alternative exists (e.g., Surya OCR vs Ollama Vision for text extraction) | Soft requirement with fallback chain | Implement fallback: try preferred → if unavailable, use alternative → show user advisory, not error |
| Dependency is platform-specific (e.g., xclip on Linux, pbcopy on macOS, PowerShell on Windows) | Platform abstraction needed | Isolate in platform/ module; detect OS at runtime; each platform provides equivalent functionality |
| Dependency requires separate installation (Python venv, native binary per OS) | Provisioning complexity | Auto-provision on first use with progress indication (create venv, pip install, download binary); bundle what can be bundled |
| Hardware capability varies (GPU VRAM, unified memory, no GPU) | Hardware-aware selection needed | Detect hardware at startup (nvidia-smi, system_profiler, sysinfo); select configuration tier (small/medium/large) automatically |

**TRADE-OFFS:** Fallback chains increase code complexity and testing surface (must test each fallback path). Quality may be lower in degraded mode (Ollama Vision has 58% text coverage vs Surya's 83%). But the application is usable by more people on more hardware configurations.

**ESCALATE WHEN:** The degraded mode produces results so poor that they mislead users. In that case, make the dependency hard rather than providing a false sense of functionality. Better to fail clearly than to succeed misleadingly.

## SOURCE
https://akitaonrails.com/2026/02/23/vibe-code-fiz-um-indexador-inteligente-de-imagens-com-ia-em-2-dias/
