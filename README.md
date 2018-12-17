# Pokemaster - Pokémon games on your command line

[![codecov](https://codecov.io/gh/kipyin/pokemaster/branch/develop/graph/badge.svg)](https://codecov.io/gh/kipyin/pokemaster) [![Travis CI](https://img.shields.io/travis/com/kipyin/pokemaster/develop.svg?label=Travis%20CI)](https://travis-ci.com/kipyin/pokemaster) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

## Motivation

I got bored.

## Installation

1. This project uses [`poetry`](https://poetry.eustace.io) to manage dependencies. Install it via
```shell
$ curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
```
2. Clone this repo:
```shell
$ git clone https://github.com/kipyin/pokemaster.git
```
3. Install dependencies using `poetry` (it will spqwn an virtualenv for you):
```shell
$ poetry install -v
```

## Testing

To run test, use
```shell
$ make test
```
or
```shell
$ poetry run pytest tests/
```
