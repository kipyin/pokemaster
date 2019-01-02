"""
Given a seed, the PRNG should have the exact same behavior.

The seed and the results are from the following link:
https://www.smogon.com/ingame/rng/pid_iv_creation#pokemon_random_number_generator
"""

from hypothesis import given
from hypothesis.strategies import integers

from pokemaster.prng import PRNG


def test_prng_default_seed_is_0():
    prng = PRNG()
    assert prng() == 0


@given(integers())
def test_prng_sanity(seed):
    prng = PRNG(seed)
    value = ((0x41C64E6D * seed + 0x6073) & 0xFFFFFFFF) >> 16
    assert prng() == value


def test_next_5():
    prng = PRNG(0x1A56B091)
    assert prng.next(5) == [0x01DB, 0x7B06, 0x5233, 0xE470, 0x5CC4]


def test_reset_prng():
    prng = PRNG()
    assert prng() == 0
    prng.next(10)
    prng.reset()
    assert prng() == 0


def test_pid_ivs_creation():
    prng = PRNG(0x560B9CE3)
    assert (0x7E482751, 0x5EE9629C) == prng.create_genome(method=2)
