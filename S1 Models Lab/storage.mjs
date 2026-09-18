import { validateExperience, replayIdentity, replayDescriptor, canonicalJson } from './experience.mjs';
import { guardDigestCollision } from './integrity.mjs';

export class MemoryStore {
  constructor() { this.map = new Map(); this.writeCount = 0; }
  getItem(key) { return this.map.has(key) ? this.map.get(key) : null; }
  setItem(key, value) { this.writeCount++; this.map.set(String(key), String(value)); }
  removeItem(key) { this.writeCount++; this.map.delete(String(key)); }
}

function freezeRows(rows) {
  return Object.freeze(rows.map(row => Object.freeze({ event: row.event, occurrences: row.occurrences })));
}

export function coalesceExperienceRows(
  rows,
  { identityFor = replayIdentity, descriptorFor = replayDescriptor } = {}
) {
  if (!Array.isArray(rows)) throw new TypeError('stored payload must be an array');
  if (typeof identityFor !== 'function' || typeof descriptorFor !== 'function') {
    throw new TypeError('identityFor and descriptorFor must be functions');
  }
  const merged = [];
  const byId = new Map();
  const descriptorsByDigest = new Map();
  for (const row of rows) {
    if (!row || typeof row !== 'object' || !Number.isSafeInteger(row.occurrences) || row.occurrences < 1) {
      throw new TypeError('invalid stored row');
    }
    const event = validateExperience(row.event);
    const identity = identityFor(event);
    const descriptor = descriptorFor(event);
    if (typeof identity !== 'string' || !identity) throw new TypeError('replay identity must be a non-empty string');
    if (typeof descriptor !== 'string') throw new TypeError('replay descriptor must be a string');
    guardDigestCollision(descriptorsByDigest, identity, descriptor, 'replay');
    const existing = byId.get(identity);
    if (existing) {
      const total = existing.occurrences + row.occurrences;
      if (!Number.isSafeInteger(total)) throw new RangeError('occurrence total exceeds safe integer range');
      existing.occurrences = total;
    } else {
      const normalized = { event, occurrences: row.occurrences };
      byId.set(identity, normalized);
      merged.push(normalized);
    }
  }
  return merged;
}

export class LocalExperienceStore {
  constructor(storage, key = 's1-experience-v0') {
    if (!storage || typeof storage.getItem !== 'function' || typeof storage.setItem !== 'function' || typeof storage.removeItem !== 'function') {
      throw new TypeError('storage must implement getItem/setItem/removeItem');
    }
    if (typeof key !== 'string' || !key) throw new TypeError('storage key is required');
    this.storage = storage;
    this.key = key;
  }

  _validateRows(rows) {
    return coalesceExperienceRows(rows);
  }

  list() {
    const raw = this.storage.getItem(this.key);
    if (raw === null) return Object.freeze([]);
    let parsed;
    try { parsed = JSON.parse(raw); } catch { throw new SyntaxError('stored S1 history is corrupt JSON'); }
    return freezeRows(this._validateRows(parsed));
  }

  _write(rows) {
    this.storage.setItem(this.key, canonicalJson(rows));
  }

  save(record) {
    const event = validateExperience(record);
    const rows = this.list().map(row => ({ event: row.event, occurrences: row.occurrences }));
    const merged = coalesceExperienceRows([...rows, { event, occurrences: 1 }]);
    this._write(merged);
    return event.id;
  }

  replaceAll(records) {
    const rows = records.map(item => item?.event ? item : { event: item, occurrences: 1 });
    const validated = this._validateRows(rows);
    this._write(validated);
  }

  clear() { this.storage.removeItem(this.key); }
  exportJson() { return canonicalJson(this.list()); }

  importJson(text) {
    if (typeof text !== 'string') throw new TypeError('import must be JSON text');
    let parsed;
    try { parsed = JSON.parse(text); } catch { throw new SyntaxError('import is not valid JSON'); }
    const validated = this._validateRows(parsed);
    this._write(validated);
    return validated.length;
  }
}
