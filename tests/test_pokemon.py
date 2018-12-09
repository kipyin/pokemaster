#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '../..')))

from pokemaster.pokemon import Pokemon


class TestPokemon:

    def test_pokemon_methods(self):

        bulbasaur = Pokemon(1)
        assert bulbasaur.id == 1
        assert bulbasaur.identifier == 'bulbasaur'
        assert bulbasaur.name == 'Bulbasaur'
        assert list(map(lambda x: x.id, bulbasaur.moves)) == [45, 33, 80, 113]
