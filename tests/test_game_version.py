from pokemaster.game_version import Game, Gen, VersionGroup


def test_generation():
    assert 3 == Gen(3)
    assert 'generation-3' == Gen(3).name


def test_game_generation():
    assert 3 == Game.EMERALD.generation


def test_game_version_group():
    assert 'black-white' == Game.BLACK.version_group.name


def test_game_name():
    assert 'omega-ruby' == Game.OMEGA_RUBY.name


def test_game_version():
    assert 17 == Game.BLACK.version
