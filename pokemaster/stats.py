"""Provides general ``Stats`` class for statistics-related functionality
and ``Conditions`` class for contests.
"""
import operator
from numbers import Real
from typing import Callable, ClassVar, Tuple, Union

import attr
from attr.validators import instance_of

from pokemaster import _database


@attr.s(slots=True, auto_attribs=True)
class Conditions:
    """Contest conditions"""

    coolness: int = 0
    beauty: int = 0
    cuteness: int = 0
    smartness: int = 0
    toughness: int = 0


@attr.s(auto_attribs=True, slots=True, frozen=True)
class Stats:
    """A generic statistics representation.

    ``Stats`` instances are "immutable".

    For IV, species strengths (a.k.a. base stats), and EV yields,
    having ``Stats`` immutable makes perfect sense, since they are
    either bound to individual Pokémon or shared within a species.
    For EV and permanent stats, since they should get updated only from
    adding/subtracting/multiplying/dividing another ``Stats`` instance,
    being mutable does not do much good for ``Stats``.

    Usage::

        >>> ev = Stats()
        >>> iv = Stats.make_iv(gene=0x00ff)
        >>> max_iv = Stats(32, 32, 32, 32, 32, 32)
        >>> species_strengths = Stats.make_species_strengths('eevee')

    """

    _NAMES: ClassVar[Tuple[str, ...]] = (
        'hp',
        'attack',
        'defense',
        'special_attack',
        'special_defense',
        'speed',
    )

    hp: Real = attr.ib(validator=instance_of(Real), default=0)
    attack: Real = attr.ib(validator=instance_of(Real), default=0)
    defense: Real = attr.ib(validator=instance_of(Real), default=0)
    special_attack: Real = attr.ib(validator=instance_of(Real), default=0)
    special_defense: Real = attr.ib(validator=instance_of(Real), default=0)
    speed: Real = attr.ib(validator=instance_of(Real), default=0)

    def __add__(self, other):
        return self._make_operator(operator.add, other)

    def __sub__(self, other):
        return self._make_operator(operator.sub, other)

    def __mul__(self, other):
        return self._make_operator(operator.mul, other)

    def __floordiv__(self, other):
        return self._make_operator(operator.floordiv, other)

    __radd__ = __add__
    __rmul__ = __mul__

    @classmethod
    def make_nature_modifiers(cls, nature: str) -> 'Stats':
        """Create a NatureModifiers instance from the Nature table.

        :param nature: The identifier of a nature.
        :return: A ``Stats`` instance.
        """
        nature_row = _database.get_nature(identifier=nature)
        modifiers = {}
        for stat in cls._NAMES:
            modifiers[stat] = 1
        if nature_row.is_neutral:
            return cls(**modifiers)
        increased_stat = nature_row.increased_stat.identifier.replace('-', '_')
        decreased_stat = nature_row.decreased_stat.identifier.replace('-', '_')
        modifiers[increased_stat] = 1.1
        modifiers[decreased_stat] = 0.9
        return cls(**modifiers)

    @classmethod
    def make_species_strengths(cls, species: str) -> 'Stats':
        """Create a Pokémon's species strengths stats.

        :param species: The identifier of a Pokémon species.
        :return: A ``Stats`` instance.
        """
        pokemon = _database.get_pokemon(species=species)
        strengths = {}
        for i, stat in enumerate(cls._NAMES):
            strengths[stat] = pokemon.stats[i].base_stat
        return cls(**strengths)

    @classmethod
    def make_iv(cls, gene: int) -> 'Stats':
        """Create IV stats from a Pokémon's gene.

        :param gene: An ``int`` generated by the PRNG.
        :return: A ``Stats`` instance.
        """
        return cls(
            hp=gene % 32,
            attack=(gene >> 5) % 32,
            defense=(gene >> 10) % 32,
            speed=(gene >> 16) % 32,
            special_attack=(gene >> 21) % 32,
            special_defense=(gene >> 26) % 32,
        )

    @classmethod
    def make_ev_yield(cls, species: str) -> 'Stats':
        """Create an EV instance from PokemonStats table.

        :param species: The identifier of a Pokémon species.
        :return: A ``Stats`` instance.
        """
        pokemon = _database.get_pokemon(species=species)
        stats = pokemon.stats
        yields = {stat: stats[i].effort for i, stat in enumerate(cls._NAMES)}
        return cls(**yields)

    def validate_iv(self) -> bool:
        """Check if each IV is between 0 and 32."""
        for stat in self._NAMES:
            if not 0 <= getattr(self, stat) <= 32:
                raise ValueError(
                    f"The {stat} IV ({getattr(self, stat)}) must be a number "
                    "between 0 and 32 inclusive."
                )
        return True

    def _make_operator(
        self,
        operator: Callable[[Real, Real], Real],
        other: Union['Stats', Real],
    ) -> 'Stats':
        """Programmatically create point-wise operators.

        :param operator: A callable (Real, Real) -> Real.
        :param other: If ``other`` is a ``Stats`` instance, then the
            operator will be applied point-wisely. If ``other`` is a
            number, then a scalar operation will be applied.
        :return: A ``Stats`` instance.
        """
        if not isinstance(other, type(self)) and not isinstance(other, Real):
            raise TypeError(
                f"unsupported operand type(s) for {operator}: "
                f"'{type(self)}' and '{type(other)}'"
            )
        result_stats = {}
        for stat in self._NAMES:
            if isinstance(other, type(self)):
                result_stats[stat] = operator(
                    getattr(self, stat), getattr(other, stat)
                )
            elif isinstance(other, Real):
                result_stats[stat] = operator(getattr(self, stat), other)
        return self.__class__(**result_stats)


@attr.s(auto_attribs=True, slots=True)
class BattleStats:
    """
    In-battle stats.
    """

    hp: Real
    attack: Real
    defense: Real
    special_attack: Real
    special_defense: Real
    speed: Real
    evasion: Real
    accuracy: Real

    @classmethod
    def from_stats(cls, stats: Stats) -> "BattleStats":
        """
        Create a ``BattleStats`` instance from a Pokémon's stats.
        """
        attribs = attr.asdict(stats)
        attribs['evasion'] = 1.0
        attribs['accuracy'] = 1.0
        return cls(**attribs)
