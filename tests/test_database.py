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
    """Sanity test for getting the correct machine in Emerald."""
    focus_punch = database.get_machine(1)
    assert 264 == focus_punch.move_id
    dive = database.get_machine(108)
    assert 291 == dive.move_id
    assert dive.is_hm is True


def test_get_move_pool():
    assert database.get_move_pool(species='eevee', move_method='level-up')
    assert 0 != len(database.get_move_pool(species='eevee'))


def test_get_pokemon_by_national_id():
    """Given the national ID, a single Pokémon should be returned."""
    bulbasaur = database.get_pokemon(national_id=1)
    assert 'bulbasaur' == bulbasaur.identifier


def test_get_pokemon_with_different_forms_by_national_id_():
    """Deoxys has 3 forms. `get_pokemon` should only return the default
    form, if no form is specified.
    """
    deoxys_normal = database.get_pokemon(national_id=386)
    assert 'deoxys-normal' == deoxys_normal.identifier


def test_get_pokemon_by_species():
    """Get a Pokémon by its species."""
    bulbasaur = database.get_pokemon(species='bulbasaur')
    assert 'bulbasaur' == bulbasaur.identifier


def test_get_pokemon_by_national_id_and_form():
    """Get a Pokémon by its National Pokédex ID and the form."""
    unown_x = database.get_pokemon(national_id=201, form='x')
    assert 'unown' == unown_x.identifier


def test_get_pokemon_by_species_and_form():
    """Get a Pokémon by its species and its form."""
    castform_rainy = database.get_pokemon(species='castform', form='rainy')
    assert 'castform-rainy' == castform_rainy.identifier


def test_get_exp_by_level():
    """"""
