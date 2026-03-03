/**
 * TEST-01: Knowledge Base Structural Integrity
 *
 * Verifies that INDEX.md and the file system are fully consistent.
 * These tests define the MINIMUM baseline — all should pass.
 * If any fail, the knowledge base has a broken reference.
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

// Extract all `base/type/file.md` paths from INDEX.md tables
function extractIndexPaths() {
  const content = fs.readFileSync(INDEX_PATH, 'utf8');
  const matches = content.match(/base\/[\w-]+\/[\w-]+\.md/g) || [];
  return [...new Set(matches)]; // deduplicate
}

// Get all actual element .md files from base/ subdirectories
function getActualElementFiles() {
  const ELEMENT_DIRS = ['procedimentos', 'protocolos', 'anti-patterns', 'conceitos', 'heuristicas', 'referencias'];
  const files = [];
  for (const dir of ELEMENT_DIRS) {
    const dirPath = path.join(BASE_DIR, dir);
    if (!fs.existsSync(dirPath)) continue;
    fs.readdirSync(dirPath)
      .filter(f => f.endsWith('.md') && f !== '.gitkeep')
      .forEach(f => files.push(`base/${dir}/${f}`));
  }
  return files;
}

describe('01 — Knowledge Base Integrity', () => {

  test('INDEX.md exists', () => {
    assert.ok(fs.existsSync(INDEX_PATH), `INDEX.md not found at: ${INDEX_PATH}`);
  });

  test('akita-agent.xml exists', () => {
    assert.ok(fs.existsSync(XML_PATH), `akita-agent.xml not found at: ${XML_PATH}`);
  });

  test('all element directories exist', () => {
    const dirs = ['procedimentos', 'protocolos', 'anti-patterns', 'conceitos', 'heuristicas', 'referencias'];
    const missing = dirs.filter(d => !fs.existsSync(path.join(BASE_DIR, d)));
    assert.deepStrictEqual(missing, [], `Missing directories: ${missing.join(', ')}`);
  });

  test('all file paths in INDEX.md exist on disk', () => {
    const indexPaths = extractIndexPaths();
    assert.ok(indexPaths.length >= 94, `Expected >= 94 paths in INDEX.md, found ${indexPaths.length}`);
    const missing = indexPaths.filter(p => !fs.existsSync(path.join(ROOT, p)));
    assert.deepStrictEqual(
      missing, [],
      `Files listed in INDEX.md but NOT found on disk:\n  ${missing.join('\n  ')}`
    );
  });

  test('all disk element files are registered in INDEX.md', () => {
    const indexPaths = new Set(extractIndexPaths());
    const actualFiles = getActualElementFiles();
    const unregistered = actualFiles.filter(f => !indexPaths.has(f));
    assert.deepStrictEqual(
      unregistered, [],
      `Files on disk but NOT in INDEX.md:\n  ${unregistered.join('\n  ')}`
    );
  });

  test('element count matches INDEX.md declaration (94 elements)', () => {
    const actualFiles = getActualElementFiles();
    assert.strictEqual(
      actualFiles.length, 94,
      `Expected 94 element files on disk, found ${actualFiles.length}`
    );
  });

  test('element counts by type match INDEX.md totals', () => {
    const expected = {
      procedimentos: 17,
      protocolos: 17,
      'anti-patterns': 14,
      conceitos: 14,
      heuristicas: 30,
      referencias: 2,
    };
    for (const [dir, count] of Object.entries(expected)) {
      const dirPath = path.join(BASE_DIR, dir);
      const actual = fs.readdirSync(dirPath).filter(f => f.endsWith('.md') && f !== '.gitkeep').length;
      assert.strictEqual(
        actual, count,
        `${dir}: expected ${count} elements, found ${actual}`
      );
    }
  });

});
