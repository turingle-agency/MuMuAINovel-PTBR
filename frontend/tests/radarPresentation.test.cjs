const assert = require('node:assert/strict');
const { join } = require('node:path');
const { test } = require('node:test');

const { shouldPoll, canCreateBrief } = require(join(
  process.env.RADAR_TEST_BUILD_DIR, 'utils', 'radarPresentation.js',
));

test('acompanha apenas pesquisas pendentes ou em execução', () => {
  for (const status of ['pending', 'running']) assert.equal(shouldPoll(status), true);
  for (const status of ['complete', 'partial', 'failed']) assert.equal(shouldPoll(status), false);
});

test('permite briefing de resultado parcial com evidência citável', () => {
  assert.equal(canCreateBrief({ status: 'partial', citable_count: 1, legacy: false }), true);
  assert.equal(canCreateBrief({ status: 'complete', citable_count: 1, legacy: false }), true);
  assert.equal(canCreateBrief({ status: 'partial', citable_count: 0, legacy: false }), false);
  assert.equal(canCreateBrief({ status: 'running', citable_count: 1, legacy: false }), false);
  assert.equal(canCreateBrief({ status: 'failed', citable_count: 1, legacy: false }), false);
  assert.equal(canCreateBrief({ status: 'complete', citable_count: 1, legacy: true }), false);
});
