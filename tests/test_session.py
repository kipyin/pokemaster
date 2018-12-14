#!/usr/bin/env python3
import os
import sys

import pokedex.db.tables
import pytest

from pokemaster.session import get_session

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '../..')))


class TestInitDatabase:
    def test_initializing_database(self):
        session = get_session()
        assert pokedex.db.tables.Pokemon.__table__.exists(session.bind)
