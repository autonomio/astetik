"""A least-squares line through scattered observations, with its confidence band."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from matplotlib.patheffects import AbstractPathEffect, withStroke
from scipy import stats

from ._mark_backend import marks
from ._presentation_ticks import count_text
from ._render_common import numerical, scalar
from ._render_context import RenderContext, RowArray
from ._types import FloatArray, JsonObject, JsonScalar

_SUPPORT = 128


@dataclass(frozen=True)
class Fit:
    """A fitted line in the displayed scale, with the summary a reader quotes."""

    r: float
    pvalue: float
    count: int

    def note(self, full: bool) -> str:
        text = f'r = {self.r:.2f}'.replace('-', '\N{MINUS SIGN}')
        if full:
            text += ', p < 0.001' if self.pvalue < 0.001 else f', p = {self.pvalue:.3f}'
        return f'{text}, n = {count_text(self.count)}'


def _record_fit(context: RenderContext, record: JsonObject, label: JsonScalar) -> None:
    """File one fit under the figure, its facet, or its hue group."""
    if label is not None:
        record['group'] = scalar(label)
    if context.facet:
        record['facet'] = {k: scalar(v) for k, v in context.facet.items()}
    if label is None and not context.facet:
        context.rec.methods['regression'] = record
    else:
        key = 'regression_by_facet' if label is None else 'regression_by_group'
        context.rec.append_method(key, record)


def fit(context: RenderContext, rows: RowArray, color: str, label: JsonScalar) -> Fit:
    """Fit a straight line in the displayed scale; the band bounds the mean response."""
    ax, data, spec, options = context.ax, context.data, context.spec, context.options
    x, y = context.column('x'), context.column('y')
    log = {d: spec.get('axes', {}).get(d, {}).get('scale') == 'log' for d in ('x', 'y')}

    def scaled(values: FloatArray, dimension: str) -> FloatArray:
        return np.log10(values) if log[dimension] else values

    def shown(values: FloatArray, dimension: str) -> FloatArray:
        return 10**values if log[dimension] else values

    tx = scaled(numerical(data.iloc[rows][x], x), 'x')
    ty = scaled(numerical(data.iloc[rows][y], y), 'y')
    count = len(rows)
    if count < 3 or np.ptp(tx) == 0:
        raise ValueError('Linear regression requires at least three observations and varying x.')
    model = stats.linregress(tx, ty)
    slope, intercept = float(model.slope), float(model.intercept)
    support = np.linspace(float(tx.min()), float(tx.max()), _SUPPORT)
    predicted = intercept + slope * support
    confidence, band = options.get('confidence', 0.95), options.get('band', True)
    residual = float(np.sqrt(np.sum((ty - intercept - slope * tx) ** 2) / (count - 2)))
    spread = np.sqrt(1 / count + (support - tx.mean()) ** 2 / np.sum((tx - tx.mean()) ** 2))
    half = float(stats.t.ppf((1 + confidence) / 2, count - 2)) * residual * spread
    px, py = shown(support, 'x'), shown(predicted, 'y')
    lower, upper = shown(predicted - half, 'y'), shown(predicted + half, 'y')
    if band:
        marks(ax).fill_between(px, lower, upper, facecolor=color, alpha=0.15, linewidth=0.0)
    width = options.get('linewidth', 1.25)
    # One pooled line is haloed to read across the points; group lines would scar them.
    paper = spec['_manifest'].colors['paper']
    halo: list[AbstractPathEffect] = []
    if label is None:
        halo.append(withStroke(linewidth=width + 1.5, foreground=paper))
    marks(ax).plot(px, py, color=color, linewidth=width, path_effects=halo)
    _record_fit(
        context,
        dict(
            method='ordinary least squares', slope=slope, intercept=intercept,
            r=float(model.rvalue), pvalue=float(model.pvalue), stderr=float(model.stderr),
            n=count, scale={d: 'log10' if log[d] else 'linear' for d in ('x', 'y')},
            band=f'{confidence:g} confidence band for the mean response' if band else None,
        ),
        label,
    )
    series: dict[str, object] = {} if label is None else {'series': label}
    for position, value, low, high in zip(px, py, lower, upper):
        interval: dict[str, object] = dict(lower=low, upper=high) if band else {}
        context.rec.mark(
            'regression', dict(x=position, predicted_y=value, **interval, **series), rows,
            'ordinary least squares', context.facet,
        )
    return Fit(float(model.rvalue), float(model.pvalue), count)
