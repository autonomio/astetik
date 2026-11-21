"""Explicit categorical aggregates and deterministic individual observation displays."""

from __future__ import annotations

import numpy as np

from ._mark_backend import marks
from ._plot_backend import drawing
from ._render_category_types import CategoryGroup
from ._render_positions import SwarmLayout, swarm_offsets, van_der_corput


def overlay(group: CategoryGroup, color: str) -> list[float]:
    """Show every observation over its summary mark, spread by a deterministic jitter."""
    context, values = group.context, group.numbers
    options = context.options
    reach = options.get('jitter', 0.12) * group.width * 2
    offsets = np.asarray([van_der_corput(i + 1) - 0.5 for i in range(len(values))]) * reach
    positions = group.position + offsets
    x, y = (values, positions) if group.horizontal else (positions, values)
    marks(context.ax).scatter(
        x, y, color=color, s=options.get('point_size', 8.0), alpha=0.6,
        edgecolors=context.spec['_manifest'].colors['paper'], linewidths=0.3, zorder=3.0,
    )
    for row, value, offset in zip(group.rows, values, offsets):
        context.rec.mark(
            'observation',
            dict(category=group.category, series=group.label, value=value, display_offset=offset),
            [int(row)],
            'identity; deterministic van der Corput categorical jitter',
            context.facet,
        )
    return [float(values.min()), float(values.max())]


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
