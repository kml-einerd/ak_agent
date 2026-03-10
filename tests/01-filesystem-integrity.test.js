'use strict';
/**
 * TESTE 01: Integridade do Filesystem
 * Verifica que todos os arquivos esperados existem e não estão vazios.
 * Camada: estrutura física do projeto.
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const BASE = path.join(ROOT, 'base');

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

function fileExists(rel) {
  return fs.existsSync(path.join(ROOT, rel));
}

function fileNotEmpty(rel) {
  const p = path.join(ROOT, rel);
  if (!fs.existsSync(p)) return false;
  return fs.statSync(p).size > 0;
}

// ─── Arquivos raiz ───────────────────────────────────────────────────────────
console.log('\n[01] Arquivos raiz obrigatórios');
assert(fileExists('akita-agent.xml'), 'akita-agent.xml existe');
assert(fileNotEmpty('akita-agent.xml'), 'akita-agent.xml não está vazio');
assert(fileExists('CLAUDE.md'), 'CLAUDE.md existe');
assert(fileExists('base/INDEX.md'), 'base/INDEX.md existe');
assert(fileNotEmpty('base/INDEX.md'), 'base/INDEX.md não está vazio');
assert(fileExists('base/ENRICHMENT-LOG.md'), 'base/ENRICHMENT-LOG.md existe');

// ─── Diretórios da knowledge base ────────────────────────────────────────────
console.log('\n[02] Diretórios da knowledge base');
const expectedDirs = [
  'base/procedimentos',
  'base/protocolos',
  'base/anti-patterns',
  'base/conceitos',
  'base/heuristicas',
  'base/referencias',
];
for (const dir of expectedDirs) {
  assert(fs.existsSync(path.join(ROOT, dir)), `Diretório ${dir} existe`);
}

// ─── Todos os arquivos .md devem ter conteúdo ─────────────────────────────────
console.log('\n[03] Todos os elementos .md têm conteúdo');
const elementTypes = {
  'base/procedimentos': 'procedure-',
  'base/protocolos':   'protocol-',
  'base/anti-patterns':'antipattern-',
  'base/conceitos':    'concept-',
  'base/heuristicas':  'heuristic-',
  'base/referencias':  'reference-',
};

const elementFiles = [];
for (const [dir, prefix] of Object.entries(elementTypes)) {
  const absDir = path.join(ROOT, dir);
  if (!fs.existsSync(absDir)) continue;
  const files = fs.readdirSync(absDir).filter(f => f.endsWith('.md') && f !== '.gitkeep' && !f.startsWith('.'));
  for (const file of files) {
    const rel = `${dir}/${file}`;
    elementFiles.push(rel);
    assert(fileNotEmpty(rel), `${rel} tem conteúdo`);
  }
}

// ─── Nomenclatura dos arquivos segue convenção ────────────────────────────────
console.log('\n[04] Nomenclatura segue convenção (prefixo correto por diretório)');
for (const [dir, prefix] of Object.entries(elementTypes)) {
  const absDir = path.join(ROOT, dir);
  if (!fs.existsSync(absDir)) continue;
  const files = fs.readdirSync(absDir).filter(f => f.endsWith('.md') && !f.startsWith('.'));
  for (const file of files) {
    assert(file.startsWith(prefix), `${dir}/${file} começa com '${prefix}'`);
  }
}

// ─── Resumo ───────────────────────────────────────────────────────────────────
console.log(`\n${'─'.repeat(60)}`);
console.log(`Resultado: ${passed} passou, ${failed} falhou`);
if (errors.length > 0) {
  console.error('Falhas:');
  errors.forEach(e => console.error(`  - ${e}`));
  process.exitCode = 1;
} else {
  console.log('Todos os testes de filesystem passaram ✓');
}

module.exports = { elementFiles };
