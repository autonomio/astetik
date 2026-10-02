"""Observed comparisons across measurements and independently labelled panels."""

from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from ._manifest import Manifest
from ._plot_backend import drawing
from ._render_common import (
    category_axes,
    color_mapping,
    equal,
    legend,
    levels,
    numerical,
    series_colors,
    zero_baseline,
)
from ._render_context import (
    Recorder,
    RenderContext,
    RendererOptions,
    RendererSpec,
    measure_columns,
    required_column,
)
from ._render_layout import figure_dimensions


def overlap(context: RenderContext) -> None:
    ax = context.ax
    data = context.data
    rows = context.rows
    spec = context.spec
    options = context.options
    rec = context.rec
    facet = context.facet
    category = spec.get('label_col') or spec.get('hue')
    if category is None:
        raise ValueError('overlap requires label_col (category labels).')
    columns = [context.column('x'), context.column('y')]
    categories = spec.get('order') or levels(data[category])
    mapping = series_colors(spec['_manifest'], columns, spec['_paper'])
    horizontal = options.get('orient', 'v') == 'h'
    baseline: list[float] = []
    for ci, cat in enumerate(categories):
        r = rows[equal(data.iloc[rows][category], cat)]
        if not len(r):
            continue
        for j, column in enumerate(columns):
            values = numerical(data.iloc[r][column], column)
            v = float(getattr(np, options.get('estimator', 'mean'))(values))
            (
                drawing(ax).barh(
                    ci,
                    v,
                    height=0.65 if j == 0 else 0.3,
                    color=mapping[column],
                    alpha=options.get('alpha', 0.85),
                )
                if horizontal
                else drawing(ax).bar(
                    ci,
                    v,
                    width=0.65 if j == 0 else 0.3,
                    color=mapping[column],
                    alpha=options.get('alpha', 0.85),
                )
            )
            baseline.append(v)
            rec.mark(
                'aggregate',
                dict(category=cat, series=column, estimate=v, n=len(r)),
                r,
                options.get('estimator', 'mean'),
                facet,
            )
    category_axes(ax, categories, horizontal)
    zero_baseline(ax, horizontal, baseline)
    legend(ax, spec, mapping)
    drawing(ax).set_xlabel('Value' if horizontal else str(category))
    drawing(ax).set_ylabel(str(category) if horizontal else 'Value')


def compare_panels(
    data: pd.DataFrame,
    spec: RendererSpec,
    manifest: Manifest,
    paper: bool,
    options: RendererOptions,
    rec: Recorder,
) -> Figure:
    category = spec.get('label_col') or spec.get('hue')
    if category is None:
        raise ValueError('compare requires label_col.')
    columns = [required_column(spec, 'x'), *measure_columns(spec, 'y')]
    columns = list(dict.fromkeys(columns))
    categories = spec.get('order') or levels(data[category])
    ncols = (
        min(len(columns), 2 if manifest.paper['preset'] == 'double' else 1)
        if paper
        else len(columns)
    )
    nrows = int(np.ceil(len(columns) / ncols))
    figure = Figure(figsize=figure_dimensions(manifest, paper, nrows, ncols), layout='constrained')
    FigureCanvasAgg(figure)
    axes = figure.subplots(nrows, ncols, squeeze=False).flat
    mapping = color_mapping(manifest, columns, paper)
    for i, ax in enumerate(axes):
        if i >= len(columns):
            ax.set_visible(False)
            continue
        column = columns[i]
        for i, label in enumerate(categories):
            rows = np.flatnonzero(equal(data[category], label))
            values = numerical(data.iloc[rows][column], column)
            drawing(ax).scatter(
                values,
                np.full(len(rows), i),
                color=mapping[column],
                s=options.get('point_size', 18.0),
                alpha=options.get('alpha', 0.85),
                edgecolors='none',
            )
            for p, v in zip(rows, values):
                rec.mark(
                    'observation',
                    dict(category=label, column=column, value=v),
                    [int(p)],
                    'identity',
                    {'column': column},
                )
        category_axes(ax, categories, True)
        ax.set_title(str(column), loc='left')
        drawing(ax).set_xlabel(str(column))
        drawing(ax).set_ylabel(str(category))
    return figure
