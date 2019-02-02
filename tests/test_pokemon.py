"""
Tests for `pokemaster.Pokemon`.
"""
from pokemaster.pokemon import Pokemon


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
