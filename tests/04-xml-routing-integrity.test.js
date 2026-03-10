'use strict';
/**
 * TESTE 04: Integridade do Routing XML
 * Verifica que:
 *   a) akita-agent.xml tem estrutura bem-formada
 *   b) Cada arquivo referenciado em <load> existe no filesystem
 *   c) Cada arquivo em <load> está no INDEX.md
 *   d) Todas as rotas têm <if>, <load> e <then>
 *   e) Os atributos source de <never-rules> e <always-rules> referenciam elementos existentes
 *   f) Os atributos source de <escalation-rules> referenciam protocolos existentes
 */

const fs   = require('fs');
const path = require('path');

const ROOT    = path.resolve(__dirname, '..');
const XML     = path.join(ROOT, 'akita-agent.xml');
const INDEX   = path.join(ROOT, 'base/INDEX.md');

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

const xmlContent   = fs.readFileSync(XML, 'utf8');
const indexContent = fs.readFileSync(INDEX, 'utf8');

// ─── Estrutura XML básica ──────────────────────────────────────────────────────
console.log('\n[01] Estrutura XML básica');
assert(xmlContent.includes('<akita-agent>'),  'Tag raiz <akita-agent> existe');
assert(xmlContent.includes('</akita-agent>'), 'Tag raiz </akita-agent> fecha');
assert(xmlContent.includes('<setup>'),        '<setup> existe');
assert(xmlContent.includes('<identity>'),     '<identity> existe');
assert(xmlContent.includes('<routing>'),      '<routing> existe');
assert(xmlContent.includes('<constraints>'),  '<constraints> existe');

// ─── Rotas têm estrutura completa ─────────────────────────────────────────────
console.log('\n[02] Cada <route> tem <if>, <load> e <then>');
const routePattern = /<route id="([^"]+)">([\s\S]*?)<\/route>/g;
let routeMatch;
const routes = [];
while ((routeMatch = routePattern.exec(xmlContent)) !== null) {
  routes.push({ id: routeMatch[1], body: routeMatch[2] });
}

assert(routes.length > 0, `Pelo menos 1 rota encontrada (encontradas: ${routes.length})`);

for (const route of routes) {
  const hasIf   = route.body.includes('<if>');
  const hasLoad = route.body.includes('<load>');
  const hasThen = route.body.includes('<then>');
  assert(hasIf,   `Rota '${route.id}' tem <if>`);
  assert(hasLoad, `Rota '${route.id}' tem <load>`);
  assert(hasThen, `Rota '${route.id}' tem <then>`);
}

// ─── Arquivos em <load> existem no filesystem ─────────────────────────────────
console.log('\n[03] Arquivos em <load> existem no filesystem');
const loadPattern = /<load>([\s\S]*?)<\/load>/g;
let loadMatch;
const allLoadedFiles = new Set();

while ((loadMatch = loadPattern.exec(xmlContent)) !== null) {
  const block = loadMatch[1];
  const fileRefs = block.match(/base\/[^\s\n`<]+\.md/g) || [];
  for (const ref of fileRefs) {
    allLoadedFiles.add(ref);
  }
}

for (const ref of allLoadedFiles) {
  const abs = path.join(ROOT, ref);
  assert(fs.existsSync(abs), `<load> ${ref} existe em disco`);
}

// ─── Arquivos em <load> estão no INDEX ────────────────────────────────────────
console.log('\n[04] Arquivos em <load> estão no INDEX');
for (const ref of allLoadedFiles) {
  assert(indexContent.includes(ref), `<load> ${ref} está no INDEX`);
}

// ─── Sources de never-rules apontam para elementos existentes ─────────────────
console.log('\n[05] source de <never-rules> aponta para elementos existentes');
const neverSectionMatch = xmlContent.match(/<never-rules>([\s\S]*?)<\/never-rules>/);
if (neverSectionMatch) {
  const neverContent = neverSectionMatch[1];
  const neverSourcePattern = /<rule source="([^"]+)">/g;
  let nm;
  while ((nm = neverSourcePattern.exec(neverContent)) !== null) {
    const src = nm[1];
    if (src === 'system') {
      assert(true, `source 'system' é válido (regra sistêmica)`);
      continue;
    }
    assert(indexContent.includes(src), `never-rule source '${src}' está no INDEX`);
  }
}

// ─── Sources de always-rules apontam para elementos existentes ────────────────
console.log('\n[06] source de <always-rules> aponta para elementos existentes');
const alwaysSectionMatch = xmlContent.match(/<always-rules>([\s\S]*?)<\/always-rules>/);
if (alwaysSectionMatch) {
  const alwaysContent = alwaysSectionMatch[1];
  const alwaysSourcePattern = /<rule source="([^"]+)">/g;
  let am;
  while ((am = alwaysSourcePattern.exec(alwaysContent)) !== null) {
    const src = am[1];
    if (src === 'system') {
      assert(true, `source 'system' é válido (regra sistêmica)`);
      continue;
    }
    assert(indexContent.includes(src), `always-rule source '${src}' está no INDEX`);
  }
}

// ─── Sources de escalation-rules apontam para protocolos existentes ──────────
console.log('\n[07] source de <escalation-rules> aponta para protocolos existentes');
const escalSectionMatch = xmlContent.match(/<escalation-rules>([\s\S]*?)<\/escalation-rules>/);
if (escalSectionMatch) {
  const escalContent = escalSectionMatch[1];
  const escalSourcePattern = /<rule source="([^"]+)">/g;
  let em;
  while ((em = escalSourcePattern.exec(escalContent)) !== null) {
    const src = em[1];
    assert(indexContent.includes(src), `escalation-rule source '${src}' está no INDEX`);
  }
}

// ─── Número de rotas ──────────────────────────────────────────────────────────
console.log('\n[08] Número de rotas');
assert(routes.length >= 10, `Pelo menos 10 rotas definidas (encontradas: ${routes.length})`);
console.log(`  Total de rotas: ${routes.length}`);
console.log(`  IDs: ${routes.map(r => r.id).join(', ')}`);

// ─── Regras meta existem ──────────────────────────────────────────────────────
console.log('\n[09] Regras meta de roteamento');
assert(xmlContent.includes('<cross-domain-rule>'),  '<cross-domain-rule> existe');
assert(xmlContent.includes('<default-rule>'),        '<default-rule> existe');
assert(xmlContent.includes('<type-based-routing>'), '<type-based-routing> existe');
assert(xmlContent.includes('<coverage-gaps>'),       '<coverage-gaps> existe');

// ─── Resumo ───────────────────────────────────────────────────────────────────
console.log(`\n${'─'.repeat(60)}`);
console.log(`Resultado: ${passed} passou, ${failed} falhou`);
if (errors.length > 0) {
  console.error('Falhas:');
  errors.forEach(e => console.error(`  - ${e}`));
  process.exitCode = 1;
} else {
  console.log('Todos os testes de integridade XML passaram ✓');
}
