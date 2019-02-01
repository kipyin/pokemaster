from pokemaster import database


def test_bind_session():
    session = database.get_session()
    assert database.SESSION is not session
    database.set_session(session)
    assert database.SESSION is session


def test_get_machine():
    """Sanity test for getting the correct machine in Emerald."""
    focus_punch = database.get_machine(1)
    assert focus_punch.move_id == 264
    dive = database.get_machine(108)
    assert dive.move_id == 291
    assert dive.is_hm is True


def test_get_move_pool():
    assert database.get_move_pool(species='eevee', move_method='level-up')
    assert len(database.get_move_pool(species='eevee')) != 0


def test_get_pokemon_by_national_id():
    """Given the national ID, a single Pokémon should be returned."""
    bulbasaur = database.get_pokemon(national_id=1)
    assert bulbasaur.identifier == 'bulbasaur'


def test_get_pokemon_with_different_forms_by_national_id_():
    """Deoxys has 3 forms. `get_pokemon` should only return the default
    form.
    """
    deoxys_normal = database.get_pokemon(national_id=386)
    assert deoxys_normal.identifier == 'deoxys-normal'


def test_get_pokemon_by_species():
    """Get a Pokémon by its species."""
    bulbasaur = database.get_pokemon(species='bulbasaur')
    assert bulbasaur.identifier == 'bulbasaur'


def test_get_pokemon_by_national_id_and_form():
    """Get a Pokémon by its National Pokédex ID and the form."""
    unown_x = database.get_pokemon(national_id=201, form='x')
    assert unown_x.identifier == 'unown'


def test_get_pokemon_by_species_and_form():
    """Get a Pokémon by its species and its form."""
    castform_rainy = database.get_pokemon(species='castform', form='rainy')
    assert castform_rainy.identifier == 'castform-rainy'
