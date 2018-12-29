from typing import Tuple, List


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

    def __init__(self, seed=0):
        # In Emerald, the initial seed is always 0.
        if not isinstance(seed, int):
            raise TypeError(f'The seed must be an integer.')
        self._seed = seed

    # XXX: __iter__?
    def _generator(self):
        while True:
            self._seed = (0x41C64E6D * self._seed + 0x6073) & 0xFFFFFFFF
            yield self._seed >> 16

    def __call__(self) -> int:
        # FIXME: will eventually return StopIteration!
        return next(self._generator())

    def reset(self, seed=None):
        """Reset the generator with seed, if given."""
        self._seed = seed or 0

    def next(self, n=1) -> List[int]:
        """Generate the next n random numbers."""
        return [self() for _ in range(n)]

    # FIXME: Can we have a better name, plz?
    # XXX: ivs -> genome?
    def create_pid_ivs(self, method=2) -> Tuple[int, int]:
        """Generate the PID and IV's using the internal generator. Return
        a tuple of two integers, in the order of 'PID' and 'IVs'.

        XXX: The two calls are consecutive?

        The generated 32-bit IVs is different from how it is actually
        stored.

        Checkout [this link](https://www.smogon.com/ingame/rng/pid_iv_creation#rng_pokemon_generation)
         for more information on Method 1, 2, and 4.
        """
        if method not in (1, 2, 4):
            raise ValueError(
                'Only methods 1, 2, 4 are supported. For more information on '
                'the meaning of the methods, see '
                'https://www.smogon.com/ingame/rng/pid_iv_creation#rng_pokemon_generation'
                ' for help.'
            )
        elif method == 1:
            pid_src_1, pid_src_2, iv_src_1, iv_src_2 = self.next(4)
        elif method == 2:
            pid_src_1, pid_src_2, _, iv_src_1, iv_src_2 = self.next(5)
        else:  # method == 4:
            pid_src_1, pid_src_2, iv_src_1, _, iv_src_2 = self.next(5)

        pid_src = pid_src_1 + (pid_src_2 << 16)
        iv_src = iv_src_1 + (iv_src_2 << 16)

        return (pid_src, iv_src)
