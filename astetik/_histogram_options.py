"""Histogram option domain: statistic, binning, and mark presentation."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Literal, TypedDict, cast

from ._types import JsonObject

Stat = Literal['count', 'density', 'proportion', 'percent']
LEGEND_LOCATIONS = (
    'best',
    'upper right',
    'upper left',
    'upper center',
    'center right',
    'center left',
    'lower right',
    'lower left',
    'lower center',
    'outside right',
    'outside top',
)


class HistogramOptions(TypedDict, total=False):
    bins: (
        int
        | Literal['auto', 'fd', 'doane', 'scott', 'stone', 'rice', 'sturges', 'sqrt']
        | list[float]
    )
    binwidth: float | None
    stat: Stat
    density: bool
    common_norm: bool
    kde: bool
    element: Literal['bars', 'step']
    multiple: Literal['layer', 'stack', 'dodge']
    shrink: float
    color: str | None
    edgecolor: str
    edgewidth: float
    rug: bool
    reference: list[Literal['mean', 'median']]
    annotate_n: bool
    legend_loc: str


HIST_DEFAULTS: JsonObject = dict(
    bins='auto',
    binwidth=None,
    stat='count',
    density=False,
    cumulative=False,
    common_norm=False,
    element='bars',
    fill=True,
    multiple='layer',
    shrink=1.0,
    alpha=0.85,
    color=None,
    edgecolor='auto',
    edgewidth=0.4,
    orient='v',
    kde=False,
    bw_method='scott',
    linewidth=1.25,
    rug=False,
    reference=[],
    annotate_n=False,
    legend_loc='best',
)
_CHOICES: dict[str, tuple[str, ...]] = {
    'stat': ('count', 'density', 'proportion', 'percent'),
    'element': ('bars', 'step'),
    'multiple': ('layer', 'stack', 'dodge'),
    'legend_loc': LEGEND_LOCATIONS,
}
_LABELS: dict[Stat, str] = {'count': 'Count', 'proportion': 'Proportion', 'percent': 'Percent'}


def statistic(options: Mapping[str, object]) -> Stat:
    """Resolve the one declared bin statistic; density=True is its legacy spelling."""
    stat = options.get('stat', 'count')
    if options.get('density', False):
        if stat not in ('count', 'density'):
            raise ValueError(f'density=True conflicts with stat={stat!r}; declare one statistic.')
        return 'density'
    return cast(Stat, stat)


def stat_label(options: Mapping[str, object], density: str) -> str:
    name = _LABELS.get(statistic(options), density)
    return f'Cumulative {name.lower()}' if options.get('cumulative', False) else name


def _number(value: object, low: float, *, inclusive: bool) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return False
    return value >= low if inclusive else value > low


def _choices(options: Mapping[str, object]) -> None:
    for name, allowed in _CHOICES.items():
        if options[name] not in allowed:
            raise ValueError(f'{name} must be one of: {", ".join(allowed)}.')
    for name in ('common_norm', 'rug', 'annotate_n'):
        if not isinstance(options[name], bool):
            raise ValueError(f'{name} must be a boolean.')
    if options['color'] is not None and not isinstance(options['color'], str):
        raise ValueError('color must be a manifest colour role, a #RRGGBB value, or null.')
    if not isinstance(options['edgecolor'], str):
        raise ValueError("edgecolor must be 'auto', a manifest colour role, or a #RRGGBB value.")
    reference = cast(list[object], options['reference'])
    if not isinstance(options['reference'], list) or sorted(map(str, reference)) not in (
        [],
        ['mean'],
        ['median'],
        ['mean', 'median'],
    ):
        raise ValueError('reference must list distinct statistics: mean, median.')


def _numbers(options: Mapping[str, object]) -> None:
    if options['binwidth'] is not None and not _number(options['binwidth'], 0, inclusive=False):
        raise ValueError('binwidth must be a finite positive number.')
    if not _number(options['shrink'], 0, inclusive=False) or cast(float, options['shrink']) > 1:
        raise ValueError('shrink must be greater than 0 and at most 1.')
    if not _number(options['edgewidth'], 0, inclusive=True):
        raise ValueError('edgewidth must be a finite nonnegative number.')


def validate_histogram(options: Mapping[str, object]) -> None:
    """Reject option combinations whose scientific reading would be ambiguous."""
    _choices(options)
    _numbers(options)
    stat = statistic(options)
    step = options['element'] == 'step'
    if not options['fill'] and not options['edgewidth']:
        raise ValueError('An unfilled histogram needs edgewidth greater than 0.')
    if options['binwidth'] is not None and options['bins'] != 'auto':
        raise ValueError('Declare bins or binwidth, not both.')
    if options['kde'] and stat != 'density':
        raise ValueError('A KDE overlay requires density=True to keep units consistent.')
    if options['cumulative'] and stat == 'density':
        raise ValueError('cumulative applies to count, proportion, or percent, not density.')
    if step and (options['multiple'] == 'dodge' or options['shrink'] != 1):
        raise ValueError('dodge and shrink apply to bars; step outlines span whole bins.')
    if options['multiple'] == 'stack' and options['kde']:
        raise ValueError('A KDE overlay cannot be read against stacked bins.')
    if options['multiple'] == 'stack' and stat != 'count' and not options['common_norm']:
        raise ValueError(f'Stacked {stat} requires common_norm=True so the stack totals one sample.')
