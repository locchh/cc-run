import pytest
from add import add


def test_add_two_positive_numbers():
    assert add(2, 3) == 5

def test_add_two_negative_numbers():
    assert add(-4, -6) == -10

def test_add_positive_and_negative():
    assert add(10, -3) == 7

def test_add_zeros():
    assert add(0, 0) == 0

def test_add_zero_to_number():
    assert add(5, 0) == 5
    assert add(0, 5) == 5

def test_add_floats():
    assert add(1.5, 2.5) == pytest.approx(4.0)

def test_add_large_numbers():
    assert add(10**9, 10**9) == 2 * 10**9

def test_add_commutative():
    assert add(3, 7) == add(7, 3)
