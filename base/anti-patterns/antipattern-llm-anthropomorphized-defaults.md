# ANTI-PATTERN: LLM Anthropomorphized Defaults

**DOMAIN:** ai-workflow
**APPEARS AS:** ChatGPT or similar LLM behaves in a friendly, empathetic, emotionally responsive manner. It uses affirmations ("Great question!"), expresses concern, pauses to acknowledge feelings. To non-technical users and journalists this looks like evidence of consciousness or sentience — it "seems alive." Technical users accept it as the default interaction mode without questioning it.
**ROOT CAUSE:** The model's default behavior is shaped by RLHF fine-tuning and system prompt scaffolding that intentionally add a "personality layer" on top of the base model. This layer is not emergent intelligence — it is a set of pre-recorded behavioral patterns reinforced during training to maximize engagement and user retention metrics, not to maximize accuracy or directness. The anthropomorphized behavior misleads users about the nature of what they are interacting with.
**RATIONALE:**
1. The personality layer is not the model — it is a behavioral overlay configured by the provider. Akita describes it as "pre-recorded phrases," not genuine emotion or reasoning. The user is interacting with a statistical compression of text (an LLM as "JPEG of ZIP" — lossy data compression), not a reasoning entity. [explicit]
2. When technical users accept the anthropomorphized default without disabling it, they inherit verbosity, hedging, sassy remarks, and unnecessary affirmations in every response — all of which increase token consumption, reduce precision, and obscure whether the model actually understood the request. [derived]
3. Non-technical users who never learn to disable this layer form false mental models about AI capabilities, causing downstream harms: trusting AI output uncritically, believing the AI "cares" about their problem, or assuming the AI has intrinsic ethical constraints it generates rather than ones that were imposed. [derived]

---

## SYMPTOMS

- LLM begins responses with "Great question!" or similar engagement openers not present in the prompt
- LLM adds unprompted emotional content ("I understand this must be frustrating…")
- LLM produces long preambles before reaching the actual answer
- LLM refuses tasks citing "values" it infers rather than explicit content policies
- Non-technical stakeholders describe the AI as "understanding" or "caring" based on interaction style

## CORRECTION

Disable the personality layer explicitly via the provider's customization interface. In ChatGPT: **Account icon → Customize the ChatGPT** → provide a direct instruction in the persona field, for example:

> "You are an assistant to software engineering. I am a senior software engineer. Answer questions directly, without verbosity, using as few words as possible for the most exact answer possible. I don't need you to be friendly, I don't need sassy remarks."

For API usage, place an equivalent directive at the top of the system prompt before any other instructions. Confirm effectiveness by checking that responses no longer include unsolicited affirmations or emotional content.

**NOT TO CONFUSE WITH:** Legitimate use of a conversational tone in user-facing products where a human-friendly style is a product requirement (e.g., a customer service chatbot). The anti-pattern applies specifically when working in technical or engineering contexts where precision and brevity are the primary requirements, and the persona overhead is pure waste.

## OPERATIONAL CONSTRAINTS
**FOR efficient LLM interaction in technical contexts TO SUCCEED:**

NEVER:
- Accept the default personality layer in technical/engineering LLM sessions [explicit — CORRECTION: "Disable the personality layer explicitly"]
- Interpret LLM affirmations ("Great question!") or emotional responses as evidence of understanding [explicit — ROOT CAUSE: "pre-recorded behavioral patterns reinforced during training"]

ALWAYS:
- Configure a direct, minimal persona via system prompt or provider customization before starting work [explicit — CORRECTION]
- Verify effectiveness by checking that responses contain no unsolicited affirmations or emotional content [explicit — CORRECTION: "Confirm effectiveness"]

GATE: System prompt or provider customization includes a directive for direct, non-verbose responses. If false, configure persona before proceeding.

## SOURCE
https://akitaonrails.com/2025/04/28/destruindo-a-personalidade-do-chatgpt-4o/
