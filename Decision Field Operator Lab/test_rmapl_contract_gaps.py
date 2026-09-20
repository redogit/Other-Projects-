"""Regression witnesses for strict, immutable, faithful RMAPL parsing.

Uses public parse_rmapl only. These are software contract tests, not RMALC
conformance or a proof that arbitrary RMAPL programs are safe to execute.
"""
from collections.abc import Mapping
import json
import math
import unittest

from rmapl import parse_rmapl
from test_rmapl import MINIMAL


def with_bound(payload):
    return f"RMAPL 0\nPROGRAM p\nLOAD source\nBOUND config={payload}\nRUN\n"


def with_objectives(payload):
    return MINIMAL.replace(
        'OBJECTIVES {"clarity":"max","ambiguity":"min"}',
        'OBJECTIVES ' + payload,
    )


def thaw(value):
    if isinstance(value, Mapping):
        return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw(item) for item in value]
    return value


class FiniteJSONContractTests(unittest.TestCase):
    def test_exponent_overflow_is_rejected_at_any_json_depth(self):
        for payload in ('1e309', '-1e309', '[1e309]', '{"x":[-1e9999]}'):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, 'finite JSON'):
                    parse_rmapl(with_bound(payload))

    def test_finite_extremes_and_json_scalar_types_are_preserved(self):
        payload = '[1e308,-1e308,1e-300,0,-0.0,true,false,null,12345678901234567890]'
        actual = thaw(parse_rmapl(with_bound(payload)).bounds['config'])
        self.assertEqual(actual, json.loads(payload))
        self.assertTrue(all(math.isfinite(x) for x in actual[:5]))
        self.assertEqual(math.copysign(1.0, actual[4]), -1.0)
        self.assertIs(actual[5], True)
        self.assertIsNone(actual[7])

    def test_nonstandard_constants_still_fail_closed(self):
        for constant in ('NaN', 'Infinity', '-Infinity'):
            with self.subTest(constant=constant):
                with self.assertRaisesRegex(ValueError, 'finite JSON'):
                    parse_rmapl(with_bound('[{"x":' + constant + '}]'))

    def test_cost_integer_overflow_is_a_contextual_validation_error(self):
        source = MINIMAL.replace('COST 1\n', 'COST ' + '1' + '0' * 400 + '\n', 1)
        with self.assertRaisesRegex(ValueError, 'COST.*finite'):
            parse_rmapl(source)


class DuplicateKeyContractTests(unittest.TestCase):
    def test_conflicting_objectives_cannot_silently_choose_last_value(self):
        with self.assertRaisesRegex(ValueError, 'OBJECTIVES.*duplicate'):
            parse_rmapl(with_objectives('{"clarity":"max","clarity":"min"}'))

    def test_duplicate_bound_keys_rejected_in_nested_objects(self):
        for payload in ('{"x":1,"x":2}', '[{"x":1,"x":1}]', '{"outer":{"x":1,"x":2}}'):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, 'BOUND config.*duplicate'):
                    parse_rmapl(with_bound(payload))

    def test_escaped_duplicate_key_is_the_same_decoded_key(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            parse_rmapl(with_bound(r'{"x":1,"\u0078":2}'))

    def test_separate_objects_can_use_the_same_key(self):
        payload = '{"first":{"x":1},"second":{"x":2}}'
        self.assertEqual(thaw(parse_rmapl(with_bound(payload)).bounds['config']), json.loads(payload))

    def test_invalid_objective_value_has_contextual_error(self):
        for value in ('[]', '{}', 'null', 'true', '7'):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, 'OBJECTIVES'):
                    parse_rmapl(with_objectives('{"clarity":' + value + '}'))

    def test_valid_objective_names_and_directions_survive(self):
        spec = parse_rmapl(with_objectives('{"human burden":"min","clarity":"max"}')).fitters[0]
        self.assertEqual(dict(spec.objectives), {'human burden': 'min', 'clarity': 'max'})


class ImmutableBoundContractTests(unittest.TestCase):
    def test_nested_mapping_cannot_be_modified_after_parsing(self):
        config = parse_rmapl(with_bound('{"limits":{"n":1}}')).bounds['config']
        with self.assertRaises(TypeError):
            config['limits']['n'] = 99

    def test_nested_array_cannot_be_modified_after_parsing(self):
        config = parse_rmapl(with_bound('{"sequence":[1,2]}')).bounds['config']
        with self.assertRaises(TypeError):
            config['sequence'][0] = 99

    def test_object_inside_array_cannot_be_modified(self):
        config = parse_rmapl(with_bound('[{"n":1}]')).bounds['config']
        with self.assertRaises(TypeError):
            config[0]['n'] = 99

    def test_nested_empty_containers_and_order_are_preserved(self):
        payload = '{"a":[{},[],null,false,0,""],"b":{"v":[3,1,2]}}'
        program = parse_rmapl(with_bound(payload))
        self.assertEqual(thaw(program.bounds['config']), json.loads(payload))
        self.assertEqual(program, parse_rmapl(with_bound(payload)))


class UnicodeCarrierContractTests(unittest.TestCase):
    def test_literal_and_escaped_unicode_in_when_are_equivalent(self):
        for separator in ('\u0085', '\u2028', '\u2029'):
            value = 'before' + separator + 'after'
            with self.subTest(separator=hex(ord(separator))):
                literal = MINIMAL.replace('"x-residual"', json.dumps(value, ensure_ascii=False), 1)
                escaped = MINIMAL.replace('"x-residual"', json.dumps(value, ensure_ascii=True), 1)
                self.assertEqual(parse_rmapl(literal), parse_rmapl(escaped))
                self.assertEqual(parse_rmapl(literal).repairs[0].trigger, value)

    def test_unicode_bound_text_is_not_an_instruction_separator(self):
        value = 'a\u0085b\u2028c\u2029d'
        self.assertEqual(
            parse_rmapl(with_bound(json.dumps(value, ensure_ascii=False))).bounds['config'],
            value,
        )

    def test_lf_crlf_and_cr_instruction_lines_remain_equivalent(self):
        expected = parse_rmapl(MINIMAL)
        for newline in ('\n', '\r\n', '\r'):
            with self.subTest(newline=repr(newline)):
                self.assertEqual(parse_rmapl(MINIMAL.replace('\n', newline)), expected)

    def test_escaped_ascii_control_characters_are_preserved(self):
        value = 'before\n\r\t\v\fafter'
        self.assertEqual(parse_rmapl(with_bound(json.dumps(value))).bounds['config'], value)


if __name__ == '__main__':
    unittest.main()
