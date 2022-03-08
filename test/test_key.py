from bfrt_helper.fields import IPv4Address
from bfrt_helper.fields import PortId
from bfrt_helper.fields import Field
from bfrt_helper.match import Ternary
from bfrt_helper.match import Exact
from bfrt_helper.match import LongestPrefixMatch
from bfrt_helper.match import Key
from bfrt_helper.util import InvalidOperation

import pytest


class EightBit(Field):
    bitwidth = 8

    def __str__(self):
        return f"0b{self.value:>08b}"


def test_equal_match_is_superset():
    match = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.1.42"), prefix=32),
        dst=Ternary(PortId(53)),
    )
    assert match >= match


def test_equal_match_is_subset():
    match = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.1.42"), prefix=32),
        dst=Ternary(PortId(53)),
    )
    assert match <= match


def test_match_is_superset():
    match1 = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.1.42"), prefix=32),
        dst=Ternary(PortId(53), dont_care=True),
    )
    match2 = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.1.42"), prefix=32),
        dst=Ternary(PortId(53)),
    )
    assert match1 >= match2


def test_match_is_subset():
    match1 = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.1.42"), prefix=32),
        dst=Ternary(PortId(53), dont_care=True),
    )
    match2 = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.1.42"), prefix=32),
        dst=Ternary(PortId(53)),
    )
    assert match2 <= match1


def test_match_expected_string():
    match = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.0.0"), prefix=24),
        dst=LongestPrefixMatch(IPv4Address("172.16.0.0"), prefix=16),
        xxx=Ternary(IPv4Address("0.0.0.0"), dont_care=True),
    )
    assert str(match) == "{  192.168.0.0/24, 172.16.0.0/16, _  }"


def test_match_equal_exact_match():
    match = Key(src=Exact(PortId(1)), dst=Exact(PortId(2)))
    assert match == match


def test_match_equal_exact_is_subset():
    match = Key(src=Exact(PortId(1)), dst=Exact(PortId(2)))
    assert match <= match


def test_match_equal_exact_is_superset():
    match = Key(src=Exact(PortId(1)), dst=Exact(PortId(2)))
    assert match >= match


def test_match_partially_equal_is_not_equal():
    match_a = Key(src=Exact(PortId(1)), dst=Exact(PortId(2)))
    match_b = Key(src=Exact(PortId(3)), dst=Exact(PortId(2)))

    assert not match_a == match_b


def test_match_partially_equal_is_not_superset():
    match_a = Key(src=Exact(PortId(1)), dst=Exact(PortId(2)))
    match_b = Key(src=Exact(PortId(3)), dst=Exact(PortId(2)))

    assert not match_a > match_b


def test_match_partially_equal_is_not_subset():
    match_a = Key(src=Exact(PortId(1)), dst=Exact(PortId(2)))
    match_b = Key(src=Exact(PortId(3)), dst=Exact(PortId(2)))

    assert not match_a < match_b


def test_match_with_subset_lpm_is_not_equal():
    superset = Key(
        src=Exact(PortId(1)),
        dst=LongestPrefixMatch(IPv4Address("192.168.0.0"), prefix=16),
    )
    subset = Key(
        src=Exact(PortId(1)),
        dst=LongestPrefixMatch(IPv4Address("192.168.42.0"), prefix=24),
    )
    assert not subset == superset


def test_match_with_subset_lpm_is_subset():
    superset = Key(
        src=Exact(PortId(1)),
        dst=LongestPrefixMatch(IPv4Address("192.168.0.0"), prefix=16),
    )
    subset = Key(
        src=Exact(PortId(1)),
        dst=LongestPrefixMatch(IPv4Address("192.168.42.0"), prefix=24),
    )
    assert subset < superset


def test_match_with_subset_lpm_is_superset():
    superset = Key(
        src=Exact(PortId(1)),
        dst=LongestPrefixMatch(IPv4Address("192.168.0.0"), prefix=16),
    )
    subset = Key(
        src=Exact(PortId(1)),
        dst=LongestPrefixMatch(IPv4Address("192.168.42.0"), prefix=24),
    )
    assert superset > subset


