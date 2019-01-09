"""Basic Pokémon API"""
from typing import ClassVar, List, MutableMapping, NoReturn, Union
from warnings import warn

import attr
from attr.validators import instance_of, optional
from pokedex.db import tables as tb

from pokemaster import query
from pokemaster.prng import PRNG
from pokemaster.stats import (
    EV,
    IV,
    Conditions,
    NatureModifiers,
    PermanentStats,
    SpeciesStrengths,
)
from pokemaster.trainer import Trainer


def _sign(x: int) -> int:
    """Get the sign of ``x``."""
    return int(abs(x) / x)


def _typed(type_, **kwargs):
    validator = [optional(instance_of(type_))]
    new_validators = kwargs.pop('validator', None)

    if isinstance(new_validators, list) and new_validators:
        validator.extend(new_validators)
    elif new_validators is not None:
        validator.append(new_validators)

    default = kwargs.pop('default', None)
    kw_only = kwargs.pop('kw_only', True)
    repr = kwargs.pop('repr', False)
    cmp = kwargs.pop('cmp', False)

    return attr.ib(
        validator=validator,
        default=default,
        kw_only=kw_only,
        repr=repr,
        cmp=cmp,
        **kwargs,
    )


@attr.s(repr=False)
class Pokemon:
    """An authentic, living Pokémon in game.

    A ``Pokemon`` instance has the exact same attributes and behaviors
    as the ones in game: a Pokémon knows up to four moves, holds some
    kind of item, have stats (hp, attack, speed, etc.), can level up
    and evolve to another Pokémon, can be in some status conditions,
    can be cured by using medicines, and much more.
    """

    prng: ClassVar = PRNG()

    # Inputs
    national_id: int = _typed(int, kw_only=False, repr=True)
    name: str = _typed(str, repr=True)
    form: str = _typed(str, repr=True)
    language: str = _typed(str)

    # Pokemon Genome Info
    # I think it's better to let the program handle the PID & IV creation.
    # If the user wants to alter a particular piece of information,
    # override it via providing the corresponding keyword argument.
    # personality = _typed(int)
    # gene = _typed(int)
    # iv_method = _typed(int, validator=in_([1, 2, 4]), default=2)

    # The 'Header' section in Pokémon data structure
    _trainer: Trainer = _typed(Trainer)
    original_trainer: Trainer = _typed(Trainer)
    nickname: str = _typed(str)
    pp_bonuses: List[int] = _typed(list)

    # Block A: Growth Data
    held_item: str = _typed(str)
    # XXX: Check that `experience` is consistent with `level`,
    # if both are set.
    experience: int = _typed(int)
    happiness: int = _typed(int)

    # Block B: Moves Data
    moves: List[Union[int, str]] = _typed(list)
    pp: List[int] = _typed(list)

    # Block C: EV and Conditions
    ev: EV = _typed(EV)
    conditions: Conditions = _typed(Conditions)

    # Block D: Miscellaneous
    pokerus: bool = _typed(bool)
    met_location: str = _typed(str)
    pokeball: str = _typed(str)
    origin_game_id: int = _typed(int)
    level_met: int = _typed(int)
    iv: IV = _typed(IV)
    egg: bool = _typed(bool)
    ability: str = _typed(str)
    ribbons: list = _typed(list)
    obedience: bool = _typed(bool)

    # Footer
    status_condition: str = _typed(str)
    _level: int = _typed(int, repr=True)
    current_hp: int = _typed(int)
    permanent_stats: PermanentStats = _typed(PermanentStats)

    # Other
    nature = _typed(str)
    gender = _typed(str)
    personality = _typed(int)
    gene = _typed(int)

    # Species Data
    growth_rate_id: int = attr.ib(init=False)
    height: int = attr.ib(init=False)
    weight: int = attr.ib(init=False)
    color: str = attr.ib(init=False)
    shape: str = attr.ib(init=False)
    habitat: str = attr.ib(init=False)
    evolutions: MutableMapping[str, tb.PokemonEvolution] = attr.ib(
        init=False, default=attr.Factory(dict)
    )

    def __attrs_post_init__(self):
        # XXX: Implement forms and languages!
        pokemon = query.pokemon(
            id=self.national_id,
            name=self.name,
            # language=self.language
        )
        self.national_id = self.national_id or pokemon.id
        self.name = self.name or pokemon.name
        # self.language = self.language or pokemon.language
        species: tb.PokemonSpecies = pokemon.species
        self.growth_rate_id = species.growth_rate_id
        self.height = species.height
        self.weight = species.weight
        self.color = species.color.identifier
        self.shape = species.shape.identifier
        self.habitat = species.habitat.identifier
        for evolved_species in species.child_species:
            conditions = evolved_species.evolutions[0]
            self.evolutions[evolved_species.identifier] = conditions

        self._level = self._level or 5
        exp = query.experience(
            level=self._level,
            growth_rate_id=species.growth_rate_id,
            experience=self.experience,
        )
        self.experience = self.experience or exp.experience
        self.happiness = self.happiness or species.base_happiness

        # FIXME: add query.moves or Move or whatever. Just make it work.
        moves = query.wild_pokemon_moves(pokemon, self._level)
        if self.moves:
            # convert all elements into ...
            pass
        else:
            self.moves = list(map(lambda x: x.identifier, moves))

        if self.pp is None:
            self.pp = list(map(lambda x: x.pp, moves))
        else:
            self.pp = list(map(lambda x, y: min(x, y.pp), self.pp, moves))

        self.ev = self.ev or EV()
        self.conditions = self.conditions or Conditions()

        if self.level_met and self.level_met != self._level:
            warn(
                f'`level_met` ({self.level_met}) '
                'is inconsistent with '
                f'`level` ({self._level})!'
            )
        else:
            self.level_met = self._level

        personality, gene = self.prng.create_genome()
        self.iv = self.iv or IV.from_gene(gene)

        correct_ability = query.ability(pokemon.abilities, personality)
        if self.ability and self.ability not in list(
            map(lambda x: x.identifier, pokemon.abilities)
        ):
            warn(
                f'{self.name} does not have ability {self.ability}! '
                f'Overriding it with {correct_ability}.'
            )
            self.ability = correct_ability
        elif self.ability is None:
            self.ability = correct_ability

        nature = (
            query.nature(identifier=self.nature)
            if self.nature
            else query.nature(personality=personality)
        )
        self.nature = nature.identifier

        if self.permanent_stats is None:
            self.permanent_stats = PermanentStats.using_formulae(
                base_stats=SpeciesStrengths.from_stats(pokemon.stats),
                level=self._level,
                iv=self.iv,
                ev=self.ev,
                nature_modifiers=NatureModifiers.from_nature(nature),
            )
        if self.current_hp:
            self.current_hp = min(self.current_hp, self.permanent_stats.hp)
        else:
            self.current_hp = self.permanent_stats.hp

        self.gender = self.gender or query.pokemon_gender(
            species.gender_rate, personality
        )

    def __repr__(self):
        return (
            f'<A Lv {self._level} '
            f'No.{self.national_id} '
            f'{self.name} '
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
    def experience_to_next(self) -> int:
        """The experience needed to get to the next level."""
        if self._level < 100:
            return (
                query.experience(
                    growth_rate_id=self.growth_rate_id, level=self._level + 1
                )
                - self.experience
            )
        else:
            return 0

    @property
    def shiny(self) -> bool:
        if self.trainer is not None:
            return (
                self.trainer.id
                ^ self.trainer.secret_id
                ^ (self.personality >> 16)
                ^ (self.personality % 0xFFFF)
            ) < 0b111
        else:
            return False

    def validate(self):
        """Check if all fields are still valid."""
        attr.validate(self)

    def gain_exp(self, new_exp: int):
        """Set the experience. Level, experience-to-next will change if
        needed.
        """
        earned_exp = new_exp - self.experience

        if earned_exp < 0:
            raise ValueError(
                f'The new experience point, {new_exp}, needs to be no less '
                f'than the current exp, {self.experience}.'
            )
        while self._level < 100 and earned_exp >= self.experience_to_next:
            earned_exp -= self.experience_to_next
            self.level_up()  # <- where evolution and other magic take place.

        # At this point, the incremental_exp is not enough to let the
        # Pokémon level up anymore. But we still need to check if it
        # overflows
        if self._level < 100:
            self.experience += earned_exp

    def level_up(self):
        """Increase Pokémon's level by one. Evolve the Pokémon if needed
        and `evolve` is True (i.e. not holding an Everstone, nor canceled
        by the player.)
        """
        if self._level >= 100:
            return

        self._level += 1
        self.experience = query.experience(
            growth_rate_id=self.growth_rate_id, level=self._level
        )
        self.permanent_stats.level_up()

        if self.held_item and self.held_item == 'everstone':
            return
        self.evolve('level-up')

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

    def learnable(self, move: tb.Move) -> bool:
        """Check if the Pokémon can learn a certain move or not.

        This will probably be used when a player is trying to use a TM
        or HM on a Pokémon, and display "XXX can't learn this move!" if
        this method returns False.
        """
        # return move.id in map(lambda x: x.id, self._learnable_moves)

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
