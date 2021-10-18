from bfrt_helper.match import Ternary
from bfrt_helper.fields import Field


class EightBit(Field):
    bitwidth = 8


def test_ternary_to_string():
    mask = 240
    value = 42 & mask
    ternary = Ternary(EightBit(value), mask=mask)
    expected = f'{value} &&& 240'
    assert str(ternary) == expected


def test_ternary_ands_value_with_mask():
    ternary = Ternary(EightBit(0b01101001), mask=0b11110000)
    expected = Ternary(EightBit(0b01100000), mask=0b11110000)
    assert ternary == expected


def test_ternary_with_non_value_type_mask_creates_value_type():
    ternary = Ternary(EightBit(0b01101001), mask=0b11111111)
    assert isinstance(ternary.mask, EightBit)


def test_ternary_no_mask_creates_all_ones():
    ternary = Ternary(EightBit(0b01101001))
    assert ternary.mask == EightBit(0b11111111)


def test_ternary_dont_care_creates_all_zeroes():
    ternary = Ternary(EightBit(0b01101001), dont_care=True)
    assert ternary.mask == EightBit(0b00000000)


def test_ternary_equals_itself():
    ternary_a = Ternary(EightBit(0b01101001))
    assert ternary_a == ternary_a


def test_ternary_is_its_own_subset():
    ternary_a = Ternary(EightBit(0b01101001))
    assert ternary_a <= ternary_a
    assert ternary_a >= ternary_a


def test_ternary_is_not_own_proper_subset():
    ternary_a = Ternary(EightBit(0b01101001))
    assert not ternary_a < ternary_a
    assert not ternary_a > ternary_a


def test_ternary_is_subset_to_highest_cardinality():
    ternary_a = Ternary(EightBit(0), dont_care=True)
    ternary_b = Ternary(EightBit(0b01101001))
    assert ternary_a > ternary_b
    assert ternary_b < ternary_a
    assert not ternary_a < ternary_b
    assert not ternary_b > ternary_a


def test_ternary_subset_contains_subset():
    ternary_a = Ternary(EightBit(0b10101000), mask=EightBit(0b11110000))
    ternary_b = Ternary(EightBit(0b10101010), mask=EightBit(0b11111100))
    assert ternary_a >= ternary_b
    assert ternary_b <= ternary_a
    assert not ternary_a <= ternary_b
    assert not ternary_b >= ternary_a


def test_ternary_subset_contains_proper_subset():
    ternary_a = Ternary(EightBit(0b10101000), mask=EightBit(0b11110000))
    ternary_b = Ternary(EightBit(0b10101010), mask=EightBit(0b11111100))
    assert ternary_a > ternary_b
    assert ternary_b < ternary_a
    assert not ternary_a < ternary_b
    assert not ternary_b > ternary_a


def test_ternary_unrelated():
    ternary_a = Ternary(EightBit(0b10101000), mask=EightBit(0b11111100))
    ternary_b = Ternary(EightBit(0b00110000), mask=EightBit(0b11110000))
    assert not ternary_a > ternary_b
    assert not ternary_b < ternary_a
    assert not ternary_a < ternary_b
    assert not ternary_b > ternary_a
    assert not ternary_a >= ternary_b
    assert not ternary_b <= ternary_a
    assert not ternary_a <= ternary_b
    assert not ternary_b >= ternary_a


def test_ternary_in_conflict():
    ternary_a = Ternary(EightBit(0b00101011), EightBit(0b00111111))
    ternary_b = Ternary(EightBit(0b11101000), EightBit(0b11111100))
    assert not ternary_a > ternary_b
    assert not ternary_b < ternary_a
    assert not ternary_a < ternary_b
    assert not ternary_b > ternary_a
    assert not ternary_a >= ternary_b
    assert not ternary_b <= ternary_a
    assert not ternary_a <= ternary_b
    assert not ternary_b >= ternary_a
    assert ternary_a.overlaps(ternary_b)
    assert ternary_b.overlaps(ternary_a)


def test_ternary_intersection():
    ternary_a = Ternary(EightBit(0b00101011), EightBit(0b00111111))
    ternary_b = Ternary(EightBit(0b11101000), EightBit(0b11111100))
    expected  = Ternary(EightBit(0b11101011), EightBit(0b11111111))
    assert expected == ternary_a & ternary_b


def test_ternary_intersection_of_subset():
    ternary_a = Ternary(EightBit(0b10101000), mask=EightBit(0b11110000))
    ternary_b = Ternary(EightBit(0b10101000), mask=EightBit(0b11111100))
    expected  = Ternary(EightBit(0b10101000), mask=EightBit(0b11111100))
    assert expected == ternary_a & ternary_b



def test_ternary_union_of_different_sets():
    ternary_a = Ternary(EightBit(0b00101011), EightBit(0b00111111))
    ternary_b = Ternary(EightBit(0b11101000), EightBit(0b11111100))
    expected  = Ternary(EightBit(0b00101000), EightBit(0b00111100))
    assert expected == ternary_a | ternary_b


def test_ternary_union_of_subset():
    ternary_a = Ternary(EightBit(0b10101000), mask=EightBit(0b11110000))
    ternary_b = Ternary(EightBit(0b10101000), mask=EightBit(0b11111100))
    expected  = Ternary(EightBit(0b10100000), mask=EightBit(0b11110000))
    assert expected == ternary_a | ternary_b


def test_ternary_iterator_contiguous():
    ternary = Ternary(EightBit(0b01101000), EightBit(0b11111100))
    expected = [
        Ternary(EightBit(0b01101000), EightBit(0b11111111)),
        Ternary(EightBit(0b01101001), EightBit(0b11111111)),
        Ternary(EightBit(0b01101010), EightBit(0b11111111)),
        Ternary(EightBit(0b01101011), EightBit(0b11111111))
    ]

    assert expected == [x for x in iter(ternary)]


def test_ternary_iterator_discontiguous():
    ternary = Ternary(EightBit(0b01101010), EightBit(0b11101110))
    expected = [
        Ternary(EightBit(0b01101010), EightBit(0b11111111)),
        Ternary(EightBit(0b01101011), EightBit(0b11111111)),
        Ternary(EightBit(0b01111010), EightBit(0b11111111)),
        Ternary(EightBit(0b01111011), EightBit(0b11111111))
    ]

    assert expected == [x for x in iter(ternary)]


def test_ternary_arbitrary_mask_subset():
    ternary1 = Ternary(EightBit(0b00101000), EightBit(0b00111100))
    ternary2 = Ternary(EightBit(0b00101010), EightBit(0b01111110))
    assert ternary1 >= ternary2
    assert ternary2 <= ternary1
    assert not ternary1 <= ternary2
    assert not ternary2 >= ternary1


def test_ternary_arbitrary_mask_proper_subset():
    ternary1 = Ternary(EightBit(0b00101000), EightBit(0b00111100))
    ternary2 = Ternary(EightBit(0b00101010), EightBit(0b01111110))
    assert ternary1 > ternary2
    assert ternary2 < ternary1
    assert not ternary1 < ternary2
    assert not ternary2 > ternary1


def test_ternary_arbitrary_mask_not_subset():
    ternary1 = Ternary(EightBit(0b00111000), EightBit(0b00111100))
    ternary2 = Ternary(EightBit(0b00101010), EightBit(0b01111110))
    assert not ternary1 > ternary2
    assert not ternary2 < ternary1
    assert not ternary1 < ternary2
    assert not ternary2 > ternary1