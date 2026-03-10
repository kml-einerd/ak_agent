'use strict';
/**
 * Runner principal — executa todos os testes em sequência
 * Uso: node tests/run-all.js
 */

const path = require('path');
const { spawnSync } = require('child_process');

const TESTS = [
  '01-filesystem-integrity.test.js',
  '02-element-format.test.js',
  '03-index-consistency.test.js',
  '04-xml-routing-integrity.test.js',
  '05-cross-references.test.js',
  '06-routing-logic.test.js',
  '07-constraints-integrity.test.js',
  '08-integration.test.js',
];

const GROUPS = {
  'Unidade - Filesystem':   ['01-filesystem-integrity.test.js'],
  'Unidade - Elementos':    ['02-element-format.test.js'],
  'Grupo - Consistência':   ['03-index-consistency.test.js', '04-xml-routing-integrity.test.js'],
  'Grupo - Relações':       ['05-cross-references.test.js', '06-routing-logic.test.js'],
  'Grupo - Regras':         ['07-constraints-integrity.test.js'],
  'Integração - End-to-End': ['08-integration.test.js'],
};

const WIDTH = 70;

function header(title) {
  const pad  = Math.max(0, WIDTH - title.length - 4);
  const left = Math.floor(pad / 2);
  const right = pad - left;
  console.log('\n' + '='.repeat(WIDTH));
  console.log('= ' + ' '.repeat(left) + title + ' '.repeat(right) + ' =');
  console.log('='.repeat(WIDTH));
}

const summary = [];
let globalPass = true;

// Executa por grupo
for (const [groupName, files] of Object.entries(GROUPS)) {
  header(groupName);
  for (const file of files) {
    const filePath = path.join(__dirname, file);
    console.log('\nExecutando: ' + file);
    console.log('-'.repeat(40));

    const result = spawnSync(process.execPath, [filePath], {
      cwd: path.resolve(__dirname, '..'),
      stdio: 'inherit',
      env: process.env,
    });

    const ok = result.status === 0;
    summary.push({ file, ok });
    if (!ok) globalPass = false;
  }
}

// Resumo final
header('RESUMO FINAL');
console.log('');
for (const s of summary) {
  const icon = s.ok ? '\u2713' : '\u2717';
  const status = s.ok ? 'PASSOU' : 'FALHOU';
  console.log('  ' + icon + ' ' + status + '  ' + s.file);
}

const totalPass = summary.filter(function(s) { return s.ok; }).length;
const totalFail = summary.filter(function(s) { return !s.ok; }).length;

console.log('');
console.log('Total: ' + summary.length + ' suítes | ' + totalPass + ' passaram | ' + totalFail + ' falharam');

if (!globalPass) {
  console.error('\nFALHA: Algumas suítes falharam.');
  process.exit(1);
} else {
  console.log('\nSUCESSO: Todas as suítes passaram.');
}
