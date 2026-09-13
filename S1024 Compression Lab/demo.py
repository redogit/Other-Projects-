#!/usr/bin/env python3
"""Reproduce a bounded frozen-period experiment. Does not use cultural records."""
import json
import random
from learning_probe import fit_period, evaluate_frozen
from sections1024 import frame, unframe, UTF8Space


def run():
    training = b'ABCD1234' * 128
    pattern, fit = fit_period(training)
    heldout = bytearray(training)
    heldout[700] ^= 1
    drift = random.Random(20260913).randbytes(1024)
    related, _ = evaluate_frozen(bytes(heldout), pattern)
    shifted, _ = evaluate_frozen(drift, pattern)
    transport = frame(training)
    if unframe(transport) != training:
        raise AssertionError('transport mismatch')
    return {'scope': 'synthetic periodic-byte task; not cultural learning',
            'seed': 20260913, 'fit': fit, 'related': related, 'shifted': shifted,
            'raw_transport_float_count': len(transport['sections'][0]['float_hex']),
            'complete_utf8_1024_rank_bits': (UTF8Space().count(1024)-1).bit_length(),
            'non_claims': ['Not a universal compressor', 'Not evidence of human understanding',
                           'Decoder, integrity, framing and engineering costs remain additional']}


if __name__ == '__main__':
    print(json.dumps(run(),indent=2))
