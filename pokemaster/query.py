"""Query helper functions.

Make simple queries in a breeze anywhere, any time.
Note that tables should not be passed as arguments! That'll defeat
the purpose of this module.
"""

import os
import warnings
from pathlib import Path
from typing import List, Tuple

import pokedex
import pokedex.db
import pokedex.db.load
from pokedex.db import tables as tb
from sqlalchemy.exc import OperationalError


def get_session(engine_uri: str = None):
    """Connect to a database with the given ``engine_uri``.

    :param engine_uri: The uri of the database. The default uri set by
    :mod:`pokedex.defaults` will be used if not specified..
    :param ensure: Ensure the database connection. If ``False`` is given,
    the validity of ``engine_uri`` will not be checked. Otherwise,
    the program will check 1) whether or not the uri is concrete; 2)
    whether or not the database is non-empty.

    :return: A :class:`~pokedex.db.multilang.MultilangScopedSession`.
    """

    engine_uri = engine_uri or pokedex.defaults.get_default_db_uri()

    try:
        session = pokedex.db.connect(engine_uri)
    except OperationalError:
        warnings.warn(f'Wrong database uri: {engine_uri}.')
        warnings.warn(
            f'Connecting to the default database: {pokedex.defaults.get_default_db_uri()}.'
        )
        session = pokedex.db.connect(pokedex.defaults.get_default_db_uri())

    if not pokedex.db.tables.Pokemon.__table__.exists(session.bind):
        # Empty database
        warnings.warn('Initializing database')
        pokedex.db.load.load(
            session, directory=None, drop_tables=True, safe=False
        )
        session = pokedex.db.connect(engine_uri)

    return session


_SESSION = get_session()


def bind_session(session):
    global _SESSION
    _SESSION = session


def pokemon(
    id: int = None, identifier: str = None, name: str = None, **kwargs
) -> tb.Pokemon:
    if id is None and identifier is None and name is None:
        raise ValueError('Gimme something to search!')
    if id is not None and isinstance(id, int):
        kwargs['id'] = id
    if identifier is not None and isinstance(identifier, str):
        kwargs['identifier'] = identifier
    if name is not None and isinstance(name, str):
        kwargs['name'] = name
    return _SESSION.query(tb.Pokemon).filter_by(**kwargs).one()


def pokemon_species(
    id: int = None, identifier: str = None, name: str = None, **kwargs
) -> tb.PokemonSpecies:
    """Get a ``PokemonSpecies`` table instance."""
    if id is None and identifier is None and name is None:
        raise ValueError('Gimme something to search!')
    if id is not None and isinstance(id, int):
        kwargs['id'] = id
    if identifier is not None and isinstance(identifier, str):
        kwargs['identifier'] = identifier
    if name is not None and isinstance(name, str):
        kwargs['name'] = name
    return _SESSION.query(tb.PokemonSpecies).filter_by(**kwargs).one()


def experience(
    growth_rate_id: int, level: int = None, experience: int = None
) -> tb.Experience:
    """Look up a Pokémon's experience at various levels."""
    if level is None and experience is None:
        raise ValueError('Gimme something to look up!')

    conditions = {}
    conditions['growth_rate_id'] = growth_rate_id

    if level is not None:
        conditions['level'] = level
    _query = _SESSION.query(tb.Experience).filter_by(**conditions)

    if experience is not None:
        _query = (
            _query.filter(tb.Experience.experience <= experience)
            .order_by(tb.Experience.experience)
            .desc()
        )
    return _query.one()


def wild_pokemon_held_item(
    prng: "PRNG", national_id: int, compound_eyes: bool
) -> tb.Item:
    """Determine the held item of a wild Pokémon."""
    pokemon_ = pokemon(id=national_id)

    held_item_chance = prng() / 0xFFFF

    if compound_eyes:
        rare_item_chance = 0.2
        common_item_chance = 0.6
    else:
        rare_item_chance = 0.05
        common_item_chance = 0.5

    for item in reversed(pokemon.items):
        if item.rarity == 5 and held_item_chance <= rare_item_chance:
            return item
        elif item.rarity == 50 and held_item_chance <= common_item_chance:
            return item
        elif item.rarity == 100:
            return item
    else:
        return None


def wild_pokemon_moves(pokemon: tb.Pokemon, level: int) -> Tuple[tb.Move]:
    """Determine the moves of a wild Pokémon."""
    pokemon_moves = (
        _SESSION.query(tb.PokemonMove)
        .join(tb.PokemonMoveMethod)
        .join(tb.VersionGroup)
        .filter(
            tb.PokemonMove.pokemon_id == pokemon.id,
            tb.PokemonMoveMethod.identifier == 'level-up',
            tb.PokemonMove.level <= level,
            tb.VersionGroup.identifier == 'emerald',
        )
        .order_by(tb.PokemonMove.level.desc(), tb.PokemonMove.order)
        .limit(4)
        .all()
    )
    return tuple(map(lambda x: x.move, pokemon_moves))


def nature(personality: int = None, identifier: str = None) -> tb.Nature:
    """Determine a Pokémon's nature from its personality value."""
    conditions = {}
    if personality is None and identifier is None:
        raise ValueError('Gimme something to look up!')
    if personality is not None:
        conditions['game_index'] = personality % 25
    if identifier is not None:
        conditions['identifier'] = identifier
    return _SESSION.query(tb.Nature).filter_by(**conditions).one()


def ability(abilities: List[tb.Ability], personality: int) -> tb.Ability:
    """Not quite a query, but definitely hides the mess.

    If a Pokémon only have one ability, then that'll be its
    ability straight away; if it has more than one ability,
    then the last bit of `personality` comes to play.
    """
    return abilities[min(len(abilities) - 1, personality % 2)]


def pokemon_gender(gender_rate: int, personality: int) -> tb.Gender:
    """Determine a Pokémon's gender by its gender rate and personality."""
    if gender_rate == -1:
        gender = 'genderless'
    elif gender_rate == 8:
        gender = 'female'
    elif gender_rate == 0:
        gender = 'male'
    else:
        # Gender is determined by the last byte of the PID.
        p_gender = personality % 0x100
        gender_threshold = 0xFF * gender_rate // 8
        if p_gender >= gender_threshold:
            gender = 'male'
        else:
            gender = 'female'
    return _SESSION.query(tb.Gender).filter_by(identifier=gender).one()
