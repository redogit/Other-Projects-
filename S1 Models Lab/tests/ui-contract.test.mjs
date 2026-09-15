import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const root = new URL('../', import.meta.url);

async function text(name) {
  return readFile(new URL(name, root), 'utf8');
}

test('README preserves experiment claim ceilings', async () => {
  const readme = await text('README.md');
  for (const required of [
    'synthetic observer/reference surface',
    'SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION',
    'real 4D != complex dimension 4',
    "S'1_Mirror",
    "S'1_Experience",
    "S'1_Suggest",
    "S'1_ObserverField"
  ]) assert.match(readme, new RegExp(required.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
});

test('schema declares the exact v0 identity', async () => {
  const schema = JSON.parse(await text('schema/s1-experience-v0.schema.json'));
  assert.equal(schema.$id, 's1-experience/v0');
  assert.deepEqual(schema.properties.operatorVersion.const, "S'1-Ops v0");
  assert.deepEqual(schema.properties.observerField.properties.version.const, 's1-observer-field/v0');
});
