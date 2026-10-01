"""Correlation rendering with explicit scientific provenance."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._plot_backend import colorbar_figure, disable_grid, drawing
from ._render_common import figure_for, numerical
from ._render_context import RenderContext


def corr(context: RenderContext) -> None:
    ax = context.ax
    data = context.data
    rows = context.rows
    options = context.options
    colors = context.colors
    rec = context.rec
    facet = context.facet
    columns = _columns(context)
    if len(columns) < 2:
        raise ValueError('Correlation requires at least two numerical columns.')
    for c in columns:
        values = numerical(data.iloc[rows][c], c)
        if np.ptp(values) == 0:
            raise ValueError(f'Correlation is undefined for constant column {c!r}.')
    if options.get('method', 'spearman') not in ('pearson', 'spearman', 'kendall'):
        raise ValueError('Correlation method must be pearson, spearman, or kendall.')
    matrix = data.iloc[rows][columns].corr(method=options.get('method', 'spearman')).to_numpy()
    masked = (
        np.ma.masked_where(np.triu(np.ones_like(matrix, dtype=bool), k=1), matrix)
        if options.get('mask', False)
        else matrix
    )
    p = drawing(ax).imshow(
        masked, cmap=colors.diverging(), vmin=-1, vmax=1, aspect='equal', interpolation='nearest'
    )
    colorbar_figure(figure_for(ax)).colorbar(
        p,
        ax=ax,
        label=f'{options.get("method", "spearman").capitalize()} correlation',
        ticks=[-1, -0.5, 0, 0.5, 1],
    )
    drawing(ax).set_xticks(
        np.arange(len(columns)), [str(c) for c in columns], rotation=45, ha='right'
    )
    drawing(ax).set_yticks(np.arange(len(columns)), [str(c) for c in columns])
    disable_grid(ax)
    for i, cy in enumerate(columns):
        for j, cx in enumerate(columns):
            if options.get('mask', False) and j > i:
                continue
            value = matrix[i, j]
            rec.mark(
                'correlation',
                dict(x=cx, y=cy, correlation=value, n=len(rows)),
                rows,
                f'{options.get("method", "spearman")} correlation; complete input rows',
                facet,
            )
            if options.get('annot', False):
                text = drawing(ax).text(
                    j,
                    i,
                    f'{value:.2f}',
                    ha='center',
                    va='center',
                    color=colors.manifest.colors['paper']
                    if abs(value) > 0.65
                    else colors.manifest.colors['ink'],
                )
                setattr(text, '_astetik_text_role', 'paper' if abs(value) > 0.65 else 'ink')
    rec.methods['correlation'] = dict(
        method=options.get('method', 'spearman'),
        domain=[-1, 1],
        missing='already validated',
        mask=options.get('mask', False),
    )


def _columns(context: RenderContext) -> list[str]:
    spec, data = context.spec, context.data
    columns = spec.get('columns') or spec.get('x')
    if columns is None:
        excluded = {spec.get(k) for k in ('hue', 'row', 'col')} | set(spec.get('key', []))
        columns = [
            c for c in data.columns if pd.api.types.is_numeric_dtype(data[c]) and c not in excluded
        ]
    elif not isinstance(columns, list):
        columns = [columns]
    return columns
