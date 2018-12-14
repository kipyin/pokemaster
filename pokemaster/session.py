#!/usr/bin/env python3
"""
    pokemaster.session
    ~~~~~~~~~~~~~~~~~~
    Make sure the database is connected.

"""

import logging
import os
from pathlib import Path

import pokedex
import pokedex.db
import pokedex.db.load
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)


def get_session(engine_uri: str = None, ensure=True):
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

    if not ensure:
        return pokedex.db.connect(engine_uri)

    try:
        session = pokedex.db.connect(engine_uri)
    except OperationalError:
        logger.info(f'Wrong database uri: {engine_uri}.')
        logger.info(
            f'Connecting to the default database: {pokedex.defaults.get_default_db_uri()}.'
        )
        session = pokedex.db.connect(pokedex.defaults.get_default_db_uri())

    if not pokedex.db.tables.Pokemon.__table__.exists(session.bind):
        # Empty database
        logger.debug('Initializing database')
        pokedex.db.load.load(
            session, directory=None, drop_tables=True, safe=False
        )
        session = pokedex.db.connect(engine_uri)

    return session
