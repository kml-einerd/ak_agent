# AKITA VAULT — EXTRACTION PASS (MULTI-AGENT)
> Paste this entire content into a Claude Code chat.
> Set INPUT at the bottom of this file before running.
> Supports: (a) a single article URL, (b) a file path to a URL list, (c) a path to a `.txt` file with article text, (d) a folder path containing multiple `.txt` files.

---

## MODE: INCREMENTAL

This is an **incremental extraction**. A knowledge base already exists with elements from previous passes.

**Critical implications:**
- INDEX.md already contains existing elements — EVERY new candidate must be checked against them
- "Semantically similar" means: same situation + same response pattern, even with different wording
- When a new article deepens an existing element (more steps, more signals, more symptoms), **EXTEND** the existing element — do not create a duplicate
- When a new article covers a genuinely different situation that happens to be in the same domain, **CREATE** a new element
- The INDEXER will load and compare against all existing elements in the relevant domain before deciding

---

## MANDATORY READS — BEFORE ANYTHING ELSE

Read all three files completely. Do not proceed without confirming all reads are done.

1. `C:\Users\dis\Downloads\KML_mkt\Vídeos e audios CDV\Akita Vault\meta\taxonomy.md`
2. `C:\Users\dis\Downloads\KML_mkt\Vídeos e audios CDV\Akita Vault\meta\templates.md`
3. `C:\Users\dis\Downloads\KML_mkt\Vídeos e audios CDV\Akita Vault\base\INDEX.md`
4. `C:\Users\dis\Downloads\KML_mkt\Vídeos e audios CDV\Akita Vault\base\ENRICHMENT-LOG.md` — to understand what has already been enriched

---

## TEAM STRUCTURE

This session operates as a coordinated team. Each role has a defined scope and produces structured output that the next role consumes. Roles are executed sequentially — not truly parallel — but each must complete its analysis before the next begins.

**ORCHESTRATOR** — manages the full session. Reads the input, builds the processing queue, coordinates handoffs, runs deduplication, produces the final report. Does not extract directly.

**EXTRACTOR-A (Structure Analyst)** — focuses exclusively on explicit, procedural content: steps, sequences, processes with defined order, workflows with verifiable outputs. Candidate type: PROCEDURE.

**EXTRACTOR-B (Pattern Analyst)** — focuses on reasoning patterns: how the author evaluates situations, what criteria he applies, what signals he reads before deciding. Candidate type: PROTOCOL, HEURISTIC.

**EXTRACTOR-C (Implicit Analyst)** — focuses on what is rejected, criticized, warned against, or assumed without explanation. What the author considers too obvious to explain reveals his strongest convictions. Candidate type: ANTI-PATTERN, CONCEPT.

**ARBITRATOR** — receives all three extractors' outputs. Resolves classification conflicts, eliminates overlaps, applies the granularity rule, assigns final TYPE to each candidate.

**QUALITY REVIEWER** — receives the arbitrated list. Applies taxonomy qualification and disqualification criteria to each element. Scores each: HIGH (clear fit), MEDIUM (fits with caveats), LOW (uncertain). Low-confidence elements go to COUNCIL.

**COUNCIL** — convened only for LOW-confidence elements. Three rounds maximum: EXTRACTOR makes case, QUALITY REVIEWER challenges, ARBITRATOR rules. Majority of explicit arguments wins — not authority.

**INDEXER** — receives all approved elements. Formats each using the correct template from templates.md. Saves to the correct path. Updates INDEX.md. Checks for semantic duplicates against already-existing elements.

---

## PROCESS

### PHASE 0 — ORCHESTRATOR: Input Resolution & Batching

**Input type detection:**

If INPUT is a **single URL**:
- Create a queue of one
- Proceed to Phase 1

If INPUT is a **file path ending in `.md`** (URL list):
- Read the file
- Extract all URLs (one per line, ignore blank lines)
- Deduplicate (remove exact duplicate URLs)
- Cross-check against EXTRACTION HISTORY in INDEX.md — skip URLs already processed in previous passes
- Print the deduplicated processing queue with count
- Process each URL sequentially through Phases 1–3

