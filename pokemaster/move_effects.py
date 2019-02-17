"""
This module defines all move effects in the Pokémon games.
"""


from typing import Sequence, Union

from typing_extensions import NoReturn

from pokemaster.battle import Field
from pokemaster.pokemon import Pokemon


def regular_damage(
    user: Pokemon,
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
    :param targets: A list of target Pokémon, or a single
        target Pokémon.
    """
    # 1. If *targets* is given, check its validity.
    # 2. For each target:
    #   1) Calculate the actual damage based on the
    #      user's attack stat and the target's defense stat.
    #   2) Reduce the target's HP.
