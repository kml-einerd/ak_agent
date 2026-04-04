# PROCEDURE: Benchmark-Driven Model Selection

**TRIGGER:** Choosing an LLM model (vision, text, embedding) for a production pipeline that will process large volumes of data
**DOMAIN:** ai-workflow
**PRE-CONDITIONS:** Task is well-defined enough to create ground truth labels; multiple candidate models available; cost of wrong choice is significant (days of wasted processing)

---

## STEPS

1. Build a ground truth corpus with representative samples (Akita: 94 files — images, audio, video, documents) and manually label each with correct classification in structured format (JSON) → measurable accuracy baseline exists
2. Design benchmark phases answering specific questions: (a) metadata extraction cost, (b) model accuracy per task type, (c) OCR engine comparison, (d) pipeline integration, (e) cost projection for real workload → each phase has a clear question and measurable answer
3. Run each candidate model against the corpus with identical prompts, measuring: task accuracy, JSON validity rate, latency per item, and cost → comparable metrics across models
4. Run multiple repetitions (minimum 3) for statistical significance with confidence intervals → results are not flukes of single runs
5. Calculate cost projection for real workload using measured timings: extrapolate from corpus to production scale (Akita: 94 files → 5K/50K/500K scenarios with time and electricity cost) → informed go/no-go decision before building
6. Build a minimal PoC implementing the winning pipeline end-to-end (Akita: 754 lines Python) to validate the full chain works before investing in production code → pipeline validated before production build

**ON_FAILURE[step-3]:** If a model produces consistently invalid output (truncated JSON, malformed responses), this is a disqualifying regression regardless of accuracy on valid outputs
**ON_FAILURE[step-5]:** If projected cost is prohibitive (e.g., $5000 in API calls vs $34 in local GPU electricity), re-evaluate architecture (local vs cloud)

---

## DONE WHEN
- Model selected based on measured benchmark data with confidence intervals from 3+ repetitions (not blog posts or intuition)
- PoC validates the full pipeline end-to-end with zero errors on the ground truth corpus
- Cost projection confirms feasibility at production scale (extrapolated from measured per-item timing to target volume)

## SOURCE
https://akitaonrails.com/2026/02/23/vibe-code-fiz-um-indexador-inteligente-de-imagens-com-ia-em-2-dias/
