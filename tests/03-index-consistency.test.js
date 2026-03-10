'use strict';
/**
 * TESTE 03: Consistência do INDEX.md
 * Verifica que:
 *   a) Cada path listado no INDEX aponta para um arquivo que existe no filesystem
 *   b) Cada arquivo no filesystem está listado no INDEX
 *   c) O INDEX não lista duplicatas
 *   d) Os paths do INDEX usam separador forward-slash (compatibilidade Linux)
 */

const fs   = require('fs');
const path = require('path');

const ROOT     = path.resolve(__dirname, '..');
const INDEX    = path.join(ROOT, 'base/INDEX.md');
const BASE_DIR = path.join(ROOT, 'base');

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

// ─── Extrai todos os paths do INDEX.md ───────────────────────────────────────
const indexContent = fs.readFileSync(INDEX, 'utf8');

// Padrão: `base/TIPO/arquivo.md` dentro de células de tabela markdown
const pathPattern = /base\/[^\s|`]+\.md/g;
const allIndexPaths = [...new Set(indexContent.match(pathPattern) || [])];

console.log(`\n[01] Paths encontrados no INDEX: ${allIndexPaths.length}`);

// ─── Cada path do INDEX deve existir no filesystem ────────────────────────────
console.log('\n[02] Paths do INDEX existem no filesystem');
for (const rel of allIndexPaths) {
  const abs = path.join(ROOT, rel);
  assert(fs.existsSync(abs), `INDEX → ${rel} existe em disco`);
}

// ─── Cada arquivo de elemento deve estar no INDEX ─────────────────────────────
console.log('\n[03] Arquivos do filesystem estão no INDEX');
const elementDirs = ['procedimentos', 'protocolos', 'anti-patterns', 'conceitos', 'heuristicas', 'referencias'];
const fsFiles = [];

for (const dir of elementDirs) {
  const absDir = path.join(BASE_DIR, dir);
  if (!fs.existsSync(absDir)) continue;
  const files = fs.readdirSync(absDir).filter(f => f.endsWith('.md') && !f.startsWith('.'));
  for (const file of files) {
    const rel = `base/${dir}/${file}`;
    fsFiles.push(rel);
    assert(allIndexPaths.includes(rel), `Filesystem → ${rel} está no INDEX`);
  }
}

// ─── Sem duplicatas no INDEX ──────────────────────────────────────────────────
console.log('\n[04] INDEX não contém paths duplicados');
const rawPaths = indexContent.match(pathPattern) || [];
const seen = new Set();
const duplicates = [];
for (const p of rawPaths) {
  if (seen.has(p)) duplicates.push(p);
  seen.add(p);
}
assert(duplicates.length === 0, `Sem paths duplicados (encontrados: ${duplicates.join(', ') || 'nenhum'})`);

// ─── Paths usam forward-slash ─────────────────────────────────────────────────
console.log('\n[05] Paths do INDEX usam forward-slash (sem backslash)');
for (const rel of allIndexPaths) {
  assert(!rel.includes('\\'), `${rel} não usa backslash`);
}

// ─── Contagem por tipo coincide com o que existe ──────────────────────────────
console.log('\n[06] Contagem de elementos por tipo');
const counts = {
  procedimentos: fsFiles.filter(f => f.includes('/procedimentos/')).length,
  protocolos:    fsFiles.filter(f => f.includes('/protocolos/')).length,
  'anti-patterns': fsFiles.filter(f => f.includes('/anti-patterns/')).length,
  conceitos:     fsFiles.filter(f => f.includes('/conceitos/')).length,
  heuristicas:   fsFiles.filter(f => f.includes('/heuristicas/')).length,
  referencias:   fsFiles.filter(f => f.includes('/referencias/')).length,
};
console.log('  Contagem atual por tipo:');
for (const [type, count] of Object.entries(counts)) {
  console.log(`    ${type}: ${count}`);
  assert(count > 0, `Tipo '${type}' tem pelo menos 1 elemento`);
}
const total = Object.values(counts).reduce((a, b) => a + b, 0);
console.log(`  Total: ${total} elementos`);

// ─── Resumo ───────────────────────────────────────────────────────────────────
console.log(`\n${'─'.repeat(60)}`);
console.log(`Resultado: ${passed} passou, ${failed} falhou`);
if (errors.length > 0) {
  console.error('Falhas:');
  errors.forEach(e => console.error(`  - ${e}`));
  process.exitCode = 1;
} else {
  console.log('Todos os testes de consistência do INDEX passaram ✓');
}
