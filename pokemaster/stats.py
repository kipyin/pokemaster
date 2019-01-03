import operator
from functools import partial
from typing import Any, List

import attr
from pokedex import formulae
from pokedex.db import tables as tb

from pokemaster.exceptions import MaxStatExceededError

STAT_NAMES = (
    'hp',
    'attack',
    'defense',
    'special_attack',
    'special_defense',
    'speed',
)


@attr.s(auto_attribs=True, slots=True)
class BaseStats:
    """The base stats of a Pokémon."""

    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int

    @classmethod
    def from_stats(cls, stats: List[tb.PokemonStat]):
        """Create an instance of BaseStats from PokemonStat table."""
        kwargs = {stat: stats[i].base_stat for i, stat in enumerate(STAT_NAMES)}
        return cls(**kwargs)


def _iv_attrib(**kwargs):
    """attr.ib for IV."""

    def validator(_, __, value):
        """Validate each IV is no greater than 32."""
        if value > 32:
            raise MaxStatExceededError(f'IV cannot exceed 32.')

    return attr.ib(validator=validator, **kwargs)


@attr.s(frozen=True, slots=True)
class IV:
    """The individual values of a Pokémon."""

    hp: int = _iv_attrib()
    attack: int = _iv_attrib()
    defense: int = _iv_attrib()
    special_attack: int = _iv_attrib()
    special_defense: int = _iv_attrib()
    speed: int = _iv_attrib()

    @classmethod
    def from_gene(cls, genome: int) -> 'IV':
        return cls(
            hp=genome % 32,
            attack=(genome >> 5) % 32,
            defense=(genome >> 10) % 32,
            speed=(genome >> 16) % 32,
            special_attack=(genome >> 21) % 32,
            special_defense=(genome >> 26) % 32,
        )


@attr.s(slots=True)
class EV:

    _hp: int = attr.ib(default=0)
    _attack: int = attr.ib(default=0)
    _defense: int = attr.ib(default=0)
    _special_attack: int = attr.ib(default=0)
    _special_defense: int = attr.ib(default=0)
    _speed: int = attr.ib(default=0)

    @_hp.validator
    def _hp_validator(self, attribute, value):
        self._validated('hp', value)

    @_attack.validator
    def _attack_validator(self, attribute, value):
        self._validated('attack', value)

    @_defense.validator
    def _defense_validator(self, attribute, value):
        self._validated('defense', value)

    @_special_attack.validator
    def _special_attack_validator(self, attribute, value):
        self._validated('special_attack', value)

    @_special_defense.validator
    def _special_defense_validator(self, attribute, value):
        self._validated('special_defense', value)

    @_speed.validator
    def _speed_validator(self, attribute, value):
        self._validated('speed', value)

    def __add__(self, other: 'EV') -> 'EV':
        return self._make_operator(operator.add, other)

    def __sub__(self, other: 'EV') -> 'EV':
        return self._make_operator(operator.sub, other)

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        self._hp = self._validated('hp', value)

    @property
    def attack(self):
        return self._attack

    @attack.setter
    def attack(self, value):
        self._attack = self._validated('attack', value)

    @property
    def defense(self):
        return self._defense

    @defense.setter
    def defense(self, value):
        self._defense = self._validated('defense', value)

    @property
    def special_attack(self):
        return self._special_attack

    @special_attack.setter
    def special_attack(self, value):
        self._special_attack = self._validated('special_attack', value)

    @property
    def special_defense(self):
        return self._special_defense

    @special_defense.setter
    def special_defense(self, value):
        self._special_defense = self._validated('special_defense', value)

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, value):
        self._speed = self._validated('speed', value)

    @classmethod
    def get_yield(cls, stats: List[tb.PokemonStat]) -> 'EV':
        """Create an EV instance from PokemonStats table."""
        kwargs = {stat: stats[i].effort for i, stat in enumerate(STAT_NAMES)}
        return cls(**kwargs)

    def _validated(self, attrib, value: int) -> int:
        current_stats_sum = sum(map(partial(getattr, self), STAT_NAMES))
        if value > 255:
            raise MaxStatExceededError(f'`{attrib}` exceeds 255!')
        elif current_stats_sum - getattr(self, attrib) + value > 510:
            raise MaxStatExceededError('Total EV exceeds 510!')
        else:
            return value

    def _make_operator(self, op, other: 'EV') -> 'EV':
        """Programmatically create point-wise operations."""
        if not isinstance(other, type(self)):
            raise TypeError(
                f"unsupported operand type(s) for {op}: "
                f"'{type(self)}' and '{type(other)}'"
            )
        kwargs = {}
        for stat in STAT_NAMES:
            kwargs[stat] = op(getattr(self, stat), getattr(other, stat))
        return EV(**kwargs)


@attr.s(slots=True, auto_attribs=True)
class NatureModifiers:
    """Stat modifiers determined by a Pokémon's nature."""

    hp: float = 1.0
    attack: float = 1.0
    defense: float = 1.0
    special_attack: float = 1.0
    special_defense: float = 1.0
    speed: float = 1.0

    @classmethod
    def from_nature(cls, nature: tb.Nature) -> 'NatureModifiers':
        """Create a NatureModifiers instance from the Nature table."""
        if nature.is_neutral:
            return cls()
        increased_stat = nature.increased_stat.identifier.replace('-', '_')
        decreased_stat = nature.decreased_stat.identifier.replace('-', '_')
        return cls(**{increased_stat: 1.1, decreased_stat: 0.9})


@attr.s(slots=True, auto_attribs=True)
class PermanentStats:
    """A Pokémon's calculated stats."""

    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int
    _metadata: dict = {}

    def level_up(self):
        if self._metadata[level] < 100:
            self._metadata[level] += 1
            new_stats = self.__class__.using_formulae(**self._metadata)
            for stat in STAT_NAMES:
                setattr(self, stat, getattr(new_stats, stat))

    @classmethod
    def using_formulae(
        cls,
        *,
        base_stats: BaseStats,
        level: int,
        iv: IV,
        ev: EV,
        nature_modifiers: NatureModifiers,
    ) -> 'PermanentStats':
        """Create a PermanentStats instance."""
        meta = {
            'base_stats': base_stats,
            'level': level,
            'iv': iv,
            'ev': ev,
            'nature_modifiers': nature_modifiers,
        }
        kwargs = {'_metadata': meta}
        for stat in STAT_NAMES:
            if stat == 'hp':
                func = formulae.calculated_hp
            else:
                func = formulae.calculated_stat
            kwargs[stat] = func(
                base_stat=getattr(base_stats, stat),
                level=level,
                iv=getattr(iv, stat),
                effort=getattr(effort, stat),
                nature=getattr(nature_modifiers, stat),
            )
        return cls(**kwargs)


@attr.s(slots=True, auto_attribs=True)
class Conditions:
    """Contest conditions"""

    coolness: int = 0
    beauty: int = 0
    cuteness: int = 0
    smartness: int = 0
    toughness: int = 0
    # feel: int = 0
