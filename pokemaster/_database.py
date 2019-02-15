"""Query helpers.

Make simple queries in a breeze anywhere, any time.
Note that tables should not be passed as arguments! That'll defeat
the purpose of this module.
"""
import warnings
from typing import List, Optional, Tuple

import pokedex
import pokedex.db
import pokedex.db.load
import pokedex.defaults
import sqlalchemy.exc
import sqlalchemy.orm.session

from pokemaster.prng import PRNG


def get_session(database_uri: str = None) -> sqlalchemy.orm.session.Session:
    """Connect to a database with the given ``engine_uri``.

    :param database_uri: The uri of the database. The default uri set by
        :mod:`pokedex.defaults` will be used if not specified.
    :return: A ``sqlalchemy.orm.session.Session``.
    """

    database_uri = database_uri or pokedex.defaults.get_default_db_uri()

    try:
        session = pokedex.db.connect(database_uri)
    except sqlalchemy.exc.OperationalError:
        warnings.warn(f'Wrong database uri: {database_uri}.')
        warnings.warn(
            'Connecting to the default database: '
            f'{pokedex.defaults.get_default_db_uri()}.'
        )
        session = pokedex.db.connect(pokedex.defaults.get_default_db_uri())

    if not pokedex.db.tables.Pokemon.__table__.exists(session.bind):
        # Empty database
        warnings.warn('Initializing database')
        pokedex.db.load.load(session, drop_tables=True, safe=False)
        session = pokedex.db.connect(database_uri)

    return session


SESSION = get_session()


def set_session(session):
    """Bind a session."""
    global SESSION
    SESSION = session


def _check_completeness(
    *args, msg='Must specify at least one value.'
) -> Optional[bool]:
    """Return True if at least one argument in args is not None."""
    for arg in args:
        if arg is not None:
            return True
    else:
        raise ValueError(msg)


def get_pokemon(
    national_id: int = None, species: str = None, form: str = None
) -> pokedex.db.tables.Pokemon:
    """Make a query from ``pokedex.db.tables.Pokemon``.

    :param national_id: The National Pokédex ID.
    :param species: Pokémon's species, the standard 386, 493, etc.
    :param form: The form identifier of a Pokémon, such as 'a' for
        'unown', 'attack' for 'deoxys', etc.
    :return: a ``pokedex.db.tables.Pokemon`` row.
    """
    _check_completeness(national_id, species)
    query: sqlalchemy.orm.query.Query = (
        SESSION.query(pokedex.db.tables.Pokemon)
        .join(pokedex.db.tables.PokemonForm)
        .join(pokedex.db.tables.PokemonSpecies)
    )
    if national_id is not None:
        query = query.filter(pokedex.db.tables.PokemonSpecies.id == national_id)
    if species is not None:
        query = query.filter(
            pokedex.db.tables.PokemonSpecies.identifier == species
        )
    if form is not None:
        query = query.filter(
            pokedex.db.tables.PokemonForm.form_identifier == form
        )
    else:
        query = query.filter(pokedex.db.tables.Pokemon.is_default == 1)
    return query.one()


def _get_experience_table(
    national_id: int = None, species: str = None
) -> sqlalchemy.orm.query.Query:
    """Get an experience table specific to the species.

    :param national_id: The National Pokédex ID.
    :param species: The Pokémon's species.
    :return: sqlalchemy.orm.query.Query
    """
    # _check_completeness([national_id, species], growth_rate_id)
    if species is not None or national_id is not None:
        pokemon = get_pokemon(species=species, national_id=national_id)
        conditions = {'growth_rate_id': pokemon.species.growth_rate_id}
    else:
        raise ValueError(
            'Must specify either the species or the National Pokédex ID.'
        )
    return SESSION.query(pokedex.db.tables.Experience).filter_by(**conditions)


def get_experience(
    national_id: int = None,
    species: str = None,
    level: int = None,
    exp: int = None,
) -> pokedex.db.tables.Experience:
    """Look up a Pokémon's experience at various levels."""

    if level is None and exp is None:
        raise ValueError('Gimme something to look up!')

    query = _get_experience_table(national_id=national_id, species=species)
    if level is not None:
        query = query.filter_by(level=level)
    if exp is not None:
        query = query.filter(
            pokedex.db.tables.Experience.experience <= exp
        ).order_by(pokedex.db.tables.Experience.experience.desc())
    result = query.first()
    if result is None:
        raise ValueError(f'Inconsistent data.')
    else:
        return result


def wild_pokemon_held_item(
    prng: PRNG, national_id: int, compound_eyes: bool
) -> Optional[pokedex.db.tables.Item]:
    """Determine the held item of a wild Pokémon."""
    pokemon_ = get_pokemon(national_id=national_id)

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
    return None


