"""Histogram series: bin provenance marks and statistical overlays."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ._histogram_draw import Canvas
from ._histogram_options import statistic
from ._render_context import RenderContext, RowArray
from ._render_density import calculate_density
from ._types import FloatArray, JsonScalar

_COMPUTATION = {
    'count': 'numpy.histogram count',
    'density': 'numpy.histogram density=n/(N*bin_width); numerator rows identified by bin bounds',
    'proportion': 'numpy.histogram proportion=n/N',
    'percent': 'numpy.histogram percent=100*n/N',
}


@dataclass(frozen=True)
class Series:
    """One compared distribution with its resolved bins and colour."""

    key: JsonScalar
    column: str
    rows: RowArray
    values: FloatArray
    color: str
    counts: NDArray[np.intp]
    heights: FloatArray
    bottom: FloatArray
    share: float


def record(context: RenderContext, item: Series, edges: FloatArray) -> None:
    options, values = context.options, item.values
    stat, cumulative = statistic(options), options.get('cumulative', False)
    computation = ('cumulative ' if cumulative else '') + _COMPUTATION[stat]
    if options.get('common_norm', False) and stat != 'count':
        computation += '; N pooled across series'
    whole = np.cumsum(item.counts) if cumulative else item.counts
    shown = whole if stat == 'count' else item.heights
    for i, (low, high, value, n) in enumerate(zip(edges[:-1], edges[1:], shown, item.counts)):
        below = (values <= high) if i == len(edges) - 2 else (values < high)
        chosen = below if cumulative else below & (values >= low)
        context.rec.mark(
            'bin',
            dict(series=item.key, column=item.column, lower=low, upper=high, value=value, n=n),
            item.rows[chosen] if stat == 'count' else item.rows,
            computation,
            context.facet,
        )


def overlays(context: RenderContext, canvas: Canvas, item: Series, top: float) -> None:
    options, rec, facet = context.options, context.rec, context.facet
    identity = dict(series=item.key, column=item.column)
    accent = item.color if context.spec.get('hue') else context.spec['_manifest'].colors['ink']
    if options.get('rug', False):
        canvas.rug(item.values, accent)
        rec.mark('rug', dict(identity, n=len(item.values)), item.rows, 'identity', facet)
    for name in options.get('reference', []):
        value = float(np.mean(item.values) if name == 'mean' else np.median(item.values))
        canvas.reference(name, value, top, accent)
        rec.mark(
            'reference', dict(identity, statistic=name, value=value), item.rows, f'numpy.{name}', facet
        )
    if not options.get('kde', False):
        return
    method = options.get('bw_method', 'scott')
    support, density, bw = calculate_density(item.values, {'bw_method': method}, item.column)
    density = density * item.share
    canvas.curve(support, density, item.color)
    label = 'Scott' if method == 'scott' else str(method)
    for xv, yv in zip(support, density):
        rec.mark(
            'density',
            dict(series=item.key, x=xv, density=yv, bandwidth=bw),
            item.rows,
            f'Gaussian KDE; {label} bandwidth',
            facet,
        )
