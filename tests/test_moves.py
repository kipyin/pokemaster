"""Make sure moves.py works."""

from pokemaster.moves import Move


def test_build_move_from_veekun():
    """Move data can be queried from veekun's pokedex."""
    laser_focus = Move.from_veekun(name='laser-focus', generation=7)
    assert laser_focus.id == 673
    assert laser_focus.identifier == "laser-focus"
    assert laser_focus.generation == 7
    assert laser_focus.type == "normal"
    assert laser_focus.power is None
    assert laser_focus.pp == laser_focus.max_pp == 30
    assert laser_focus.accuracy is None
    assert laser_focus.priority == 0
    assert laser_focus.target == "user"
    assert laser_focus.damage_class == "status"
    assert laser_focus.effect_id == 391
    assert laser_focus.effect_chance is None
    assert laser_focus.category == "unique"
    assert laser_focus.ailemnt is None
