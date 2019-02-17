"""
This module provides battle-related classes.
"""

from typing import Sequence, Tuple

import attr

from pokemaster.pokemon import Pokemon
from pokemaster.weather import Weather


@attr.s(slots=True, auto_attribs=True)
class Team:
    """A collection of active Pokémon on a battle field."""

    members: Sequence[Pokemon]


@attr.s(slots=True, auto_attribs=True)
class Field:
    """A battle field."""

    teams: Tuple[Team, Team]
    weather: Weather = Weather("clear-skies")
