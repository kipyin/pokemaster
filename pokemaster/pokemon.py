#!/usr/bin/env python3
"""
    Basic Pokémon API

"""
from enum import IntEnum
from typing import AnyStr, ClassVar, List, Tuple, Union

import attr
from attr.validators import instance_of as _instance_of
from pokedex import formulae
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
        >>> prng.reset(seed=0x1A56B091)
        >>> prng()
        475
        >>> prng = PRNG(seed=0x1A56B091)
        >>> prng()
        475

    References:
        https://bulbapedia.bulbagarden.net/wiki/Pseudorandom_number_generation_in_Pokémon
        https://www.smogon.com/ingame/rng/pid_iv_creation#pokemon_random_number_generator
    """

    # In Emerald, the initial seed is always 0.
    _seed: int = attr.ib(default=0, validator=_instance_of(int))

    def _generator(self):
        while True:
            self._seed = (0x41C64E6D * self._seed + 0x6073) & 0xFFFFFFFF
            yield self._seed >> 16

    def __call__(self) -> int:
        return next(self._generator())

    def reset(self, seed=None):
        """Reset the generator with seed, if given."""
        self._seed = seed or 0

    def next(self, n=1) -> List[int]:
        """Generate the next n random numbers."""
        return [self() for _ in range(n)]

    def create_pid_ivs(self, method=2) -> Tuple[int, int]:
        """Generate the PID and IV's using the internal generator. Return
        a tuple of two integers, in the order of 'PID' and 'IVs'.

        The generated 32-bit IVs is different from how it is actually
        stored.

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


@attr.s(slots=True, auto_attribs=True)
class Stats:
    """A Pokémon stats vector."""

    hp: int = 0
    attack: int = 0
    defense: int = 0
    special_attack: int = 0
    special_defense: int = 0
    speed: int = 0

    stat_names: tuple = attr.ib(
        default=(
            'hp',
            'attack',
            'defense',
            'special_attack',
            'special_defense',
            'speed',
        ),
        repr=False,
        init=False,
    )

    # # Aliases
    # @property
    # def atk(self):
    #     return self.attack

    # @property
    # def def(self):
    #     return self.defense

    # @property
    # def spatk(self):
    #     return self.special_attack

    # @property
    # def spdef(self):
    #     return self.special_defense

    # @property
    # def spd(self):
    #     return self.speed

    # def __add__(self, other):
    #     """Point-wise addition."""
    #     return self._pointwise(operator.add, other)

    # def __sub__(self, other):
    #     """Point-wise subtraction."""
    #     return self._pointwise(operator.sub, other)

    # def __mul__(self, other):
    #     """Point-wise multiplication."""
    #     return self._pointwise(operator.mul, other)

    # def __iadd__(self, other):
    #     """Point-wise in-place addition."""
    #     return self._pointwise(operator.iadd, other)

    # def __isub__(self, other):
    #     """Point-wise in-place subtraction."""
    #     return self._pointwise(operator.isub, other)

    # def __imul__(self, other):
    #     """Point-wise in-place multiplication."""
    #     retrun self._pointwise(operator.imul, other)

    # def _pointwise(self, op, other):
    #     """Apply point-wise operation."""
    #     if not isinstance(other, Stats):
    #         raise NotImpletemented
    #     return Stats(**dict(map(lambda x: (x, op(getattr(self, x), getattr(other, x)), self.stat_names))))

    def astuple(self) -> tuple:
        """Return a tuple of the 8 stats."""
        return tuple([getattr(self, stat) for stat in self.stat_names])

    def asdict(self) -> dict:
        """Return a dict of the 8 stats."""
        return {stat: getattr(self, stat) for stat in self.stat_names}


@attr.s
class EffortValue(Stats):
    def set(self, **stats):
        """Set the effort value.

        Each stat cannot exceed 255, and the sum cannot exceed 510.
        """
        total = 0
        for stat, value in stats.items():
            added_value = getattr(self, stat) + value
            if added_value > 255:
                raise ValueError(
                    f'{stat} cannot exceed 255. Current: {added_value}.'
                )
            total += added_value

        if total > 510:
            raise ValueError(f'Total EVs cannot exceed 510. Current: {total}.')

        for stat, value in stats.items():
            setattr(self, stat, value)


