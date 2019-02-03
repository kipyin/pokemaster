# `pokemaster` - Get Real, Living™ Pokémon in Python

[![codecov](https://codecov.io/gh/kipyin/pokemaster/branch/develop/graph/badge.svg)](https://codecov.io/gh/kipyin/pokemaster) [![Travis CI](https://img.shields.io/travis/com/kipyin/pokemaster/develop.svg?label=Travis%20CI)](https://travis-ci.com/kipyin/pokemaster) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

## What is this?

`pokemaster` lets you create Pokémon
that is native to the core series Pokémon games
developed by Game Freak & Nintendo.

In `pokemaster`, 
everything you get is
what you would expect in the games:
a Pokémon has a bunch of attributes,
knows up to four moves,
can be evolved to another species,
can learn, forget, and remember certain moves,
can use moves to do stuff 
(such as attacking another Pokémon),
can consume certain items,
and much, much more.

## Installation

Install with `pip`:

```shell
$ pip install pokemaster
```

## Basic Usage

To summon a Real, Living™ Pokémon:

```pydocstring
>>> from pokemaster import Pokemon
>>> bulbasaur = Pokemon(national_id=1, level=5)
>>> eevee = Pokemon('eevee', level=10, gender='female')
```

