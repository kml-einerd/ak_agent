# PROCEDURE: Two-Pass LLM Script Generation

**TRIGGER:** Structured content (newsletter, article, documentation) needs to be transformed into natural spoken-word audio script for TTS synthesis
**DOMAIN:** ai-workflow / content-publishing
**PRE-CONDITIONS:** Source content is available in text form. LLM API access is configured. TTS model is ready to consume the output script.

---

## STEPS

1. Pass 1 — Structural conversion: send the source content to LLM with instruction to convert it into dialogue format, preserving ALL content, changing only form → output is a structured script with speakers, natural sentence breaks, and spoken transitions. Do NOT allow the LLM to summarize, omit, or paraphrase content in this pass.
2. Validate Pass 1 output: confirm all source content items are present in the script, no facts were dropped, speaker turns are correctly attributed → proceed only if content integrity check passes
3. Pass 2 — Naturalization: send the structured script from Pass 1 to LLM with instruction to make it sound natural for spoken delivery — rewrite overly formal sentences, adjust rhythm, add spoken filler phrases where appropriate → output is a script optimized for TTS
4. Review Pass 2 output for quality: check that no content was lost during naturalization, spoken rhythm sounds natural when read aloud → this is the final script sent to TTS

**ON_FAILURE[step-1]:** If LLM summarizes or omits content, add explicit constraint: "DO NOT summarize. Every item from the source must appear in the script. If you cannot fit all content, split into multiple scripts."
**ON_FAILURE[step-2]:** If content integrity check fails, rerun Pass 1 with stricter instruction. Do not proceed to Pass 2 with incomplete content.
**ON_FAILURE[step-3]:** If naturalization introduces factual errors or drops content, roll back to Pass 1 output and use it directly as the TTS script, accepting lower naturalness.

---

## DONE WHEN
- Script contains all content from the source material (verified by cross-checking every item from the source against the final script)
- Script reads naturally when spoken aloud with no awkward formal phrasing (verified by reading a sample section aloud)
- TTS synthesis produces audio without unnatural pauses, clipped syllables, or abrupt transitions

## SOURCE
https://akitaonrails.com/2026/02/18/servindo-ia-na-nuvem-meu-tts-pessoal-bastidores-do-the-m-akita-chronicles/
