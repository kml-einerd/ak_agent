'use strict';
/**
 * TESTE 05: Cross-References entre Elementos
 * Verifica que:
 *   a) Seções REFERENCED BY em CONCEPTs apontam para arquivos que existem
 *   b) ANTI-PATTERNs com seção OPERATIONAL CONSTRAINTS têm GATE definido
 *   c) HEURISTICs com OPERATIONAL CONSTRAINTS têm GATE definido
 *   d) Todos os links SOURCE são URLs válidas (formato http/https)
 *   e) O domínio de cada arquivo é um dos domínios catalogados
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

function readElements(dir) {
  const absDir = path.join(ROOT, dir);
  if (!fs.existsSync(absDir)) return [];
  return fs.readdirSync(absDir)
    .filter(f => f.endsWith('.md') && !f.startsWith('.'))
    .map(f => ({
      file: f,
      rel:  `${dir}/${f}`,
      content: fs.readFileSync(path.join(ROOT, dir, f), 'utf8'),
    }));
}

const KNOWN_DOMAINS = new Set([
  'ai-workflow', 'security', 'frontend', 'backend', 'architecture',
  'database', 'deployment', 'self-hosting', 'ai-image-generation', 'testing',
  'design-system', 'content-publishing', 'infrastructure', 'email',
  'async-jobs', 'ai-infrastructure', 'media',
]);

// ─── REFERENCED BY em conceitos ───────────────────────────────────────────────
console.log('\n[01] REFERENCED BY em CONCEPTs aponta para arquivos existentes');
const concepts = readElements('base/conceitos');
for (const { file, content } of concepts) {
  const refByMatch = content.match(/## REFERENCED BY\s*([\s\S]*?)(?=\n##|\n---|\n## SOURCE|$)/);
  if (!refByMatch) continue;
  const refSection = refByMatch[1];
  const refs = refSection.match(/base\/[^\s\n]+\.md/g) || [];
  for (const ref of refs) {
    const abs = path.join(ROOT, ref);
    assert(fs.existsSync(abs), `${file} REFERENCED BY → ${ref} existe`);
  }
}

// ─── OPERATIONAL CONSTRAINTS com GATE ─────────────────────────────────────────
console.log('\n[02] Elementos com OPERATIONAL CONSTRAINTS têm GATE');
const antiPatterns = readElements('base/anti-patterns');
const heuristics   = readElements('base/heuristicas');

const withConstraints = [...antiPatterns, ...heuristics].filter(
  e => e.content.includes('## OPERATIONAL CONSTRAINTS') || e.content.includes('OPERATIONAL CONSTRAINTS')
);
for (const { file, content } of withConstraints) {
  assert(content.includes('GATE:'), `${file} tem GATE em OPERATIONAL CONSTRAINTS`);
}

// ─── NEVER/ALWAYS dentro de OPERATIONAL CONSTRAINTS ───────────────────────────
console.log('\n[03] OPERATIONAL CONSTRAINTS contêm NEVER e ALWAYS');
for (const { file, content } of withConstraints) {
  const hasNever  = content.includes('NEVER:') || content.includes('NEVER\n');
  const hasAlways = content.includes('ALWAYS:') || content.includes('ALWAYS\n');
  assert(hasNever,  `${file} tem lista NEVER em OPERATIONAL CONSTRAINTS`);
  assert(hasAlways, `${file} tem lista ALWAYS em OPERATIONAL CONSTRAINTS`);
}

// ─── SOURCE é URL válida ───────────────────────────────────────────────────────
console.log('\n[04] Seções SOURCE contêm URL http(s)');
const allElements = [
  ...readElements('base/procedimentos'),
  ...readElements('base/protocolos'),
  ...readElements('base/anti-patterns'),
  ...readElements('base/conceitos'),
  ...readElements('base/heuristicas'),
];

for (const { file, content } of allElements) {
  const sourceMatch = content.match(/## SOURCE\s*([\s\S]*?)(?=\n##|$)/);
  if (!sourceMatch) {
    assert(false, `${file} tem ## SOURCE`);
    continue;
  }
  const sourceSection = sourceMatch[1];
  const hasUrl = /https?:\/\//.test(sourceSection);
  assert(hasUrl, `${file} SOURCE tem URL http(s)`);
}

// ─── DOMAIN é um dos domínios catalogados ─────────────────────────────────────
console.log('\n[05] **DOMAIN:** contém valor catalogado');
const allWithDomain = [
  ...readElements('base/procedimentos'),
  ...readElements('base/protocolos'),
  ...readElements('base/anti-patterns'),
  ...readElements('base/conceitos'),
  ...readElements('base/heuristicas'),
  ...readElements('base/referencias'),
];

for (const { file, content } of allWithDomain) {
  const domainMatch = content.match(/\*\*DOMAIN:\*\*\s*(.+)/);
  if (!domainMatch) {
    assert(false, `${file} tem **DOMAIN:**`);
    continue;
  }
  const domainVal = domainMatch[1].trim();
  // Pode ser multi-domínio: "ai-workflow / content-publishing"
  const parts = domainVal.split(/[\s/,]+/).filter(Boolean);
  const allValid = parts.every(p => KNOWN_DOMAINS.has(p));
  assert(allValid, `${file} DOMAIN '${domainVal}' — todas partes são domínios conhecidos`);
}

// ─── Resumo ───────────────────────────────────────────────────────────────────
console.log(`\n${'─'.repeat(60)}`);
console.log(`Resultado: ${passed} passou, ${failed} falhou`);
if (errors.length > 0) {
  console.error('Falhas:');
  errors.forEach(e => console.error(`  - ${e}`));
  process.exitCode = 1;
} else {
  console.log('Todos os testes de cross-references passaram ✓');
}
