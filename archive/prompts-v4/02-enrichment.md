# AKITA VAULT — ENRICHMENT PASS (MULTI-AGENT)
> Run AFTER 01-extraction has been completed.
> Paste this entire content into a Claude Code chat session.
> Set SCOPE at the bottom of this file before running.

---

## MODE: INCREMENTAL

This enrichment pass supports **incremental runs**. The knowledge base may already contain enriched elements from previous passes.

**Critical implications:**
- ENRICHMENT-LOG.md records all previously enriched elements — do NOT re-enrich them unless SCOPE = `full`
- New elements from the latest extraction pass are the priority targets
- Extended elements (modified during incremental extraction) should be re-evaluated — the extension may have introduced new limitation language or weakened an existing rationale

---

## MANDATORY READS — BEFORE ANYTHING ELSE

Read all of the following completely before doing anything else.

1. `C:\Users\dis\Downloads\KML_mkt\Vídeos e audios CDV\Akita Vault\meta\taxonomy.md`
2. `C:\Users\dis\Downloads\KML_mkt\Vídeos e audios CDV\Akita Vault\meta\templates.md`
3. `C:\Users\dis\Downloads\KML_mkt\Vídeos e audios CDV\Akita Vault\base\INDEX.md`
4. `C:\Users\dis\Downloads\KML_mkt\Vídeos e audios CDV\Akita Vault\base\ENRICHMENT-LOG.md`

**Element loading strategy (to manage context):**
- If SCOPE = `new` → read only elements NOT listed in ENRICHMENT-LOG.md + elements marked `[extended]` in the latest extraction. For cross-reference, also read existing elements in the same domains as the new ones.
- If SCOPE = `full` → read every element file listed in INDEX.md (all of them, not a sample). Use this only when doing a complete re-evaluation.
- If the total element count exceeds **80 elements** and SCOPE = `full`, split into domain batches: process one domain completely before moving to the next. Save between domains.

Confirm all reads are complete before proceeding.

---

## CONTEXT: WHAT THIS PASS DOES

Extraction produced raw knowledge elements. Enrichment makes them operational. Three transformations:

**Limitation → Constraint:** Passive observations about what fails get rewritten as executable conditions for success. An agent cannot act on "X is bad" — it can act on "for X to succeed: NEVER [A], ALWAYS [B], GATE [C]."

**Reasoning Reconstruction:** Elements with thin or absent rationale get their reasoning chain rebuilt. The reasoning chain is what allows the agent to apply a rule correctly in edge cases — not just in the exact situations described.

**Reclassification:** Elements placed in the wrong type during extraction get moved to the correct type based on their actual content structure.

This pass does not change what was extracted. It deepens and operationalizes it.

---

## TEAM STRUCTURE

**ORCHESTRATOR** — reads all elements, builds the enrichment queue, coordinates the team, resolves disputes, produces the enrichment log and final report.

**CONSTRAINT ENGINEER** — specialist in Rule 1. Identifies limitation language. Rewrites as operational constraint blocks (NEVER / ALWAYS / GATE). Derives conditions from source content only — never invents.

**RATIONALE ARCHAEOLOGIST** — specialist in Rule 2. Identifies thin rationale. Reconstructs reasoning chains by reading what the element implies, what the source article stated, and what is logically necessary for the rule to hold. Labels reconstructed steps as `[derived]`.

**RECLASSIFIER** — specialist in Rules 3 and 4. Identifies elements in the wrong type based on their actual content. Proposes type changes with justification. Does not reclassify based on preference — only based on taxonomy criteria.

**VALIDATOR** — receives all proposed enrichments. Checks each against three criteria: (1) all new content is derivable from existing element or source article, (2) enrichment does not contradict the original element, (3) enrichment makes the element more operational, not more verbose. Approves, requests revision, or flags for COUNCIL.

**COUNCIL** — convened when VALIDATOR disputes an enrichment. Three rounds: ENGINEER/ARCHAEOLOGIST/RECLASSIFIER defends the enrichment, VALIDATOR challenges, ORCHESTRATOR rules. Maximum 3 rounds per element.

---

## ENRICHMENT RULES

### RULE 1 — Limitation → Constraint (CONSTRAINT ENGINEER)

