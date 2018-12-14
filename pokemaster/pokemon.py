#!/usr/bin/env python3
"""
    Basic Pokémon API

"""
from enum import IntEnum
import datetime
from random import randint
from typing import AnyStr, ClassVar, Union, List, Generator, Callable, Tuple

import attr
from attr.validators import instance_of as _instance_of
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


@attr.s(slots=True)
class PRNG:
    """A linear congruential random number generator.

    Usage::

        >>> prng = PRNG()
        >>> prng()
        0
        >>> prng()
        59774
        >>> # hex, oct, bin can be passed for debugging:
        >>> prng(format=hex)
        '0x5271'
        >>> prng.reset(seed=0x1A56B091)
        >>> prng()
        475
        >>> # Resetting is (roughly) equivalent to:
        >>> prng = PRNG(seed=0x1A56B091)
        >>> prng()
        475

    """

    # In Emerald, the initial seed is always 0.
    _seed: int = attr.ib(default=0, validator=_instance_of(int))
    _value: int = attr.ib(init=False)

    def __attrs_post_init__(self):
        self._value = self._seed

    def _generator(self):
        while True:
            self._value = (0x41C64E6D * self._value + 0x00006073) & 0xFFFFFFFF
            yield self._value >> 16

    def __call__(self, format: Callable = int) -> Union[int, str]:
        valid_formats = (str, bin, oct, int, hex)
        if format not in valid_formats:
            raise ValueError(f'format must be one of {valid_formats}.')
        return format(next(self._generator()))

    def reset(self, seed=None):
        """Reset the generator with seed, if given."""
        self._seed = seed or 0
        self._value = self._seed

    def next(self, n=1, format=int) -> List[Union[str, int]]:
        """Generate the next n random numbers."""
        return [self(format=format) for _ in range(n)]

    def get_pid_ivs(
        self, method=2
    ) -> Tuple[int, int]:  # Can we have a proper name?
        """Generate the PID and IV's using the internal generator. Return
        a tuple of two integers, in the order of 'PID' and 'IVs'.

        Checkout [this link](https://www.smogon.com/ingame/rng/pid_iv_creation#rng_pokemon_generation)
         for more information on Method 1, 2, and 4.
        """
        if method not in [1, 2, 4]:
            raise ValueError(
                'Only methods 1, 2, 4 are supported. For more information on '
                'the meaning of the methods, see '
                'https://www.smogon.com/ingame/rng/pid_iv_creation#rng_pokemon_generation'
                ' for help.'
            )
        elif method == 1:
            pid1, pid2, iv1, iv2 = self.next(4)
        elif method == 2:
            pid1, pid2, _, iv1, iv2 = self.next(5)
        else:  # method == 4:
            pid1, pid2, iv1, _, iv2 = self.next(5)

        pid = pid1 + (pid2 << 16)
        ivs = iv1 + (iv2 << 16)
        return (pid, ivs)


class Gender(IntEnum):

    FEMALE = 1
    MALE = 2
    GENDERLESS = 3


@attr.s(auto_attribs=True)
class Trainer:
    """A trainer"""

    prng: ClassVar[PRNG] = None
    name: AnyStr

    def __attrs_post_init__(self):
        self.id = self.prng()
        self.secret_id = self.prng()


class Pokemon:
    """A Pokémon"""

    session: ClassVar = get_session()
    prng: ClassVar[PRNG] = None

    def __init__(self, identity: Union[str, int], level=None):

        if isinstance(identity, str):
            self._pokemon = util.get(
                self.session, tb.Pokemon, identifier=identity
            )
            self._species = util.get(
                self.session, tb.PokemonSpecies, identifier=identity
            )
        elif isinstance(identity, int):
            self._pokemon = util.get(self.session, tb.Pokemon, id=identity)
            self._species = util.get(
                self.session, tb.PokemonSpecies, id=identity
            )
        else:
            raise TypeError(
                f'`identity` must be a str or an int, not {type(identity)}'
            )

        # TODO: method 1 for legendaries, method 2 for all others.
        self._pid, self._ivs = self.prng.get_pid_ivs(method=2)

        if self._species.gender_rate == -1:  # Genderless
            self.gender = Gender.GENDERLESS
        elif self._species.gender_rate == 8:  # Female-only
            self.gender = Gender.FEMALE
        elif self._species.gender_rate == 0:  # Male-only
            self.gender = Gender.MALE
        else:
            # Gender is determined by the last byte of the PID.
            gender_value = self._pid % 0xFF
            gender_threshold = 0xFF * self._species.gender_rate // 8
            if gender_value >= gender_threshold:
                self.gender = Gender.MALE
            else:
                self.gender = Gender.FEMALE

        self._trainer = Trainer('')

        self.id = self._pokemon.id
        self.identifier = self._pokemon.identifier
        self.name = self._pokemon.name
        self.level = level or 5

        self._all_moves = (
            self.session.query(tb.Move)
            .join(tb.PokemonMove, tb.Move.id == tb.PokemonMove.move_id)
            .filter(tb.PokemonMove.pokemon_id == self.id)
            .filter(tb.PokemonMove.version_group_id == 6)  # Hack
        )
        self._moves = []

        self._all_abilities = (
            self.session.query(tb.Ability)
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
            self.session.query(tb.Nature)
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
