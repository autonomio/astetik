"""Histogram rendering with explicit scientific provenance."""

from __future__ import annotations

import numpy as np

from ._plot_backend import drawing
from ._render_common import (
    groups,
    legend,
    numerical,
    series_colors,
    zero_baseline,
)
from ._render_context import (
    RenderContext,
    RowArray,
    measure_columns,
)
from ._render_density import calculate_density
from ._types import FloatArray, JsonScalar


def hist(context: RenderContext) -> None:
    ax = context.ax
    data = context.data
    rows = context.rows
    spec = context.spec
    options = context.options
    colors = context.colors
    rec = context.rec
    facet = context.facet
    columns = measure_columns(spec, 'x')
    hue = spec.get('hue')
    if hue and len(columns) > 1:
        raise ValueError('Multiple histogram columns and hue cannot be combined.')
    mapping = (
        spec['_hue_colors'] if hue else series_colors(spec['_manifest'], columns, spec['_paper'])
    )
    # All compared distributions share bin boundaries resolved from the full input.
    full = np.concatenate([numerical(data[c], c) for c in columns])
    bins = options.get('bins', 'auto')
    if isinstance(bins, bool):
        raise ValueError('bins must be an integer, explicit edges, or a NumPy bin rule.')
    edges = np.histogram_bin_edges(full, bins=bins)
    if len(edges) < 2 or not np.isfinite(edges).all() or not np.all(np.diff(edges) > 0):
        raise ValueError('Histogram bin edges must be finite and strictly increasing.')
    if edges[0] > full.min() or edges[-1] < full.max():
        raise ValueError(
            'Histogram bin edges must cover every observation; filtering belongs in the declared data protocol.'
        )
    horizontal = options.get('orient', 'v') == 'h'
    for column in columns:
        for label, r in groups(data, rows, hue):
            values = numerical(data.iloc[r][column], column)
            counts, _ = np.histogram(values, bins=edges, density=options.get('density', False))
            raw_counts, _ = np.histogram(values, bins=edges)
            key = label if hue else column
            if horizontal:
                drawing(ax).barh(
                    edges[:-1],
                    counts,
                    height=np.diff(edges),
                    align='edge',
                    color=mapping[key],
                    alpha=options.get('alpha', 0.85),
                    edgecolor=colors.manifest.colors['paper'],
                    linewidth=0.4,
                )
            else:
                drawing(ax).bar(
                    edges[:-1],
                    counts,
                    width=np.diff(edges),
                    align='edge',
                    color=mapping[key],
                    alpha=options.get('alpha', 0.85),
                    edgecolor=colors.manifest.colors['paper'],
                    linewidth=0.4,
                )
            for i, (low, high, value, n) in enumerate(
                zip(edges[:-1], edges[1:], counts, raw_counts)
            ):
                chosen = (values >= low) & (
                    (values <= high) if i == len(edges) - 2 else (values < high)
                )
                rec.mark(
                    'bin',
                    dict(series=key, column=column, lower=low, upper=high, value=value, n=n),
                    r if options.get('density', False) else r[chosen],
                    'numpy.histogram density=n/(N*bin_width); numerator rows identified by bin bounds'
                    if options.get('density', False)
                    else 'numpy.histogram count',
                    facet,
                )
            _overlay(context, values, r, key, mapping[key], column)
    rec.methods['histogram'] = dict(
        bins=edges.tolist(),
        density=options.get('density', False),
        shared_bins=True,
        final_bin_right_closed=True,
    )
    legend(ax, spec, mapping if hue or len(columns) > 1 else {})
    if horizontal:
        drawing(ax).set_xlabel('Density' if options.get('density', False) else 'Count')
        drawing(ax).set_ylabel(str(columns[0]))
        zero_baseline(ax, True, [])
    else:
        drawing(ax).set_xlabel(str(columns[0]))
        drawing(ax).set_ylabel('Density' if options.get('density', False) else 'Count')
        zero_baseline(ax, False, [])


def _overlay(
    context: RenderContext,
    values: FloatArray,
    rows: RowArray,
    key: JsonScalar,
    color: str,
    column: str,
) -> None:
    options, ax, rec, facet = context.options, context.ax, context.rec, context.facet
    horizontal = options.get('orient', 'v') == 'h'
    if not options.get('kde', False):
        return
    support, density, bw = calculate_density(values, {}, column)
    if not options.get('density', False):
        raise ValueError('A KDE overlay requires density=True to keep units consistent.')
    (
        drawing(ax).plot(density, support, color=color)
        if horizontal
        else drawing(ax).plot(support, density, color=color)
    )
    for xv, yv in zip(support, density):
        rec.mark(
            'density',
            dict(series=key, x=xv, density=yv, bandwidth=bw),
            rows,
            'Gaussian KDE; Scott bandwidth',
            facet,
        )
