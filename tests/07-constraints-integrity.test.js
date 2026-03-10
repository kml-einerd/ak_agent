'use strict';
/**
 * TESTE 07: Integridade das Constraints
 * Verifica que:
 *   a) O XML tem número razoável de never-rules, always-rules e escalation-rules
 *   b) Cada tipo de formato de resposta está definido
 *   c) Os 6 tipos de elementos têm formato de resposta no XML
 *   d) hard-rules de setup são verificáveis
 *   e) load-scope define o limite de 8 arquivos
 */

const fs   = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const XML  = path.join(ROOT, 'akita-agent.xml');

let passed = 0;
let failed = 0;
const errors = [];

function assert(condition, label) {
  if (condition) {
    console.log('  \u2713 ' + label);
    passed++;
  } else {
    console.error('  \u2717 ' + label);
    failed++;
    errors.push(label);
  }
}

const xml = fs.readFileSync(XML, 'utf8');

function countTag(tag) {
  const pattern = new RegExp('<' + tag + '[^>]*>', 'g');
  const matches = xml.match(pattern);
  return matches ? matches.length : 0;
}

// --- Setup hard-rules
console.log('\n[01] Setup hard-rules');
const hardRulesMatch = xml.match(/<hard-rules>([\s\S]*?)<\/hard-rules>/);
if (hardRulesMatch) {
  const content = hardRulesMatch[1];
  assert(content.includes('INDEX.md'), 'hard-rule: INDEX.md deve ser lido');
  assert(content.includes('element files were loaded'), 'hard-rule: declarar arquivos carregados');
  assert(content.includes('general LLM knowledge'), 'hard-rule: proibir conhecimento geral');
  assert(content.includes('element type'), 'hard-rule: identificar tipo de elemento');
}

// --- Setup mandatory-read
console.log('\n[02] Mandatory-read tem 5 passos');
const mandatoryMatch = xml.match(/<mandatory-read>([\s\S]*?)<\/mandatory-read>/);
if (mandatoryMatch) {
  const steps = mandatoryMatch[1].match(/<step/g) || [];
  assert(steps.length === 5, 'mandatory-read tem 5 passos (encontrados: ' + steps.length + ')');
}

// --- Load scope
console.log('\n[03] Load-scope define limite de 8 arquivos');
const loadScopeMatch = xml.match(/<load-scope>([\s\S]*?)<\/load-scope>/);
if (loadScopeMatch) {
  assert(loadScopeMatch[1].includes('8'), 'load-scope menciona limite de 8');
  assert(loadScopeMatch[1].includes('PROTOCOL'), 'load-scope define prioridade iniciando com PROTOCOL');
}

// --- Never/Always/Escalation rules count
console.log('\n[04] Número de regras nas constraints');
const neverSection   = xml.match(/<never-rules>([\s\S]*?)<\/never-rules>/);
const alwaysSection  = xml.match(/<always-rules>([\s\S]*?)<\/always-rules>/);
const escalSection   = xml.match(/<escalation-rules>([\s\S]*?)<\/escalation-rules>/);

function countRules(section) {
  if (!section) return 0;
  const matches = section[1].match(/<rule /g);
  return matches ? matches.length : 0;
}

const neverCount  = countRules(neverSection);
const alwaysCount = countRules(alwaysSection);
const escalCount  = countRules(escalSection);

console.log('  never-rules: ' + neverCount);
console.log('  always-rules: ' + alwaysCount);
console.log('  escalation-rules: ' + escalCount);

assert(neverCount  >= 10, 'Pelo menos 10 never-rules (encontradas: ' + neverCount + ')');
assert(alwaysCount >= 8,  'Pelo menos 8 always-rules (encontradas: ' + alwaysCount + ')');
assert(escalCount  >= 5,  'Pelo menos 5 escalation-rules (encontradas: ' + escalCount + ')');

// --- Response formats para os 6 tipos
console.log('\n[05] Response-format definido para os 6 tipos de elementos');
const responseFormatsMatch = xml.match(/<response-format>([\s\S]*?)<\/response-format>/);
if (responseFormatsMatch) {
  const rfContent = responseFormatsMatch[1];
  const requiredTypes = ['PROCEDURE', 'PROTOCOL', 'ANTI-PATTERN', 'HEURISTIC', 'CONCEPT', 'REFERENCE'];
  for (const type of requiredTypes) {
    assert(rfContent.includes('type="' + type + '"'), 'response-format para tipo ' + type + ' existe');
  }
}

// --- Identity sections
console.log('\n[06] Identity tem what-it-is e what-it-is-not');
const identityMatch = xml.match(/<identity>([\s\S]*?)<\/identity>/);
if (identityMatch) {
  assert(identityMatch[1].includes('<what-it-is>'),     '<what-it-is> definido');
  assert(identityMatch[1].includes('<what-it-is-not>'), '<what-it-is-not> definido');
  assert(identityMatch[1].includes('<operational-objective>'), '<operational-objective> definido');
  assert(identityMatch[1].includes('<quality-standard>'),      '<quality-standard> definido');
}

// --- Coverage gaps documentados
console.log('\n[07] Coverage gaps documentados');
const gapsMatch = xml.match(/<coverage-gaps>([\s\S]*?)<\/coverage-gaps>/);
if (gapsMatch) {
  const gaps = gapsMatch[1].match(/<gap>/g) || [];
  assert(gaps.length >= 4, 'Pelo menos 4 coverage gaps documentados (encontrados: ' + gaps.length + ')');
  assert(gapsMatch[1].includes('CI/CD'),          'Gap CI/CD documentado');
  assert(gapsMatch[1].toLowerCase().includes('authentication'), 'Gap authentication documentado');
}

console.log('\n' + '-'.repeat(60));
console.log('Resultado: ' + passed + ' passou, ' + failed + ' falhou');
if (errors.length > 0) {
  console.error('Falhas:');
  errors.forEach(function(e) { console.error('  - ' + e); });
  process.exitCode = 1;
} else {
  console.log('Todos os testes de integridade das constraints passaram');
}
