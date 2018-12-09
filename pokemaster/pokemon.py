#!/usr/bin/env python3
"""
    Basic Pokémon API

"""
from random import randint
from typing import *

from pokedex.db import tables as tb, util, connect

from pokemaster import session


class Pokemon:
    """A Pokémon.
    """

    SESSION: ClassVar = session.initialize_database()

    def __init__(self, identity: Union[str, int], level=None):

        _session = Pokemon.SESSION

        if isinstance(identity, str):
            self._pokemon = util.get(_session, tb.Pokemon, identifier=identity)
            self._species = util.get(_session, tb.PokemonSpecies, identifier=identity)
        elif isinstance(identity, int):
            self._pokemon = util.get(_session, tb.Pokemon, id=identity)
            self._species = util.get(_session, tb.PokemonSpecies, id=identity)
        else:
            raise TypeError(
                f'`identity` must be a str or an int, not {type(identity)}'
            )

        self.pid = randint(0x00000000, 0xffffffff)  # Hack

        self.id = self._pokemon.id
        self.identifier = self._pokemon.identifier
        self.name = self._pokemon.name
        self.level = level or 5

        # A Pokémon's gender is determined by the last byte of its PID.
        # The tb.Species.gender_rate is the probablity of a Pokémon being
        # a female, in eighth. -1 for genderless.
        # So to convert between these two intepretations, we need to
        # translate the probability into binary, and then compare the
        # last byte of the PID with the binary probability. If the former
        # is greater, then this Pokémon is male.
        self._gender_base_value = self._species.gender_rate

        self._all_moves = (
            _session
            .query(tb.Move)
            .join(tb.PokemonMove, tb.Move.id == tb.PokemonMove.move_id)
            .filter(tb.PokemonMove.pokemon_id == self.id)
            .filter(tb.PokemonMove.version_group_id == 6)  # Hack
            .filter(tb.PokemonMove.pokemon_move_method_id.in_([1, 2]))
            .filter(tb.PokemonMove.level <= self.level)
            .order_by(tb.PokemonMove.level.desc())
            .order_by(tb.PokemonMove.order)
        )
        self.moves = self._all_moves.limit(4).all()

        # self._all_abilities = (
        #     _session
        #     .query(tb.Ability)
        #     .join(tb.PokemonAbility)
        #     .filter(tb.PokemonAbility.pokemon_id == self.id)
        # )
        # self.abilities = (
        #     self._all_abilities
        #     .filter(tb.PokemonAbility.is_hidden == 0)
        #     .all()
        # )
        # self.hidden_ability = (
        #     self._all_abilities
        #     .filter(tb.PokemonAbility.is_hidden == 1)
        #     .one_or_none()
        # )

