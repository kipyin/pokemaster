#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '../..')))

from construct import Int32ul

from pokemaster.pokemon import Pokemon


class TestPokemon:
    def test_pokemon_properties(self):

        bulbasaur = Pokemon(1)
        assert bulbasaur.id == 1
        assert bulbasaur.identifier == 'bulbasaur'
        assert bulbasaur.name == 'Bulbasaur'
        assert list(map(lambda x: x.id, bulbasaur.moves)) == [45, 33, 80, 113]

    def test_pokemon_gender(self):
        bulbasaur = Pokemon(1)
        bulbasaur.pid = Int32ul.build(0xC0FFEE)
        assert bulbasaur.gender == 2  # male
        nidoran_f = Pokemon('nidoran-f')
        assert nidoran_f.gender == 1
