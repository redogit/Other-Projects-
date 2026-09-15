function finitePositiveInt(value, name, min = 2) {
  if (!Number.isInteger(value) || value < min) throw new RangeError(`${name} must be an integer >= ${min}`);
}

function finitePositive(value, name) {
  if (!Number.isFinite(value) || value <= 0) throw new RangeError(`${name} must be finite and positive`);
}

function frozenPoint(values) {
  return Object.freeze(values.map(v => Object.is(v, -0) ? 0 : v));
}

export function sampleS3({etaSteps=7, xi1Steps=16, xi2Steps=16, radius=1.6} = {}) {
  finitePositiveInt(etaSteps, 'etaSteps');
  finitePositiveInt(xi1Steps, 'xi1Steps', 3);
  finitePositiveInt(xi2Steps, 'xi2Steps', 3);
  finitePositive(radius, 'radius');
  const points4 = [];
  const groups = [];
  for (let e = 0; e < etaSteps; e++) {
    const eta = (Math.PI / 2) * (e / (etaSteps - 1));
    const indices = [];
    for (let i = 0; i < xi1Steps; i++) {
      const xi1 = 2 * Math.PI * (i / xi1Steps);
      for (let j = 0; j < xi2Steps; j++) {
        const xi2 = 2 * Math.PI * (j / xi2Steps);
        const p = frozenPoint([
          radius * Math.cos(eta) * Math.cos(xi1),
          radius * Math.cos(eta) * Math.sin(xi1),
          radius * Math.sin(eta) * Math.cos(xi2),
          radius * Math.sin(eta) * Math.sin(xi2)
        ]);
        indices.push(points4.length);
        points4.push(p);
      }
    }
    groups.push(Object.freeze({ band: `eta-${e}`, pointIndices: Object.freeze(indices) }));
  }
  return Object.freeze({ id: 's3-sample', points4: Object.freeze(points4), groups: Object.freeze(groups) });
}

export function sampleTesseractBoundary({steps=4, halfExtent=1.4} = {}) {
  finitePositiveInt(steps, 'steps');
  finitePositive(halfExtent, 'halfExtent');
  const coords = Array.from({length: steps}, (_, i) => -halfExtent + (2 * halfExtent * i) / (steps - 1));
  const points4 = [];
  const indexByKey = new Map();
  const groups = [];
  const axes = ['x','y','z','w'];
  for (let axis = 0; axis < 4; axis++) {
    for (const sign of [-1, 1]) {
      const cell = `${axes[axis]}${sign < 0 ? '-' : '+'}`;
      const indices = [];
      for (const a of coords) for (const b of coords) for (const c of coords) {
        const p = [0,0,0,0];
        p[axis] = sign * halfExtent;
        const free = [0,1,2,3].filter(i => i !== axis);
        p[free[0]] = a; p[free[1]] = b; p[free[2]] = c;
        const normalized = p.map(v => Object.is(v, -0) ? 0 : v);
        const key = normalized.map(v => v.toPrecision(15)).join('|');
        let idx = indexByKey.get(key);
        if (idx === undefined) {
          idx = points4.length;
          indexByKey.set(key, idx);
          points4.push(frozenPoint(normalized));
        }
        indices.push(idx);
      }
      groups.push(Object.freeze({ cell, pointIndices: Object.freeze([...new Set(indices)]) }));
    }
  }
  return Object.freeze({ id: 'tesseract-boundary', points4: Object.freeze(points4), groups: Object.freeze(groups) });
}
