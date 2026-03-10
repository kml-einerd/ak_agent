'use strict';
/**
 * TESTE 02: Formato dos Elementos
 * Verifica que cada tipo de elemento tem os campos obrigatórios do seu template.
 * Camada: qualidade do conteúdo de cada arquivo individualmente.
 *
 * Formatos esperados (derivados de akita-agent.xml <response-format> e exemplos):
 *   PROCEDURE  → # PROCEDURE:, **TRIGGER:**, **DOMAIN:**, ## STEPS, ## DONE WHEN, ## SOURCE
 *   PROTOCOL   → # PROTOCOL:,  **DOMAIN:**, **APPLIES TO:**,  ## EVALUATION, ## SOURCE
 *   ANTI-PATTERN → # ANTI-PATTERN:, **DOMAIN:**, **APPEARS AS:**, ## SYMPTOMS, ## CORRECTION, ## SOURCE
 *   HEURISTIC  → # HEURISTIC:, **DOMAIN:**, **RULE:**, **APPLIES WHEN:**, ## SOURCE
 *   CONCEPT    → # CONCEPT:,   **DOMAIN:**, **DEFINITION:**, **NOT:**, ## SOURCE
 *   REFERENCE  → # REFERENCE:, **DOMAIN:**, **WHEN TO CONSULT:**,  ## CONTENT, ## SOURCE (opcional)
 */

const fs   = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

let passed = 0;
let failed = 0;
const errors = [];

function assert(condition, label) {
  if (condition) {
    console.log(`  ✓ ${label}`);
    passed++;
  } else {
    console.error(`  ✗ ${label}`);
    failed++;
    errors.push(label);
  }
}

function readFile(rel) {
  return fs.readFileSync(path.join(ROOT, rel), 'utf8');
}

function checkFields(content, fields, fileLabel) {
  for (const field of fields) {
    assert(content.includes(field), `${fileLabel} → contém '${field}'`);
  }
}

// ─── Procedures ──────────────────────────────────────────────────────────────
console.log('\n[01] PROCEDURE — campos obrigatórios');
const procedureDir = 'base/procedimentos';
const procedureFiles = fs.readdirSync(path.join(ROOT, procedureDir))
  .filter(f => f.endsWith('.md') && !f.startsWith('.'));

for (const file of procedureFiles) {
  const rel = `${procedureDir}/${file}`;
  const content = readFile(rel);
  console.log(`\n  Arquivo: ${file}`);
  checkFields(content, [
    '# PROCEDURE:',
    '**DOMAIN:**',
    '## STEPS',
    '## DONE WHEN',
    '## SOURCE',
  ], file);
}

// ─── Protocols ───────────────────────────────────────────────────────────────
console.log('\n[02] PROTOCOL — campos obrigatórios');
const protocolDir = 'base/protocolos';
const protocolFiles = fs.readdirSync(path.join(ROOT, protocolDir))
  .filter(f => f.endsWith('.md') && !f.startsWith('.'));

for (const file of protocolFiles) {
  const rel = `${protocolDir}/${file}`;
  const content = readFile(rel);
  console.log(`\n  Arquivo: ${file}`);
  checkFields(content, [
    '# PROTOCOL:',
    '**DOMAIN:**',
    '## SOURCE',
  ], file);
  // Pelo menos um dos identificadores de avaliação
  const hasEval = content.includes('## EVALUATION') || content.includes('SIGNAL') || content.includes('DIAGNOSE');
  assert(hasEval, `${file} → contém seção de avaliação (EVALUATION/SIGNAL/DIAGNOSE)`);
}

// ─── Anti-Patterns ───────────────────────────────────────────────────────────
console.log('\n[03] ANTI-PATTERN — campos obrigatórios');
const antiDir = 'base/anti-patterns';
const antiFiles = fs.readdirSync(path.join(ROOT, antiDir))
  .filter(f => f.endsWith('.md') && !f.startsWith('.'));

for (const file of antiFiles) {
  const rel = `${antiDir}/${file}`;
  const content = readFile(rel);
  console.log(`\n  Arquivo: ${file}`);
  checkFields(content, [
    '# ANTI-PATTERN:',
    '**DOMAIN:**',
    '**APPEARS AS:**',
    '## CORRECTION',
    '## SOURCE',
  ], file);
}

// ─── Concepts ────────────────────────────────────────────────────────────────
console.log('\n[04] CONCEPT — campos obrigatórios');
const conceptDir = 'base/conceitos';
const conceptFiles = fs.readdirSync(path.join(ROOT, conceptDir))
  .filter(f => f.endsWith('.md') && !f.startsWith('.'));

for (const file of conceptFiles) {
  const rel = `${conceptDir}/${file}`;
  const content = readFile(rel);
  console.log(`\n  Arquivo: ${file}`);
  checkFields(content, [
    '# CONCEPT:',
    '**DOMAIN:**',
    '**DEFINITION:**',
    '## SOURCE',
  ], file);
  const hasNot = content.includes('**NOT:**') || content.includes('**NOT ');
  assert(hasNot, `${file} → contém campo NOT (confusões comuns)`);
}

// ─── Heuristics ──────────────────────────────────────────────────────────────
console.log('\n[05] HEURISTIC — campos obrigatórios');
const heuristicDir = 'base/heuristicas';
const heuristicFiles = fs.readdirSync(path.join(ROOT, heuristicDir))
  .filter(f => f.endsWith('.md') && !f.startsWith('.'));

for (const file of heuristicFiles) {
  const rel = `${heuristicDir}/${file}`;
  const content = readFile(rel);
  console.log(`\n  Arquivo: ${file}`);
  checkFields(content, [
    '# HEURISTIC:',
    '**DOMAIN:**',
    '**RULE:**',
    '## SOURCE',
  ], file);
  const hasApplies = content.includes('**APPLIES WHEN:**') || content.includes('APPLIES WHEN');
  assert(hasApplies, `${file} → contém APPLIES WHEN`);
}

// ─── References ──────────────────────────────────────────────────────────────
console.log('\n[06] REFERENCE — campos obrigatórios');
const refDir = 'base/referencias';
const refFiles = fs.readdirSync(path.join(ROOT, refDir))
  .filter(f => f.endsWith('.md') && !f.startsWith('.'));

for (const file of refFiles) {
  const rel = `${refDir}/${file}`;
  const content = readFile(rel);
  console.log(`\n  Arquivo: ${file}`);
  checkFields(content, [
    '# REFERENCE:',
    '**DOMAIN:**',
    '## CONTENT',
  ], file);
}

// ─── Resumo ───────────────────────────────────────────────────────────────────
console.log(`\n${'─'.repeat(60)}`);
console.log(`Resultado: ${passed} passou, ${failed} falhou`);
if (errors.length > 0) {
  console.error('Falhas:');
  errors.forEach(e => console.error(`  - ${e}`));
  process.exitCode = 1;
} else {
  console.log('Todos os testes de formato passaram ✓');
}
