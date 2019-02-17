"""
Tests for `pokemaster.Pokemon`.
"""
import pytest

from pokemaster.pokemon import Pokemon


@pytest.fixture
def bulbasaur():
    """
    A level 5 bulbasaur
    """
    yield Pokemon('bulbasaur', level=5)


def test_instantiate_pokemon_with_specified_ability():
    """
    Since a Pokémon's ability is controlled by the PRNG, and coming up
    with a valid PRNG to get the desired ability is just backwards.
    Therefore, one can just pass the desired ability when instantiating
    a Pokémon. The same reasoning applies to ``Pokemon.gender`` and
    ``Pokemon.nature``.
    """
    nidorina = Pokemon('nidorina', ability='rivalry', level=10)
    assert 'rivalry' == nidorina.ability


def test_instantiate_pokemon_with_specified_nature():
    """
    A Pokémon's nature can be specified upon instantiation.
    """
    nidorina = Pokemon('nidorina', nature='gentle', level=10)
    assert 'gentle' == nidorina.nature


# XXX: Should we allow *any* gender value? e.g. a male Nidorina?
def test_instantiate_pokemon_with_specified_gender():
    """A Pokémon's gender can be specified upon instantiation."""
    nidorina = Pokemon('nidorina', gender='male', level=10)
    assert 'male' == nidorina.gender


def test_instantiate_pokemon_with_exp():
    """
    A ``Pokemon`` instance can be created by specifying the desired
    exp. points it has, and its level will be inferred automatically.
    """
    eevee = Pokemon(species='eevee', exp=2000)
    assert 12 == eevee.level
    assert 2000 == eevee.exp


def test_gain_exp():
    """
    ``Pokemon.gain_exp()`` adds the earned exp. points to the Pokémon's
    current exp. points.
    """
    eevee = Pokemon(species='eevee', exp=2000)
    eevee.gain_exp(1)
    assert 2001 == eevee.exp


def test_exp_to_next_level():
    """
    ``Pokemon.exp_to_next_level`` calculates the amount of exp. points
    required to get to the next level dynamically, i.e. it is
    calculated every time it is called.
    """
    eevee = Pokemon(species='eevee', exp=2000)
    assert 197 == eevee.exp_to_next_level
    eevee.gain_exp(1)
    assert 196 == eevee.exp_to_next_level


def test_exp_to_next_level_is_0_for_max_level():
    """
    ``Pokemon.exp_to_next_level`` is 0 if the Pokémon reaches level 100.
    """
    eevee = Pokemon(species='eevee', level=100)
    assert 0 == eevee.exp_to_next_level


def test_level_100_pokemon_cannot_gain_exp_points():
    """
    Level 100 ``Pokemon`` cannot gain any more exp. points.
    """
    eevee = Pokemon(species='eevee', level=100)
    eevee.gain_exp(1)
    assert 100 == eevee.level
    assert 1000000 == eevee.exp


def test_pokemon_level_up():
    """
    If a Pokémon gains the exact exp. points to the next level,
    it should level up.
    """
    bulbasaur = Pokemon(species='bulbasaur', level=5)
    bulbasaur.gain_exp(earned_exp=bulbasaur.exp_to_next_level)
    assert 6 == bulbasaur.level


def test_pokemon_evolution_by_level_up():
    """
    A Pokémon have the ability to evolve when it attains to
    a certain level.
    """
    bulbasaur = Pokemon(national_id=1, level=15)
    bulbasaur.gain_exp(earned_exp=bulbasaur.exp_to_next_level)
    assert 'ivysaur' == bulbasaur.species
    assert 2 == bulbasaur.national_id


def test_pokemon_default_moves():
    """
    A ``Pokemon`` will always know the last 4 moves it learned by
    level-up.
    """
    eevee = Pokemon(species='eevee', level=42)
    assert ['quick-attack', 'bite', 'baton-pass', 'take-down'] == list(
        eevee.moves
    )


def test_pokemon_use_machine_to_learn_moves():
    """
    A ``Pokemon`` can learn new moves by using TMs/HMs.
    """
    eevee = Pokemon(species='eevee', level=42)
    eevee.use_machine(6)  # toxic
    assert ['bite', 'baton-pass', 'take-down', 'toxic'] == list(eevee.moves)


def test_pokemon_not_forgetting_hm_moves():
    """
    Moves learned by using a hidden machine cannot be forgotten.
    """
    mew = Pokemon('mew', level=10)
    for hm in range(101, 105):
        mew.use_machine(hm)
    with pytest.raises(ValueError):
        assert mew.use_machine(105)


def test_pokemon_not_forgetting_move_when_known_less_than_4_moves():
    """
    If a Pokémon knows less than four moves, there is no way for this
    Pokémon to forget any existing moves in the games, even when the
    move to forget is specified.
    """
    mew = Pokemon('mew', level=10)
    mew.use_machine(1, forget='pound')
    assert ['pound', 'transform', 'focus-punch'] == list(mew.moves)


def test_pokemon_battle_stats():
    """
    When entering and exiting a battle, a Pokémon's in-battle stats
    reset to the default values.
    """
    mew = Pokemon('mew', level=10)
    assert 1.0 == mew._battle_stats.evasion
    mew._battle_stats.evasion = 0
    assert 0 == mew._battle_stats.evasion
    mew._reset_battle_stats()
    assert 1.0 == mew._battle_stats.evasion
