"""Explicit categorical aggregates and deterministic individual observation displays."""

from __future__ import annotations

import numpy as np

from ._plot_backend import drawing
from ._render_category_types import CategoryGroup
from ._render_positions import SwarmLayout, swarm_offsets, van_der_corput


def aggregate(group: CategoryGroup) -> list[float]:
    context = group.context
    options, rec = context.options, context.rec
    if group.values is None:
        estimate, error = float(len(group.rows)), None
        computation = 'row count'
    else:
        estimator, err = options.get('estimator', 'mean'), options.get('errorbar')
        estimate = float(
            {'mean': np.mean, 'median': np.median, 'sum': np.sum}[estimator](group.values)
        )
        if err and len(group.values) < 2:
            raise ValueError('SD/SE error bars require at least two observations per group.')
        error = (
            float(np.std(group.values, ddof=1) / (np.sqrt(len(group.values)) if err == 'se' else 1))
            if err
            else None
        )
        computation = f'{estimator}; errorbar={err}; ddof=1'
    if group.horizontal:
        drawing(context.ax).barh(
            group.position,
            estimate,
            height=group.width * 0.88,
            xerr=error,
            color=group.color,
            alpha=options.get('alpha', 0.85),
            linewidth=0,
        )
    else:
        drawing(context.ax).bar(
            group.position,
            estimate,
            width=group.width * 0.88,
            yerr=error,
            color=group.color,
            alpha=options.get('alpha', 0.85),
            linewidth=0,
        )
    rec.mark(
        'aggregate',
        dict(
            category=group.category,
            series=group.label,
            estimate=estimate,
            n=len(group.rows),
            error=error,
        ),
        group.rows,
        computation,
        context.facet,
    )
    return [estimate] if error is None else [estimate - error, estimate + error]


def observations(group: CategoryGroup) -> None:
    context, values = group.context, group.numbers
    options = context.options
    position = group.position
    if context.kind == 'swarm':
        displacement = swarm_offsets(
            context.ax,
            values,
            SwarmLayout(
                position, group.horizontal, options.get('point_size', 18.0), group.width * 0.45
            ),
        )
    else:
        displacement = (
            np.asarray([van_der_corput(i + 1) - 0.5 for i in range(len(group.rows))])
            * 2
            * options.get('jitter', 0.0)
        )
        if context.spec.get('hue') and options.get('dodge', True):
            displacement /= group.hue_count
        elif context.spec.get('hue'):
            position = group.category_index
    positions = position + displacement
    x, y = (values, positions) if group.horizontal else (positions, values)
    drawing(context.ax).scatter(
        x,
        y,
        color=group.color,
        s=options.get('point_size', 18.0),
        alpha=options.get('alpha', 0.85),
        edgecolors='none',
    )
    for p, value, offset in zip(group.rows, values, displacement):
        context.rec.mark(
            'observation',
            dict(category=group.category, series=group.label, value=value, display_offset=offset),
            [int(p)],
            'identity; deterministic display-space swarm packing'
            if context.kind == 'swarm'
            else 'identity; deterministic van der Corput categorical jitter',
            context.facet,
        )
