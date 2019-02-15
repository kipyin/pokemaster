"""
Game version API.
"""

import enum
from collections import namedtuple

VersionTuple = namedtuple(
    'VersionTuple', ('generation', 'version_group', 'version')
)


class Gen(enum.IntEnum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7

    @property
    def name(self):
        return f"generation-{self.value}"


class VersionGroup(enum.IntEnum):
    RED_BLUE = 1
    YELLOW = 2
    GOLD_SILVER = 3
    CRYSTAL = 4
    RUBY_SAPPHIRE = 5
    EMERALD = 6
    FIRE_RED_LEAF_GREEN = 7
    DIAMOND_PEARL = 8
    PLATINUM = 9
    HEART_GOLD_SOUL_SILVER = 10
    BLACK_WHITE = 11
    BLACK_2_WHITE_2 = 14
    X_Y = 15
    OMEGA_RUBY_ALPHA_SAPPHIRE = 16
    SUN_MOON = 17
    ULTRA_SUN_ULTRA_MOON = 18

    @property
    def name(self):
        return self._name_.replace("_", "-").lower()

    @property
    def id(self):
        return self.value


class Game(enum.Enum):
    RED = VersionTuple(1, 1, 1)
    BLUE = VersionTuple(1, 1, 2)
    YELLOW = VersionTuple(1, 2, 3)
    GOLD = VersionTuple(2, 3, 4)
    SILVER = VersionTuple(2, 3, 5)
    CRYSTAL = VersionTuple(2, 4, 6)
    RUBY = VersionTuple(3, 5, 7)
    SAPPHIRE = VersionTuple(3, 5, 8)
    EMERALD = VersionTuple(3, 6, 9)
    FIRE_RED = VersionTuple(3, 7, 10)
    LEAF_GREEN = VersionTuple(3, 7, 11)
    DIAMOND = VersionTuple(4, 8, 12)
    PEARL = VersionTuple(4, 8, 13)
    PLATINUM = VersionTuple(4, 9, 14)
    HEART_GOLD = VersionTuple(4, 10, 15)
    SOUL_SILVER = VersionTuple(4, 10, 16)
    BLACK = VersionTuple(5, 11, 17)
    WHITE = VersionTuple(5, 11, 18)
    BLACK_2 = VersionTuple(5, 14, 21)
    WHITE_2 = VersionTuple(5, 14, 22)
    X = VersionTuple(6, 15, 23)
    Y = VersionTuple(6, 15, 24)
    OMEGA_RUBY = VersionTuple(6, 16, 25)
    ALPHA_SAPPHIRE = VersionTuple(6, 16, 26)
    SUN = VersionTuple(7, 17, 27)
    MOON = VersionTuple(7, 17, 28)
    ULTRA_SUN = VersionTuple(7, 18, 29)
    ULTRA_MOON = VersionTuple(7, 18, 30)

    def __init__(self, generation, version_group, version):
        self.generation = Gen(generation)
        self.version_group = VersionGroup(version_group)
        self.version = version

    @property
    def name(self):
        return self._name_.replace("_", "-").lower()
