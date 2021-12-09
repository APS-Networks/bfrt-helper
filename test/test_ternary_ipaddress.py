from bfrt_helper.fields import IPv4Address
from bfrt_helper.match import Ternary
from bfrt_helper.match import IPv4AddressTernary


def test_ternary_ipaddress_equals_itself():
    address = Ternary(IPv4Address("192.168.0.1"))
    assert address == address


def test_ternary_ipaddress_empty_mask_creates_ipaddress_mask():
    address = Ternary(IPv4Address("192.168.0.1"))
    expected = IPv4Address("255.255.255.255")
    assert expected == address.mask


def test_ternary_ipaddress_dontcare_mask_creates_ipaddress_mask():
    address = Ternary(IPv4Address("192.168.0.1"), dont_care=True)
    expected = IPv4Address("0.0.0.0")
    assert expected == address.mask


def test_ternary_ipaddress_ands_value_with_mask():
    address = Ternary(IPv4Address("192.168.248.42"), "255.255.0.0")
    expected = Ternary(IPv4Address("192.168.0.0"), "255.255.0.0")
    assert address == expected


def test_ternary_ipaddress_to_string():
    ternary = IPv4AddressTernary("192.168.0.0", mask="255.255.255.0")
    assert str(ternary) == "192.168.0.0 &&& 255.255.255.0"


def test_ternary_ipaddress_equality():
    ternary = Ternary(IPv4Address("192.168.0.0"), mask=IPv4Address("255.255.255.0"))
    assert ternary == ternary


def test_ternary_ipaddress_inequality():
    ternary1 = Ternary(IPv4Address("192.168.0.0"), mask=IPv4Address("255.255.255.0"))
    ternary2 = Ternary(IPv4Address("192.168.1.0"), mask=IPv4Address("255.255.255.0"))
    assert ternary1 != ternary2


def test_ternary_ipaddress_internal_representation():
    ternary = Ternary(IPv4Address("192.168.0.0"), mask=IPv4Address("255.255.255.0"))
    assert ternary.value_bytes() == b"\xc0\xa8\x00\x00"
    assert ternary.mask_bytes() == b"\xff\xff\xff\x00"


def test_ternary_ipaddress_masks_supplied_value():
    ternary = Ternary(IPv4Address("192.168.42.24"), mask=IPv4Address("255.255.0.0"))
    expected = Ternary(IPv4Address("192.168.0.0"), mask=IPv4Address("255.255.0.0"))
    assert ternary == expected


def test_ternary_ipaddress_max_value():
    expected = (1 << 32) - 1
    assert IPv4Address.max_value() == expected


def test_ternary_ipaddress_iterator():
    ''' It has the full mask as a ternary expression masks off the value bits'''
    ternary = Ternary(IPv4Address("192.168.42.24"), mask="255.255.255.252")
    expected = [
        IPv4AddressTernary("192.168.42.24", mask="255.255.255.255"),
        IPv4AddressTernary("192.168.42.25", mask="255.255.255.255"),
        IPv4AddressTernary("192.168.42.26", mask="255.255.255.255"),
        IPv4AddressTernary("192.168.42.27", mask="255.255.255.255"),
    ]

    assert [x for x in iter(ternary)] == expected


def test_ternary_ipaddress_with_full_mask_to_string():
    ternary = Ternary(IPv4Address("192.168.0.0"), "255.255.255.255")
    assert str(ternary) == "192.168.0.0"