def get_pokemon_default_moves(
    level: int,
    national_id: int = None,
    species: str = None,
    form: str = None,
    version_group: str = 'emerald',
) -> Tuple[pokedex.db.tables.Move]:
    """Determine the moves of a wild Pokémon."""
    pokemon = get_pokemon(national_id, species, form)
    pokemon_moves: List[pokedex.db.tables.PokemonMove] = reversed(
        SESSION.query(pokedex.db.tables.PokemonMove)
        .join(pokedex.db.tables.PokemonMoveMethod)
        .join(pokedex.db.tables.VersionGroup)
        .filter(
            pokedex.db.tables.PokemonMove.pokemon_id == pokemon.id,
            pokedex.db.tables.PokemonMoveMethod.identifier == 'level-up',
            pokedex.db.tables.PokemonMove.level <= level,
            pokedex.db.tables.VersionGroup.identifier == version_group,
        )
        .order_by(pokedex.db.tables.PokemonMove.level.desc())
        .order_by(pokedex.db.tables.PokemonMove.order)
        .limit(4)
        .all()
    )

    # Just to get the signatures.
    def _get_move(x: pokedex.db.tables.PokemonMove) -> pokedex.db.tables.Move:
        return x.move

    return tuple(map(_get_move, pokemon_moves))


def get_nature(
    personality: int = None, identifier: str = None
) -> pokedex.db.tables.Nature:
    """Determine a Pokémon's nature from its personality value."""
    conditions = {}
    if personality is None and identifier is None:
        raise ValueError('Gimme something to look up!')
    if personality is not None:
        conditions['game_index'] = personality % 25
    if identifier is not None:
        conditions['identifier'] = identifier
    return SESSION.query(pokedex.db.tables.Nature).filter_by(**conditions).one()


def get_ability(
    national_id: int = None,
    species: str = None,
    form: str = None,
    personality: int = None,
) -> pokedex.db.tables.Ability:
    """Not quite a query, but definitely hides the mess.

    If a Pokémon only have one ability, then that'll be its
    ability straight away; if it has more than one ability,
    then the last bit of `personality` comes to play.
    """
    pokemon_ = get_pokemon(species=species, national_id=national_id, form=form)
    abilities = pokemon_.abilities
    return abilities[min(len(abilities) - 1, personality % 2)]


# FIXME: change `gender_rate` to `species` (issue #6)
def get_pokemon_gender(
    national_id: int = None,
    species: str = None,
    form: str = None,
    personality: int = None,
) -> pokedex.db.tables.Gender:
    """Determine a Pokémon's gender by its gender rate and personality."""
    pokemon = get_pokemon(national_id=national_id, species=species, form=form)
    gender_rate = pokemon.species.gender_rate
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
    return (
        SESSION.query(pokedex.db.tables.Gender)
        .filter_by(identifier=gender)
        .one()
    )


def get_move(move: str = None, move_id: int = None) -> pokedex.db.tables.Move:
    """"""
    _check_completeness(move, move_id)
    conditions = {'generation': 3}
    if move is not None:
        conditions['identifier'] = move
    if move_id is not None:
        conditions['id'] = move_id
    return (SESSION.query(pokedex.db.tables.Move).filter_by(**conditions)).one()


# TODO: get it via the machine no. or the move name
def get_machine(
    machine_number: int = None, move_identifier: str = None, move_id: int = None
) -> Optional[pokedex.db.tables.Machine]:
    """
    Get a TM or HM by the machine number，or the move's identifier,
    if it is a valid machine.
    """
    _check_completeness(machine_number, move_identifier, move_id)
    query = (
        SESSION.query(pokedex.db.tables.Machine)
        .join(pokedex.db.tables.VersionGroup)
        .join(pokedex.db.tables.Move)
        .filter(pokedex.db.tables.VersionGroup.identifier == 'emerald')
    )
    if machine_number is not None:
        query = query.filter(
            pokedex.db.tables.Machine.machine_number == machine_number
        )
    if move_identifier is not None:
        query = query.filter(
            pokedex.db.tables.Move.identifier == move_identifier
        )
    if move_id is not None:
        query = query.filter(pokedex.db.tables.Move.id == move_id)
    return query.one_or_none()


def get_move_pool(
    species: str, move_method: str = None
) -> List[pokedex.db.tables.PokemonMove]:
    """Get a pool of moves that a Pokémon can learn via a specific method."""
    query = (
        SESSION.query(pokedex.db.tables.PokemonMove)
        .join(pokedex.db.tables.PokemonMoveMethod)
        .join(pokedex.db.tables.Pokemon)
        .join(pokedex.db.tables.PokemonSpecies)
        .filter(
            pokedex.db.tables.PokemonSpecies.identifier == species,
            pokedex.db.tables.VersionGroup.identifier == 'emerald',
        )
    )
    if move_method is not None:
        query = query.filter(
            pokedex.db.tables.PokemonMoveMethod.identifier == move_method
        )
    return query.all()


if __name__ == '__main__':
    p = get_machine(108)
    print(p.move.identifier)
