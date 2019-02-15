from pokemaster.game_version import GameVersion, Gen, VersionGroup


def test_generation():
    assert 3 == Gen(3)
    assert 'generation-3' == Gen(3).identifier


def test_game_generation():
    assert 3 == GameVersion.EMERALD.generation


def test_game_version_group():
    assert VersionGroup.EMERALD == GameVersion.EMERALD.version_group


def test_game_version_identifier():
    assert 'omega-ruby' == GameVersion.OMEGA_RUBY.identifier


def test_game_version_id():
    assert 17 == GameVersion.BLACK.id
