# HEURISTIC: Input Quality Dominates AI Output

**DOMAIN:** ai-workflow
**RULE:** For AI generation tasks, input quality determines output quality more than model selection. Invest in input preparation before evaluating model upgrades.
**APPLIES WHEN:** Any AI pipeline producing generative output (TTS, image generation, text summarization, code generation) where output quality is unsatisfactory and the first instinct is to swap the model.
**RATIONALE:**
1. For TTS specifically: if the reference audio sample cuts the first syllable, every generated voice will cut the first syllable. If the script uses generic filler phrases, the generated audio will sound generic. The model faithfully reproduces what it receives — it cannot compensate for bad input. [explicit]
2. The same principle generalizes: an LLM given a vague prompt produces a vague output; a TTS model given a poorly punctuated script produces awkward pauses. The model amplifies input structure, it does not repair it. [derived]
3. Model swaps are expensive (evaluation time, integration cost, regression risk) and often produce marginal gains over fixing the input. Input quality improvements are cheap and produce compounding returns across all future runs. [derived]
**COUNTER-INDICATION:** Does not apply when the input is already well-structured and the output failure is a known model capability gap (e.g., a language the model was not trained on, or a domain outside its knowledge cutoff).

## SOURCE
https://akitaonrails.com/2026/02/18/servindo-ia-na-nuvem-meu-tts-pessoal-bastidores-do-the-m-akita-chronicles/
