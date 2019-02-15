"""
Provides weather-related mechanisms.
"""

from typing import ClassVar, Union

import attr
from typing_extensions import Final

from pokemaster.pokemon import Pokemon

WEATHERS: Final = {
    "clear-skies": {},
    "harsh-sunlight": {
        3: {
            "natural": "The sunlight is strong.",
            "move": "The sunlight got bright!",
            "ability": "{pokemon}'s Drought intensified the sun's rays!",
            "after-turn": "The sunlight is strong.",
            "end": "The sunlight faded.",
        },
        4: {
            "natural": None,
            "move": "The sunlight turned harsh!",
            "ability": "{pokemon}'s Drought intensified the sun's rays!",
            "after-turn": "The sunlight is strong.",
            "end": "The sunlight faded.",
        },
        5: {
            "natural": None,
            "move": "The sunlight turned harsh!",
            "ability": "The sunlight turned harsh!",
            "after-turn": None,
            "end": "The sunlight faded.",
        },
    },
    "rain": {
        3: {
            "natural": "It is raining.",
            "move": "It started to rain!",
            "ability": "{pokemon}'s Drizzle made it rain!",
            "after-turn": "Rain continues to fall.",
            "end": "The rain stopped.",
        },
        4: {
            "natural": "It started to rain!",
            "move": "It started to rain!",
            "ability": "{pokemon}'s Drizzle made it rain!",
            "after-turn": "Rain continues to fall.",
            "end": "The rain stopped.",
        },
        5: {
            "natural": "It started to rain!",
            "move": "It started to rain!",
            "ability": "{pokemon}'s Drizzle made it rain!",
            "after-turn": "Rain continues to fall.",
            "end": "The rain stopped.",
        },
    },
    "sandstorm": {
        3: {
            "natural": "A sandstorm is raging.",
            "move": "A sandstorm brewed!",
            "ability": "{pokemon}'s Sand Stream whipped up a sandstorm!",
            "after-turn": "The sandstorm rages.",
            "damage": "{pokemon} is buffeted by the sandstorm!",
            "end": "The sandstorm subsided.",
        },
        4: {
            "natural": "A sandstorm brewed!",
            "move": "A sandstorm brewed!",
            "ability": "{pokemon}'s Sand Stream whipped up a sandstorm!",
            "after-turn": "The sandstorm rages.",
            "damage": "{pokemon} is buffeted by the sandstorm!",
            "end": "The sandstorm subsided.",
        },
        5: {
            "natural": "A sandstorm kicked up!",
            "move": "A sandstorm kicked up!",
            "ability": "A sandstorm kicked up!",
            "after-turn": None,
            "damage": "{pokemon} is buffeted by the sandstorm!",
            "end": "The sandstorm subsided.",
        },
    },
    "hail": {
        3: {
            "natural": None,
            "move": "It started to hail!",
            "ability": None,
            "after-turn": "Hail continues to fall.",
            "damamge": "{pokemon} is pelted by Hail!",
            "end": "The hail stopped.",
        },
        4: {
            "natural": "It started to hail!",
            "move": "It started to hail!",
            "ability": "{pokemon}'s Snow Warning whipped up a hailstorm!",
            "after-turn": "Hail continues to fall.",
            "damage": "{pokemon} is buffeted by the Hail!",
            "end": "The hail stopped.",
        },
        5: {
            "natural": "It started to hail!",
            "move": "It started to hail!",
            "ability": "It started to hail!",
            "after-turn": None,
            "damage": "{pokemon} is buffeted by the Hail!",
            "end": "The hail stopped.",
        },
    },
}


def weather_name_converter(name: str) -> str:
    """Convert ``Weather.name`` attribute to name-style
    (lowercase, ASCII, slugified string).
    """
    return name.replace(" ", "-").lower().strip()


def weather_name_validator(_, __, name: str) -> None:
    """Validate ``Weather.name`` attribute."""
    if name not in WEATHERS.keys():
        raise ValueError(
            f"Unsupported weather {name}. " f"Valid weathers are {WEATHERS}"
        )


def weather_generation_validator(_, __, generation: int) -> None:
    """Only Generation 3 ~ 5 are supported."""
    if generation not in range(3, 6):
        raise ValueError(
            f"Invalid generation: Gen. {generation}. "
            f"Only Generation 3 ~ 5 are supported."
        )


def weather_trigger_validator(weather: "Weather", _, trigger: str) -> None:
    """Validate if the trigger is one of 'natural', 'move', or 'ability'."""
    if trigger not in ['natural', 'move', 'ability']:
        # Make sure the trigger is valid.
        raise ValueError(
            f"Invalid trigger for {weather.name}: {trigger}. "
            "Valid triggers are 'natural', 'move', or 'ability'."
        )
    elif weather.name == 'clear-skies' and trigger != 'natural':
        # Clear skies has no description.
        raise ValueError(f"Clear skies cannot be triggered by {trigger}.")
    elif (
        weather.name != 'clear-skies'
        and WEATHERS[weather.name][weather.generation][trigger] is None
    ):
        # Entries without descriptions (except for Clear skies) are also
        # invalid.

        # The trigger in adverb.
        how = 'naturally' if trigger == 'natural' else f'via {trigger}'
        raise ValueError(
            f"{weather.name} cannot occur {how} in Gen. "
            f"{weather.generation}."
        )


@attr.s(auto_attribs=True, slots=True)
class Weather:
    """A type of weather, such as *rain* or *sandstorm*.

    :param name: The name of the weather, such as 'rain' or
        'sandstorm'.
    :param duration: How long the weather lasts. A weather
        lasts forever by default.
    :param generation: The game generation.
    :param trigger: How the weather is triggered. Valid
        triggers are 'natural', 'ability', and 'move'.
    """

    name: str = attr.ib(
        validator=weather_name_validator, converter=weather_name_converter
    )
    duration: Union[int, float] = float('inf')
    generation: int = attr.ib(validator=weather_generation_validator, default=3)
    trigger: str = attr.ib(
        validator=weather_trigger_validator, default='natural'
    )
    _init_msg: str = attr.ib(init=False)
    _damage_msg: str = attr.ib(init=False)
    _after_turn_msg: str = attr.ib(init=False)
    _end_msg: str = attr.ib(init=False)

    def __attrs_post_init__(self):
        if self.name == 'clear-skies':
            return
        messages = WEATHERS[self.name][self.generation]
        self._init_msg = messages[self.trigger]
        self._damage_msg = messages.get("damage", None)
        self._after_turn_msg = messages["after-turn"]
        self._end_msg = messages["end"]

    def get_init_msg(self, pokemon: Pokemon) -> str:
        """Return the weather's initiation message."""
        if self.trigger == "ability":
            return self._init_msg.format(pokemon=pokemon.species)
        else:
            return self._init_msg

    def get_damage_msg(self, damaged_pokemon: Pokemon) -> str:
        """Return the message when the weather damages
        a Pokémon.
        """
        if self._damage_msg is not None:
            return self._damage_msg.format(pokemon=damaged_pokemon.species)
        else:
            raise ValueError(f"{self.name} does not have a damamge message!")

    def get_after_turn_msg(self):
        """Return the message that prints out right before
        a turn ends.
        """
        if self._after_turn_msg is not None:
            return self._after_turn_msg
        else:
            raise ValueError(
                f"{self.name} does not have an after-turn message in "
                f"Gen {self.generation}"
            )

    def get_end_msg(self):
        """Return the message that prints out when the weather
        effect ends.
        """
        return self._end_msg
