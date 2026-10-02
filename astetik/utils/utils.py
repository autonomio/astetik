"""Import-compatible v1 helpers with explicit scientific migration errors."""
from __future__ import annotations

from typing import NoReturn

from .._legacy import migration


def _highlight_color(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.utils._highlight_color', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


def _sort_strings(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.utils._sort_strings', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


def table_prep(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.utils.table_prep', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


def _title_handling(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.utils._title_handling', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


def _scaler(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.utils._scaler', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


def _limiter(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.utils._limiter', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


def _n_decider(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.utils._n_decider', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


def _check_type(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.utils._check_type', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


def multicol_transform(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.utils.multicol_transform', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


def factorplot_sizing(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.utils.factorplot_sizing', 'Use an explicit preparation step with retained input and receipt before astetik.render.')


__all__ = ['_check_type', '_highlight_color', '_limiter', '_n_decider', '_scaler', '_sort_strings', '_title_handling', 'factorplot_sizing', 'multicol_transform', 'table_prep']
