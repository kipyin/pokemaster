"""
Tests for ``pokemaster.stats``.
"""
from pokemaster.stats import Stats


def test_stats_addition():
    assert Stats() + Stats(1, 2, 3, 4, 5, 6) == Stats(1, 2, 3, 4, 5, 6)
    assert Stats(1, 2, 3, 4, 5, 6) + 1 == Stats(2, 3, 4, 5, 6, 7)
    assert 1 + Stats(1, 2, 3, 4, 5, 6) == Stats(2, 3, 4, 5, 6, 7)


def test_stats_subtraction():
    assert Stats(7, 7, 7, 7, 7, 7) - Stats(1, 2, 3, 4, 5, 6) == Stats(
        6, 5, 4, 3, 2, 1
    )
    assert Stats(7, 7, 7, 7, 7, 7) - 7 == Stats()


def test_stats_multiplication():
    assert Stats(1, 2, 3, 4, 5, 6) * Stats(1, 2, 3, 4, 5, 6) == Stats(
        1, 4, 9, 16, 25, 36
    )
    assert Stats(1, 2, 3, 4, 5, 6) * 2 == Stats(2, 4, 6, 8, 10, 12)
    assert 2 * Stats(1, 2, 3, 4, 5, 6) == Stats(2, 4, 6, 8, 10, 12)
