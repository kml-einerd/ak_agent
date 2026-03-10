'use strict';
/**
 * TESTE 06: Lógica de Routing
 * Simula o motor de roteamento do akita-agent.xml e verifica que:
 *   a) Cada rota carrega pelo menos 1 arquivo
 *   b) Nenhuma rota ultrapassa o limite de 8 arquivos
 *   c) O tipo de resposta de cada rota corresponde ao tipo de elemento carregado
 *   d) A rota default não carrega arquivos de elementos
 *   e) Domínios principais têm pelo menos 1 rota
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

const xmlContent = fs.readFileSync(XML, 'utf8');

function parseRoutes(xml) {
  const routes = [];
  const routePattern = /<route id="([^"]+)">([\s\S]*?)<\/route>/g;
  let m;
  while ((m = routePattern.exec(xml)) !== null) {
    const id   = m[1];
    const body = m[2];
    const ifMatch   = body.match(/<if>([\s\S]*?)<\/if>/);
    const loadMatch = body.match(/<load>([\s\S]*?)<\/load>/);
    const thenMatch = body.match(/<then>([\s\S]*?)<\/then>/);
    const files = loadMatch ? (loadMatch[1].match(/base\/[^\s\n`<]+\.md/g) || []) : [];
    routes.push({
      id,
      condition: ifMatch  ? ifMatch[1].trim()  : '',
      files,
      response:  thenMatch ? thenMatch[1].trim() : '',
    });
  }
  return routes;
}

const routes = parseRoutes(xmlContent);

console.log('\n[01] Cada rota carrega pelo menos 1 arquivo');
for (const route of routes) {
  assert(route.files.length >= 1, "Rota '" + route.id + "' carrega " + route.files.length + " arquivo(s)");
}

console.log('\n[02] Nenhuma rota ultrapassa o limite de 8 arquivos');
for (const route of routes) {
  assert(route.files.length <= 8, "Rota '" + route.id + "' tem " + route.files.length + " arquivo(s) (max 8)");
}

console.log('\n[03] <then> menciona o tipo de elemento carregado');
function detectElementType(filePath) {
  if (filePath.includes('/procedimentos/'))  return 'PROCEDURE';
  if (filePath.includes('/protocolos/'))     return 'PROTOCOL';
  if (filePath.includes('/anti-patterns/'))  return 'ANTI-PATTERN';
  if (filePath.includes('/conceitos/'))      return 'CONCEPT';
  if (filePath.includes('/heuristicas/'))    return 'HEURISTIC';
  if (filePath.includes('/referencias/'))    return 'REFERENCE';
  return 'UNKNOWN';
}

// Verifica que o <then> menciona pelo menos o tipo PRIMARY da rota
// (o tipo mais frequente ou de maior prioridade entre os arquivos carregados)
for (const route of routes) {
  const typeCounts = {};
  for (const f of route.files) {
    const t = detectElementType(f);
    if (t !== 'UNKNOWN') typeCounts[t] = (typeCounts[t] || 0) + 1;
  }
  // Tipo primário = o que aparece mais (ou PROTOCOL se empate)
  const PRIORITY = ['PROTOCOL','PROCEDURE','ANTI-PATTERN','HEURISTIC','CONCEPT','REFERENCE'];
  let primaryType = null;
  let maxCount = 0;
  for (const ptype of PRIORITY) {
    if ((typeCounts[ptype] || 0) > maxCount) {
      maxCount = typeCounts[ptype];
      primaryType = ptype;
    }
  }
  if (!primaryType) continue;
  const thenMentions = route.response.toUpperCase().includes(primaryType);
  assert(thenMentions, "Rota '" + route.id + "' <then> menciona tipo primário '" + primaryType + "'");
}

console.log('\n[04] Sem arquivos duplicados dentro de uma rota');
for (const route of routes) {
  const unique = new Set(route.files);
  assert(unique.size === route.files.length,
    "Rota '" + route.id + "' sem duplicatas (" + route.files.length + " arquivos)");
}

console.log('\n[05] Domínios principais têm pelo menos 1 rota');
const domainChecks = {
  'ai-workflow': routes.filter(function(r) { return r.id.startsWith('ai-'); }),
  'security':    routes.filter(function(r) { return r.id.startsWith('security-'); }),
  'frontend':    routes.filter(function(r) { return r.id.startsWith('frontend-'); }),
  'backend':     routes.filter(function(r) { return r.id.startsWith('backend-'); }),
  'architecture':routes.filter(function(r) { return r.id.startsWith('architecture-'); }),
  'database/deployment': routes.filter(function(r) { return r.id.startsWith('database-') || r.id.startsWith('deployment-'); }),
  'testing':     routes.filter(function(r) { return r.id.startsWith('testing-'); }),
};
for (const domain in domainChecks) {
  assert(domainChecks[domain].length >= 1,
    "Domínio '" + domain + "' tem " + domainChecks[domain].length + " rota(s)");
}

console.log('\n[06] Regras meta de roteamento');
assert(xmlContent.includes('<cross-domain-rule>'), '<cross-domain-rule> definida');
const crossDomainMatch = xmlContent.match(/<cross-domain-rule>([\s\S]*?)<\/cross-domain-rule>/);
if (crossDomainMatch) {
  assert(crossDomainMatch[1].includes('8'), 'Cross-domain rule menciona limite de 8 arquivos');
  assert(
    crossDomainMatch[1].includes('PROTOCOL') && crossDomainMatch[1].includes('PROCEDURE'),
    'Cross-domain rule define prioridade PROTOCOL > PROCEDURE'
  );
}

console.log('\n[07] Default rule carrega apenas INDEX.md e faz pergunta de clarificação');
const defaultMatch = xmlContent.match(/<default-rule>([\s\S]*?)<\/default-rule>/);
if (defaultMatch) {
  assert(defaultMatch[1].includes('INDEX.md'), 'Default rule carrega INDEX.md');
  assert(
    defaultMatch[1].includes('clarifying question') || defaultMatch[1].includes('one clarifying'),
    'Default rule faz UMA pergunta de clarificação'
  );
}

console.log('\n[08] Estatísticas de routing');
const totalFiles = routes.reduce(function(sum, r) { return sum + r.files.length; }, 0);
const avgFiles   = (totalFiles / routes.length).toFixed(1);
console.log('  Total rotas: ' + routes.length);
console.log('  Total arquivos referenciados: ' + totalFiles);
console.log('  Média arquivos por rota: ' + avgFiles);
assert(parseFloat(avgFiles) >= 1.5, 'Média de arquivos por rota >= 1.5 (atual: ' + avgFiles + ')');

console.log('\n' + '-'.repeat(60));
console.log('Resultado: ' + passed + ' passou, ' + failed + ' falhou');
if (errors.length > 0) {
  console.error('Falhas:');
  errors.forEach(function(e) { console.error('  - ' + e); });
  process.exitCode = 1;
} else {
  console.log('Todos os testes de lógica de routing passaram');
}
