from bfrt_helper.fields import Field
from bfrt_helper.fields import StringField
from bfrt_helper.fields import InvalidValue
from bfrt_helper.fields import InvalidOperation
import pytest


class EightBit(Field):
    bitwidth = 8


class ThirtyTwoBit(Field):
    bitwidth = 32


def test_field_to_string():
    field = EightBit(12)
    assert str(field) == "12"


def test_field_representation():
    field = EightBit(12)
    assert repr(field) == "EightBit(12)"


def test_field_equality():
    field = EightBit(42)
    assert field == field


def test_field_inequality():
    field_a = EightBit(42)
    field_b = EightBit(65)
    assert field_a != field_b


def test_field_raises_if_value_above_max():
    bad_value = EightBit.max_value() + 1

    with pytest.raises(InvalidValue):
        EightBit(bad_value)


def test_field_and_field():
    field_a = EightBit(0b11110000)
    field_b = EightBit(0b10101010)
    expected = EightBit(0b10100000)
    assert field_a & field_b == expected


def test_field_or_field():
    field_a = EightBit(0b11110000)
    field_b = EightBit(0b10101010)
    expected = EightBit(0b11111010)
    assert field_a | field_b == expected


def test_field_xor_field():
    field_a = EightBit(0b11110000)
    field_b = EightBit(0b10101010)
    expected = EightBit(0b01011010)
    assert field_a ^ field_b == expected


def test_field_to_bytes():
    field = ThirtyTwoBit(0xFFCCAABB)
    expected = b"\xff\xcc\xaa\xbb"
    assert field.to_bytes() == expected


def test_string_field_to_string():
    field = StringField("test")
    assert str(field) == "'test'"


def test_string_field_representation():
    field = StringField(value="test")
    assert repr(field) == "StringField('test')"


def test_string_field_invalid_operations():
    field = StringField("test")

    with pytest.raises(InvalidOperation):
        field & field

    with pytest.raises(InvalidOperation):
        field | field

    with pytest.raises(InvalidOperation):
        field ^ field

    with pytest.raises(InvalidOperation):
        field.max_value()
