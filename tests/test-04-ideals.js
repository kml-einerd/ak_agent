/**
 * TEST-04: Ideals — Enrichment Quality
 *
 * Tests the GAP between "how things should be" and "how they currently are."
 * These tests define the IDEAL state for actionable, production-ready elements.
 *
 * Based on the ENRICHMENT-LOG.md, the February 2026 batch (63 elements) had
 * 14 anti-patterns and heuristics enriched with OPERATIONAL CONSTRAINTS.
 * The March 2026 batch (31 new elements) was NEVER enriched.
 *
 * EXPECTED STATE: SEVERAL TESTS WILL FAIL (RED phase).
 * - 5 new anti-patterns missing OPERATIONAL CONSTRAINTS
 * - Some new procedures missing ON_FAILURE handlers
 * - Some new procedures missing at least 1 measurable DONE WHEN criterion
 *
 * GREEN phase: run the enrichment pass on the March 2026 batch.
 */
'use strict';

const { test, describe } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const BASE_DIR = path.join(ROOT, 'base');

function loadElementFiles(type) {
  const dirPath = path.join(BASE_DIR, type);
  return fs.readdirSync(dirPath)
    .filter(f => f.endsWith('.md') && f !== '.gitkeep')
    .map(f => ({
      name: f,
      path: path.join(dirPath, f),
      content: fs.readFileSync(path.join(dirPath, f), 'utf8'),
    }));
}

// ─── ANTI-PATTERN ENRICHMENT ─────────────────────────────────────────────────
//
// Ideal: every anti-pattern has an OPERATIONAL CONSTRAINTS block with
// NEVER/ALWAYS/GATE so the agent can emit actionable decision gates.
// Without this, the pattern is diagnostic-only — no operational value.
//
describe('04a — ANTI-PATTERN enrichment: OPERATIONAL CONSTRAINTS', () => {
  const antiPatterns = loadElementFiles('anti-patterns');

  for (const { name, content } of antiPatterns) {
    test(`${name}: has OPERATIONAL CONSTRAINTS section`, () => {
      assert.ok(
        content.includes('## OPERATIONAL CONSTRAINTS'),
        `${name} is missing ## OPERATIONAL CONSTRAINTS\n` +
        `  → Run enrichment pass: add NEVER/ALWAYS/GATE block before ## SOURCE`
      );
    });

    test(`${name}: OPERATIONAL CONSTRAINTS has NEVER clause`, () => {
      if (!content.includes('## OPERATIONAL CONSTRAINTS')) return; // skip if no section
      const constraintsBlock = content.split('## OPERATIONAL CONSTRAINTS')[1];
      assert.ok(
        constraintsBlock.includes('NEVER'),
        `${name} OPERATIONAL CONSTRAINTS missing NEVER clause`
      );
    });

    test(`${name}: OPERATIONAL CONSTRAINTS has ALWAYS clause`, () => {
      if (!content.includes('## OPERATIONAL CONSTRAINTS')) return;
      const constraintsBlock = content.split('## OPERATIONAL CONSTRAINTS')[1];
      assert.ok(
        constraintsBlock.includes('ALWAYS'),
        `${name} OPERATIONAL CONSTRAINTS missing ALWAYS clause`
      );
    });

    test(`${name}: OPERATIONAL CONSTRAINTS has GATE condition`, () => {
      if (!content.includes('## OPERATIONAL CONSTRAINTS')) return;
      const constraintsBlock = content.split('## OPERATIONAL CONSTRAINTS')[1];
      assert.ok(
        constraintsBlock.includes('GATE'),
        `${name} OPERATIONAL CONSTRAINTS missing GATE condition`
      );
    });
  }
});

// ─── PROCEDURE ENRICHMENT ─────────────────────────────────────────────────────
//
// Ideal: every procedure has at least one ON_FAILURE handler and at least
// one measurable criterion in DONE WHEN. Without these, the procedure
// is ambiguous about completion and recovery.
//
describe('04b — PROCEDURE enrichment: ON_FAILURE handlers', () => {
  const procedures = loadElementFiles('procedimentos');

  for (const { name, content } of procedures) {
    test(`${name}: has at least one ON_FAILURE handler`, () => {
      assert.ok(
        content.includes('ON_FAILURE'),
        `${name} has no ON_FAILURE handlers\n` +
        `  → Add ON_FAILURE[step-N] entries for steps that can fail`
      );
    });

    test(`${name}: DONE WHEN has at least 2 criteria`, () => {
      if (!content.includes('## DONE WHEN')) return;
      const doneBlock = content.split('## DONE WHEN')[1].split('##')[0];
      const criteria = (doneBlock.match(/^[-*•]\s+.+/gm) || []);
      assert.ok(
        criteria.length >= 2,
        `${name} DONE WHEN has only ${criteria.length} criteria (minimum: 2)`
      );
    });
  }
});

