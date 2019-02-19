"""
This module defines all move effects in the Pokémon games.
"""


from typing import Iterable, Sequence, Union

from pokedex.db import tables
from typing_extensions import NoReturn

from pokemaster._database import get_move
from pokemaster.battle import Field
from pokemaster.pokemon import Pokemon


def calculate_damage(
    source: Pokemon, target: Pokemon, move: tables.Move, field: Field
) -> int:
    """Calculate the actual damage a move deals.

    :param source: The move's user.
    :param target: The move's target.
    :param move: A row from ``Move`` table in the database.
    :param field: A ``Field`` instance.
    :return: int
    """
    if move.power is None:
        return 0

    if move.damage_class.identifier == 'physical':
        effective_attack = getattr(source.stats, "attack")
        effective_defense = getattr(target.stats, "defense")
    elif move.damage_class.identifier == 'special':
        effective_attack = getattr(source.stats, "special_attack")
        effective_defense = getattr(target.stats, "special_defense")
    else:
        raise ValueError(
            f"Unknown damage class: {move.damage_class.identifier}."
        )

    base_damage = (
        2 * source.level // 5 + 2
    ) * move.power * effective_attack // effective_defense // 50 + 2


def regular_damage(
    user: Pokemon,
    move: "Move",
    field: Field,
    power: int,
    targets: Union[Pokemon, Sequence[Pokemon]] = None,
) -> NoReturn:
    """Deal regular damage to target Pokémon.

    If *targets* is specified, then the damage will be taken
    on that targets. If it is not specified, then the default
    targets from *field* will be selected.

    :param user: The move user.
    :param field: A ``pokemaster.Field`` instance.
    :param power: The base power of the move.
    :param targets: A list of target Pokémon, or a single
        target Pokémon.
    """
    # 1. If *targets* is given, check its validity.
    # 2. For each target:
    #   1) Calculate the actual damage based on the power,
    #      the user's attack stat and the target's defense
    #      stat.
    #   2) Reduce the target's HP.

    opponents = field.perspective(user).opponents
    if isinstance(targets, Pokemon) and targets in opponents:
        # the target is a single Pokémon
        targets = [targets]
    elif isinstance(targets, Iterable) and set(targets) ^ set(opponents):
        pass
    elif targets is None:
        targets = opponents
    else:
        raise ValueError(f"Invalid targets: {targets}.")
