#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '../..')))

import pytest
from construct import Int32ul

from pokemaster.pokemon import Pokemon, Trainer, pokemon_prng, PRNG


class TestPRNG:
    def test_prng(self):
        """The PRNG is used in the rest of the tests, thus needs to be tested
        first.

        The seed and the results are from the following link:
        https://www.smogon.com/ingame/rng/pid_iv_creation#pokemon_random_number_generator
        """
        seed = 0x1A56B091
        prng = pokemon_prng(seed)
        assert [next(prng) for _ in range(5)] == [
            0x01DB,
            0x7B06,
            0x5233,
            0xE470,
            0x5CC4,
        ]

    def test_new_prng_class(self):
        """An instance of a PRNG class should behave exactly like the old
        pokemon_prng.
        """
        prng = PRNG(0x1A56B091)
        assert [prng() for _ in range(5)] == [
            0x01DB,
            0x7B06,
            0x5233,
            0xE470,
            0x5CC4,
        ]

    def test_reset_prng(self):
        prng = PRNG()
        assert prng() == 0
        prng.reset(seed=0x1A56B091)
        assert prng() == 475

    def test_format_output(self):
        prng = PRNG(0x1A56B091)
        assert [prng(format=hex) for _ in range(5)] == [
            '0x1db',
            '0x7b06',
            '0x5233',
            '0xe470',
            '0x5cc4',
        ]

    def test_next_5(self):
        prng = PRNG(0x1A56B091)
        assert prng.next(5) == [0x01DB, 0x7B06, 0x5233, 0xE470, 0x5CC4]

    def test_next_5_formatted(self):
        prng = PRNG(0x1A56B091)
        assert prng.next(5, format=hex) == [
            '0x1db',
            '0x7b06',
            '0x5233',
            '0xe470',
            '0x5cc4',
        ]

    def test_get_pid_ivs(self):
        prng = PRNG(0x560B9CE3)
        assert (0x7E482751, 0x5EE9629C) == prng.get_pid_ivs(method=2)


@pytest.fixture(scope='module')
def bulbasaur():
    """Instantiate a Bulbasaur with pid=0xc0ffee."""
    prng = PRNG()
    Pokemon.prng = prng
    Trainer.prng = prng
    bulbasaur = Pokemon(1)
    bulbasaur._pid = Int32ul.build(0xC0FFEE)
    yield bulbasaur


@pytest.mark.skip(
    reason='Involves probablity. To be fixed with the new Pokémon model.'
)
class TestPokemonPID:
    """PID related mechanisms."""

    def test_pokemon_gender(self, bulbasaur):
        assert bulbasaur.gender == 2  # male
        nidoran_f = Pokemon('nidoran-f')
        assert nidoran_f.gender == 1

    def test_pokemon_ablity(self, bulbasaur):
        assert bulbasaur.ability.identifier == 'overgrow'

    def test_pokemon_nature(self, bulbasaur):
        assert bulbasaur.nature.identifier == 'bold'

    def test_pokemon_shininess(self, bulbasaur):
        """See https://bulbapedia.bulbagarden.net/wiki/Personality_value#Example"""
        bulbasaur._pid = Int32ul.build(2_814_471_828)
        bulbasaur.trainer = Trainer('')
        assert bulbasaur.shiny


class TestPokemonMoves:
    def test_pokemon_initial_moves(self, bulbasaur):
        assert bulbasaur.id == 1
        assert bulbasaur.identifier == 'bulbasaur'
        assert bulbasaur.name == 'Bulbasaur'
        assert list(map(lambda x: x.id, bulbasaur.moves)) == [45, 33, 80, 113]
