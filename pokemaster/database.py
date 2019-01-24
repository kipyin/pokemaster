"""Query helper functions.

Make simple queries in a breeze anywhere, any time.
Note that tables should not be passed as arguments! That'll defeat
the purpose of this module.
"""
import warnings
from typing import List, Tuple

import pokedex
import pokedex.db
import pokedex.db.load
import pokedex.defaults
import sqlalchemy.orm.session
from pokedex.db import tables as tb
from sqlalchemy.exc import OperationalError


def get_session(engine_uri: str = None) -> sqlalchemy.orm.session.Session:
    """Connect to a database with the given ``engine_uri``.

    :param engine_uri: The uri of the database. The default uri set by
    :mod:`pokedex.defaults` will be used if not specified..
    :return: A ``sqlalchemy.orm.session.Session``.
    """

    engine_uri = engine_uri or pokedex.defaults.get_default_db_uri()

    try:
        session = pokedex.db.connect(engine_uri)
    except OperationalError:
        warnings.warn(f'Wrong database uri: {engine_uri}.')
        warnings.warn(
            'Connecting to the default database: '
            f'{pokedex.defaults.get_default_db_uri()}.'
        )
        session = pokedex.db.connect(pokedex.defaults.get_default_db_uri())

    if not pokedex.db.tables.Pokemon.__table__.exists(session.bind):
        # Empty database
        warnings.warn('Initializing database')
        pokedex.db.load.load(session, drop_tables=True, safe=False)
        session = pokedex.db.connect(engine_uri)

    return session


SESSION = get_session()


def bind_session(session):
    global SESSION
    SESSION = session


def get_pokemon(
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
    return SESSION.query(tb.Pokemon).filter_by(**kwargs).one()


def pokemon_species(
    national_id: int = None, identifier: str = None, name: str = None, **kwargs
) -> tb.PokemonSpecies:
    """Get a ``PokemonSpecies`` table instance."""
    if national_id is None and identifier is None and name is None:
        raise ValueError('Gimme something to search!')
    if national_id is not None and isinstance(national_id, int):
        kwargs['id'] = national_id
    if identifier is not None and isinstance(identifier, str):
        kwargs['identifier'] = identifier
    if name is not None and isinstance(name, str):
        kwargs['name'] = name
    return SESSION.query(tb.PokemonSpecies).filter_by(**kwargs).one()


def get_experience(
    species_identifier: str = None,
    growth_rate_id: int = None,
    level: int = None,
    exp: int = None,
) -> tb.Experience:
    """Look up a Pokémon's experience at various levels."""

    if growth_rate_id is not None:
        # If `growth_rate_id` is given, then ignore `species_identifier`.
        conditions = {'growth_rate_id': growth_rate_id}
    elif species_identifier is not None:
        species = get_pokemon(identifier=species_identifier)
        conditions = {'growth_rate_id': species.growth_rate_id}
    else:
        raise ValueError(
            'Must specify either the species or the growth rate ID.'
        )

    if level is None and exp is None:
        raise ValueError('Gimme something to look up!')

    if level is not None:
        conditions['level'] = level
    _query = SESSION.query(tb.Experience).filter_by(**conditions)

    if exp is not None:
        _query = (
            _query.filter(tb.Experience.experience <= exp)
            .order_by(tb.Experience.experience)
            .desc()
        )
    return _query.one()


def wild_pokemon_held_item(
    prng: "PRNG", national_id: int, compound_eyes: bool
) -> tb.Item:
    """Determine the held item of a wild Pokémon."""
    pokemon_ = get_pokemon(id=national_id)

    held_item_chance = prng() / 0xFFFF

    if compound_eyes:
        rare_item_chance = 0.2
        common_item_chance = 0.6
    else:
        rare_item_chance = 0.05
        common_item_chance = 0.5

    for item in reversed(pokemon_.items):
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
    pokemon_moves: List[tb.PokemonMove] = (
        SESSION.query(tb.PokemonMove)
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
    return SESSION.query(tb.Nature).filter_by(**conditions).one()


def ability(species: str, personality: int) -> tb.Ability:
    """Not quite a query, but definitely hides the mess.

    If a Pokémon only have one ability, then that'll be its
    ability straight away; if it has more than one ability,
    then the last bit of `personality` comes to play.
    """
    pokemon_ = get_pokemon(identifier=species)
    abilities = pokemon_.abilities
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
    return SESSION.query(tb.Gender).filter_by(identifier=gender).one()
