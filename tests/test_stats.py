import attr
import pytest
from attr.exceptions import FrozenInstanceError
from hypothesis import given
from hypothesis.strategies import integers, lists

from pokemaster.exceptions import MaxStatExceededError
from pokemaster.stats import EV, IV


@given(lists(elements=integers(min_value=33), min_size=6, max_size=6))
def test_error_when_iv_exceeds_32(iv_values):
    with pytest.raises(MaxStatExceededError):
        IV(*iv_values)


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


def test_single_ev_cannot_exceed_255():
    with pytest.raises(MaxStatExceededError):
        ev = EV()
        ev.attack = 256

    with pytest.raises(MaxStatExceededError):
        EV(hp=256)


def test_total_ev_cannot_exceed_510():
    with pytest.raises(MaxStatExceededError):
        EV(hp=255, attack=255, defense=255)
    ev = EV()
    ev.attack = 255
    ev.hp = 255
    with pytest.raises(MaxStatExceededError):
        ev.defense = 255