@attr.s(auto_attribs=True)
class Trainer:
    """A trainer"""

    prng: ClassVar[PRNG] = None
    name: AnyStr  # TODO: Restrict to charsets only.

    def __attrs_post_init__(self):
        self.id = self.prng()
        self.secret_id = self.prng()


class GrowthRate(IntEnum):
    """The experience groups.

    The group names are consistent with those in Bulbapedia.
    """

    SLOW = 1
    MEDIUM_FAST = 2
    FAST = 3
    MEDIUM_SLOW = 4
    FLUCTUATING = 5
    ERRATIC = 6


def get_experience(level, growth_rate: GrowthRate) -> int:
    """Return the amount of experience determined by a Pokémon's level
    and its growth rate.

    https://bulbapedia.bulbagarden.net/wiki/Experience
    """
    if level not in range(0, 101):
        raise ValueError('Level must be in range(1, 101).')

    n = level

    if n in (0, 1):
        return 0

    square = lambda x: pow(x, 2)
    cube = lambda x: pow(x, 3)

    if growth_rate == GrowthRate.SLOW:
        return (cube(n) * 5) // 4
    elif growth_rate == GrowthRate.MEDIUM_FAST:
        return cube(n)
    elif growth_rate == GrowthRate.FAST:
        return (4 * cube(n)) // 5
    elif growth_rate == GrowthRate.MEDIUM_SLOW:
        return (6 * cube(n)) // 5 - 15 * square(n) + 100 * n - 140
    elif growth_rate == GrowthRate.FLUCTUATING:
        if n <= 15:
            return cube(n) * ((n + 1) // 3 + 24) // 50
        elif n <= 36:
            return cube(n) * (n + 14) // 50
        else:
            return cube(n) * (n // 2 + 32) // 50
    elif growth_rate == GrowthRate.ERRATIC:
        if n <= 50:
            return cube(n) * (100 - n) // 50
        elif n <= 68:
            return cube(n) * (150 - n) // 100
        elif n <= 98:
            return cube(n) * ((1911 - 10 * n) // 3) // 500
        else:
            return cube(n) * (160 - n) // 100
    else:
        raise ValueError(f'{growth_rate} is not a valid growth rate group.')


def get_experience_to_next(level, growth_rate: GrowthRate) -> int:
    return get_experience(level + 1, growth_rate) - get_experience(
        level, growth_rate
    )


class Pokemon:
    """A Pokémon"""

    session: ClassVar = get_session()
    prng: ClassVar[PRNG] = None

    def __init__(
        self, identity: Union[str, int], level=None, pid_method=2, is_egg=False
    ):

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
        # The PRNG should not be wasted on invalid Pokémon calls.
        self._pid, self._ivs = self.prng.create_pid_ivs(method=pid_method)

        # TODO: @property
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

        # TODO: @property? Assigning a trainer to a Pokémon will change
        # the Pokémon's current trainer and the original trainer.
        # Does shininess change?
        self.trainer = None

        # These are mutable (upon evolution).
        self.id = self._pokemon.id
        self.identifier = self._pokemon.identifier
        self.name = self._pokemon.name

        self.is_egg = is_egg
        # Can only be changed via gaining experience and applying Rare
        # Candies?
        if self.is_egg:
            self._level = 0
        else:
            self._level = level or 5

        # Immutable? Even after evolution?
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

        # Completely determined by the PID? Immutable once this Pokémon
        # is spawn?
        self.nature = (
            self.session.query(tb.Nature)
            .filter_by(game_index=self._pid % 25)
            .one()
        )
        # fmt: off
        if self.nature.is_neutral:
            self._nature_modifiers = Stats()
        else:
            self._nature_modifiers = Stats(
                **{
                    self.nature.increased_stat.identifier.replace('-', '_'): 1.1,
                    self.nature.decreased_stat.identifier.replace('-', '_'): 0.9
                }
            )
        # fmt: on

        # Also mutable upon evolution.
        self._learnable_moves = (
            self.session.query(tb.Move)
            .join(tb.PokemonMove, tb.Move.id == tb.PokemonMove.move_id)
            .join(tb.PokemonMove.version_group)
            .join(tb.PokemonMove.method)
            .filter(tb.PokemonMove.pokemon_id == self.id)
            .filter(tb.VersionGroup.identifier == 'emerald')  # Hack
        )

        # Should be settable, but only in certain ways.
        self.moves = (
            self._learnable_moves.filter(tb.PokemonMove.level <= self._level)
            .filter(tb.PokemonMoveMethod.identifier == 'level-up')
            .order_by(tb.PokemonMove.level.desc(), tb.PokemonMove.order)
            .limit(4)
            .all()
        )

        # Will never ever change.
        self.individual_values = Stats(
            hp=self._ivs % 32,
            attack=(self._ivs >> 5) % 32,
            defense=(self._ivs >> 10) % 32,
            speed=(self._ivs >> 16) % 32,
            special_attack=(self._ivs >> 21) % 32,
            special_defense=(self._ivs >> 26) % 32,
        )

        # Will change upon evolution.
        base_stats = (
            self.session.query(tb.PokemonStat)
            .join(tb.Stat)
            .filter(tb.PokemonStat.pokemon_id == self.id)
            .filter(tb.Stat.is_battle_only == False)
            .all()
        )

        def _stat_attr(base_stat) -> str:
            """Get the stat attributes (hp, attack, etc.) from identifiers."""
            return base_stat.stat.identifier.replace('-', '_')

        # fmt: off
        # Base stats and effort points will change upon evolution.
        # effort values should be settable.
        self.base_stats = Stats(**dict(map(lambda x: (_stat_attr(x), x.base_stat), base_stats)))
        self.effort_points = Stats(**dict(map(lambda x: (_stat_attr(x), x.effort), base_stats)))
        self.effort_values = EffortValue(**dict(map(lambda x: (_stat_attr(x), 0), base_stats)))
        # fmt: on
        self._stats = self._calculate_stats()

        # FIXME: use the actual minimum experience at spawn.
        self._experience = 0
        self._experience_to_next = 0

    def __repr__(self):
        return f'<Level {self.level} No.{self.id} {self._pokemon.name} at {id(self)}>'

    def learnable(self, move: tb.Move) -> bool:
        """Check if the Pokémon can learn a certain move or not."""
        return move.id in map(lambda x: x.id, self._learnable_moves)

    def _calculate_stats(self) -> Stats:
        """Return the calculated stats."""
        stats = Stats()
        for stat in stats.stat_names:
            if stat == 'hp':
                func = formulae.calculated_hp
            else:
                func = formulae.calculated_stat
            # A nature modifier with value 0 is OK, it will fail the clause
            # `if nature:` and skip the stats modification.
            setattr(
                stats,
                stat,
                func(
                    base_stat=getattr(self.base_stats, stat),
                    level=self.level,
                    iv=getattr(self.individual_values, stat),
                    effort=getattr(self.effort_values, stat),
                    nature=getattr(self._nature_modifiers, stat),
                ),
            )
        return stats

    @property
    def stats(self):
        """The calculated stats. Stats are re-calculated only when
        leveling up, or taking a Vitamin.
        """
        return self._stats

    @property
    def iv(self):
        """Alias to individual_values."""
        return self.individual_values

    @property
    def shiny(self):
        if self.trainer is not None:
            return (
                self.trainer.id
                ^ self.trainer.secret_id
                ^ (self._pid >> 16)
                ^ (self._pid % 0xFFFF)
            ) < 8
        else:
            return False

    @property
    def experience(self):
        return self._experience

    @experience.setter
    def experience(self):
        """Set the experience. Level, experience-to-next will change if
        needed.
        """

    @property
    def level(self):
        return self._level

    def level_up(self, evolve=True):
        """Increase Pokémon's level by one. Evolve the Pokémon if needed
        and `evolve` is True (i.e. not holding an Everstone, nor canceld
        by the player.)
        """
        self._level += 1
        self._stats = self._calculate_stats()

    def _evolve(self):
        """Evolve the Pokémon. Many things will change.

        This method should not be called directly. Any evolution should
        be properly triggered upon meeting some condition.
        """
