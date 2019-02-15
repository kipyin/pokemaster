"""Basic Pokémon API"""
from collections import deque
from numbers import Real
from typing import List

from pokedex.db import tables as tb
from typing_extensions import NoReturn

from pokemaster import _database
from pokemaster.prng import PRNG
from pokemaster.stats import BattleStats, Conditions, Stats


def _sign(x: int) -> int:
    """Get the sign of ``x``."""
    return int(abs(x) / x)


class Pokemon:
    """
    A Real, Living™ Pokémon.

    A ``Pokemon`` instance has the exact same attributes and behaviors
    as the ones in game: a Pokémon knows up to four moves, holds some
    kind of item, have stats (hp, attack, speed, etc.), can level up
    and evolve to another Pokémon, can be in some status conditions,
    can be cured by using medicines, and much more.
    """

    _prng = PRNG()

    def __init__(
        self,
        species: str = None,
        national_id: int = None,
        form: str = None,
        level: int = None,
        exp: int = None,
        gender: str = None,
        ability: str = None,
        nature: str = None,
        iv: Stats = None,
    ):
        """Instantiate a Pokémon.

        :param str species: The species of the Pokémon, in lowercase
            ASCII.
        :param int national_id: The Pokémon's index number in the
            National Pokédex. At least one of ``species`` and
            ``national_id`` must be specified to instantiate a Pokémon.
            If both are present, then they need to be consistent with
            each other.
        :param str form: The variant of the Pokémon, in lowercase ASCII.
        :param int level: The current level of the Pokémon. Must be an
            ``int`` between 1 and 100. Needs to be consistent with
            ``exp``, if specified.
        :param int exp: The current get_experience of the Pokémon.
            If the level is also specified, the level and the exp.
            points need to be consistent. At least one of ``level`` and
            ``exp`` must be specified to instantiate a Pokémon.
            Leaving this to None while having ``level`` set will
            automatically set the exp. points to the minimum amount
            required to be at the specified level.
        :param str gender: The Pokémon's gender. It needs to be
            consistent with the Pokémon's gender rate. If the gender
            is not set, a random gender will be assigned based on the
            Pokémon's gender rate and the personality ID.
        :param str ability: The Pokémon's ability. The ability needs
            to be consistent with the Pokémon's species. If this is not
            specified, a random ability will be determined from the
            personality ID.
        :param str nature: The Pokémon's nature. If this is not
            specified, a random nature will be determined from the
            personality ID.
        :param MutableMapping[str, int] iv: A dictionary of the
            Pokémon's individual values. The keys are the names of the
            statistics (hp, attack, defense, special-attack,
            special-defense, speed). Each individual value must not
            exceed 32. If it is not specified, a random set of IV's will
            be generated using the PRNG.
        """
        _pokemon = _database.get_pokemon(
            national_id=national_id, species=species, form=form
        )
        _growth = _database.get_experience(
            national_id=national_id, species=species, level=level, exp=exp
        )

        _species = _pokemon.species
        self._national_id = _species.id
        self._species = _species.identifier
        self._form = form

        self._height = _pokemon.height / 10  # In meters
        self._weight = _pokemon.weight / 10  # In meters
        self._types = list(map(lambda x: x.identifier, _pokemon.types))

        self._level = _growth.level
        self._exp = _growth.experience if exp is None else exp
        self._happiness = 0

        if iv is None:
            _gene = self._prng.create_gene()
            self._iv = Stats.make_iv(_gene)
        elif isinstance(iv, Stats) and iv.validate_iv():
            self._iv = iv
        else:
            raise TypeError(f"`iv` must be of type `pokemaster.Stats`.")

        self._personality = self._prng.create_personality()
        self._nature = (
            nature or _database.get_nature(self._personality).identifier
        )
        self._ability = (
            ability
            or _database.get_ability(
                species=self._species, personality=self._personality
            ).identifier
        )
        self._gender = gender or _database.get_pokemon_gender(
            species=self.species, personality=self._personality
        )

        self._species_strengths = Stats.make_species_strengths(self._species)
        self._nature_modifiers = Stats.make_nature_modifiers(self._nature)
        self._ev = Stats()
        self._stats = self._calculate_stats()
        self._current_hp = self._stats.hp
        self._conditions = Conditions()

        _moves = _database.get_pokemon_default_moves(
            species=self._species, level=self._level
        )
        self._moves = deque(map(lambda x: x.identifier, _moves), maxlen=4)
        self._pp = list(map(lambda x: x.pp, _moves))

        self._held_item = None

        self._battle_stats = BattleStats.from_stats(self._stats)

    @property
    def ability(self) -> str:
        """The Pokémon's ability."""
        return self._ability

    @property
    def current_hp(self) -> Real:
        """The amount of HP the Pokémon currently has."""
        return self._current_hp

    @property
    def exp(self) -> int:
        """The current exp. points."""
        return self._exp

    @property
    def exp_to_next_level(self) -> int:
        """The exp. points needed to get to the next level."""
        if self._level < 100:
            return (
                _database.get_experience(
                    species=self._species, level=self._level + 1
                ).experience
                - self._exp
            )
        else:
            return 0

    @property
    def form(self) -> str:
        """The Pokémon's form."""
        return self._form

    @property
    def gender(self) -> str:
        """
        The Pokémon's gender.

        Possible values are: 'male', 'female', and 'genderless'.
        """
        return self._gender

    @property
    def held_item(self) -> str:
        """The item the Pokémon is currently holding."""
        return self._held_item

    @property
    def level(self) -> int:
        """The Pokémon's level."""
        return self._level

    @property
    def moves(self) -> List[str]:
        """The Pokémon's learned moves."""
        return list(self._moves)

    @property
    def national_id(self) -> int:
        """The Pokémon's national ID."""
        return self._national_id

    @property
    def nature(self) -> str:
        """The Pokémon's nature."""
        return self._nature

    @property
    def species(self) -> str:
        """The Pokémon's species."""
        return self._species

    @property
    def stats(self) -> Stats:
        """The statistics of the Pokémon."""
        return self._stats

    @property
    def types(self) -> List[str]:
        """The Pokémon's types."""
        return self._types

    def _calculate_stats(self) -> Stats:
        """Calculate the Pokémon's stats."""
        residual_stats = Stats(
            hp=10 + self._level,
            attack=5,
            defense=5,
            special_attack=5,
            special_defense=5,
            speed=5,
        )
        stats = (
            (self._species_strengths * 2 + self._iv + self._ev // 4)
            * self._level
            // 100
            + residual_stats
        ) * self._nature_modifiers
        if self._species_strengths.hp == 1:
            stats.hp = 1
        return stats

    def _check_evolution_condition(
        self, trigger: str, evolution: tb.PokemonEvolution
    ) -> bool:
        """Check the evolution conditions."""
        if trigger != evolution.trigger.identifier:
            return False
        evolve = False
        if evolution.minimum_level:
            # The minimum level for the Pokémon.
            evolve = True if self._level >= evolution.minimum_level else False
        if evolution.held_item:
            # the item the Pokémon must hold.
            if self.held_item and self.held_item == evolution.held_item:
                evolve = True
        if evolution.time_of_day:
            # The required time of day. enum: [day, night]
            ...
        if evolution.known_move:
            # the move the Pokémon must know.
            ...
        if evolution.minimum_happiness:
            # The minimum happiness value the Pokémon must have.
            evolve = (
                True
                if self._happiness >= evolution.minimum_happiness
                else False
            )
        if evolution.minimum_beauty:
            # The minimum Beauty value the Pokémon must have.
            evolve = (
                True
                if self._conditions.beauty >= evolution.minimum_beauty
                else False
            )
        if evolution.relative_physical_stats:
            # The required relation between the Pokémon’s Attack and Defense
            # stats, as sgn(atk-def).
            if evolution.relative_physical_stats == _sign(
                self.stats.attack - self.stats.defense
            ):
                evolve = True
        if evolution.party_species:
            # the species that must be present in the party.
            ...
        return evolve

    def _evolve(self, trigger: str) -> NoReturn:
        """Evolve the Pokémon via ``trigger``.

        :param trigger: the event that triggers the evolution. Valid
            triggers are: level-up, trade, use-item, and shed.
        :return: Nothing.
        """
        pokemon = _database.get_pokemon(species=self._species)
        for child_species in pokemon.species.child_species:
            if self._check_evolution_condition(
                trigger=trigger, evolution=child_species.evolutions[0]
            ):
                evolved_species = child_species.identifier
                break
        else:
            return

        evolved_pokemon = _database.get_pokemon(species=evolved_species)
        self._ability = _database.get_ability(
            species=evolved_pokemon.species.identifier,
            personality=self._personality,
        )
        self._form = evolved_pokemon.default_form  # TODO: use the correct form
        self._height = evolved_pokemon.height
        self._national_id = evolved_pokemon.species.id
        self._species = evolved_pokemon.species.identifier
        self._species_strengths = Stats.make_species_strengths(
            species=evolved_pokemon.species.identifier
        )
        self._stats = self._calculate_stats()
        self._weight = evolved_pokemon.weight

    def gain_exp(self, earned_exp: int) -> NoReturn:
        """Add ``earned_exp`` to the Pokémon's exp. points.

        :param earned_exp: The earned get_experience points upon defeating
            an opponent Pokémon.
        :return: NoReturn
        """
        # earned_exp = new_exp - self._exp

        if earned_exp < 0:
            raise ValueError(
                f'The new exp. points, {self._exp + earned_exp}, '
                f'needs to be no less '
                f'than the current exp, {self._exp}.'
            )
        while self._level < 100 and earned_exp >= self.exp_to_next_level:
            earned_exp -= self.exp_to_next_level
            self._level_up()  # <- where evolution and other magic take place.

        # At this point, the incremental_exp is not enough to let the
        # Pokémon level up anymore. But we still need to check if it
        # overflows
        if self._level < 100:
            self._exp += earned_exp

    def _learn_move(
        self, learn: str, forget: str = None, move_method: str = None
    ) -> NoReturn:
        """Learn a new move.

        If ``move_to_forget`` is not given, then the last move in the
        move set will be forgotten. HM moves are skipped.

        :param str learn: The name of the move to learn.
        :param str forget: The name of the move to forget.
        :return: NoReturn.
        """
        # If the move to forget is specified, then first check if it
        # is a valid move to forget or not.
        # If the move is not specified, then assume forgetting the
        # first move on the list.
        if forget is not None:
            if forget not in self._moves:
                raise ValueError(
                    'Cannot forget a move: '
                    f'{self.species} does not know move {forget}.'
                )
        else:
            forget = self._moves[0]
        # Get the tables.Machine by the move identifier.
        # If `forget_machine` is not None (i.e. it is a machine) and
        # `forget_machine.is_hm` is True, then the Pokémon cannot forget
        # the move.
        # Otherwise, remove the move from `self._moves`.
        forget_machine = _database.get_machine(move_identifier=forget)
        if forget_machine is not None and forget_machine.is_hm:
            raise ValueError(
                f'{self._species} cannot forget {forget_machine.move.identifier}!'
            )
        elif len(self._moves) == 4:
            self._moves.remove(forget)

        move_pool = _database.get_move_pool(
            species=self._species, move_method=move_method
        )
        if learn in map(lambda x: x.move.identifier, move_pool):
            self._moves.append(learn)
        else:
            raise ValueError(f'{self._species} cannot learn move {learn}!')

    def use_machine(self, machine: int, forget: str = None) -> NoReturn:
        """Use a TM or HM to learn a new move.

        :param machine: The machine number. For TMs, it is the TM
            number as-is. For HMs, it is the HM number plus 100. For
            example, the machine number of TM50 is 50, and the machine
            number of HM08 is 108.
        :param forget: The move to forget. If this is ``None``, then
            the earliest learned move will be forgotten.
        :return: NoReturn.
        """
        move_to_learn = _database.get_machine(
            machine_number=machine
        ).move.identifier
        self._learn_move(learn=move_to_learn, forget=forget)

    def _level_up(self):
        """
        Increase Pokémon's level by one. Evolve the Pokémon as needed.
        """
        if self._level >= 100:
            return

        self._level += 1
        self._exp = _database.get_experience(
            species=self._species, level=self._level
        ).experience
        self._stats = self._calculate_stats()
        if self.held_item and self.held_item == 'everstone':
            return
        self._evolve('level-up')

    def _reset_battle_stats(self):
        """
        Recalculate the battle stats.
        """
        self._battle_stats = BattleStats.from_stats(self._stats)
