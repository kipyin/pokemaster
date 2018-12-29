#!/usr/bin/env python3
from functools import partial

import attr
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from pokemaster.pokemon import Gender, Pokemon, Trainer
from pokemaster.prng import PRNG


@pytest.fixture(scope='class')
def bulbasaur():
    """Instantiate a Bulbasaur.

    According to the PID, this is a male bulbasaur with Overgrow ability,
    hardy nature, and not shiny.
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


@pytest.fixture(scope='function')
def garchomp():
    """A Level 78 Garchomp with the following IVs and EVs and an
    Adamant nature:

    +===========+=====+========+=========+========+========+========+=======+
    |           |  HP | Attack | Defense | Sp.Atk | Sp.Def |  Speed | Total |
    +===========+=====+========+=========+========+========+========+=======+
    | Base stat | 108 |   130  |    95   |   80   |   85   |   102  |  600  |
    +-----------+-----+--------+---------+--------+--------+--------+-------+
    |    IV     |  24 |    12  |    30   |   16   |   23   |     5  |  110  |
    +-----------+-----+--------+---------+--------+--------+--------+-------+
    |    EV     |  74 |   190  |    91   |   48   |   84   |    23  |  510  |
    +-----------+-----+--------+---------+--------+--------+--------+-------+
    |   Total   | 289 |   278  |   193   |  135   |  171   |   171  |       |
    +-----------+-----+--------+---------+--------+--------+--------+-------+

    https://bulbapedia.bulbagarden.net/wiki/Statistic#Example_2
    """
    Pokemon.prng = PRNG(0x1C262455)
    garchomp = Pokemon('garchomp', pid_method=4, level=78)
    garchomp.effort_values.set(
        hp=74,
        attack=190,
        defense=91,
        special_attack=48,
        special_defense=84,
        speed=23,
    )
    yield garchomp


def test_trainer_sanity():
    Trainer.prng = PRNG()
    t = Trainer('Kip')
    assert t.id == 0
    assert t.secret_id == 59774


class TestPIDRelatedMechanisms:
    def test_bulbasaur_ids(self, bulbasaur):
        assert bulbasaur.trainer.id == 0
        assert bulbasaur.trainer.secret_id == 59774
        assert bulbasaur._pid == 833639025
        assert bulbasaur._ivs == 2948981452

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


class TestPokemonStats:
    def test_ivs(self):
        """Seed and IVs can be found in:
        https://sites.google.com/site/ivtopidapplet/home
        """
        Pokemon.prng = PRNG(0x35CC77B9)
        weedle = Pokemon(13)
        assert weedle._pid == 0xEF72C69F
        assert weedle._ivs == 0xFFFFFFFF

    def test_iv(self, garchomp):
        assert garchomp.iv.astuple() == (24, 12, 30, 16, 23, 5)

    def test_base_stats_sanity(self, garchomp):
        for stat in garchomp.base_stats.astuple():
            assert stat != 0

    def test_calculate_stats(self, garchomp):
        calculated_stats = garchomp._calculate_stats()
        assert calculated_stats.hp == 289
        assert calculated_stats.attack == 278
        assert calculated_stats.defense == 193
        assert calculated_stats.special_attack == 135
        assert calculated_stats.special_defense == 171
        assert calculated_stats.speed == 171


class TestPokemonExperience:
    """Level should change when gained enough experience.

    Since the fixture only run once per test, not once per example,
    we have to do manual setups. Also, the EV doesn't matter when
    testing the exoeriences.
    """

    def test_experience(self, garchomp):
        assert garchomp.experience == 593_190

    # 616_298 - 593_190 = 23_108
    @given(st.integers(0, 23_108))
    def test_pokemon_gaining_experience_without_leveling_up(self, exp):
        garchomp = Pokemon('garchomp', level=78)
        garchomp.experience += exp
        assert garchomp.experience == 593_190 + exp
        assert garchomp.level == 78

    def test_pokemon_gaining_exact_experience_to_level_up(self, garchomp):
        garchomp.experience += 23_108
        assert garchomp.experience == 616_298
        assert garchomp.level == 79

    # 640_000 - 593_190 = 46_810
    @given(st.integers(23_108, 46_810))
    def test_pokemon_gaining_experience_to_get_one_level_up(self, exp):
        garchomp = Pokemon('garchomp', level=78)
        garchomp.experience += exp
        assert garchomp.experience == 593_190 + exp
        assert garchomp.level == 79

    # 1_250_000 - 593_190 = 656_810
    # Using @given will make hypothesis fuss about how slow the test is.
    @pytest.mark.parametrize('exp', [656_810, 656_811, 1_656_810])
    def test_pokemon_gaining_experience_to_get_to_level_100(self, exp):
        garchomp = Pokemon('garchomp', level=78)
        garchomp.experience += exp
        assert garchomp.experience == 1_250_000
        assert garchomp.level == 100


class TestPokemonMoves:
    def test_pokemon_initial_moves(self, bulbasaur):
        assert list(map(lambda x: x.id, bulbasaur.moves)) == [45, 33]

    # def test_learnable_moves(self, bulbasaur):
    #     assert bulbasaur.learnable(get_move('cut'))
    #     assert not bulbasaur.learnable(get_move('pound'))
