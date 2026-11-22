"""Publication options for line, scatter, bar, box, violin, and panel figures."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Literal, TypedDict

from ._histogram_options import LEGEND_LOCATIONS
from ._types import JsonObject


class MarkOptions(TypedDict, total=False):
    markersize: float
    dashes: bool
    confidence: float
    interval: Literal['band', 'bars']
    band_alpha: float
    capsize: float
    band: bool
    fit_groups: bool
    annotate_fit: bool
    points: Literal['none', 'outliers', 'all']
    inner: Literal['box', 'quartiles', 'none']
    means: bool
    ncols: int | None
    labels: Literal['a', 'A', '(a)'] | None


_SHARED: JsonObject = dict(color=None, legend_loc='best', annotate_n=False)
LINE_DEFAULTS: JsonObject = dict(
    linewidth=1.25, alpha=1.0, marker=None, markersize=4.0, linestyle='solid', sort=True,
    drawstyle='default', dashes=False, estimator=None, errorbar=None, confidence=0.95,
    interval='band', band_alpha=0.2, capsize=2.0, **_SHARED,
)
SCATTER_DEFAULTS: JsonObject = dict(
    point_size=18.0, alpha=0.85, marker='o', hue_mode='auto', edgecolor='auto', edgewidth=0.3,
    **_SHARED,
)
FIT_DEFAULTS: JsonObject = dict(
    SCATTER_DEFAULTS, alpha=0.8, fit_reg=True, draw_scatter=True, linewidth=1.25, band=True,
    confidence=0.95, fit_groups=False, annotate_fit=False,
)
BAR_DEFAULTS: JsonObject = dict(
    estimator='sum', errorbar=None, confidence=0.95, orient='v', alpha=0.85, width=0.8,
    capsize=2.0, linewidth=0.8, points='none', point_size=8.0, jitter=0.12, edgecolor='auto',
    edgewidth=0.0, **_SHARED,
)
BOX_DEFAULTS: JsonObject = dict(
    whis=1.5, width=0.8, orient='v', alpha=0.75, fill=True, linewidth=0.8, points='outliers',
    point_size=8.0, jitter=0.12, means=False, **_SHARED,
)
VIOLIN_DEFAULTS: JsonObject = dict(
    bw_method='scott', gridsize=128, cut=0.0, split=False, width=0.8, alpha=0.75, orient='v',
    fill=True, linewidth=0.8, inner='box', points='none', point_size=8.0, jitter=0.12, **_SHARED,
)
PANELS_DEFAULTS: JsonObject = dict(ncols=None, labels='a')

_LINES = ('line', 'longitudinal')
_CHOICES: dict[str, tuple[object, ...]] = {
    'interval': ('band', 'bars'),
    'inner': ('box', 'quartiles', 'none'),
    'labels': ('a', 'A', '(a)', None),
}
_POINTS = {'box': ('outliers', 'all')}
_FLAGS = ('dashes', 'band', 'fit_groups', 'annotate_fit', 'means', 'annotate_n')
_NONNEGATIVE = ('capsize', 'markersize', 'edgewidth')


def _real(value: object) -> float:
    """A finite number, or NaN so that every range comparison fails."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return math.nan
    return float(value)


def _domains(kind: str, options: Mapping[str, object]) -> None:
    for name in _FLAGS:
        if name in options and not isinstance(options[name], bool):
            raise ValueError(f'{name} must be a boolean.')
    choices = dict(_CHOICES, points=_POINTS.get(kind, ('none', 'all')))
    choices['legend_loc'] = (*LEGEND_LOCATIONS, *(('end',) if kind in _LINES else ()))
    for name, allowed in choices.items():
        if name in options and options[name] not in allowed:
            raise ValueError(f'{name} must be one of: {", ".join(map(str, allowed))}.')
    if options.get('color') is not None and not isinstance(options['color'], str):
        raise ValueError('color must be a manifest colour role, a #RRGGBB value, or null.')
    if 'edgecolor' in options and not isinstance(options['edgecolor'], str):
        raise ValueError("edgecolor must be 'auto', a manifest colour role, or a #RRGGBB value.")


def _numbers(options: Mapping[str, object]) -> None:
    for name in _NONNEGATIVE:
        if not _real(options.get(name, 0)) >= 0:
            raise ValueError(f'{name} must be a finite nonnegative number.')
    if not 0 < _real(options.get('confidence', 0.95)) < 1:
        raise ValueError('confidence must be a number strictly between 0 and 1.')
    if not 0 <= _real(options.get('band_alpha', 0.2)) <= 1:
        raise ValueError('band_alpha must be a number between 0 and 1.')
    ncols = options.get('ncols')
    if ncols is not None and (isinstance(ncols, bool) or not isinstance(ncols, int) or ncols < 1):
        raise ValueError('ncols must be a positive integer.')


def validate_marks(kind: str, options: Mapping[str, object]) -> None:
    """Reject options whose statistical or visual reading would be ambiguous."""
    _domains(kind, options)
    _numbers(options)
    estimator, errorbar = options.get('estimator'), options.get('errorbar')
    if kind in _LINES:
        if estimator == 'sum':
            raise ValueError('A line joins observations, or a mean or median at each x.')
        if estimator is not None and not options.get('sort', True):
            raise ValueError('An estimate at each x is ordered by x; sort=False cannot apply.')
        if options.get('dashes') and options.get('linestyle', 'solid') != 'solid':
            raise ValueError('dashes assigns a line style per series; leave linestyle solid.')
    elif 'estimator' in options and estimator is None:
        raise ValueError("estimator must be 'mean', 'median', or 'sum'.")
    if errorbar in ('sd', 'se', 'ci') and estimator != 'mean':
        raise ValueError(f"errorbar={errorbar!r} describes a mean; declare estimator='mean'.")
    if errorbar == 'iqr' and estimator != 'median':
        raise ValueError("errorbar='iqr' describes a median; declare estimator='median'.")
