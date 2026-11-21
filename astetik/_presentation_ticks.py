"""Tick positions and plain-text tick labels the declared font can typeset."""

from __future__ import annotations

import math

from matplotlib.axis import Axis
from matplotlib.ticker import LogFormatterSciNotation, MaxNLocator, ScalarFormatter

from ._histogram_options import statistic
from ._spec_types import PlotSpec

_SUPERSCRIPT = str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹')


def value_locator(integer: bool = False) -> MaxNLocator:
    """At most five intervals on 1-2-2.5-5 steps, the sequence readers expect."""
    return MaxNLocator(nbins=5, steps=[1, 2, 2.5, 5, 10], integer=integer)


def counted(spec: PlotSpec, dimension: str, horizontal: bool) -> bool:
    """Whether this axis shows whole-number counts."""
    kind = spec['kind']
    counts = kind in {'count', 'multicount'} or (
        kind == 'hist'
        and statistic(spec['options']) == 'count'
        and not spec['options'].get('common_norm', False)
    )
    return counts and dimension == ('x' if horizontal else 'y')


def count_text(count: int) -> str:
    """A sample size as tick labels print numbers: thousands set apart from five digits."""
    return f'{count:,}'.replace(',', '\N{NO-BREAK SPACE}') if count >= 10000 else str(count)


def _plain(x: float, low: float, high: float) -> str:
    exponent = math.floor(math.log10(x) + 1e-9)
    coefficient = round(x / 10**exponent, 6)
    if low >= 1:
        power = '10' + str(exponent).translate(_SUPERSCRIPT)
        return power if coefficient == 1 else f'{coefficient:g}\N{MULTIPLICATION SIGN}{power}'
    # The bundled font has no superscript minus, so sub-unit decades stay decimal.
    if low >= 1e-4 and high <= 1e5:
        return f'{x:.10g}'
    return f'{coefficient:g}e{exponent}'.replace('-', '\N{MINUS SIGN}')


class _PlainLog(LogFormatterSciNotation):
    """Label the ticks Matplotlib would label, in text that needs no math layout."""

    def __call__(self, x: float, pos: int | None = None) -> str:
        if not super().__call__(x, pos):
            return ''
        if x == 0:
            return '0'
        view = self.axis.get_view_interval() if self.axis else (1.0, 1.0)
        bounds = [abs(v) for v in view if v]
        label = _plain(abs(x), min(bounds, default=1.0), max(bounds, default=1.0))
        return f'\N{MINUS SIGN}{label}' if x < 0 else label


class _PlainScalar(ScalarFormatter):
    """Whole decimal labels: no detached multiplier, thousands set apart by a space."""

    def __call__(self, x: float, pos: int | None = None) -> str:
        text = super().__call__(x, pos)
        digits = len(text.lstrip('\N{MINUS SIGN}-').split('.')[0])
        if digits < 5 or not text.strip('\N{MINUS SIGN}-.0123456789') == '':
            return text
        whole, _, fraction = text.partition('.')
        sign = whole[: len(whole) - digits]
        grouped = f'{int(whole[len(sign):]):,}'.replace(',', '\N{NO-BREAK SPACE}')
        return sign + grouped + (f'.{fraction}' if fraction else '')


def plain_ticks(axis: Axis) -> None:
    """Label a linear axis with complete numbers the reader need not rescale."""
    formatter = _PlainScalar(useOffset=False, useMathText=False)
    formatter.set_scientific(False)
    axis.set_major_formatter(formatter)


def log_ticks(axis: Axis) -> None:
    """Replace math-markup labels on a log or symlog axis with plain text."""
    linthresh = getattr(axis.get_transform(), 'linthresh', None)
    axis.set_major_formatter(_PlainLog(linthresh=linthresh))
    if linthresh is None:
        axis.set_minor_formatter(_PlainLog(linthresh=linthresh))
