from typing import List, Tuple

from pokedex.db import tables as tb

from pokemaster.session import get_session

DEFAULT_SESSION = get_session()


def pokemon_species(
    session, id: int = None, identifier: str = None
) -> tb.PokemonSpecies:
    """Get a ``PokemonSpecies`` table instance."""
    conditions = {}
    if species_id is None and species_identifier is None:
        raise ValueError('Gimme something to search!')
    if id is not None:
        conditions['id'] = id
    if identifier is not None:
        conditions['identifier'] = identifier
    return session.query(tb.PokemonSpecies).filter(**conditions).one()


def experience(session, level: int, growth_rate_id: int) -> int:
    """Look up a Pokémon's experience at various levels."""
    return (
        session.query(tb.Experience)
        .filter_by(growth_rate_id=growth_rate_id, level=level)
        .one()
        .experience
    )


def wild_pokemon_held_item(
    session, prng: "PRNG", pokemon: tb.Pokemon, compound_eyes: bool
) -> tb.Item:
    """Determine the held item of a wild Pokémon."""

    held_item_chance = prng() / 0xFFFF

    if compound_eyes:
        rare_item_chance = 0.2
        common_item_chance = 0.6
    else:
        rare_item_chance = 0.05
        common_item_chance = 0.5

    for item in reversed(pokemon.items):
        if item.rarity == 5 and held_item_chance <= rare_item_chance:
            return item
        elif item.rarity == 50 and held_item_chance <= common_item_chance:
            return item
        elif item.rarity == 100:
            return item
    else:
        return None


def wild_pokemon_moves(
    session, pokemon: tb.Pokemon, level: int
) -> Tuple[tb.Move]:
    """Determine the moves of a wild Pokémon."""
    pokemon_moves = (
        session.query(tb.PokemonMove)
        .join(tb.PokemonMoveMethod)
        .join(tb.VersionGroup)
        .filter(
            tb.PokemonMove.pokemon_id == pokemon.id,
            tb.PokemonMoveMethod.identifier == 'level-up',
            tb.PokemonMove.level <= level,
            tb.VersionGroup.identifier == 'emerald',
        )
        .order_by(tb.PokemonMove.level.desc(), tb.PokemonMove.order)
        .limit(4)
        .all()
    )
    return tuple(map(lambda x: x.move, pokemon_moves))


def nature(session, personality: int) -> tb.Nature:
    """Determine a Pokémon's nature from its personality value."""
    return session.query(tb.Nature).filter_by(game_index=personality % 25).one()


def ability(
    session, abilities: List[tb.Ability], personality: int
) -> tb.Ability:
    """Not quite a query, but definitely hides the mess.

    If a Pokémon only have one ability, then that'll be its
    ability straight away; if it has more than one ability,
    then the last bit of `personality` comes to play.
    """
    return abilities[min(len(abilities) - 1, personality % 2)]


def pokemon_gender(session, gender_rate: int, personality: int) -> tb.Gender:
    """Determine a Pokémon's gender by its gender rate and personality."""
    if gender_rate == -1:
        gender = 'genderless'
    elif gender_rate == 8:
        gender = 'female'
    elif gender_rate == 0:
        gender = 'male'
    else:
        # Gender is determined by the last byte of the PID.
        p_gender = personality % 0x100
        gender_threshold = 0xFF * gender_rate // 8
        if p_gender >= gender_threshold:
            gender = 'male'
        else:
            gender = 'female'
    return session.query(tb.Gender).filter_by(identifier=gender).one()
