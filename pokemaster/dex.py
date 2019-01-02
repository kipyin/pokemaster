import enum
from collections import OrderedDict
from typing import ClassVar, List, Union

import attr


@attr.s(repr=False, auto_attribs=True)
class PokedexEntry:
    """A Pokédex entry."""

    national_id: int


class SearchMode(IntEnum):

    BY_NAME = 1
    BY_COLOR = 2
    BY_TYPE = 3


class OrderMode(enum.Enum):

    HOENN = enum.auto()
    NATIONAL = enum.auto()
    A_Z = enum.auto()
    HEAVIEST = enum.auto()
    LIGHTEST = enum.auto()
    TALLEST = enum.auto()
    SMALLEST = emum.auto()


@attr.s(repr=False, auto_attribs=True)
class Pokedex:
    """A Pokédex."""

    NATIONAL: ClassVar[bool] = False
    # SEARCH_MODE: ClassVar[SearchMode] = SearchMode.BY_NAME
    # SORT_MODE: ClassVar[OrderMode] = OrderMode.HOENN

    seen: OrderedDict = OrderedDict()
    owned: OrderedDict = OrderedDict()

    def search(
        self,
        criterion: Union[str, int],
        mode=SearchMode.BY_NAME,
        order_by=OrderMode.HOENN,
    ) -> List[PokedexEntry]:
        """Look up a Pokédex entry by a specific criterion."""
