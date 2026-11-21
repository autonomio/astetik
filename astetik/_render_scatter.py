"""Scatter observations with an optional least-squares fit and its confidence band."""

from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.artist import Artist
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D

from ._mark_backend import PointPaint, marks
from ._mark_colors import edge_color, legend_size, series_mapping
from ._plot_backend import colorbar_figure, drawing
from ._presentation_legend import Placement, place_legend
from ._presentation_ticks import count_text
from ._render_common import figure_for, groups, levels, numerical, scalar
from ._render_context import RenderContext, RendererOptions, RendererSpec, RowArray
from ._scatter_fit import Fit, fit
from ._types import JsonScalar


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


def _paint(context: RenderContext, color: str) -> PointPaint:
    options = context.options
    return PointPaint(
        color=color, s=options.get('point_size', 18.0), alpha=options.get('alpha', 0.85),
        marker=options.get('marker', 'o'),
        edgecolors=edge_color(context, context.spec['_manifest'].colors['paper']),
        linewidths=options.get('edgewidth', 0.3),
    )


def _continuous(context: RenderContext, paint: PointPaint) -> None:
    ax, data, rows, hue = context.ax, context.data, context.rows, context.spec.get('hue')
    if hue is None:
        raise ValueError('Continuous hue requires a column.')
    values = numerical(data[hue], hue)
    low, high = float(values.min()), float(values.max())
    ink = context.spec['_manifest'].colors['ink']
    points = drawing(ax).scatter(
        data.iloc[rows][context.column('x')], data.iloc[rows][context.column('y')],
        c=values[rows], cmap=context.colors.sequential(), norm=Normalize(low, high),
        s=paint.get('s', 18.0), alpha=paint.get('alpha', 0.85), marker=paint.get('marker', 'o'),
        edgecolors=ink, linewidths=0.35,
    )
    colorbar_figure(figure_for(ax)).colorbar(points, ax=ax, label=str(hue))
    context.rec.methods['hue'] = {'kind': 'continuous', 'column': hue, 'normalization': [low, high]}


def _legend(context: RenderContext, entries: list[tuple[str, str]], notes: list[str]) -> None:
    """Keys painted exactly as their points, then any fit or sample-size note."""
    paint = _paint(context, '')
    handles: list[Artist] = [
        Line2D(
            [], [], linestyle='None', marker=paint.get('marker', 'o'),
            markersize=float(np.sqrt(paint.get('s', 18.0))), markerfacecolor=color,
            markeredgecolor=paint.get('edgecolors', 'none'),
            markeredgewidth=paint.get('linewidths', 0.0), alpha=paint.get('alpha', 1.0), label=label,
        )
        for label, color in entries
    ]
    bare, annotated = not handles, context.options.get('annotate_n', False)
    handles += [Line2D([], [], linestyle='None', label=note) for note in notes]
    if handles and context.spec.get('legend', True) and (context.lead or notes or annotated):
        loc = context.options.get('legend_loc', 'best')
        place_legend(context.ax, Placement(loc, handles, legend_size(context), bare))


Partitions = list[tuple[JsonScalar, RowArray]]


def _points(context: RenderContext) -> tuple[Partitions, dict[JsonScalar, str], bool]:
    """Draw and record the observations; return their groups and each group's colour."""
    ax, data, rows, spec = context.ax, context.data, context.rows, context.spec
    x, y, hue = context.column('x'), context.column('y'), spec.get('hue')
    continuous = numeric_hue(data, spec, context.options)
    partitions: Partitions = [(None, rows)]
    mapping: dict[JsonScalar, str] = {None: spec['_manifest'].colors['ink']}
    if continuous:
        _continuous(context, _paint(context, ''))
    else:
        partitions = groups(data, rows, hue, spec['_hue_colors'])
        colors = series_mapping(context, [y], bool(hue))
        mapping = {label: colors[label if hue else y] for label, _ in partitions}
        if context.kind != 'regs' or context.options.get('draw_scatter', True):
            for label, members in partitions:
                marks(ax).scatter(
                    data.iloc[members][x].to_numpy(), data.iloc[members][y].to_numpy(),
                    **_paint(context, mapping[label]),
                )
    for position in rows:
        values: dict[str, object] = {x: data.iloc[position][x], y: data.iloc[position][y]}
        if hue:
            values[hue] = data.iloc[position][hue]
        context.rec.mark('observation', values, [int(position)], 'identity', context.facet)
    return partitions, mapping, bool(hue) and not continuous


def _entries(
    context: RenderContext, partitions: Partitions, mapping: dict[JsonScalar, str],
    fits: dict[JsonScalar, Fit],
) -> list[tuple[str, str]]:
    """Legend text and colour per hue group, with its fit or sample size when asked."""
    options = context.options
    counted, fitted = options.get('annotate_n', False), bool(fits) and options.get('annotate_fit', False)
    if not (counted or fitted):
        # One legend serves every panel, so it keys every group of the figure.
        return [(str(label), color) for label, color in context.spec['_hue_colors'].items()]
    entries: list[tuple[str, str]] = []
    for label, members in partitions:
        note = fits[label].note(False) if fitted else f'n = {count_text(len(members))}'
        entries.append((f'{label} ({note})', mapping[label]))
    return entries


def scatter(context: RenderContext) -> None:
    spec, options, rows = context.spec, context.options, context.rows
    partitions, mapping, grouped = _points(context)
    fitted = context.kind == 'regs' and options.get('fit_reg', True)
    by_group = fitted and options.get('fit_groups', False)
    annotate, counted = options.get('annotate_fit', False), options.get('annotate_n', False)
    if by_group and not grouped:
        raise ValueError('fit_groups fits one line per categorical hue group; declare hue.')
    if annotate and not fitted:
        raise ValueError('annotate_fit reports a fitted line; enable fit_reg.')
    fits = {
        label: fit(context, members, mapping[label], label)
        for label, members in partitions
        if by_group
    }
    ink = spec['_manifest'].colors['ink']
    pooled = fit(context, rows, ink, None) if fitted and not by_group else None
    entries = _entries(context, partitions, mapping, fits) if grouped else []
    notes = [pooled.note(True)] if annotate and pooled else []
    if counted and not notes and not entries:
        notes = [f'n = {count_text(len(rows))}']
    _legend(context, entries, notes)
    drawing(context.ax).set_xlabel(context.column('x'))
    drawing(context.ax).set_ylabel(context.column('y'))