def test_match_with_subset_lpm_is_not_subset():
    superset = Key(
        src=Exact(PortId(1)),
        dst=LongestPrefixMatch(IPv4Address("192.168.0.0"), prefix=16),
    )
    subset = Key(
        src=Exact(PortId(1)),
        dst=LongestPrefixMatch(IPv4Address("192.168.42.0"), prefix=24),
    )
    assert not superset < subset


def test_match_with_subset_lpm_is_not_superset():
    superset = Key(
        src=Exact(PortId(1)),
        dst=LongestPrefixMatch(IPv4Address("192.168.0.0"), prefix=16),
    )
    subset = Key(
        src=Exact(PortId(1)),
        dst=LongestPrefixMatch(IPv4Address("192.168.42.0"), prefix=24),
    )
    assert not subset > superset


def test_match_difference_multiple_lpm():
    match1 = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.0.0"), prefix=16),
        dst=LongestPrefixMatch(IPv4Address("192.168.42.0"), prefix=24),
    )
    match2 = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.32.0"), prefix=24),
        dst=LongestPrefixMatch(IPv4Address("192.168.0.0"), prefix=16),
    )
    expected = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.32.0"), prefix=24),
        dst=LongestPrefixMatch(IPv4Address("192.168.42.0"), prefix=24),
    )

    result = match1.intersection(match2)
    assert result == expected


# def test_match():


def test_match_difference_lpm_and_exact_superset_first():
    match1 = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.0.0"), prefix=16),
        dst=Exact(PortId(42)),
    )
    match2 = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.32.0"), prefix=24),
        dst=Exact(PortId(42)),
    )
    expected = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.32.0"), prefix=24),
        dst=Exact(PortId(42)),
    )
    result = match1.intersection(match2)
    assert result == expected


def test_match_difference_lpm_and_exact_subset_first():
    match1 = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.0.0"), prefix=16),
        dst=Exact(PortId(42)),
    )
    match2 = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.32.0"), prefix=24),
        dst=Exact(PortId(42)),
    )
    expected = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.32.0"), prefix=24),
        dst=Exact(PortId(42)),
    )
    result = match2.intersection(match1)
    assert result == expected


def test_match_difference_raises_if_not_equal():
    match1 = Key(src=Exact(PortId(65)), dst=Exact(PortId(42)))
    match2 = Key(src=Exact(PortId(65)), dst=Exact(PortId(32)))

    with pytest.raises(InvalidOperation):
        match1.intersection(match2)


def test_match_difference_lpm_only():
    match1 = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.0.0"), prefix=16),
        dst=LongestPrefixMatch(IPv4Address("192.168.42.0"), prefix=24),
    )
    match2 = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.32.0"), prefix=24),
        dst=LongestPrefixMatch(IPv4Address("192.168.0.0"), prefix=16),
    )
    expected = Key(
        src=LongestPrefixMatch(IPv4Address("192.168.32.0"), prefix=24),
        dst=LongestPrefixMatch(IPv4Address("192.168.42.0"), prefix=24),
    )
    result = match1.intersection(match2)
    assert result == expected

    result = match2.intersection(match1)
    assert result == expected


def test_match_with_equal_and_lpm_is_subset():
    match_a = Key(
        src=Exact(PortId(42)),
        dst=LongestPrefixMatch(IPv4Address("192.168.0.0"), prefix=16),
    )
    match_b = Key(
        src=Exact(PortId(42)),
        dst=LongestPrefixMatch(IPv4Address("192.168.42.0"), prefix=24),
    )

    assert match_a > match_b
    assert match_b < match_a
    assert not match_a < match_b
    assert not match_b > match_a


