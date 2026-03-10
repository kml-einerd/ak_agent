'use strict';
/**
 * TESTE 08: Integração — Simulação de Queries do Agent
 * Simula o fluxo completo de uma query ao Akita Agent:
 *   Pergunta → Route match → Load files → Format check
 * Testa as rotas mais críticas com queries reais.
 */

const fs   = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const XML  = path.join(ROOT, 'akita-agent.xml');
const INDEX = path.join(ROOT, 'base/INDEX.md');

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

const xmlContent   = fs.readFileSync(XML, 'utf8');
const indexContent = fs.readFileSync(INDEX, 'utf8');

// ─── Motor de roteamento simplificado ─────────────────────────────────────────
function parseRoutes(xml) {
  const routes = [];
  const rp = /<route id="([^"]+)">([\s\S]*?)<\/route>/g;
  let m;
  while ((m = rp.exec(xml)) !== null) {
    const body = m[2];
    const loadM = body.match(/<load>([\s\S]*?)<\/load>/);
    routes.push({
      id:    m[1],
      files: loadM ? (loadM[1].match(/base\/[^\s\n`<]+\.md/g) || []) : [],
    });
  }
  return routes;
}

function loadElement(rel) {
  const abs = path.join(ROOT, rel);
  if (!fs.existsSync(abs)) return null;
  return fs.readFileSync(abs, 'utf8');
}

const routes = parseRoutes(xmlContent);
const routeMap = {};
routes.forEach(function(r) { routeMap[r.id] = r; });

// ─── Teste de cada rota crítica ───────────────────────────────────────────────
const criticalRoutes = [
  { id: 'ai-project-setup',    desc: 'Iniciar projeto com IA' },
  { id: 'ai-debugging',        desc: 'Debug de erro em sessão IA' },
  { id: 'ai-llm-loop',         desc: 'LLM preso em loop' },
  { id: 'ai-code-quality',     desc: 'Qualidade de código AI-assisted' },
  { id: 'ai-pair-programming', desc: 'Melhores práticas com IA' },
  { id: 'security-audit',      desc: 'Auditoria de segurança de código AI' },
  { id: 'backend-async-jobs',  desc: 'Jobs assíncronos' },
  { id: 'architecture-database', desc: 'Escolha de banco de dados' },
  { id: 'database-backup',     desc: 'Backup de SQLite' },
  { id: 'testing-strategy',    desc: 'Estratégia de testes' },
];

console.log('\n[01] Rotas críticas existem no XML');
for (const cr of criticalRoutes) {
  assert(routeMap[cr.id] !== undefined, "Rota '" + cr.id + "' existe (" + cr.desc + ")");
}

console.log('\n[02] Fluxo completo: rota → arquivos → conteúdo carregável');
for (const cr of criticalRoutes) {
  const route = routeMap[cr.id];
  if (!route) continue;

  for (const file of route.files) {
    const content = loadElement(file);
    assert(content !== null, "Rota '" + cr.id + "' → " + file + " carregável");
    if (content) {
      assert(content.length > 100, "Rota '" + cr.id + "' → " + file + " tem conteúdo substancial (>" + 100 + " chars)");
    }
  }
}

// ─── Teste de setup obrigatório ───────────────────────────────────────────────
console.log('\n[03] INDEX.md pode ser carregado como primeiro passo');
const indexContent2 = loadElement('base/INDEX.md');
assert(indexContent2 !== null, 'INDEX.md carregável');
assert(indexContent2.length > 1000, 'INDEX.md tem conteúdo substancial');
assert(indexContent2.includes('## ELEMENTS BY TYPE'), 'INDEX.md tem seção ELEMENTS BY TYPE');
assert(indexContent2.includes('## ELEMENTS BY DOMAIN'), 'INDEX.md tem seção ELEMENTS BY DOMAIN');

// ─── Teste de limite de carga ─────────────────────────────────────────────────
console.log('\n[04] Simulação de cross-domain: ai-debugging + security-audit (limite 8)');
const aiDebugFiles    = routeMap['ai-debugging']     ? routeMap['ai-debugging'].files     : [];
const secAuditFiles   = routeMap['security-audit']   ? routeMap['security-audit'].files   : [];
const combined        = Array.from(new Set([...aiDebugFiles, ...secAuditFiles]));
assert(combined.length <= 8, 'Cross-domain ai-debugging + security-audit dentro do limite 8 (tem: ' + combined.length + ')');

const aiLoopFiles   = routeMap['ai-llm-loop']      ? routeMap['ai-llm-loop'].files      : [];
const backendFiles  = routeMap['backend-async-jobs'] ? routeMap['backend-async-jobs'].files : [];
const combined2     = Array.from(new Set([...aiLoopFiles, ...backendFiles]));
assert(combined2.length <= 8, 'Cross-domain ai-llm-loop + backend-async-jobs dentro do limite 8 (tem: ' + combined2.length + ')');

// ─── Teste de formato de resposta por rota ────────────────────────────────────
console.log('\n[05] Verificação de formato de elemento por rota crítica');

const FORMAT_SIGNATURES = {
  PROCEDURE:      ['# PROCEDURE:', '## STEPS', '## DONE WHEN'],
  PROTOCOL:       ['# PROTOCOL:', '## EVALUATION'],
  'ANTI-PATTERN': ['# ANTI-PATTERN:', '## SYMPTOMS', '## CORRECTION'],
  HEURISTIC:      ['# HEURISTIC:', '**RULE:**'],
  CONCEPT:        ['# CONCEPT:', '**DEFINITION:**'],
  REFERENCE:      ['# REFERENCE:', '## CONTENT'],
};

// Para rota ai-project-setup — deve ter PROCEDURE e CONCEPT
const setupRoute = routeMap['ai-project-setup'];
if (setupRoute) {
  for (const file of setupRoute.files) {
    const content = loadElement(file);
    if (!content) continue;
    if (file.includes('/procedimentos/')) {
      assert(content.includes('# PROCEDURE:'), file + ' é PROCEDURE válido');
      assert(content.includes('## STEPS'),     file + ' tem ## STEPS');
      assert(content.includes('## DONE WHEN'), file + ' tem ## DONE WHEN');
    }
    if (file.includes('/conceitos/')) {
      assert(content.includes('# CONCEPT:'),      file + ' é CONCEPT válido');
      assert(content.includes('**DEFINITION:**'), file + ' tem **DEFINITION:**');
    }
    if (file.includes('/anti-patterns/')) {
      assert(content.includes('# ANTI-PATTERN:'), file + ' é ANTI-PATTERN válido');
      assert(content.includes('## SYMPTOMS'),     file + ' tem ## SYMPTOMS');
    }
  }
}

// Para rota ai-llm-loop — deve ter PROTOCOL
const loopRoute = routeMap['ai-llm-loop'];
if (loopRoute) {
  for (const file of loopRoute.files) {
    const content = loadElement(file);
    if (!content) continue;
    assert(content.includes('# PROTOCOL:'),  file + ' é PROTOCOL válido');
    assert(content.includes('## EVALUATION') || content.includes('SIGNAL'),
      file + ' tem seção de avaliação');
  }
}

// ─── Teste de fallback (rota default) ─────────────────────────────────────────
console.log('\n[06] Comportamento de fallback documentado');
assert(xmlContent.includes('<default-rule>'),  'default-rule existe no XML');
assert(xmlContent.includes('no routing rule'), 'default-rule tem condição IF no match');

// ─── Resumo total da integração ───────────────────────────────────────────────
console.log('\n[07] Resumo de cobertura da integração');
const totalRoutes    = routes.length;
const testedRoutes   = criticalRoutes.filter(function(cr) { return routeMap[cr.id]; }).length;
const coveragePct    = ((testedRoutes / totalRoutes) * 100).toFixed(0);
console.log('  Total rotas: ' + totalRoutes);
console.log('  Rotas testadas: ' + testedRoutes);
console.log('  Cobertura: ' + coveragePct + '%');
assert(testedRoutes >= 8, 'Pelo menos 8 rotas críticas testadas (testadas: ' + testedRoutes + ')');

console.log('\n' + '-'.repeat(60));
console.log('Resultado: ' + passed + ' passou, ' + failed + ' falhou');
if (errors.length > 0) {
  console.error('Falhas:');
  errors.forEach(function(e) { console.error('  - ' + e); });
  process.exitCode = 1;
} else {
  console.log('Todos os testes de integracao passaram');
}