**Trigger language** (any equivalent formulation):
- "X is bad/poor/wrong for Y"
- "avoid X" / "don't use X when Y"
- "X causes problems / fails / breaks when Y"
- ANTI-PATTERN corrections stated as "do X instead" without conditions
- HEURISTIC COUNTER-INDICATION that implies a condition not yet made explicit

**Transformation — add this block to the element:**

```
## OPERATIONAL CONSTRAINTS
**FOR [intended outcome] TO SUCCEED:**

NEVER:
- [specific condition that causes failure — one per line]

ALWAYS:
- [specific enabling condition — one per line]

GATE: [boolean condition to evaluate before proceeding — if false, do not proceed]
```

**Derivation rule:** NEVER and ALWAYS items must be derived from explicit or clearly implied content in the element or its source. Mark implied derivations as `[implied]`. Do not invent. If derivation is uncertain, leave item blank and flag for VALIDATOR.

---

### RULE 2 — Rationale Reconstruction (RATIONALE ARCHAEOLOGIST)

**Trigger:** RATIONALE field is absent, single-sentence, or states the conclusion without the chain.

**Target format:**
```
**RATIONALE:**
1. [premise: an observable fact or stated condition]
2. [what follows from that premise — the logical step]
3. [therefore: why the rule holds — the conclusion of the chain]
```

Minimum 2 steps. Maximum 5. Each step must be a distinct logical move, not a restatement.

Mark fully reconstructed rationales as `[derived]`. Mark partially reconstructed as `[partial — derived from: {what was used}]`.

---

### RULE 3 — Reclassification: REFERENCE → PROTOCOL (RECLASSIFIER)

**Trigger:** A REFERENCE element contains a situation + response pattern: some signal the reader observes + some judgment or action that follows.

**Action:** Reclassify as PROTOCOL. Reformat using PROTOCOL template. Rename file: `reference-X.md` → `protocol-X.md`. Move to `protocolos/`. Update INDEX.md.

---

### RULE 4 — Reclassification: HEURISTIC → PROTOCOL (RECLASSIFIER)

**Trigger:** A HEURISTIC where:
- APPLIES WHEN covers more than one distinct situation type that would require different responses, OR
- COUNTER-INDICATION reveals conditional logic complex enough that the rule's application is non-trivial

**Action:** Promote to PROTOCOL. Reformat. Move file to `protocolos/`. Update INDEX.md.

---

## PROCESS

### PHASE 1 — ORCHESTRATOR: Queue Building

Declare: `[ORCHESTRATOR]`

**1A — Scope resolution:**
- If SCOPE = `new`: identify elements NOT in ENRICHMENT-LOG.md + elements with `[extended]` tag. These are the candidates.
- If SCOPE = `full`: all elements in INDEX.md are candidates.
- State: "Enrichment scope: {new|full} — {N} candidate elements out of {M} total"

**1B — Queue building:**
For each candidate element, check against all 4 rules. Build four lists:
- Rule 1 candidates (limitation language detected)
- Rule 2 candidates (thin rationale)
- Rule 3 candidates (REFERENCE with judgment pattern)
- Rule 4 candidates (HEURISTIC with complex conditions)

An element can appear in multiple lists. State the full queue before proceeding.

**1C — Previously enriched re-check (SCOPE = `new` only):**
For elements that were EXTENDED during the latest extraction and already appear in ENRICHMENT-LOG.md: check if the extension introduced new limitation language or weakened the existing rationale. If yes, add to the appropriate rule queue. If no, skip.

---

### PHASE 2 — SPECIALIST PASSES

**CONSTRAINT ENGINEER** processes all Rule 1 candidates.

Declare: `[CONSTRAINT ENGINEER — N elements]`

For each element:
- Quote the limitation language found
- Derive NEVER, ALWAYS, GATE items from source content
- State derivation basis for each item (explicit / implied / derived)
- Produce the enriched block
- Label: `CONSTRAINT ENGINEER → VALIDATOR: {element name}`

---

**RATIONALE ARCHAEOLOGIST** processes all Rule 2 candidates.

Declare: `[RATIONALE ARCHAEOLOGIST — N elements]`

For each element:
- State what the current RATIONALE contains (or note: "absent")
- Trace the reasoning chain from available content
- Produce the 2-5 step chain
- Label each step: explicit / derived
- Label: `RATIONALE ARCHAEOLOGIST → VALIDATOR: {element name}`

---

