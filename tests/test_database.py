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
