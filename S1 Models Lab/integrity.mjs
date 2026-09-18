export function guardDigestCollision(index, digest, canonical, label = 'payload') {
  if (!(index instanceof Map)) throw new TypeError('index must be a Map');
  if (typeof digest !== 'string' || !digest) throw new TypeError('digest must be a non-empty string');
  if (typeof canonical !== 'string') throw new TypeError('canonical payload must be a string');
  if (typeof label !== 'string' || !label) throw new TypeError('label must be a non-empty string');
  if (index.has(digest)) {
    const prior = index.get(digest);
    if (prior !== canonical) throw new RangeError(`${label} digest collision: equal digest names unequal canonical payloads`);
    return prior;
  }
  index.set(digest, canonical);
  return canonical;
}