**RECLASSIFIER** processes all Rule 3 and Rule 4 candidates.

Declare: `[RECLASSIFIER — N elements]`

For each element:
- Quote the content that triggers reclassification
- State the taxonomy criterion that supports the new type
- Produce the reformatted element using the correct template
- State new filename and path
- Label: `RECLASSIFIER → VALIDATOR: {element name} — from {old type} to {new type}`

---

### PHASE 3 — VALIDATION

**VALIDATOR** reviews all enriched elements.

Declare: `[VALIDATOR]`

For each enriched element, check three criteria:
1. **Derivability:** Is all new content derivable from the element or its source? Mark any invented content as a violation.
2. **Consistency:** Does the enrichment contradict anything in the original element?
3. **Operationality:** Does the enrichment make the element more actionable for an AI agent? If it only adds words without adding utility, reject.

Decision per element:
- **APPROVE** — passes all three criteria
- **REVISE** — fails one criterion — state what must change, return to specialist
- **COUNCIL** — specialist and validator genuinely disagree after one revision — escalate

---

### PHASE 4 — COUNCIL *(only for disputed elements)*

Declare: `[COUNCIL CONVENED — {element name}]`

Round 1: Specialist defends the enrichment — why is it derivable and operational?
Round 2: VALIDATOR challenges — what specifically violates the criteria?
Round 3: ORCHESTRATOR rules — approve with modification, approve as-is, or reject with explanation.

Maximum 3 rounds. No extensions.

---

### PHASE 5 — SAVING AND LOGGING

After all enrichments are approved:

1. Update each element file in place — add enriched sections, do not delete original content
2. For reclassifications: create new file, delete old file, update INDEX.md
3. Add `ENRICHMENT_UNCERTAIN: true` header to any element that was flagged but not fully resolved
4. **Append** to `C:\Users\dis\Downloads\KML_mkt\Vídeos e audios CDV\Akita Vault\base\ENRICHMENT-LOG.md` — do NOT overwrite previous passes. Use a new dated section:

```markdown
---

## ENRICHMENT PASS — [DATE]

**Scope:** {new|full}
**Input:** {N} elements from {extraction date} pass
**Output:** {N} elements enriched ({N} constraint, {N} rationale, {N} reclassification)

### [Element Name]
- **File:** [path]
- **Rules applied:** [list]
- **Specialist:** [who enriched it]
- **Validator verdict:** APPROVED / REVISED / COUNCIL
- **Content added:** [summary of what was added]
- **Derived content:** [yes/no — if yes, what and why]
```

5. Update ENRICHMENT STATUS block in INDEX.md — add a new line for this pass, preserve previous pass info.

---

### PHASE 6 — ORCHESTRATOR: Final Report

Declare: `[ORCHESTRATOR — ENRICHMENT REPORT]`

- **Scope:** {new|full}
- **Baseline:** elements in scope before enrichment
- **Elements processed per rule**
- **Elements approved / revised / rejected**
- **Reclassifications:** list old → new type
- **Council cases:** how resolved
- **Elements marked ENRICHMENT_UNCERTAIN:** list + reason
- **Overall assessment:** which element types benefited most from enrichment? Which were already operational?
- **Post-enrichment total:** {N} elements total, {N} enriched across all passes
- **Next step:** Update `akita-agent.xml` to include routes for any new elements or reclassified elements. If new domains were added, new routing blocks are needed. Use the ROUTING and CONSTRAINTS sections of the existing XML as a template.

---

## HARD CONSTRAINTS

- Every specialist must declare their role at the start of each output block
- VALIDATOR cannot be bypassed — every enrichment goes through validation
- Specialists cannot self-approve their own enrichments
- Original element content is never deleted — only added to
- COUNCIL maximum is 3 rounds — no exceptions
- `ENRICHMENT_UNCERTAIN` flag must be added to the file, not just the report
- ENRICHMENT-LOG.md is append-only — never overwrite or delete entries from previous passes
- If SCOPE = `new`, elements already in ENRICHMENT-LOG.md are skipped UNLESS they were extended in the latest extraction pass

---

## SCOPE

> **Instructions:** Replace the placeholder below with your scope before running.
> - `new` — only enrich elements from the latest extraction pass (recommended for incremental use)
> - `full` — re-evaluate all elements (use sparingly, only when taxonomy or templates changed)

SCOPE: `new`