def test_match_is_overlap():
    match_a = Key(
        src=Ternary(EightBit(0b10100000), EightBit(0b11110000)),
        dst=Ternary(EightBit(0b11001100), EightBit(0b11110000)),
    )
    match_b = Key(
        src=Ternary(EightBit(0b10100000), EightBit(0b11110000)),
        dst=Ternary(EightBit(0b00001100), EightBit(0b00111100)),
    )
    assert match_a.overlaps(match_b)


def test_match_with_equal_is_overlap():
    match_a = Key(
        src=Exact(EightBit(0b10101100)),
        dst=Ternary(EightBit(0b11010000), EightBit(0b11110000)),
    )
    match_b = Key(
        src=Exact(EightBit(0b10101100)),
        dst=Ternary(EightBit(0b00011100), EightBit(0b00111100)),
    )
    assert match_a.overlaps(match_b)


def test_match_with_not_equal_is_overlap():
    match_a = Key(
        src=Exact(EightBit(0b10101100)),
        dst=Ternary(EightBit(0b11010000), EightBit(0b11110000)),
    )
    match_b = Key(
        src=Exact(EightBit(0b11001100)),
        dst=Ternary(EightBit(0b00011100), EightBit(0b00111100)),
    )
    assert not match_a.overlaps(match_b)


def test_match_mixed_sets_overlap():
    match_a = Key(
        src=Ternary(EightBit(0b10100000), EightBit(0b11110000)),
        dst=Ternary(EightBit(0b11001100), EightBit(0b11111100)),
    )
    match_b = Key(
        src=Ternary(EightBit(0b10101000), EightBit(0b11111100)),
        dst=Ternary(EightBit(0b11000000), EightBit(0b11110000)),
    )
    assert match_a.overlaps(match_b)


def test_match_superset_ternary_is_not_overlap():
    match_a = Key(
        src=Ternary(EightBit(0b11110000), mask=0b10100000),
        dst=Ternary(EightBit(0b11110000), mask=0b10100000),
    )
    match_b = Key(
        src=Ternary(EightBit(0b11110000), mask=0b10100000),
        dst=Ternary(EightBit(0b11111100), mask=0b10101000),
    )

    assert not match_a.overlaps(match_b)


def test_match_subset_ternary_is_not_overlap():
    match_a = Key(
        src=Ternary(EightBit(0b11110000), mask=0b10100000),
        dst=Ternary(EightBit(0b11111100), mask=0b10101000),
    )
    match_b = Key(
        src=Ternary(EightBit(0b11110000), mask=0b10100000),
        dst=Ternary(EightBit(0b11110000), mask=0b10100000),
    )
    assert not match_a.overlaps(match_b)


def test_match_superset_ternary_with_equal_is_not_overlap():
    match_a = Key(
        src=Exact(EightBit(0b10101100)),
        dst=Ternary(EightBit(0b11110000), EightBit(0b10100000)),
    )
    match_b = Key(
        src=Exact(EightBit(0b10101100)),
        dst=Ternary(EightBit(0b11111100), EightBit(0b10101000)),
    )
    assert not match_a.overlaps(match_b)


def test_match_subset_ternary_with_equal_is_not_overlap():
    match_a = Key(
        src=Exact(EightBit(0b10101100)),
        dst=Ternary(EightBit(0b11111100), EightBit(0b10101000)),
    )
    match_b = Key(
        src=Exact(EightBit(0b10101100)),
        dst=Ternary(EightBit(0b11110000), EightBit(0b10100000)),
    )
    assert not match_a.overlaps(match_b)


def test_match_intersection():
    match_a = Key(
        src=Ternary(EightBit(0b10101100), EightBit(0b11111100)),
        dst=Ternary(EightBit(0b10110000), EightBit(0b11110000)),
    )
    match_b = Key(
        src=Ternary(EightBit(0b00101100), EightBit(0b00111111)),
        dst=Ternary(EightBit(0b10110001), EightBit(0b11110011)),
    )
    expected = Key(
        src=Ternary(EightBit(0b10101100), EightBit(0b11111111)),
        dst=Ternary(EightBit(0b10110001), EightBit(0b11110011)),
    )
    assert (match_a & match_b) == expected