// ─── HEURISTIC ENRICHMENT ─────────────────────────────────────────────────────
//
// Ideal: every heuristic has a multi-step numbered RATIONALE (at least 2 steps),
// not a single paragraph. Multi-step rationale makes the reasoning
// auditable and the derivation visible.
//
describe('04c — HEURISTIC enrichment: numbered RATIONALE', () => {
  const heuristics = loadElementFiles('heuristicas');

  for (const { name, content } of heuristics) {
    test(`${name}: RATIONALE has at least 2 numbered steps`, () => {
      if (!content.includes('**RATIONALE:**')) return;
      const rationaleBlock = content.split('**RATIONALE:**')[1].split('**COUNTER-INDICATION:**')[0];
      const numberedSteps = (rationaleBlock.match(/^\d+\.\s+.+/gm) || []);
      assert.ok(
        numberedSteps.length >= 2,
        `${name} RATIONALE has ${numberedSteps.length} numbered steps (minimum: 2)\n` +
        `  → Expand rationale to a multi-step reasoning chain per ENRICHMENT-LOG RULE 2`
      );
    });
  }
});

// ─── CONCEPT ENRICHMENT ───────────────────────────────────────────────────────
//
// Ideal: every concept has a NOT section (common confusions), a RATIONALE,
// and states which other elements use it. Without these, the concept
// is just a definition with no operational context.
//
describe('04d — CONCEPT enrichment: NOT + RATIONALE + usage references', () => {
  const concepts = loadElementFiles('conceitos');

  for (const { name, content } of concepts) {
    test(`${name}: has NOT section (common confusions)`, () => {
      const hasNot = content.includes('**NOT:**') || content.includes('## NOT') ||
                     content.includes('NOT TO CONFUSE') || content.includes('**NOT**');
      assert.ok(
        hasNot,
        `${name} is missing a NOT/NOT TO CONFUSE WITH section\n` +
        `  → Add clarification of what this concept is NOT to prevent misuse`
      );
    });

    test(`${name}: has RATIONALE for why the concept matters`, () => {
      assert.ok(
        content.includes('**RATIONALE:**') || content.includes('## RATIONALE'),
        `${name} missing RATIONALE\n` +
        `  → Add rationale explaining why this concept matters for the knowledge base`
      );
    });
  }
});

// ─── USABILITY: AGENT RESPONSE FORMAT ─────────────────────────────────────────
//
// Ideal: akita-agent.xml's <constraints> section should reference every
// anti-pattern and heuristic that has OPERATIONAL CONSTRAINTS. Unreferenced
// constraints are defined but never enforced.
//
describe('04e — USABILITY: XML constraints cover enriched elements', () => {
  const xmlPath = path.join(ROOT, 'akita-agent.xml');
  const xmlContent = fs.readFileSync(xmlPath, 'utf8');

  // Elements that SHOULD appear in <never-rules> or <always-rules>
  // (per ENRICHMENT-LOG: these 9 elements have constraint blocks)
  const shouldBeConstrainedInXml = [
    'antipattern-llm-unsupervised-coding',
    'antipattern-no-architecture-rules-upfront',
    'antipattern-reinventing-wheel-llm',
    'antipattern-funciona-ja-accumulation',
    'antipattern-vibe-coding-without-expertise',
    'antipattern-frontend-equals-framework',
    'antipattern-catch-all-error-retry',
    'antipattern-one-shot-prompt',
    'antipattern-multi-task-mega-prompt',
    'heuristic-scope-inflation-vibe-coding',
    'heuristic-bigger-newer-not-better',
    'heuristic-match-model-to-harness',
    'heuristic-agent-skills-token-cost',
  ];

  for (const elementSlug of shouldBeConstrainedInXml) {
    test(`akita-agent.xml: <constraints> references ${elementSlug}`, () => {
      assert.ok(
        xmlContent.includes(elementSlug),
        `akita-agent.xml <constraints> does not reference "${elementSlug}"\n` +
        `  → Add NEVER/ALWAYS rules sourced from this element's OPERATIONAL CONSTRAINTS`
      );
    });
  }
});
