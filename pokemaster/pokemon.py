"""Basic Pokémon API"""

from collections import OrderedDict, namedtuple
from enum import IntEnum
from itertools import combinations
from typing import Any, AnyStr, ClassVar, List, NoReturn, Tuple, Union

import attr
from attr.validators import and_, in_, instance_of
from pokedex.db import tables as tb
from pokedex.db import util
from sqlalchemy.orm.exc import NoResultFound

from pokemaster import query
from pokemaster.charset import Charset
from pokemaster.prng import PRNG
from pokemaster.session import get_session
from pokemaster.stats import (
    EV,
    IV,
    BaseStats,
    Conditions,
    NatureModifiers,
    PermanentStats,
)
from pokemaster.trainer import Trainer


@attr.s(auto_attribs=True, repr=False, cmp=False)
class Pokemon:
    """A Pokémon."""

    session: ClassVar = get_session()
    prng: ClassVar[PRNG] = PRNG()

    # Inputs
    species: tb.PokemonSpecies = None
    form_identifier: str = None
    iv_method: int = attr.ib(validator=in_([1, 2, 4]), default=2)

    # Pokemon Genome Info
    personality: int = None
    gene: int = None

    # The 'Header' secion in Pokémon data structure
    _trainer: Trainer = None
    original_trainer: Trainer = None
    nickname: str = None
    pp_bonuses: Tuple[int] = (0, 0, 0, 0)

    # Block A: Growth Data
    held_item: tb.Item = None
    # XXX: Check that `experience` is consistent with `level`,
    # if both are set.
    _experience: int = None
    happiness: int = None

    # Block B: Attacks Data
    moves: Tuple[tb.Move] = (None, None, None, None)
    pp: Tuple[int] = (None, None, None, None)

    # Block C: EV and Conditions
    ev: EV = EV()  # 0 most of the times.
    conditions: Conditions = Conditions()

    # Block D: Miscellaneous
    pokerus: bool = False  # FIXME: use flags
    met_location: str = None  # Captured only
    pokeball: str = None  # Captured only
    origin_game_id: int = None
    level_met: int = None
    iv: IV = None
    egg: bool = False
    ability: tb.Ability = None
    ribbons: list = None
    obedience: bool = False

    # Footer
    status_condition: Any = None  # TODO: Implement status conditions. Enums?
    level: int = attr.ib(default=None, validator=in_(range(1, 101)))
    current_hp: int = None
    permanent_stats: PermanentStats = None

    # Other
    nature: tb.Nature = None
    gender: tb.Gender = None

    def __repr__(self):
        return (
            f'<A Lv {self.level} '
            f'No.{self.species.id} '
            f'{self.species.name} '
            f'at {id(self)}>'
        )

    @property
    def trainer(self):
        return self._trainer

    @trainer.setter
    def trainer(self, new_trainer: Trainer):
        if self._trainer is None:
            self.original_trainer = new_trainer
        self._trainer = new_trainer

    @property
    def ability(self):
        _abilities = self._pokemon.abilities
        if len(_abilities) == 1:
            return _abilities[0]
        else:
            return _abilities[self._personality % 2]

    @property
    def experience_to_next(self) -> int:
        """The experience needed to get to the next level."""
        if self.level < 100:
            return (
                query.experience(
                    self.session,
                    growth_rate_id=self.species.growth_rate_id,
                    level=self.level + 1,
                )
                - self._experience
            )
        else:
            return 0

    @property
    def experience(self) -> int:
        """The current experience points the Pokémon has."""
        return self._experience

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
        while self.level < 100 and earned_exp >= self.experience_to_next:
            earned_exp -= self.experience_to_next
            self.level_up()  # <- where evolution and other magic take place.

        # At this point, the incremental_exp is not enough to let the
        # Pokémon level up anymore. But we still need to check if it
        # overflows
        if self.level < 100:
            self._experience += earned_exp

    def learnable(self, move: tb.Move) -> bool:
        """Check if the Pokémon can learn a certain move or not.

        This will probably be used when a player is trying to use a TM
        or HM on a Pokémon, and display "XXX can't learn this move!" if
        this method returns False.
        """
        # return move.id in map(lambda x: x.id, self._learnable_moves)

    @property
    def shiny(self) -> bool:
        if self.trainer is not None:
            return (
                self.trainer.id
                ^ self.trainer.secret_id
                ^ (self._personality >> 16)
                ^ (self._personality % 0xFFFF)
            ) < 0b111
        else:
            return False

    def _validate_pokemon(self):
        """Check the input consistencies."""
        self.personality = self.personality or self.prng.create_personality()
        self.gene = self.gene or self.prng.create_gene(self.iv_method)

    def level_up(self):
        """Increase Pokémon's level by one. Evolve the Pokémon if needed
        and `evolve` is True (i.e. not holding an Everstone, nor canceled
        by the player.)
        """
        if self.level >= 100:
            return

        self.level += 1
        self._experience = query.experience(
            self.session,
            growth_rate_id=self.species.growth_rate_id,
            level=self.level,
        )
        pokemon = util.get(self.session, tb.Pokemon, id=self.species.id)
        self.permanent_stats = PermanentStats.using_formulae(pokemon.stats)

        if self.held_item and self.held_item.identifier == 'everstone':
            return
        # for evolution in self._evolution_triggers['level-up']:
        #     if self.check_evolution_condition(evolution):
        #         self.evolve()

    def evolve(self):
        """Evolve the Pokémon."""
        for child in self.species.child_species:
            evolution = child.evolutions[0]
            self._evolution_triggers[evolution.trigger.identifier].append(
                evolution
            )

    def check_evolution_condition(self, evolution: tb.PokemonEvolution) -> bool:
        """Check the evolution conditions."""
        evolve = False
        if evolution.minimum_level:
            # The minimum level for the Pokémon.
            evolve = True if self.level >= evolution.minimum_level else False
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

    def use_item(self, item):
        """Consume an item and activate the effect, if any."""

    @classmethod
    def from_wild_encounter(
        cls,
        *,
        species_id: int,
        level: int,
        iv_method: int = 2,
        location: str,
        compound_eyes=False,
        personality=None,
        gene=None,
    ) -> 'Pokemon':
        """Create a wild Pokemon instance via specifying the speices
        and the level.

        Exactly how speices, form, and level are determined is not
        the interest of this class-method.

        :param bool compound_eyes: whether or not the leading Pokémon's
        ability is Compound Eyes. This affects the rarity of the
        encountered Pokémon's held item.

        https://bulbapedia.bulbagarden.net/wiki/Compound_Eyes_(Ability)#Outside_of_battle
        """
        species = util.get(cls.session, tb.PokemonSpecies, id=species_id)
        pokemon = util.get(cls.session, tb.Pokemon, id=species_id)

        personality = personality or cls.prng.create_personality()
        gene = gene or cls.prng.create_gene(iv_method)

        moves = query.wild_pokemon_moves(cls.session, pokemon, level)
        nature = query.nature(cls.session, personality)
        iv = IV.from_gene(gene)
        permanent_stats = PermanentStats.using_formulae(
            base_stats=BaseStats.from_stats(pokemon.stats),
            level=level,
            iv=iv,
            ev=EV(),
            nature_modifiers=NatureModifiers.from_nature(nature),
        )
        return cls(
            species=species,
            personality=personality,
            gene=gene,
            held_item=query.wild_pokemon_held_item(
                cls.session, cls.prng, pokemon, compound_eyes
            ),
            level=level,
            experience=query.experience(
                cls.session, level, species.growth_rate_id
            ),
            happiness=species.base_happiness,
            moves=moves,
            pp=tuple(map(lambda x: x.pp, moves)),
            met_location=location,
            iv=iv,
            ability=query.ability(cls.session, pokemon.abilities, personality),
            current_hp=permanent_stats.hp,
            permanent_stats=permanent_stats,
            nature=nature,
            gender=query.pokemon_gender(
                cls.session, species.gender_rate, personality
            ),
        )

    @classmethod
    def from_capture(
        cls,
        *,
        trainer: Trainer,
        wild_pokemon: 'Pokemon',
        pokeball: str,
        nickname: str,
        **kwargs,
    ) -> 'Pokemon':
        """Create a Pokémon instance from capturing a wild Pokémon."""
        return cls(
            # Attributes 'inherit' from the wild Pokémon:
            species=wild_pokemon.species,
            personality=wild_pokemon.personality,
            gene=wild_pokemon.gene,
            held_item=wild_pokemon.held_item,
            experience=wild_pokemon.experience,
            happiness=wild_pokemon.happiness,
            moves=wild_pokemon.moves,
            pp=wild_pokemon.moves,
            pokerus=wild_pokemon.pokerus,
            met_location=wild_pokemon.met_location,
            level_met=wild_pokemon.level,
            iv=wild_pokemon.iv,
            ability=wild_pokemon.ability,
            status_condition=wild_pokemon.status_condition,
            level=wild_pokemon.level,
            current_hp=wild_pokemon.current_hp,
            permanent_stats=wild_pokemon.permanent_stats,
            nature=wild_pokemon.nature,
            gender=wild_pokemon.gender,
            # Attributes set upon capturing the Pokémon:
            trainer=trainer,
            original_trainer=original_trainer,
            nickname=nickname,
            pokeball=pokeball,
            **kwargs,
        )
