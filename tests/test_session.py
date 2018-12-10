#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '../..')))

import pytest

from pokemaster.session import get_session
import pokedex.db.tables


class TestInitDatabase:
    def test_initializing_database(self):
        session = get_session()
        assert pokedex.db.tables.Pokemon.__table__.exists(session.bind)
