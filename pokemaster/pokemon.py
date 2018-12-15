#!/usr/bin/env python3
"""
    Basic Pokémon API

"""
from enum import IntEnum
from typing import AnyStr, Callable, ClassVar, List, Tuple, Union

import attr
from attr.validators import instance_of as _instance_of
from pokedex.db import connect
from pokedex.db import tables as tb
from sqlalchemy.orm.exc import NoResultFound

from pokemaster.session import get_session


def get_move(identity: Union[str, int]) -> tb.Move:
    """Get a move by id or identifier."""
    session = get_session()
    try:
        if isinstance(identity, str):
            return session.query(tb.Move).filter_by(identifier=identity).one()
        elif isinstance(identity, int):
            return session.query(tb.Move).filter_by(id=identity).one()
        else:
            raise TypeError(
                f'`identity` must be a str or an int, not {type(identity)}'
            )
    except NoResultFound:
        raise ValueError(f'Cannot find move {identity}.')


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

    References:
        https://bulbapedia.bulbagarden.net/wiki/Pseudorandom_number_generation_in_Pokémon
        https://www.smogon.com/ingame/rng/pid_iv_creation#pokemon_random_number_generator
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
        if method not in (1, 2, 4):
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
    name: AnyStr  # TODO: Restrict to charsets only.

    def __attrs_post_init__(self):
        self.id = self.prng()
        self.secret_id = self.prng()


class Pokemon:
    """A Pokémon"""

    session: ClassVar = get_session()
    prng: ClassVar[PRNG] = None

    def __init__(self, identity: Union[str, int], level=None):

        try:
            if isinstance(identity, str):
                self._pokemon = (
                    self.session.query(tb.Pokemon)
                    .filter_by(identifier=identity)
                    .one()
                )
                self._species = (
                    self.session.query(tb.PokemonSpecies)
                    .filter_by(identifier=identity)
                    .one()
                )
            elif isinstance(identity, int):
                self._pokemon = (
                    self.session.query(tb.Pokemon).filter_by(id=identity).one()
                )
                self._species = (
                    self.session.query(tb.PokemonSpecies)
                    .filter_by(id=identity)
                    .one()
                )
            else:
                raise TypeError(
                    f'`identity` must be a str or an int, not {type(identity)}'
                )
        except NoResultFound:
            raise ValueError(f'Cannot find pokemon {identity}.')

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
            p_gender = self._pid % 0x100
            gender_threshold = 0xFF * self._species.gender_rate // 8
            if p_gender >= gender_threshold:
                self.gender = Gender.MALE
            else:
                self.gender = Gender.FEMALE

        self.trainer = Trainer('')

        self.id = self._pokemon.id
        self.identifier = self._pokemon.identifier
        self.name = self._pokemon.name
        self.level = level or 5

        obtainable_abilities = (
            self.session.query(tb.Ability)
            .join(tb.PokemonAbility)
            .filter_by(pokemon_id=self.id)
            .filter_by(is_hidden=0)
            .order_by(tb.PokemonAbility.slot)
            .all()
        )
        if len(obtainable_abilities) == 1:
            self.ability = obtainable_abilities[0]
        else:
            self.ability = obtainable_abilities[self._pid % 2]

        self.nature = (
            self.session.query(tb.Nature)
            .filter_by(game_index=self._pid % 25)
            .one()
        )

        self.shiny = (
            self.trainer.id
            ^ self.trainer.secret_id
            ^ (self._pid >> 16)
            ^ (self._pid % 0xFFFF)
        ) < 8

        self._learnable_moves = (
            self.session.query(tb.Move)
            .join(tb.PokemonMove, tb.Move.id == tb.PokemonMove.move_id)
            .join(tb.PokemonMove.version_group)
            .join(tb.PokemonMove.method)
            .filter(tb.PokemonMove.pokemon_id == self.id)
            .filter(tb.VersionGroup.identifier == 'emerald')  # Hack
        )

        self.moves = (
            self._learnable_moves.filter(tb.PokemonMove.level <= self.level)
            .filter(tb.PokemonMoveMethod.identifier == 'level-up')
            .order_by(tb.PokemonMove.level.desc(), tb.PokemonMove.order)
            .limit(4)
            .all()
        )

    def learnable(self, move: tb.Move) -> bool:
        """Check if the Pokémon can learn a certain move or not."""
        return move.id in map(lambda x: x.id, self._learnable_moves)
