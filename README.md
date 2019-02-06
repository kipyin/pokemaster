# `pokemaster` - Get Real, Living™ Pokémon in Python

[![codecov](https://codecov.io/gh/kipyin/pokemaster/branch/master/graph/badge.svg)](https://codecov.io/gh/kipyin/pokemaster) [![Travis CI](https://img.shields.io/travis/com/kipyin/pokemaster/master.svg?label=Travis%20CI)](https://travis-ci.com/kipyin/pokemaster) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

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

`pokemaster` can be installed via `pip`, but you have to have `pokedex`
installed first:

```shell
$ pip install git+https://github.com/kipyin/pokedex
$ pip install pokemaster
```

## Basic Usage

To summon a Real, Living™ Pokémon:

```python
>>> from pokemaster import Pokemon
>>> bulbasaur = Pokemon(national_id=1, level=5)
>>> eevee = Pokemon('eevee', level=10, gender='female')
```

## Development

### Installing

To make contribution,
you need to clone the repo first, of course:

```shell
$ git clone https://github.com/kipyin/pokemaster.git
$ cd pokemaster
```

If you have `poetry` installed,
you can install the dependencies directly:

```shell
$ poetry install -v
$ pip install git+https://github.com/kipyin/pokedex
```

If you have `invoke` already,
you can install the dependencies with:

```shell
$ invoke install
```

This command installs `poetry` and `pokedex`, 
and then runs `poetry install` for you.

This will equip everything you need for the development.

### Linting

We use `black` to format the code,
and `isort` to sort the imports.

To format the code,
use [invoke](http://docs.pyinvoke.org/en/stable/):

```shell
$ invoke lint
```

### Testing

After making commits,
make sure all tests are passed.
To run tests, do

```shell
$ invoke test
```

If you want to see the coverage:

```shell
$ invoke test-html
```

## LICENSE

MIT License

Copyright (c) 2019 Kip Yin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
