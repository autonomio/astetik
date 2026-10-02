"""Import-compatible v1 helpers with explicit scientific migration errors."""
from __future__ import annotations

from typing import NoReturn

from .._legacy import migration


def groupby_func(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.transform.groupby_func', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


def rescaler(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.transform.rescaler', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


def intervals(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.transform.intervals', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


def equal_samples(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.transform.equal_samples', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


def mean_zero(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.transform.mean_zero', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


def _groupby(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.transform._groupby', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


def _boolcols_to_cat(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.transform._boolcols_to_cat', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


__all__ = ['_boolcols_to_cat', '_groupby', 'equal_samples', 'groupby_func', 'intervals', 'mean_zero', 'rescaler']
