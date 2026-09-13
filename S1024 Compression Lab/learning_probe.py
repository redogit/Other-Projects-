#!/usr/bin/env python3
"""Declared tiny learned-compression experiment; no human learning claim.

Train on one 1,024-byte section, freeze a periodic-byte model, then evaluate
previously unused sections. Period choices are fixed before observing holdout.
Standalone byte counts charge both the period dictionary and all exceptions.
The raw alternative is retained whenever compression would expand the payload.
"""
from __future__ import annotations
import struct
from sections1024 import SECTION_BYTES
PERIODS = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)


def encode_periodic(data: bytes, pattern: bytes) -> bytes:
    if len(data) != SECTION_BYTES: raise ValueError('requires exactly 1,024 bytes')
    if not 1 <= len(pattern) <= SECTION_BYTES: raise ValueError('invalid pattern length')
    exceptions = [(i, byte) for i, byte in enumerate(data)
                  if byte != pattern[i % len(pattern)]]
    return (b'P' + struct.pack('>HH', len(pattern), len(exceptions)) + pattern +
            b''.join(struct.pack('>HB', i, byte) for i, byte in exceptions))


def decode_payload(payload: bytes) -> bytes:
    if payload[:1] == b'R':
        if len(payload) != SECTION_BYTES + 1: raise ValueError('invalid raw record')
        return payload[1:]
    if payload[:1] != b'P' or len(payload) < 6: raise ValueError('invalid period record')
    p, n = struct.unpack('>HH', payload[1:5])
    if not 1 <= p <= SECTION_BYTES or n > SECTION_BYTES or len(payload) != 5 + p + 3 * n:
        raise ValueError('invalid period lengths')
    pattern = payload[5:5+p]
    out = bytearray(pattern[i % p] for i in range(SECTION_BYTES))
    previous = -1
    for i in range(n):
        offset, byte = struct.unpack('>HB', payload[5+p+3*i:8+p+3*i])
        if not previous < offset < SECTION_BYTES or byte == out[offset]:
            raise ValueError('noncanonical exception')
        out[offset], previous = byte, offset
    return bytes(out)


def fit_period(training: bytes) -> tuple[bytes, dict]:
    if len(training) != SECTION_BYTES: raise ValueError('wrong training size')
    # Selection sees training only. Raw fallback is a later transmission gate.
    scored = [(len(encode_periodic(training, training[:p])), p) for p in PERIODS]
    cost, p = min(scored)
    return training[:p], {'period': p, 'training_standalone_bytes': cost,
                         'candidate_periods': list(PERIODS),
                         'raw_standalone_bytes': SECTION_BYTES + 1}


def evaluate_frozen(data: bytes, pattern: bytes) -> tuple[dict, bytes]:
    model_packet = encode_periodic(data, pattern)
    raw_packet = b'R' + data
    selected = model_packet if len(model_packet) < len(raw_packet) else raw_packet
    if decode_payload(model_packet) != data or decode_payload(selected) != data:
        raise AssertionError('learning codec does not preserve bytes')
    return {'model_bytes': 3 + len(pattern),
            'residual_and_count_bytes': len(model_packet) - 3 - len(pattern),
            'model_plus_residual_bytes': len(model_packet),
            'raw_record_bytes': len(raw_packet),
            'signed_candidate_gain_bytes': len(raw_packet) - len(model_packet),
            'selected_record_bytes': len(selected),
            'selected': 'PERIODIC' if selected[:1] == b'P' else 'RAW',
            'lossless_round_trip': True,
            'model_frozen_before_test': True}, selected
