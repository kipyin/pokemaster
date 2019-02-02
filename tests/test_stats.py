import pytest
from attr.exceptions import FrozenInstanceError
from hypothesis import given
from hypothesis.strategies import integers, lists

from pokemaster.exceptions import MaxStatExceededError
from pokemaster.stats import Stats


def test_stats_addition():
    assert Stats() + Stats(1, 2, 3, 4, 5, 6) == Stats(1, 2, 3, 4, 5, 6)
    assert Stats(1, 2, 3, 4, 5, 6) + 1 == Stats(2, 3, 4, 5, 6, 7)
    assert 1 + Stats(1, 2, 3, 4, 5, 6) == Stats(2, 3, 4, 5, 6, 7)


def test_stats_subtraction():
    assert Stats(7, 7, 7, 7, 7, 7) - Stats(1, 2, 3, 4, 5, 6) == Stats(
        6, 5, 4, 3, 2, 1
    )
    assert Stats(7, 7, 7, 7, 7, 7) - 7 == Stats()


def test_stats_multiplication():
    assert Stats(1, 2, 3, 4, 5, 6) * Stats(1, 2, 3, 4, 5, 6) == Stats(
        1, 4, 9, 16, 25, 36
    )
    assert Stats(1, 2, 3, 4, 5, 6) * 2 == Stats(2, 4, 6, 8, 10, 12)
    assert 2 * Stats(1, 2, 3, 4, 5, 6) == Stats(2, 4, 6, 8, 10, 12)


@pytest.mark.skip
@given(lists(elements=integers(min_value=33), min_size=6, max_size=6))
def test_error_when_iv_exceeds_32(iv_values):
    with pytest.raises(MaxStatExceededError):
        Stats(*iv_values)


@pytest.mark.skip
@given(
    lists(elements=integers(min_value=0, max_value=32), min_size=6, max_size=6)
)
def test_iv_immutability(iv_values):
    """Once the IV is set, it should not be changed."""
    iv = IV(*iv_values)
    for stat in [
        'hp',
        'attack',
        'defense',
        'special_attack',
        'special_defense',
        'speed',
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(iv, stat, 32)


@pytest.mark.skip
def test_single_ev_cannot_exceed_255():
    with pytest.raises(MaxStatExceededError):
        Stats(hp=256)


@pytest.mark.skip
def test_total_ev_cannot_exceed_510():
    with pytest.raises(MaxStatExceededError):
        Stats(hp=255, attack=255, defense=255)
