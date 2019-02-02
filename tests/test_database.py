"""
Tests for `pokemaster.database`.
"""

from pokemaster import database


def test_bind_session():
    session = database.get_session()
    assert database.SESSION is not session
    database.set_session(session)
    assert database.SESSION is session


def test_get_machine():
    """
    """
    focus_punch = database.get_machine(1)
    assert 264 == focus_punch.move_id
    dive = database.get_machine(108)
    assert 291 == dive.move_id
    assert dive.is_hm is True


def test_get_move_pool():
    """
    """
    assert database.get_move_pool(species='eevee', move_method='level-up')
    assert 0 != len(database.get_move_pool(species='eevee'))


def test_get_pokemon_by_national_id():
    """
    A Pokémon's National Pokédex ID alone is enough to determine the
    exact Pokémon we want to get.
    """
    bulbasaur = database.get_pokemon(national_id=1)
    assert 'bulbasaur' == bulbasaur.identifier


def test_get_pokemon_by_species():
    """
    A Pokémon's species (kind) alone is enough to determine the exact
    Pokémon we want to get.
    """
    bulbasaur = database.get_pokemon(species='bulbasaur')
    assert 'bulbasaur' == bulbasaur.identifier


def test_get_default_pokemon_form():
    """
    The default form of a Pokémon is returned if the Pokémon has
    multiple forms.
    """
    deoxys_normal = database.get_pokemon(national_id=386)
    assert 'deoxys-normal' == deoxys_normal.identifier


def test_get_specific_pokemon_form():
    """
    A Pokémon's species and a form name is sufficient to get the exact
    Pokémon form for those who have multiple forms.
    """
    castform_rainy = database.get_pokemon(species='castform', form='rainy')
    assert 'castform-rainy' == castform_rainy.identifier
