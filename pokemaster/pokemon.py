#!/usr/bin/env python3
"""
    Basic Pokémon API

"""
import datetime
from random import randint
from typing import AnyStr, ClassVar, Union, List, Generator, Callable

import attr
from construct import Struct, Int8ul, Int16ul, Int24ul, Int32ul, Padding
from pokedex.db import tables as tb, util, connect

from pokemaster.session import get_session


def pokemon_prng(seed: int):
    """The Linear Congruential random number generator in Gen III & IV.

    Stolen from `pokedex.struct._pokemon_struct`.

    References:
        https://bulbapedia.bulbagarden.net/wiki/Pseudorandom_number_generation_in_Pokémon
        https://www.smogon.com/ingame/rng/pid_iv_creation#pokemon_random_number_generator
    """
    while True:
        seed = 0x41C64E6D * seed + 0x00006073
        seed &= 0xFFFFFFFF
        yield seed >> 16


@attr.s
class PRNG:
    """A linear congruential random number generator.

    Usage::

        >>> prng = PRNG()
        >>> prng()
        0
        >>> prng()
        59774
        >>> prng.format = hex
        >>> prng()
        '0x5271'
        >>> prng.reset(seed=0x1A56B091)
        >>> prng()
        >>> '0x1db'  # format persists

    """

    _seed: int = attr.ib(default=0)
    _value: int = attr.ib(init=False)
    format: Callable = attr.ib(init=False, default=int)

    def __attrs_post_init__(self):
        self._value = self._seed

    def reset(self, seed=None):
        self._seed = seed or 0
        self._value = self._seed

    def _generator(self):
        while True:
            self._value = (0x41C64E6D * self._value + 0x00006073) & 0xFFFFFFFF
            yield self._value >> 16

    def __call__(self):
        return self.format(next(self._generator()))


@attr.s(slots=True, auto_attribs=True)
class Trainer:
    """A trainer"""

    # _seed: ClassVar[int] = datetime.datetime.now().microsecond % 0xFFFF
    # _prng: ClassVar[Generator] = random_number_generator(_seed)

    name: AnyStr = b""
    id: int = randint(0, 0xFFFF)
    secret_id: int = randint(0, 0xFFFF)


class Pokemon:
    """A Pokémon"""

    SESSION: ClassVar = get_session()
    # PRNG: ClassVar[Generator]

    def __init__(self, identity: Union[str, int], level=None):

        self._session = Pokemon.SESSION

        if isinstance(identity, str):
            self._pokemon = util.get(
                self._session, tb.Pokemon, identifier=identity
            )
            self._species = util.get(
                self._session, tb.PokemonSpecies, identifier=identity
            )
        elif isinstance(identity, int):
            self._pokemon = util.get(self._session, tb.Pokemon, id=identity)
            self._species = util.get(
                self._session, tb.PokemonSpecies, id=identity
            )
        else:
            raise TypeError(
                f'`identity` must be a str or an int, not {type(identity)}'
            )

        # Build a gender-consistent PID.
        gender_struct = Struct('value' / Int8ul, 'other' / Int24ul)

        if self._species.gender_rate == -1:  # Genderless
            gender_value = 0b11111111
            self.gender = 3
        elif self._species.gender_rate == 8:  # Female-only
            gender_value = 0b11111110
            self.gender = 1
        elif self._species.gender_rate == 0:  # Male-only
            gender_value = 0b00000000
            self.gender = 2
        else:
            # endpoints included.
            gender_value = randint(0b00000001, 0b11111101)
            gender_threshold = 0xFF * self._species.gender_rate // 8
            if gender_value >= gender_threshold:
                self.gender = 2
            else:
                self.gender = 1

        gender_other = randint(0, 0xFFFFFF)  # Also hack.
        self._pid = gender_struct.build(
            dict(value=gender_value, other=gender_other)
        )

        self._trainer = Trainer()

        self.id = self._pokemon.id
        self.identifier = self._pokemon.identifier
        self.name = self._pokemon.name
        self.level = level or 5

        self._all_moves = (
            self._session.query(tb.Move)
            .join(tb.PokemonMove, tb.Move.id == tb.PokemonMove.move_id)
            .filter(tb.PokemonMove.pokemon_id == self.id)
            .filter(tb.PokemonMove.version_group_id == 6)  # Hack
        )
        self._moves = []

        self._all_abilities = (
            self._session.query(tb.Ability)
            .join(tb.PokemonAbility)
            .filter(tb.PokemonAbility.pokemon_id == self.id)
            .filter(tb.PokemonAbility.is_hidden == 0)
            .order_by(tb.PokemonAbility.slot)
            .all()
        )

    @property
    def moves(self):
        """List of this Pokémon's current moves."""
        if self._moves:
            return self._moves
        return (
            self._all_moves.filter(
                tb.PokemonMove.pokemon_move_method_id.in_([1, 2])
            )
            .filter(tb.PokemonMove.level <= self.level)
            .order_by(tb.PokemonMove.level.desc(), tb.PokemonMove.order)
            .limit(4)
            .all()
        )

    @property
    def ability(self):
        """The Pokémon's ability.

        In Generations III and IV, if a Pokémon's species has morethan
        one Ability, its Ability is determined by the lowest bit of its
        personality value; i.e., whether p is even or odd. If p is even
        (the lowest bit is 0), the Pokémon has its first Ability. If p
        is odd (the lowest bit is 1), it has the second.

        https://bulbapedia.bulbagarden.net/wiki/Personality_value#Ability
        """
        # Evolutions?
        if len(self._all_abilities) == 1:
            return self._all_abilities[0]
        elif Int32ul.parse(self._pid) % 2 == 0:
            return self._all_abilities[0]
        else:
            return self._all_abilities[1]

    @property
    def nature(self):
        """The Pokémon's nature.

        Determined by pid % 25. Use the ``game_index`` column in
        :class:`~pokedex.db.tables.Nature`.

        https://bulbapedia.bulbagarden.net/wiki/Personality_value#Nature
        """
        nature_index = Int32ul.parse(self._pid) % 25
        return (
            self._session.query(tb.Nature)
            .filter(tb.Nature.game_index == nature_index)
            .one()
        )

    @property
    def shiny(self):
        """Determine the shininess of a Pokémon.

        https://bulbapedia.bulbagarden.net/wiki/Personality_value#Shininess
        """
        shiny_struct = Struct('p2' / Int16ul, 'p1' / Int16ul)
        p1 = shiny_struct.parse(self._pid).p1
        p2 = shiny_struct.parse(self._pid).p2
        if self.trainer.id ^ self.trainer.secret_id ^ p1 ^ p2 < 8:
            return True
        else:
            return False
