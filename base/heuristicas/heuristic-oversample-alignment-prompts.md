# HEURISTIC: Oversample Alignment Prompts

**DOMAIN:** ai-workflow
**RULE:** When alignment prompt data is orders of magnitude smaller than the raw training corpus, oversample (repeat) the prompts 50-100x to ensure they influence the model's output bias during LoRA fine-tuning.
**APPLIES WHEN:** Training a LoRA where the structured Q&A alignment prompts are ~8KB but the raw documentation/code corpus is 800KB+ — without oversampling, the corpus dominates and the alignment has no visible effect on the model's responses.
**RATIONALE:** LoRA training adjusts model weights proportionally to the data volume it processes. If alignment prompts represent 1% of training data, they produce ~1% of weight updates, which is insufficient to override the base model's existing training on older versions. Oversampling to 100x via `numpy.random.choice(len(dataset), size=100, replace=True)` makes alignment prompts ~50% of effective training volume, increasing their influence on response patterns. The base model's existing knowledge (e.g., Zig 0.11/0.12) was trained on vastly more data and is "stronger" — repetition compensates for this imbalance. This is analogous to how commercial providers use hundreds of human-written prompt/response pairs to force specific behaviors in alignment.
**COUNTER-INDICATION:** Over-oversampling causes overfitting — the model memorizes alignment answers verbatim and cannot generalize to rephrased questions. If the alignment dataset is already comparable in size to the corpus, oversampling is unnecessary and harmful. Also, oversampled alignment only teaches response patterns, not actual understanding — the model may confidently claim "I know Zig 0.14" while producing non-compiling code.

## SOURCE
https://akitaonrails.com/2025/05/03/ensinando-zig-mais-recente-pra-sua-llm-treinando-loras-quase/
