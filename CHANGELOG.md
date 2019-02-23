# Changelog

<!-- TOWNCRIER -->


## Pokemaster 0.2.1 (2019-02-22)


### Bugfixes


- Minor bugfix ([#19](https://github.com/kipyin/pokemaster/issues/19), [#20](https://github.com/kipyin/pokemaster/issues/20), [#21](https://github.com/kipyin/pokemaster/issues/21))


### Features


- Added random functions to `pokemaster.prng.PRNG`.

  More specifically,
  the following methods are introduced to the `PRNG` class:

  - `random()` generates a random `float` in [0, 1).
  - `uniform(a, b)` generates a random `float` in [a, b).
  This is equivalent to `a + (b - a) * PRNG().random()`. ([#23](https://github.com/kipyin/pokemaster/issues/23))


## Pokemaster 0.2.0 (2019-02-16)

### Features

- Added in-battle stats to `Pokemon`. ([#15](https://github.com/kipyin/pokemaster/issues/15))
- Added `pokemaster.Weather` class for weather-related mechanisms. ([#17](https://github.com/kipyin/pokemaster/issues/17))
- Added `pokemaster.game_version.Game` enum
  to manage game versions, version groups, and generations. ([#18](https://github.com/kipyin/pokemaster/issues/18))


## Pokemaster 0.1.4 (2019-02-12)

### Bugfixes


- Pokémon cannot forget HM moves.

  Also, Pokémon cannot forget any move
  if it knows less than 4 moves,
  even when the move is passed by the `forget` kwarg. ([#13](https://github.com/kipyin/pokemaster/issues/13))


## Pokemaster 0.1.3 (2019-02-06)

No significant changes.
