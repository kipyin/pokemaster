"""Search things from veekun's pokedex.

Usage:
    pokemaster search <category> [query]

Example:
    pkm search pokemon mew
"""

import click

import pokemaster._database as db


@click.command()
@click.argument("category", type=click.Choice["pokemon", "move"])
@click.argument("value")
def search(category: str, value: str):
    """Search something from veekun's pokedex."""
    if category == "pokemon":
        db.get_pokemon()
