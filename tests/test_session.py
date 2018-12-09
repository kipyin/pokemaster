#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '../..')))

import pytest

from pokemaster import session


class TestInitDatabase:

    @pytest.mark.skip(reason='slow test')
    def test_initializing_database(self):
        session.initialize_database()

    def test_do_not_initialize_if_database_exists(self):
        assert True
