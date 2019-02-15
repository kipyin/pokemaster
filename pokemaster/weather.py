"""
Provides weather-related mechanisms.
"""

from typing import Union

import attr
from typing_extensions import Final

SUPPORTED_WEATHERS: Final = [
    "clear-skies",
    "harsh-sunlight",
    "rain",
    "sandstorm",
    "hail",
]


def weather_name_converter(name: str) -> str:
    """Convert ``Weather.name`` attribute to name-style
    (lowercase, ASCII, slugified string).
    """
    name = name.replace(" ", "-")
    name = name.lower().strip()
    return name


def weather_name_validator(_, __, name: str) -> None:
    """Validate ``Weather.name`` attribute."""
    if name not in SUPPORTED_WEATHERS:
        raise ValueError(
            f"Unsupported weather {name}. "
            f"Valid weathers are {SUPPORTED_WEATHERS}"
        )


@attr.s(auto_attribs=True, slots=True)
class Weather:
    """A type of weather, such as *rain* or *sandstorm*.

    :param name: The name of the weather, such as 'rain' or
        'sandstorm'.
    :param duration: How long the weather lasts. A weather
        lasts forever by default.
    """

    name: str = attr.ib(
        validator=weather_name_validator, converter=weather_name_converter
    )
    duration: Union[int, float] = float('inf')
