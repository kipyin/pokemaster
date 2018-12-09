#!/usr/bin/env python3
"""
    pokemaster.session
    ~~~~~~~~~~~~~~~~~~
    Make sure the database is connected.

"""

import os

from pathlib import Path

from pokedex.db import connect
from pokedex.db.load import load
from pokedex import defaults


def initialize_database(engine_uri: str=None, directory: str=None):

    engine_uri = engine_uri or defaults.get_default_db_uri()
    directory = directory or defaults.get_default_csv_dir()

    session = connect(engine_uri)

    # if not session.info:
    #     print('Initializing database')
    #     os.system('pokedex setup -q')  # TODO: replace this with subprocess
    #     session = connect(engine_uri)

    return session
