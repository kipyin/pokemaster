from typing import ClassVar

import attr

from pokemaster.charset import Charset
from pokemaster.prng import PRNG


@attr.s(auto_attribs=True)
class Trainer:
    """A trainer"""

    prng: ClassVar[PRNG] = None
    name: Charset

    def __attrs_post_init__(self):
        self.id = self.prng()
        self.secret_id = self.prng()


@attr.s
class NPC(Trainer):
    """A non-player character."""
