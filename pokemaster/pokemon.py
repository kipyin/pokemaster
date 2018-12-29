#!/usr/bin/env python3
"""
    Basic Pokémon API

"""
from enum import IntEnum
from typing import AnyStr, ClassVar, List, Tuple, Union, NoReturn

import attr
from attr.validators import instance_of as _instance_of
from pokedex import formulae
from pokedex.db import tables as tb
from sqlalchemy.orm.exc import NoResultFound

from pokemaster.session import get_session


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


class Pokemon:
    """A Pokémon"""

    session: ClassVar = get_session()
    prng: ClassVar[PRNG] = PRNG()

    def __init__(
        self, identity: Union[str, int], level=None, pid_method=2, is_egg=False
    ):

        self._pokemon = self._query_pokemon(identity)

        if level is None:
            pass
        elif isinstance(level, int):
            if level not in range(0, 101):
                raise ValueError(
                    f'Invalid level {level}. Level must be between 0 and 100.'
                )
        else:
            raise TypeError(f'Level must be an int, not a {type(level)}')

        # The PRNG should not be wasted on invalid Pokémon calls, so this
        # is called after a Pokémon is validated.
        self._pid, self._ivs = self.prng.create_pid_ivs(method=pid_method)

        # TODO: @property? Assigning a trainer to a Pokémon will change
        # the Pokémon's current trainer and the original trainer.
        # Does shininess change?
        self.trainer = None
        self._original_trainer = None
        self._current_trainer = None

        # XXX: Hmmm is there a more descriptive way to do this?
        self.is_egg = is_egg
        # Can only be changed via gaining experience and applying Rare
        # Candies?
        if self.is_egg:
            self._level = 0
        else:
            self._level = level or 5

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
            .filter(tb.PokemonMove.pokemon_id == self._id)
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
            .filter(tb.PokemonStat.pokemon_id == self._id)
            .filter(tb.Stat.is_battle_only == False)
            .all()
        )

        def _stat_attr(base_stat) -> str:
            """Get the stat attributes (hp, attack, etc.) from identifiers."""
            return base_stat.stat.identifier.replace('-', '_')

        # fmt: off
        # Base stats and effort points will change upon evolution.
        # effort values should be settable?
        self.base_stats = Stats(**dict(map(lambda x: (_stat_attr(x), x.base_stat), base_stats)))
        self.effort_points = Stats(**dict(map(lambda x: (_stat_attr(x), x.effort), base_stats)))
        self.effort_values = EffortValue(**dict(map(lambda x: (_stat_attr(x), 0), base_stats)))
        # fmt: on
        self._stats = self._calculate_stats()

        self._experience = self._query_experience(level=self._level)

        self._evolution_triggers = defaultdict(list)
        for child in self._pokemon.species.child_species:
            evolution = child.evolutions[0]
            self._evolution_triggers[evolution.trigger.identifier].append(
                evolution
            )

        # TODO: use self._pokemon.items to genenrate random held items.
        self._held_item = None

    def __repr__(self):
        return f'<A Lv {self.level} No.{self._id} {self._pokemon.name} at {id(self)}>'

    # TODO: make the args (*args, **kwargs) to allow initialzing from
    # arbitrary criteria.
    def _query_pokemon(self, identity):
        """Set the pokemon property by the id or identifier.

        This method should be called first when initializing a Pokémon.
        """
        try:
            if isinstance(identity, str):
                return (
                    self.session.query(tb.Pokemon)
                    .filter_by(identifier=identity)
                    .one()
                )
            elif isinstance(identity, int):
                return (
                    self.session.query(tb.Pokemon).filter_by(id=identity).one()
                )
            else:
                raise TypeError(
                    f'`identity` must be a str or an int, not {type(identity)}'
                )
        except NoResultFound:
            raise ValueError(f'Cannot find Pokémon {identity}.')

    @property
    def _id(self) -> int:
        """This Pokémon's id."""
        return self._pokemon.id

    @property
    def _identifier(self) -> str:
        """This Pokémon's identifier."""
        return self._pokemon.identifier

    @property
    def name(self) -> str:
        """This Pokémon's name."""
        return self._pokemon.name

    @property
    def ability(self):
        _abilities = self._pokemon.abilities
        if len(_abilities) == 1:
            return _abilities[0]
        else:
            return _abilities[self._pid % 2]

    def _query_experience(self, level):
        """Look up this Pokémon's experience at various levels."""
        return (
            self.session.query(tb.Experience)
            .filter_by(
                growth_rate_id=self._pokemon.species.growth_rate_id, level=level
            )
            .one()
            .experience
        )

    @property
    def _experience_to_next(self) -> int:
        """The experience needed to get to the next level."""
        if self._level < 100:
            return (
                self._query_experience(level=self._level + 1) - self._experience
            )
        else:
            return 0

    @property
    def experience(self) -> int:
        """The current experience points the Pokémon has."""
        return self._experience

    # XXX: use gain_exp of some sort instead? This can be confusing?
    @experience.setter
    def experience(self, new_exp: int):
        """Set the experience. Level, experience-to-next will change if
        needed.

        Usage::
            >>> pokemon.experience += 53
        """
        earned_exp = new_exp - self._experience

        # XXX: No known mechanism decreases the exp, right?
        if earned_exp < 0:
            raise ValueError(
                f'The new experience point, {new_exp}, needs to be no less '
                f'than the current exp, {self._experience}.'
            )
        while self.level < 100 and earned_exp >= self._experience_to_next:
            earned_exp -= self._experience_to_next
            self._level_up()  # <- where evolution and other magic take place.

        # At this point, the incremental_exp is not enough to let the
        # Pokémon level up anymore. But we still need to check if it
        # overflows
        if self._level < 100:
            self._experience += earned_exp

    def learnable(self, move: tb.Move) -> bool:
        """Check if the Pokémon can learn a certain move or not.

        This will probably be used when a player is trying to use a TM
        or HM on a Pokémon, and display "XXX can't learn this move!" if
        this method returns False.
        """
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

    # XXX: Should `gender` return a tb.Gender or a Gender Enum?
    @property
    def gender(self) -> Gender:
        if self._pokemon.species.gender_rate == -1:  # Genderless
            return Gender.GENDERLESS
        elif self._pokemon.species.gender_rate == 8:  # Female-only
            return Gender.FEMALE
        elif self._pokemon.species.gender_rate == 0:  # Male-only
            return Gender.MALE
        else:
            # Gender is determined by the last byte of the PID.
            p_gender = self._pid % 0x100
            gender_threshold = 0xFF * self._pokemon.species.gender_rate // 8
            if p_gender >= gender_threshold:
                return Gender.MALE
            else:
                return Gender.FEMALE

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
            ) < 0b111
        else:
            return False

    @property
    def level(self):
        return self._level

    def _level_up(self):
        """Increase Pokémon's level by one. Evolve the Pokémon if needed
        and `evolve` is True (i.e. not holding an Everstone, nor canceled
        by the player.)
        """
        if self._level >= 100:
            return

        self._level += 1
        self._experience = self._query_experience(self._level)
        self._stats = self._calculate_stats()

        if self._held_item and self._held_item.identifier == 'everstone':
            return
        for evolution in self._evolution_triggers['level-up']:
            if self._check_evolution_condition(evolution):
                self._evolve()

    def _evolve(self):
        """Evolve the Pokémon."""
        self._pokemon = self._query_pokemon(species.id)
        self._base_stats = self._calculate_stats()

    def _check_evolution_condition(
        self, evolution: tb.PokemonEvolution
    ) -> bool:
        """Check the evolution conditions."""
        evolve = False
        if evolution.minimum_level:
            # The minimum level for the Pokémon.
            evolve = True if self._level >= evolution.minimum_level else False
        if evolution.gender:
            # the Pokémon’s required gender, or None if gender doesn’t matter
            evolve = True if self._gender == evolution.gender.id else False
        if evolution.location:
            # the location the evolution must be triggered at.
            ...
        if evolution.held_item:
            # the item the Pokémon must hold.
            if self._held_item and self._held_item.id == evolution.held_item:
                evolve = True
        if evolution.time_of_day:
            # The required time of day. enum: [day, night]
            ...
        if evolution.known_move:
            # the move the Pokémon must know.
            ...
        if evolution.known_move_type:
            # the type the Pokémon must know a move of.
            ...
        if evolution.minimum_happiness:
            # The minimum happiness value the Pokémon must have.
            ...
        if evolution.minimum_beauty:
            # The minimum Beauty value the Pokémon must have.
            ...
        if evolution.minimum_affection:
            # The minimum number of “affection” hearts the Pokémon must have
            # in Pokémon-Amie.
            ...
        if evolution.relative_physical_stats:
            # The required relation between the Pokémon’s Attack and Defense
            # stats, as sgn(atk-def).
            ...
        if evolution.party_species:
            # the species that must be present in the party.
            ...
        if evolution.party_type:
            # a type that at least one party member must have.
            ...
        if evolution.trade_species:
            # the species for which this one must be traded.
            ...
        if evolution.needs_overworld_rain:
            # True iff it needs to be raining outside of battle.
            ...
        if evolution.turn_upside_down:
            # True iff the 3DS needs to be turned upside-down as this Pokémon
            # levels up.
            ...
        return evolve
