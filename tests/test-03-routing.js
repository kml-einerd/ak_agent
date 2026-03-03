/**
 * TEST-03: Routing Coverage
 *
 * Verifies that every element in INDEX.md is reachable via at least one
 * route in akita-agent.xml. An element with no route is a dead element —
 * the agent can never load it, making it invisible to users.
 *
 * EXPECTED STATE: MANY TESTS WILL FAIL (RED phase).
 * Self-hosting and ai-image-generation domains have NO routes in akita-agent.xml.
 * Several newer ai-workflow elements also lack routes.
 *
 * GREEN phase: add route definitions to akita-agent.xml for missing elements.
 */
'use strict';

const { test, describe } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const BASE_DIR = path.join(ROOT, 'base');
const INDEX_PATH = path.join(BASE_DIR, 'INDEX.md');
const XML_PATH = path.join(ROOT, 'akita-agent.xml');

// Extract all file paths referenced in <load> blocks of akita-agent.xml
function extractRoutedPaths() {
  const xml = fs.readFileSync(XML_PATH, 'utf8');
  const matches = xml.match(/base\/[\w-]+\/[\w-]+\.md/g) || [];
  return new Set(matches);
}

// Extract all element file paths from INDEX.md
function extractIndexPaths() {
  const content = fs.readFileSync(INDEX_PATH, 'utf8');
  const matches = content.match(/base\/[\w-]+\/[\w-]+\.md/g) || [];
  return [...new Set(matches)];
}

// Extract all paths referenced in XML <load> blocks but not in INDEX.md
// (dead references — routes pointing to non-existent elements)
function extractDeadRoutes() {
  const xml = fs.readFileSync(XML_PATH, 'utf8');
  const routedPaths = xml.match(/base\/[\w-]+\/[\w-]+\.md/g) || [];
  const indexPaths = new Set(extractIndexPaths());
  return [...new Set(routedPaths)].filter(p => !indexPaths.has(p));
}

describe('03 — Routing Coverage', () => {

  test('akita-agent.xml has no dead routes (paths not in INDEX.md)', () => {
    const dead = extractDeadRoutes();
    assert.deepStrictEqual(
      dead, [],
      `Routes in XML pointing to non-existent elements:\n  ${dead.join('\n  ')}`
    );
  });

  // Every element in INDEX.md must appear in at least one <load> block
  const routedPaths = extractRoutedPaths();
  const indexPaths = extractIndexPaths();

  for (const elementPath of indexPaths) {
    test(`${elementPath}: has at least one route in akita-agent.xml`, () => {
      assert.ok(
        routedPaths.has(elementPath),
        `No route loads "${elementPath}" — element is unreachable by the agent`
      );
    });
  }

});
