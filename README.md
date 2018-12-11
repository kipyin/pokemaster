# Pokemaster - Pokémon games on your command line

[![codecov](https://codecov.io/gh/kipyin/pokemaster/branch/develop/graph/badge.svg)](https://codecov.io/gh/kipyin/pokemaster) [![Build Status](https://travis-ci.com/kipyin/pokemaster.svg?branch=develop)](https://travis-ci.com/kipyin/pokemaster) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

## Installation

1. This project uses [`poetry`](https://poetry.eustace.io) to manage dependencies. Install it via
```bash
$ curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
```
2. The database comes from [eevee](https://eev.ee)'s [pokedex](https://github.com/veekun/pokedex). You can either:
    - [Directly download the repo](https://github.com/veekun/pokedex/wiki/Getting-Data#1-get-the-code) (note: Python 3 is **OK**) and populate the database once you've successfully installed it using `$ pokedex setup`, or
    - Let `poetry` to handle it for you. If you do so, it will use [my fork](https://github.com/kipyin/pokedex) of eevee's `pokedex`.

