import assert from 'node:assert/strict';
import { test } from 'node:test';
import { getPaperFields } from '../../src/lib/paper-fields.ts';

const fields = (title, topics = [], id = '') => getPaperFields({ id, title, topics });

test('banking, international finance and corporate finance can overlap', () => {
  const result = fields('Banks’ Foreign Currency Exposure and the Real Effects of Exchange Rate Shocks');
  assert.ok(result.includes('Banking'));
  assert.ok(result.includes('International Finance'));
  assert.ok(fields('Does Board Size Matter?').includes('Corporate Finance'));
});

test('household and real estate finance retain both labels', () => {
  assert.deepEqual(fields('Household Mortgage Decisions'), ['Banking', 'Household Finance', 'Real Estate']);
});

test('known topic aliases supplement titles without duplicate fields', () => {
  assert.deepEqual(fields('A General Study', ['banking', 'Financial intermediation', 'Labor']), ['Banking', 'Labor & Human Capital']);
  assert.deepEqual(fields('A General Study', ['General interest']), ['Unclassified']);
});

test('ambiguous titles and unrelated substrings stay unclassified', () => {
  assert.deepEqual(fields('Succession'), ['Unclassified']);
  assert.deepEqual(fields('Repairing Paintings'), ['Unclassified']);
  assert.deepEqual(fields('A General Study', ['Unclassified', 'Asset pricing']), ['Asset Pricing']);
});

test('unicode hyphens and cross-field technology work', () => {
  assert.ok(fields('Non‑Bank Lending').includes('Banking'));
  assert.ok(fields('Artificial Intelligence and Debt Collection').includes('FinTech & AI'));
  assert.ok(fields('Biodiversity Transition Risk and Corporate Employment').includes('Sustainable Finance'));
  assert.ok(fields('Biodiversity Transition Risk and Corporate Employment').includes('Labor & Human Capital'));
});

test('the verified regulatory avoidance paper is accessible under banking', () => {
  assert.ok(fields('Strategically Staying Small: The Consequences of Regulatory Avoidance', [], 'author-roster-20261014-ec6c79c18c81').includes('Banking'));
});
