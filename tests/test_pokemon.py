#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '../..')))

import pytest
from construct import Int32ul

from pokemaster.pokemon import Pokemon, Trainer


@pytest.fixture(scope='module')
def bulbasaur():
    """Instantiate a Bulbasaur with pid=0xc0ffee."""
    bulbasaur = Pokemon(1)
    bulbasaur._pid = Int32ul.build(0xC0FFEE)
    yield bulbasaur


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
        bulbasaur.trainer = Trainer(id=24294, secret_id=38834)
        assert bulbasaur.shiny


class TestPokemonMoves:
    def test_pokemon_initial_moves(self, bulbasaur):
        assert bulbasaur.id == 1
        assert bulbasaur.identifier == 'bulbasaur'
        assert bulbasaur.name == 'Bulbasaur'
        assert list(map(lambda x: x.id, bulbasaur.moves)) == [45, 33, 80, 113]
