"""Tests for ``pokemaster.weather.Weather``."""
import pytest

from pokemaster.pokemon import Pokemon
from pokemaster.weather import Weather


def test_weather_name_conversion():
    """Users can pass the weathers' English names (with spaces and
    uppercase letters) to ``Weather()`` instantiation and getting the
    correct weather."""
    assert 'clear-skies' == Weather('Clear Skies').name


def test_weather_name_validation():
    """Only battle-affecting and Generation III weathers are
    accepted."""
    with pytest.raises(ValueError):
        Weather('Mysterious air current')


def test_weather_trigger_validation():
    """Must specify how a weather is triggered."""
    with pytest.raises(ValueError):
        # Clear skies cannot be triggered (actually, the trigger is
        # 'natural'.)
        Weather('Clear skies', trigger='move')
    with pytest.raises(ValueError) as exec_info:
        Weather('Hail', trigger='ability')
    assert "hail cannot occur via ability in Gen. 3." == str(exec_info.value)


def test_weather_generation_validation():
    """Only Gen 3 ~ 5 are supported."""
    with pytest.raises(ValueError):
        assert Weather('hail', generation=6)


def test_weather_messages():
    """Message-related methods works."""
    sandstorm = Weather('Sandstorm', trigger="ability")
    tyranitar = Pokemon('tyranitar', level=100)
    assert (
        "tyranitar's Sand Stream whipped up a sandstorm!"
        == sandstorm.get_init_msg(tyranitar)
    )
    assert (
        "tyranitar is buffeted by the sandstorm!"
        == sandstorm.get_damage_msg(tyranitar)
    )
    assert "The sandstorm rages." == sandstorm.get_after_turn_msg()
    assert "The sandstorm subsided." == sandstorm.get_end_msg()


def test_weather_modifier():
    """Weather modifier caluclation is included in ``Weather`` for
    convenience."""
    rain = Weather('Rain')
    harsh_sunlight = Weather('Harsh sunlight')
    assert 1.5 == rain.modifier("water")
    assert 1.5 == harsh_sunlight.modifier("fire")
    assert 0.5 == rain.modifier("fire")
    assert 0.5 == harsh_sunlight.modifier("water")
    assert 1 == rain.modifier("steel")
