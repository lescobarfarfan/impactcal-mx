"""Single seeding entry point (CAL-GEN-04).

All randomness in the project routes through here. `numpy.random.default_rng`
uses PCG64, whose stream is bit-reproducible across operating systems and
architectures for a given seed. Cross-platform caveats that seeding does NOT
cover (document per run, see CAL-GEN-05):

- Multi-threaded BLAS reductions can differ in the last ulp across machines;
  pin thread counts for exact replication (e.g. OMP_NUM_THREADS=1).
- PyMC/PyTensor sampling is reproducible given `random_seed=` per sampler call
  AND identical package versions (pin via environment.lock.yml).
"""

from __future__ import annotations

import numpy as np

_GLOBAL_SEED: int | None = None


def set_seed(seed: int) -> None:
    """Fix the project-wide base seed. Call once per run; recorded in the manifest."""
    global _GLOBAL_SEED
    _GLOBAL_SEED = int(seed)


def get_seed() -> int:
    """Return the base seed, failing loudly if none was set (nothing stochastic runs unseeded)."""
    if _GLOBAL_SEED is None:
        raise RuntimeError("No seed set. Call impactcal.infra.set_seed(seed) first (CAL-GEN-04).")
    return _GLOBAL_SEED


def get_rng(stream: str = "default") -> np.random.Generator:
    """Return a named, independent, reproducible RNG stream.

    Streams derived via SeedSequence.spawn-like keying on the stream name, so
    adding a new stream never perturbs existing ones.
    """
    base = get_seed()
    key = np.frombuffer(stream.encode("utf-8"), dtype=np.uint8)
    ss = np.random.SeedSequence(entropy=base, spawn_key=tuple(int(b) for b in key))
    return np.random.default_rng(ss)
