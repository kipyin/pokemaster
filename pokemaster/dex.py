import enum
from collections import OrderedDict
from typing import ClassVar, List, Union

import attr

from pokemaster import query


def _no_init(**kwargs):
    return attr.ib(init=False, **kwargs)


@attr.s(repr=False, auto_attribs=True)
class DexEntry:
    """A Pokédex entry."""

    national_id: int



class SearchMode(enum.IntEnum):

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
    SMALLEST = enum.auto()


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
    ) -> List[DexEntry]:
        """Look up a Pokédex entry by a specific criterion."""
