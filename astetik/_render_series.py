"""Series rendering with explicit scientific provenance."""

from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from scipy import stats

from ._plot_backend import colorbar_figure, drawing
from ._render_common import (
    figure_for,
    groups,
    legend,
    levels,
    numerical,
    scalar,
    series_colors,
)
from ._render_context import (
    RenderContext,
    RendererOptions,
    RendererSpec,
    measure_columns,
)
from ._types import JsonObject


def numeric_hue(data: pd.DataFrame, spec: RendererSpec, options: RendererOptions) -> bool:
    hue = spec.get('hue')
    mode = options.get('hue_mode', 'auto')
    if not hue:
        if mode != 'auto':
            raise ValueError('hue_mode requires a hue column.')
        return False
    if mode == 'categorical':
        return False
    if mode == 'continuous':
        numerical(data[hue], hue)
        return True
    # Explicit manifest category identities take precedence over storage dtype.
    if all(str(scalar(v)) in spec['_manifest'].categories for v in levels(data[hue])):
        return False
    return bool(
        pd.api.types.is_numeric_dtype(data[hue]) and not pd.api.types.is_bool_dtype(data[hue])
    )


def scatter(context: RenderContext) -> None:
    ax = context.ax
    data = context.data
    rows = context.rows
    spec = context.spec
    options = context.options
    colors = context.colors
    rec = context.rec
    facet = context.facet
    kind = context.kind
    x, y, hue = context.column('x'), context.column('y'), spec.get('hue')
    numerical_hue = numeric_hue(data, spec, options)
    if numerical_hue:
        if hue is None:
            raise ValueError('Continuous hue requires a column.')
        hvalues = numerical(data[hue], hue)
        norm = Normalize(hvalues.min(), hvalues.max())
        p = drawing(ax).scatter(
            data.iloc[rows][x],
            data.iloc[rows][y],
            c=hvalues[rows],
            cmap=colors.sequential(),
            norm=norm,
            s=options.get('point_size', 18.0),
            alpha=options.get('alpha', 0.85),
            marker=options.get('marker', 'o'),
            edgecolors=colors.manifest.colors['ink'],
            linewidths=0.35,
        )
        colorbar_figure(figure_for(ax)).colorbar(p, ax=ax, label=str(hue))
        partitions, mapping = [(None, rows)], {}
        rec.methods['hue'] = {
            'kind': 'continuous',
            'column': hue,
            'normalization': [float(hvalues.min()), float(hvalues.max())],
        }
    else:
        mapping = spec['_hue_colors']
        partitions = groups(data, rows, hue)
        for label, r in partitions:
            drawing(ax).scatter(
                data.iloc[r][x],
                data.iloc[r][y],
                color=mapping.get(label, colors.primary),
                s=options.get('point_size', 18.0),
                alpha=options.get('alpha', 0.85),
                marker=options.get('marker', 'o'),
                edgecolors='none',
                label=str(label) if label is not None else None,
            )
    for label, r in partitions:
        for position in r:
            values: dict[str, object] = {
                str(x): data.iloc[position][x],
                str(y): data.iloc[position][y],
            }
            if hue:
                values[str(hue)] = data.iloc[position][hue]
            rec.mark('observation', values, [int(position)], 'identity', facet)
    if kind == 'regs' and options.get('fit_reg', True):
        _regression(context)
    legend(ax, spec, mapping)
    drawing(ax).set_xlabel(str(x))
    drawing(ax).set_ylabel(str(y))


def line(context: RenderContext) -> None:
    ax = context.ax
    data = context.data
    rows = context.rows
    spec = context.spec
    options = context.options
    rec = context.rec
    facet = context.facet
    x, ys, hue = context.column('x'), spec.get('y'), spec.get('hue')
    ys = measure_columns(spec, 'y')
    mapping = spec['_hue_colors'] if hue else series_colors(spec['_manifest'], ys, spec['_paper'])
    if hue and len(ys) > 1:
        raise ValueError('Multiple y columns and hue cannot be combined in one line plot.')
    for y in ys:
        for label, r in groups(data, rows, hue):
            if options.get('sort', True):
                r = r[np.argsort(data.iloc[r][x].to_numpy(), kind='stable')]
            key = label if hue else y
            drawing(ax).plot(
                data.iloc[r][x],
                data.iloc[r][y],
                color=mapping[key],
                linewidth=options.get('linewidth', 1.25),
                alpha=options.get('alpha', 0.85),
                marker=options.get('marker', 'o'),
                linestyle=options.get('linestyle', 'solid'),
                drawstyle=options.get('drawstyle', 'default'),
                label=str(key),
            )
            for p in r:
                values: dict[str, object] = {
                    str(x): data.iloc[p][x],
                    str(y): data.iloc[p][y],
                    'series': key,
                }
                rec.mark(
                    'observation',
                    values,
                    [int(p)],
                    'identity; line connects observations in stable x order'
                    if options.get('sort', True)
                    else 'identity; input row order',
                    facet,
                )
    legend(ax, spec, mapping if hue or len(ys) > 1 else {})
    drawing(ax).set_xlabel(str(x))
    drawing(ax).set_ylabel(str(ys[0]) if len(ys) == 1 else 'Value')


def _regression(context: RenderContext) -> None:
    ax, data, rows, options, colors, rec, facet = (
        context.ax,
        context.data,
        context.rows,
        context.options,
        context.colors,
        context.rec,
        context.facet,
    )
    x, y = context.column('x'), context.column('y')
    xv, yv = numerical(data.iloc[rows][x], x), numerical(data.iloc[rows][y], y)
    if len(rows) < 3 or np.ptp(xv) == 0:
        raise ValueError('Linear regression requires at least three observations and varying x.')
    model = stats.linregress(xv, yv)
    support = np.linspace(float(xv.min()), float(xv.max()), 128)
    prediction = model.intercept + model.slope * support
    drawing(ax).plot(
        support, prediction, color=colors.primary, linewidth=options.get('linewidth', 1.25)
    )
    method: JsonObject = dict(
        method='ordinary least squares',
        slope=float(model.slope),
        intercept=float(model.intercept),
        r=float(model.rvalue),
        pvalue=float(model.pvalue),
        stderr=float(model.stderr),
        n=len(rows),
    )
    if facet:
        rec.append_method(
            'regression_by_facet', dict(facet={k: scalar(v) for k, v in facet.items()}, **method)
        )
    else:
        rec.methods['regression'] = method
    for xv, yv in zip(support, prediction):
        rec.mark('regression', dict(x=xv, predicted_y=yv), rows, 'ordinary least squares', facet)
