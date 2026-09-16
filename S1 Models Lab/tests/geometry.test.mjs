import test from 'node:test';
import assert from 'node:assert/strict';
import { sampleS3, sampleTesseractBoundary } from '../geometry.mjs';

test('S3 samples lie on declared radius and are deterministic', () => {
  const radius = 1.6;
  const a = sampleS3({etaSteps:4, xi1Steps:8, xi2Steps:8, radius});
  const b = sampleS3({etaSteps:4, xi1Steps:8, xi2Steps:8, radius});
  assert.deepEqual(a, b);
  assert.equal(a.id, 's3-sample');
  assert.ok(a.points4.length > 0);
  for (const p of a.points4) {
    const norm2 = p.reduce((s,x) => s + x*x, 0);
    assert.ok(Math.abs(norm2 - radius*radius) < 1e-10);
  }
});

test('tesseract boundary samples expose all eight signed cells', () => {
  const halfExtent = 1.4;
  const out = sampleTesseractBoundary({steps:3, halfExtent});
  assert.equal(out.id, 'tesseract-boundary');
  const cells = new Set(out.groups.map(g => g.cell));
  assert.deepEqual([...cells].sort(), ['w+','w-','x+','x-','y+','y-','z+','z-']);
  for (const p of out.points4) {
    assert.ok(p.some(v => Math.abs(Math.abs(v) - halfExtent) < 1e-12));
  }
});
