"""
Tests for ``pokemaster.weather.Weather``.
"""
import pytest

from pokemaster.weather import Weather


def test_weather_name_conversion():
    """Users can pass the weathers' English names (with spaces and
    uppercase letters) to ``Weather()`` instantiation and getting
    the correct weather.
    """
    assert 'clear-skies' == Weather('Clear Skies').name


def test_weather_name_validation():
    """Only battle-affecting and Generation III weathers are accepted.
    """
    with pytest.raises(ValueError):
        assert Weather('Mysterious air current')
