"""
Given a seed, the PRNG should have the exact same behavior.

The seed and the results are from the following link:
https://www.smogon.com/ingame/rng/pid_iv_creation#pokemon_random_number_generator
"""
import pytest

from pokemaster.prng import PRNG


def test_prng_default_seed_is_0():
    prng = PRNG()
    assert prng() == 0


def test_next_5():
    prng = PRNG(0x1A56B091)
    assert prng.next(4) == [0x01DB, 0x7B06, 0x5233, 0xE470]
    assert prng.next() == 0x5CC4


def test_reset_prng():
    prng = PRNG()
    assert prng() == 0
    prng.next(10)
    prng.reset()
    assert prng() == 0


def test_pid_ivs_creation():
    prng = PRNG(0x560B9CE3)
    assert (0x7E482751, 0x5EE9629C) == prng.create_genome(method=2)


def test_uniform():
    prng = PRNG(0x1A56B091)
    with pytest.raises(TypeError):
        prng.uniform("10")
    with pytest.raises(TypeError):
        prng.uniform(min=10, max="20")

    assert prng.uniform() == 0x01DB / 0x10000
    assert prng.uniform(10) == 10 * 0x7B06 / 0x10000
    assert prng.uniform(5, 10) == 5 * 0x5233 / 0x10000 + 5
    with pytest.raises(ValueError):
        prng.uniform(10, 5)
