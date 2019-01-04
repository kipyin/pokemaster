#!/usr/bin/env python3
from pathlib import Path

import pokedex.db.tables
import pokedex.defaults
import pytest

from pokemaster.query import get_session


def test_connect_to_default_db_if_uri_is_gibberish():
    session = get_session('sqlite:///dev/null')
    assert pokedex.db.tables.Pokemon.__table__.exists(session.bind)


def test_connect_to_default_db_if_no_uri_is_given():
    session = get_session()
    assert pokedex.db.tables.Pokemon.__table__.exists(session.bind)


def test_set_up_db_if_db_is_empty():
    db_path = Path(
        pokedex.defaults.get_default_db_uri().replace('sqlite:///', '')
    )
    # Remove the existing db uri in the default path
    if db_path.exists():
        db_path.unlink()
    # Create a fake db
    db_path.touch()
    # Should populate the db.
    session = get_session()
    assert pokedex.db.tables.Pokemon.__table__.exists(session.bind)
