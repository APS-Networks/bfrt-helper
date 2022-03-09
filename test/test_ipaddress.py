from bfrt_helper.fields import IPv4Address
from bfrt_helper.match import Ternary


def test_ternary_ipaddress_dont_care_mask_is_zeroed():
    ternary = Ternary(IPv4Address("192.168.42.24"), dont_care=True)
    expected = IPv4Address("0.0.0.0")
    assert ternary.mask == expected


def test_ternary_ipaddress_default_mask_is_all_ones():
    ternary = Ternary(IPv4Address("192.168.42.24"))
    expected = IPv4Address("255.255.255.255")
    assert ternary.mask == expected


def test_ipaddress_to_string():
    address = IPv4Address("192.168.0.1")
    assert str(address) == "192.168.0.1"


def test_ipaddress_internal_representation():
    address = IPv4Address("192.168.0.1")
    assert address.to_bytes() == b"\xc0\xa8\x00\x01"


def test_ipaddress_representation():
    address = IPv4Address("192.168.0.1")
    assert repr(address) == "IPv4Address('192.168.0.1')"


def test_ipaddress_equal():
    address = IPv4Address("192.168.0.1")
    assert address == address


def test_ipaddress_inequal():
    address1 = IPv4Address("192.168.0.1")
    address2 = IPv4Address("192.168.0.2")
    assert address1 != address2


def test_ipaddress_from_bytes():
    address = IPv4Address("192.168.0.1")
    address_bytes = address.to_bytes()
    reconstituted = IPv4Address.from_bytes(address_bytes)
    assert address == reconstituted


def test_ipaddress_bitwise_and():
    address = IPv4Address("192.168.42.42")
    mask = IPv4Address("255.255.0.0")
    masked = address & mask
    expected = IPv4Address("192.168.0.0")
    assert masked == expected


def test_ternary_ipaddress_dont_care_mask_has_same_type():
    ternary = Ternary(IPv4Address("192.168.42.24"), dont_care=True)
    assert isinstance(ternary.mask, IPv4Address)


def test_ternary_ipaddress_default_mask_has_same_type():
    ternary = Ternary(IPv4Address("192.168.42.24"))
    assert isinstance(ternary.mask, IPv4Address)
