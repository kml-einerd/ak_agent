/**
 * TEST-02: Element Structure — Required Fields Per Type
 *
 * Each element type has a documented required format (from akita-agent.xml
 * <response-format> and <quality-standard> sections). These tests verify
 * that every element file meets the structural minimum.
 *
 * EXPECTED STATE: All tests pass (basic structure was set during extraction).
 * If any fail, the element was incorrectly structured at creation time.
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

// ─── PROCEDURES ──────────────────────────────────────────────────────────────
describe('02a — PROCEDURE required fields', () => {
  const procedures = loadElementFiles('procedimentos');

  for (const { name, content } of procedures) {
    test(`${name}: has DOMAIN field`, () => {
      assert.ok(content.includes('**DOMAIN:**'), `Missing **DOMAIN:** in ${name}`);
    });

    test(`${name}: has TRIGGER field`, () => {
      assert.ok(content.includes('**TRIGGER:**'), `Missing **TRIGGER:** in ${name}`);
    });

    test(`${name}: has PRE-CONDITIONS field`, () => {
      assert.ok(content.includes('**PRE-CONDITIONS:**'), `Missing **PRE-CONDITIONS:** in ${name}`);
    });

    test(`${name}: has numbered STEPS section`, () => {
      assert.ok(content.includes('## STEPS'), `Missing ## STEPS in ${name}`);
    });

    test(`${name}: has at least 3 steps`, () => {
      const steps = (content.match(/^\d+\./gm) || []);
      assert.ok(steps.length >= 3, `${name} has only ${steps.length} steps (minimum: 3)`);
    });

    test(`${name}: has DONE WHEN section`, () => {
      assert.ok(content.includes('## DONE WHEN'), `Missing ## DONE WHEN in ${name}`);
    });

    test(`${name}: has SOURCE link`, () => {
      assert.ok(content.includes('## SOURCE'), `Missing ## SOURCE in ${name}`);
    });
  }
});

// ─── PROTOCOLS ───────────────────────────────────────────────────────────────
describe('02b — PROTOCOL required fields', () => {
  const protocols = loadElementFiles('protocolos');

  for (const { name, content } of protocols) {
    test(`${name}: has DOMAIN field`, () => {
      assert.ok(content.includes('**DOMAIN:**'), `Missing **DOMAIN:** in ${name}`);
    });

    test(`${name}: has APPLIES TO field`, () => {
      assert.ok(content.includes('**APPLIES TO:**'), `Missing **APPLIES TO:** in ${name}`);
    });

    test(`${name}: has RATIONALE field`, () => {
      assert.ok(content.includes('**RATIONALE:**'), `Missing **RATIONALE:** in ${name}`);
    });

    test(`${name}: has SIGNAL|DIAGNOSE|INTERVENE evaluation table`, () => {
      const hasSignal = content.includes('SIGNAL');
      const hasDiagnose = content.includes('DIAGNOSE');
      const hasIntervene = content.includes('INTERVENE');
      assert.ok(
        hasSignal && hasDiagnose && hasIntervene,
        `${name} missing SIGNAL/DIAGNOSE/INTERVENE evaluation table`
      );
    });

    test(`${name}: has TRADE-OFFS section`, () => {
      assert.ok(content.includes('**TRADE-OFFS:**'), `Missing **TRADE-OFFS:** in ${name}`);
    });

    test(`${name}: has ESCALATE WHEN section`, () => {
      assert.ok(content.includes('**ESCALATE WHEN:**'), `Missing **ESCALATE WHEN:** in ${name}`);
    });

    test(`${name}: has SOURCE link`, () => {
      assert.ok(content.includes('## SOURCE'), `Missing ## SOURCE in ${name}`);
    });
  }
});

// ─── ANTI-PATTERNS ────────────────────────────────────────────────────────────
describe('02c — ANTI-PATTERN required fields', () => {
  const antiPatterns = loadElementFiles('anti-patterns');

  for (const { name, content } of antiPatterns) {
    test(`${name}: has DOMAIN field`, () => {
      assert.ok(content.includes('**DOMAIN:**'), `Missing **DOMAIN:** in ${name}`);
    });

    test(`${name}: has APPEARS AS field`, () => {
      assert.ok(content.includes('**APPEARS AS:**'), `Missing **APPEARS AS:** in ${name}`);
    });

    test(`${name}: has ROOT CAUSE field`, () => {
      assert.ok(content.includes('**ROOT CAUSE:**'), `Missing **ROOT CAUSE:** in ${name}`);
    });

    test(`${name}: has SYMPTOMS section`, () => {
      assert.ok(content.includes('## SYMPTOMS'), `Missing ## SYMPTOMS in ${name}`);
    });

    test(`${name}: has CORRECTION section`, () => {
      assert.ok(content.includes('## CORRECTION'), `Missing ## CORRECTION in ${name}`);
    });

    test(`${name}: has SOURCE link`, () => {
      assert.ok(content.includes('## SOURCE'), `Missing ## SOURCE in ${name}`);
    });
  }
});

// ─── HEURISTICS ───────────────────────────────────────────────────────────────
describe('02d — HEURISTIC required fields', () => {
  const heuristics = loadElementFiles('heuristicas');

  for (const { name, content } of heuristics) {
    test(`${name}: has DOMAIN field`, () => {
      assert.ok(content.includes('**DOMAIN:**'), `Missing **DOMAIN:** in ${name}`);
    });

    test(`${name}: has RULE field`, () => {
      assert.ok(content.includes('**RULE:**'), `Missing **RULE:** in ${name}`);
    });

    test(`${name}: has APPLIES WHEN field`, () => {
      assert.ok(content.includes('**APPLIES WHEN:**'), `Missing **APPLIES WHEN:** in ${name}`);
    });

    test(`${name}: has RATIONALE field`, () => {
      assert.ok(content.includes('**RATIONALE:**'), `Missing **RATIONALE:** in ${name}`);
    });

    test(`${name}: has COUNTER-INDICATION field`, () => {
      assert.ok(
        content.includes('**COUNTER-INDICATION:**'),
        `Missing **COUNTER-INDICATION:** in ${name}`
      );
    });

    test(`${name}: has SOURCE link`, () => {
      assert.ok(content.includes('## SOURCE'), `Missing ## SOURCE in ${name}`);
    });
  }
});

// ─── CONCEPTS ─────────────────────────────────────────────────────────────────
describe('02e — CONCEPT required fields', () => {
  const concepts = loadElementFiles('conceitos');

  for (const { name, content } of concepts) {
    test(`${name}: has DOMAIN field`, () => {
      assert.ok(content.includes('**DOMAIN:**'), `Missing **DOMAIN:** in ${name}`);
    });

    test(`${name}: has content body (not empty)`, () => {
      const lines = content.split('\n').filter(l => l.trim().length > 0);
      assert.ok(lines.length >= 5, `${name} has too few lines (${lines.length}) — likely empty`);
    });

    test(`${name}: has SOURCE link`, () => {
      assert.ok(content.includes('## SOURCE'), `Missing ## SOURCE in ${name}`);
    });
  }
});

// ─── REFERENCES ───────────────────────────────────────────────────────────────
describe('02f — REFERENCE required fields', () => {
  const references = loadElementFiles('referencias');

  for (const { name, content } of references) {
    test(`${name}: has DOMAIN field`, () => {
      assert.ok(content.includes('**DOMAIN:**'), `Missing **DOMAIN:** in ${name}`);
    });

    test(`${name}: has SOURCE link`, () => {
      assert.ok(content.includes('## SOURCE'), `Missing ## SOURCE in ${name}`);
    });
  }
});
