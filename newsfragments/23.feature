Added random functions to `pokemaster.prng.PRNG`.

More specifically,
the following methods are introduced to the `PRNG` class:

- `random()` generates a random `float` in [0, 1).
- `uniform(a, b)` generates a random `float` in [a, b).
This is equivalent to `a + (b - a) * PRNG().random()`.
