import pytest

from pokemaster import query


def test_bind_session():
    session = query.get_session()
    assert query._SESSION is not session
    query.bind_session(session)
    assert query._SESSION is session


def test_query_pokemon_species():
    with pytest.raises(ValueError):
        query.pokemon_species()

    assert query.pokemon_species(id=10).identifier == 'caterpie'
    assert query.pokemon_species(identifier='caterpie').id == 10
    assert query.pokemon_species(id=10, identifier='caterpie').id == 10
