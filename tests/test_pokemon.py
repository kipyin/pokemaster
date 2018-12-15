#!/usr/bin/env python3
import os
import sys

import pytest
from construct import Int32ul
from hypothesis import given
from hypothesis import strategies as st

from pokemaster.pokemon import PRNG, Gender, Pokemon, Trainer, get_move


class TestPRNG:
    """Given a seed, the PRNG should have the exact same behavior.

    The seed and the results are from the following link:
    https://www.smogon.com/ingame/rng/pid_iv_creation#pokemon_random_number_generator
    """

    def test_prng_sanity(self):
        prng = PRNG()
        assert prng() == 0
        prng = PRNG(0x1A56B091)
        assert prng() == 0x01DB

    def test_format_output(self):
        prng = PRNG(0x1A56B091)
        assert prng(format=hex) == '0x1db'
        assert prng(format=bin) == '0b111101100000110'
        assert prng(format=oct) == '0o51063'
        assert prng(format=str) == '58480'
        assert prng(format=int) == 23748
        with pytest.raises(ValueError):
            assert prng(format=bytes)

    def test_next_5(self):
        prng = PRNG(0x1A56B091)
        assert prng.next(5) == [0x01DB, 0x7B06, 0x5233, 0xE470, 0x5CC4]

    def test_next_5_formatted(self):
        prng = PRNG(0x1A56B091)
        assert prng.next(5, format=hex) == [
            '0x1db',
            '0x7b06',
            '0x5233',
            '0xe470',
            '0x5cc4',
        ]

    def test_reset_prng(self):
        prng = PRNG()
        assert prng() == 0
        prng.next(10)
        prng.reset()
        assert prng() == 0

    def test_get_pid_ivs(self):
        prng = PRNG(0x560B9CE3)
        assert (0x7E482751, 0x5EE9629C) == prng.get_pid_ivs(method=2)


def test_gender_sanity():
    assert Gender.FEMALE == 1
    assert Gender.MALE == 2
    assert Gender.GENDERLESS == 3


class TestTrainer:
    @given(name=st.text())
    def test_trainer_sanity(self, name):
        Trainer.prng = PRNG()
        some_guy = Trainer(name)
        assert some_guy.id == 0
        assert some_guy.secret_id == 59774


@pytest.fixture(scope='class')
def bulbasaur():
    """Instantiate a Bulbasaur.

    According to the PID, this is a male bulbasaur with Overgrow ability,
    hardy nature, shiny?
    """
    prng = PRNG()
    Pokemon.prng = prng
    Trainer.prng = prng
    kip = Trainer('Kip')
    # kip.id = 0
    # kip.secret_id = 59774
    bulbasaur = Pokemon(1)
    # bulbasaur.pid = 833639025
    # bulbasaur.ivs = 2948981452
    bulbasaur.trainer = kip
    yield bulbasaur


class TestPokemonPID:
    """PID related mechanisms."""

    def test_bulbasaur_ids(self, bulbasaur):
        assert bulbasaur.trainer.id == 0
        assert bulbasaur.trainer.secret_id == 59774
        assert bulbasaur._pid == 833_639_025
        assert bulbasaur._ivs == 2_948_981_452

    def test_pokemon_gender(self, bulbasaur):
        assert bulbasaur.gender == Gender.MALE  # male
        nidoran_f = Pokemon('nidoran-f')
        nidoran_f.trainer = bulbasaur.trainer
        assert nidoran_f.gender == Gender.FEMALE
        nidoran_m = Pokemon('nidoran-m')
        nidoran_m.trainer = bulbasaur.trainer
        assert nidoran_m.gender == Gender.MALE
        magnemite = Pokemon('magnemite')
        magnemite.trainer = bulbasaur.trainer
        assert magnemite.gender == Gender.GENDERLESS

    def test_pokemon_ablity(self, bulbasaur):
        assert bulbasaur.ability.identifier == 'overgrow'

    def test_pokemon_nature(self, bulbasaur):
        assert bulbasaur.nature.identifier == 'hardy'

    def test_pokemon_shininess(self, bulbasaur):
        """See https://bulbapedia.bulbagarden.net/wiki/Personality_value#Example"""
        assert not bulbasaur.shiny


class TestPokemonMoves:
    def test_get_move(self):
        assert get_move(1).identifier == 'pound'
        assert get_move('pound').id == 1
        with pytest.raises(TypeError):
            get_move(b'pound')
        with pytest.raises(ValueError):
            get_move('some-gibberish-move')

    def test_pokemon_initial_moves(self, bulbasaur):
        assert list(map(lambda x: x.id, bulbasaur.moves)) == [45, 33]

    def test_learnable_moves(self, bulbasaur):
        assert bulbasaur.learnable(get_move('cut'))
        assert not bulbasaur.learnable(get_move('pound'))
