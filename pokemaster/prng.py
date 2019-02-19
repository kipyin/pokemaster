"""
Provides the pseudo-random number generator used in various places.
"""
from numbers import Real
from typing import List, Tuple, Union

import attr


@attr.s(slots=True, auto_attribs=True, cmp=False)
class PRNG:
    """A linear congruential random number generator.

    Usage::

        >>> prng = PRNG()
        >>> prng()
        0
        >>> prng()
        59774
        >>> prng.reset(seed=0x1A56B091)
        >>> prng()
        475
        >>> prng = PRNG(seed=0x1A56B091)
        >>> prng()
        475

    References:
        https://bulbapedia.bulbagarden.net/wiki/Pseudorandom_number_generation_in_Pokémon
        https://www.smogon.com/ingame/rng/pid_iv_creation#pokemon_random_number_generator
    """

    _seed: int = attr.ib(validator=attr.validators.instance_of(int), default=0)
    _gen: int = attr.ib(validator=attr.validators.in_(range(1, 8)), default=3)
    _source_seed: int = attr.ib(init=False)

    def __attrs_post_init__(self):
        self._source_seed = self._seed

    def _generator(self):
        if self._gen == 3:
            while True:
                self._seed = (0x41C64E6D * self._seed + 0x6073) & 0xFFFFFFFF
                yield self._seed >> 16
        else:
            return ValueError(f"Gen. {self._gen} PRNG is not supported yet.")

    def __call__(self) -> int:
        try:
            return next(self._generator())
        except StopIteration:
            self.reset()
            return next(self._generator())

    def reset(self, seed=None):
        """Reset the generator with a seed, if given."""
        self._seed = seed or 0

    def next(self, n=1) -> Union[int, List[int]]:
        """Generate the next n random numbers."""
        if n == 1:
            return self()
        else:
            return [self() for _ in range(n)]

    def create_genome(self, method=2) -> Tuple[int, int]:
        """
        Generate the PID and IVs using the internal generator. Return
        a tuple of two integers, in the order of 'PID' and 'IVs'.

        The generated 32-bit IVs is different from how it is actually
        stored.

        Checkout [this link](https://www.smogon.com/ingame/rng/pid_iv_creation#rng_pokemon_generation)
        for more information on Method 1, 2, and 4.
        """
        return self.create_personality(), self.create_gene(method)

    def create_personality(self) -> int:
        """Create the Personality ID (PID) for a Pokémon.

        :return: int
        """
        pid_src_1, pid_src_2 = self.next(2)
        return pid_src_1 + (pid_src_2 << 16)

    def create_gene(self, method: int = 2) -> int:
        """Create the number used to generate a Pokémon's IVs.

        :param method: the Pokémon generation method. Valid values
            are 1, 2, and 4.
        :return: int
        """
        if method not in (1, 2, 4):
            raise ValueError(
                'Only methods 1, 2, 4 are supported. For more information on '
                'the meaning of the methods, see '
                'https://www.smogon.com/ingame/rng/pid_iv_creation#rng_pokemon_generation'
                ' for help.'
            )
        elif method == 1:
            iv_src_1, iv_src_2 = self.next(2)
        elif method == 2:
            _, iv_src_1, iv_src_2 = self.next(3)
        else:  # method == 4:
            iv_src_1, _, iv_src_2 = self.next(3)

        return iv_src_1 + (iv_src_2 << 16)

    def random(
        self, min: Union[int, float] = None, max: Union[int, float] = None
    ) -> float:
        """Return a random number between *min* and *max*.

        Usage::

            PRNG.random() -> a random number between [0, 1)
            PRNG.random(n) -> a random number between [0, n)
            PRNG.random(m, n) -> a random number between [m, n)

        """
        if min is not None and not isinstance(min, Real):
            raise TypeError(f"'min' must be an int or a float.")
        if max is not None and not isinstance(max, Real):
            raise TypeError(f"'max' must be an int or a float.")

        if min is None and max is None:
            # PRNG.random() -> [0, 1)
            return self.next() / 0x10000
        elif (min is not None and max is None) or (
            min is None and max is not None
        ):
            # PRNG.random(n) -> [0, n)
            cap = min or max
            return self.next() / 0x10000 * cap
        else:
            # PRNG.random(m, n) -> [m, n)
            if max <= min:
                raise ValueError("'max' must be strictly greater than 'min'.")
            return self.next() / 0x10000 * (max - min) + min
