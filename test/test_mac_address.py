from bfrt_helper.fields import MACAddress
from bfrt_helper.match import Ternary


def test_ipaddress_to_string():
    address = MACAddress('aa:bb:cc:dd:ee:ff')
    assert str(address) == 'aa:bb:cc:dd:ee:ff'


def test_ipaddress_internal_representation():
    address = MACAddress('aa:bb:cc:dd:ee:ff')
    assert address.to_bytes() == b'\xaa\xbb\xcc\xdd\xee\xff'


def test_ipaddress_representation():
    address = MACAddress('aa:bb:cc:dd:ee:ff')
    assert repr(address) == 'MACAddress(\'aa:bb:cc:dd:ee:ff\')'


def test_ipaddress_equal():
    address = MACAddress('aa:bb:cc:dd:ee:ff')
    assert address == address


def test_ipaddress_inequal():
    address1 = MACAddress('aa:bb:cc:dd:ee:ff')
    address2 = MACAddress('ff:ee:dd:cc:bb:aa')
    assert address1 != address2


def test_ipaddress_from_bytes():
    address = MACAddress('aa:bb:cc:dd:ee:ff')
    address_bytes = address.to_bytes()
    reconstituted = MACAddress.from_bytes(address_bytes)
    assert address == reconstituted


def test_ipaddress_bitwise_and():
    address = MACAddress('aa:bb:cc:dd:ee:ff')
    mask = MACAddress('ff:ff:ff:00:00:00')
    masked = address & mask
    expected = MACAddress('aa:bb:cc:00:00:00')
    assert masked == expected


def test_ternary_ipaddress_dont_care_mask_has_same_type():
    ternary = Ternary(MACAddress('aa:bb:cc:dd:ee:ff'), dont_care=True)
    assert isinstance(ternary.mask, MACAddress)


def test_ternary_ipaddress_default_mask_has_same_type():
    ternary = Ternary(MACAddress('aa:bb:cc:dd:ee:ff'))
    assert isinstance(ternary.mask, MACAddress)


def test_ternary_ipaddress_equals_itself():
    ternary = Ternary(MACAddress('aa:bb:cc:dd:ee:ff'))
    assert ternary == ternary


def test_ternary_ipaddress_empty_mask_creates_ipaddress_mask():
    ternary = Ternary(MACAddress('aa:bb:cc:dd:ee:ff'))
    expected = MACAddress('ff:ff:ff:ff:ff:ff')
    assert expected == ternary.mask


def test_ternary_ipaddress_dontcare_mask_creates_ipaddress_mask():
    ternary = Ternary(MACAddress('aa:bb:cc:dd:ee:ff'), dont_care=True)
    expected = MACAddress('00:00:00:00:00:00')
    assert expected == ternary.mask


def test_ternary_ipaddress_ands_value_with_mask():
    ternary = Ternary(MACAddress('aa:bb:cc:dd:ee:ff'), 'ff:ff:ff:00:00:00')
    expected = Ternary(MACAddress('aa:bb:cc:00:00:00'), 'ff:ff:ff:00:00:00')
    assert ternary == expected


def test_ternary_ipaddress_to_string():
    ternary = Ternary(MACAddress('aa:bb:cc:dd:ee:ff'), 'ff:ff:ff:00:00:00')
    assert str(ternary) == "aa:bb:cc:00:00:00 &&& ff:ff:ff:00:00:00"