Changelog
=========

.. towncrier release notes start

Pokemaster 0.2.0 (2019-02-16)
-----------------------------

Features
~~~~~~~~

- Added in-battle stats to ``Pokemon``. (`#15 <https://github.com/kipyin/pokemaster/issues/15>`_)
- Added ``pokemaster.Weather`` class for weather-related mechanisms. (`#17 <https://github.com/kipyin/pokemaster/issues/17>`_)
- Added ``pokemaster.game_version.Game`` enum
  to manage game versions, version groups, and generations. (`#18 <https://github.com/kipyin/pokemaster/issues/18>`_)


Pokemaster 0.1.4 (2019-02-12)
-----------------------------

Bugfixes
~~~~~~~~

- Pokémon cannot forget HM moves.

  Also, Pokémon cannot forget any move
  if it knows less than 4 moves,
  even when the move is passed by the ``forget`` kwarg. (`#{13} <https://github.com/kipyin/pokemaster/issues/{13}>`_)


Pokemaster 0.1.3 (2019-02-06)
-----------------------------

No significant changes.
