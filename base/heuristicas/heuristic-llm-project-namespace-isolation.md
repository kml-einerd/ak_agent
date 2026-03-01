# HEURISTIC: Isolate Project Name from Training Corpus

**DOMAIN:** ai-workflow
**RULE:** Never name a project with the same name (or a substring) of a well-known open-source library or framework — the LLM will conflate the project with its training data for the real library and produce wrong code.
**APPLIES WHEN:** Starting a new AI-assisted project where an LLM will be given the codebase as context and asked to generate or modify code.
**RATIONALE:**
1. LLMs are trained on vast corpora where well-known projects appear in thousands of examples. When the LLM sees a file in a project called "my-react" or "qwen-cli," it has competing signals: the provided context (your code) and the dense training data for React.js or Qwen's actual API. [explicit]
2. The model interpolates between these signals, causing it to generate code that mixes your custom API with the real library's API — producing code that references functions that don't exist in your project. [derived]
3. This is not a failure of reasoning but of signal disambiguation: the model cannot reliably weight "what I was shown" over "what I know" when the names collide. [derived]
**COUNTER-INDICATION:** When explicitly building a wrapper, plugin, or adapter for an existing library, the name collision is intentional and expected — in that case, provide very explicit disambiguation in the CLAUDE.md/CONVENTIONS.md (e.g., "This project wraps React but has its own component API — never use React.createClass or any React API directly").

## SOURCE
https://akitaonrails.com/2025/05/01/quando-llms-nao-funcionam-pra-programar-um-caso-de-uso-mais-real/