If INPUT is a **file path ending in `.txt`** (article text):
- Read the file directly as article content
- Use the filename as article identifier (e.g., `article-18.txt`)
- Create a queue of one
- Proceed to Phase 1

If INPUT is a **folder path**:
- List all `.txt` files in the folder
- Sort alphabetically
- Each file = one article in the queue
- Print the processing queue with count
- Process each file sequentially through Phases 1–3

**Batching rule:** If the queue has **more than 8 articles**, split into batches of 8. Process one batch completely (Phases 1–4) before starting the next. Between batches, save all elements and update INDEX.md — this is a **checkpoint**. If the session is interrupted, only the current batch is lost.

**Pre-extraction snapshot:** Before processing the first article, state the current element count from INDEX.md. This is the baseline for the final report.

---

### PHASE 1 — PARALLEL EXTRACTION (per article)

**1A — EXTRACTOR-A: Structure Analysis**

Declare: `[EXTRACTOR-A — Article: {URL}]`

Scan the article for explicit, ordered, procedural content. For each candidate:
- Quote the source sentence or passage
- Propose element name
- Identify TRIGGER, PRE-CONDITIONS, STEPS, DONE WHEN
- Assign tentative TYPE: PROCEDURE

Pass output to ARBITRATOR labeled: `EXTRACTOR-A OUTPUT → ARBITRATOR`

---

**1B — EXTRACTOR-B: Pattern Analysis**

Declare: `[EXTRACTOR-B — Article: {URL}]`

Scan for reasoning patterns: moments where the author evaluates a situation and produces a judgment. For each candidate:
- Quote the source sentence or passage
- Identify the signal the author reads, the diagnosis applied, the intervention chosen
- Note if it is a single-rule thumb rule (HEURISTIC) or multi-signal evaluation (PROTOCOL)
- Assign tentative TYPE: PROTOCOL or HEURISTIC

Pass output labeled: `EXTRACTOR-B OUTPUT → ARBITRATOR`

---

**1C — EXTRACTOR-C: Implicit Analysis**

Declare: `[EXTRACTOR-C — Article: {URL}]`

Scan for: things the author rejects without detailed explanation (reveals what he considers obviously wrong), terms he uses without defining (reveals assumed shared vocabulary), patterns he warns against (anti-patterns).

For each candidate:
- Quote the source sentence or passage (or note: "implied by...")
- Reconstruct the implicit reasoning
- Assign tentative TYPE: ANTI-PATTERN or CONCEPT

Pass output labeled: `EXTRACTOR-C OUTPUT → ARBITRATOR`

---

### PHASE 2 — ARBITRATION AND QUALITY GATE

**2A — ARBITRATOR: Consolidation**

Declare: `[ARBITRATOR]`

Receive all three extractor outputs. For each candidate across all three:
1. Check for overlaps: same content extracted by multiple extractors → keep best-classified version, discard others (note reason)
2. Apply granularity rule: split candidates with different triggers, merge candidates that are inseparable
3. Resolve classification conflicts: if two extractors classified the same content differently, apply taxonomy criteria and decide — state explicit reasoning
4. Produce a clean consolidated candidate list with final TYPE assignment

Output labeled: `ARBITRATOR CONSOLIDATED LIST → QUALITY REVIEWER`

---

**2B — QUALITY REVIEWER: Validation**

Declare: `[QUALITY REVIEWER]`

For each element in the consolidated list:
- Apply universal qualification criteria (taxonomy.md)
- Apply type-specific qualification and disqualification criteria
- Score: HIGH / MEDIUM / LOW confidence
- For MEDIUM: note the caveat but approve
- For LOW: state the specific uncertainty — send to COUNCIL

Output: approved list (HIGH + MEDIUM) + council referrals (LOW)

---

**2C — COUNCIL: Uncertain Element Resolution** *(only if LOW-confidence elements exist)*

Declare: `[COUNCIL CONVENED — {N} elements under review]`

For each uncertain element, 3 rounds maximum:

Round 1 — EXTRACTOR (whichever originally proposed it) makes the case for inclusion: what qualifies it?
Round 2 — QUALITY REVIEWER challenges: what specifically fails?
Round 3 — ARBITRATOR rules: include with classification X, or exclude with reason Y.

