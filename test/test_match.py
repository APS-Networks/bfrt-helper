from bfrt_helper.fields import IPv4Address
from bfrt_helper.fields import PortId
from bfrt_helper.match import Ternary
from bfrt_helper.match import Exact
from bfrt_helper.match import LPM
from bfrt_helper.match import Match
from bfrt_helper.util import InvalidOperation

import pytest



def test_equal_match_is_superset():
    match = Match(
            LPM(IPv4Address('192.168.1.42'), prefix=32),
            Ternary(PortId(53)))
    assert match >= match



def test_equal_match_is_subset():
    match = Match(
            LPM(IPv4Address('192.168.1.42'), prefix=32),
            Ternary(PortId(53)))
    assert match <= match



def test_match_is_superset():
    match1 = Match(
            LPM(IPv4Address('192.168.1.42'), prefix=32),
            Ternary(PortId(53), dont_care=True))
    match2 = Match(
            LPM(IPv4Address('192.168.1.42'), prefix=32),
            Ternary(PortId(53)))
    assert match1 >= match2



def test_match_is_subset():
    match1 = Match(
            LPM(IPv4Address('192.168.1.42'), prefix=32),
            Ternary(PortId(53), dont_care=True))
    match2 = Match(
            LPM(IPv4Address('192.168.1.42'), prefix=32),
            Ternary(PortId(53)))
    assert match2 <= match1


def test_match_expected_string():
    match = Match(
        LPM(IPv4Address('192.168.0.0'), prefix=24),
        LPM(IPv4Address('172.16.0.0'), prefix=16),
        Ternary(IPv4Address('0.0.0.0'), dont_care=True)
    )
    assert str(match) == '{  192.168.0.0/24, 172.16.0.0/16, _  }'



def test_match_equal_exact_match():
    match = Match(Exact(PortId(1)), Exact(PortId(2)))
    assert match == match



def test_match_equal_exact_is_subset():
    match = Match(Exact(PortId(1)), Exact(PortId(2)))
    assert match <= match



def test_match_equal_exact_is_superset():
    match = Match(Exact(PortId(1)), Exact(PortId(2)))
    assert match >= match



def test_match_partially_equal_is_not_equal():
    match_a = Match(Exact(PortId(1)), Exact(PortId(2)))
    match_b = Match(Exact(PortId(3)), Exact(PortId(2)))

    assert not match_a == match_b



def test_match_partially_equal_is_not_superset():
    match_a = Match(Exact(PortId(1)), Exact(PortId(2)))
    match_b = Match(Exact(PortId(3)), Exact(PortId(2)))

    assert not match_a > match_b



def test_match_partially_equal_is_not_subset():
    match_a = Match(Exact(PortId(1)), Exact(PortId(2)))
    match_b = Match(Exact(PortId(3)), Exact(PortId(2)))

    assert not match_a < match_b


def test_match_with_subset_lpm_is_not_equal():
    superset = Match(Exact(PortId(1)), LPM(IPv4Address("192.168.0.0"), prefix=16))
    subset = Match(Exact(PortId(1)), LPM(IPv4Address("192.168.42.0"), prefix=24))
    assert not subset == superset

def test_match_with_subset_lpm_is_subset():
    superset = Match(Exact(PortId(1)), LPM(IPv4Address("192.168.0.0"), prefix=16))
    subset = Match(Exact(PortId(1)), LPM(IPv4Address("192.168.42.0"), prefix=24))
    assert subset < superset


def test_match_with_subset_lpm_is_superset():
    superset = Match(Exact(PortId(1)), LPM(IPv4Address("192.168.0.0"), prefix=16))
    subset = Match(Exact(PortId(1)), LPM(IPv4Address("192.168.42.0"), prefix=24))
    assert superset > subset


def test_match_with_subset_lpm_is_not_subset():
    superset = Match(Exact(PortId(1)), LPM(IPv4Address("192.168.0.0"), prefix=16))
    subset = Match(Exact(PortId(1)), LPM(IPv4Address("192.168.42.0"), prefix=24))
    assert not superset < subset


def test_match_with_subset_lpm_is_not_superset():
    superset = Match(Exact(PortId(1)), LPM(IPv4Address("192.168.0.0"), prefix=16))
    subset = Match(Exact(PortId(1)), LPM(IPv4Address("192.168.42.0"), prefix=24))
    assert not subset > superset




def test_match_difference_multiple_lpm():
    match1 = Match(
        LPM(IPv4Address("192.168.0.0"), prefix=16),
        LPM(IPv4Address("192.168.42.0"), prefix=24))
    match2 = Match(
        LPM(IPv4Address("192.168.32.0"), prefix=24),
        LPM(IPv4Address("192.168.0.0"), prefix=16))
    expected = Match(
        LPM(IPv4Address("192.168.32.0"), prefix=24),
        LPM(IPv4Address("192.168.42.0"), prefix=24))

    result = match1.difference_to(match2)
    assert result == expected
# def test_match():
    

def test_match_difference_lpm_and_exact_superset_first():
    match1 = Match(
        LPM(IPv4Address("192.168.0.0"), prefix=16),
        Exact(PortId(42)))
    match2 = Match(
        LPM(IPv4Address("192.168.32.0"), prefix=24),
        Exact(PortId(42)))
    expected = Match(
        LPM(IPv4Address("192.168.32.0"), prefix=24),
        Exact(PortId(42)))
    result = match1.difference_to(match2)
    assert result == expected


def test_match_difference_lpm_and_exact_subset_first():
    match1 = Match(
        LPM(IPv4Address("192.168.0.0"), prefix=16),
        Exact(PortId(42)))
    match2 = Match(
        LPM(IPv4Address("192.168.32.0"), prefix=24),
        Exact(PortId(42)))
    expected = Match(
        LPM(IPv4Address("192.168.32.0"), prefix=24),
        Exact(PortId(42)))
    result = match2.difference_to(match1)
    assert result == expected


def test_match_difference_raises_if_not_equal():
    match1 = Match(
        Exact(PortId(65)),
        Exact(PortId(42)))
    match2 = Match(
        Exact(PortId(65)),
        Exact(PortId(32)))

    with pytest.raises(InvalidOperation):
        match1.difference_to(match2)
    

def test_match_difference_lpm_only():
    match1 = Match(
        LPM(IPv4Address("192.168.0.0"), prefix=16),
        LPM(IPv4Address("192.168.42.0"), prefix=24))
    match2 = Match(
        LPM(IPv4Address("192.168.32.0"), prefix=24),
        LPM(IPv4Address("192.168.0.0"), prefix=16))
    expected = Match(
        LPM(IPv4Address("192.168.32.0"), prefix=24),
        LPM(IPv4Address("192.168.42.0"), prefix=24))
    result = match1.difference_to(match2)
    assert result == expected

    result = match2.difference_to(match1)
    assert result == expected


def test_match_with_equal_and_lpm_is_subset():
    match_a = Match(
            Exact(PortId(42)), 
            LPM(IPv4Address("192.168.0.0"), prefix=16))
    match_b = Match(
            Exact(PortId(42)), 
            LPM(IPv4Address("192.168.42.0"), prefix=24))

    assert match_a > match_b
    assert match_b < match_a
    assert not match_a < match_b
    assert not match_b > match_a