No element gets more than 3 rounds. Unresolved after 3 rounds → exclude, flag in report.

Output: final decision per uncertain element. Merge with approved list.

---

### PHASE 3 — FORMATTING AND SAVING

**INDEXER**

Declare: `[INDEXER]`

For each approved element:

1. **Duplicate check (MANDATORY):** Read INDEX.md. For each candidate, identify the domain. Load ALL existing elements in that domain (read the actual files, not just the index row). Compare:
   - **Exact match** (same situation + same response) → SKIP, note in report
   - **Partial overlap** (same situation, but new article adds depth — more steps, more signals, new failure modes) → EXTEND the existing element. Add new content with `[extended from: {source}]` tag. Do not duplicate existing content.
   - **Different situation** in same domain → CREATE new element

2. Format using the correct template from templates.md. Fill ALL fields — no blanks.

3. RATIONALE is mandatory. Minimum 2 explicit reasoning steps. Derive from article if available, reconstruct if not (mark as `[derived]`).

4. Save to correct path:
   - PROCEDURE → `base\procedimentos\procedure-[slug].md`
   - PROTOCOL → `base\protocolos\protocol-[slug].md`
   - ANTI-PATTERN → `base\anti-patterns\antipattern-[slug].md`
   - CONCEPT → `base\conceitos\concept-[slug].md`
   - HEURISTIC → `base\heuristicas\heuristic-[slug].md`
   - REFERENCE → `base\referencias\reference-[slug].md`

5. Add INDEX.md entry for each NEW element. For EXTENDED elements, update the existing index row if the trigger/applies-to changed.

6. Update EXTRACTION HISTORY in INDEX.md — add a NEW row for this extraction pass, do not overwrite the previous row.

7. Add the source URLs/files to `source-blog.md` (append, do not overwrite existing entries).

After ALL articles in this batch are processed: run a cross-article deduplication pass. Compare new elements against each other AND against all pre-existing elements. If two are semantically equivalent, merge the better-formed one and note the source consolidation.

---

### PHASE 4 — ORCHESTRATOR: Final Report

Declare: `[ORCHESTRATOR — FINAL REPORT]`

Output:
- **Baseline:** element count before this pass (from Phase 0 snapshot)
- **Articles processed:** N (of M in queue)
- **New elements created by type:** PROCEDURE N | PROTOCOL N | ANTI-PATTERN N | CONCEPT N | HEURISTIC N | REFERENCE N
- **Existing elements extended:** list with element name + what was added
- **Elements excluded:** list with reasons
- **Exact duplicates skipped:** list with matching existing element
- **Council cases:** how many, how resolved
- **Cross-article deduplication:** how many merges
- **New total:** element count after this pass
- **Coverage assessment:** which domains grew, which are still sparse
- **Recommendation:** which articles produced richest extractions
- **Next step:** Run `02-enrichment.md` targeting only the new/extended elements from this pass

---

## HARD CONSTRAINTS

- Every role declaration must use the exact format: `[ROLE-NAME]` before its output
- ARBITRATOR cannot be overruled by any single extractor
- COUNCIL must complete all 3 rounds — no early resolution
- INDEXER must check for duplicates before saving every element — this includes reading existing element files, not just index rows
- No element is saved without passing QUALITY REVIEWER
- RATIONALE field cannot be left empty or single-sentence in any element
- NEVER overwrite an existing element file without explicitly stating what changed and why (extend = add, never delete existing content)
- If a batch has more than 8 articles, checkpoint between batches — save everything before starting the next batch
- Every article/text in the queue gets the full pipeline (Phase 1-3) — never skip an article because "it looks similar to the previous one"

---

## INPUT

> **Instructions:** Replace the placeholder below with your input before running.
> Accepted formats:
> - Single URL: `https://example.com/article`
> - URL list file: `C:\...\source-blog-batch-2.md`
> - Single text file: `C:\...\temp-articles\article-18.txt`
> - Folder of text files: `C:\...\temp-articles\`

INPUT: `[REPLACE WITH YOUR INPUT]`
