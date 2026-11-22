"""Violin displays: a Gaussian density per group, with its quartiles marked inside."""

from __future__ import annotations

import numpy as np
from matplotlib.colors import to_rgba

from ._mark_backend import Values, marks
from ._render_category_types import CategoryGroup
from ._render_density import calculate_density
from ._render_groups import overlay
from ._render_shapes import quartiles, record_quartiles
from ._types import FloatArray


def _inner(group: CategoryGroup, centre: float, reach: FloatArray, support: FloatArray) -> None:
    """Mark the quartiles inside a violin, as a slim box or as lines across its width."""
    context, summary = group.context, quartiles(group)
    options, colors = context.options, context.spec['_manifest'].colors
    ax, flat = marks(context.ax), group.horizontal

    def segment(position: Values, value: Values, width: float, style: str = 'solid') -> None:
        x, y = (value, position) if flat else (position, value)
        ax.plot(x, y, color=colors['ink'], linewidth=width, linestyle=style, zorder=4.0)

    if options.get('inner', 'box') == 'box':
        middle = np.asarray([centre, centre])
        segment(middle, np.asarray([summary['whislo'], summary['whishi']]), 0.8)
        segment(middle, np.asarray([summary['q1'], summary['q3']]), 3.0)
        x, y = (summary['med'], centre) if flat else (centre, summary['med'])
        ax.scatter(np.asarray([x]), np.asarray([y]), color=colors['paper'], s=5.0,
                   edgecolors=colors['ink'], linewidths=0.4, zorder=5.0)
    else:
        split = options.get('split', False)
        sign = ((-1.0, 0.0), (0.0, 1.0))[group.hue_index] if split else (-1.0, 1.0)
        for name, style in (('q1', 'dashed'), ('med', 'solid'), ('q3', 'dashed')):
            half = float(np.interp(summary[name], support, reach))
            span = np.asarray([centre + sign[0] * half, centre + sign[1] * half])
            segment(span, np.asarray([summary[name], summary[name]]), 0.8, style)
    record_quartiles(group, summary, f'quartiles marked inside the violin as {options.get("inner", "box")}')


def violin(group: CategoryGroup) -> None:
    context, values = group.context, group.numbers
    options, color = context.options, group.color
    axis = 'x' if group.horizontal else 'y'
    log = context.spec.get('axes', {}).get(axis, {}).get('scale') == 'log'
    # On a logarithmic axis the density is estimated in the scale the reader sees.
    support, density, bandwidth = calculate_density(
        np.log10(values) if log else values, options, group.value_column
    )
    support = 10**support if log else support
    extent = density / density.max() * group.width * 0.45
    centre, split = group.position, options.get('split', False)
    lower, upper = centre - extent, centre + extent
    if split:
        if group.hue_count != 2:
            raise ValueError('split violins require exactly two hue categories.')
        centre = float(group.category_index)
        middle = np.full(len(extent), centre)
        lower, upper = (centre - extent, middle) if group.hue_index == 0 else (middle, centre + extent)
    fill = marks(context.ax).fill_between if group.horizontal else marks(context.ax).fill_betweenx
    fill(
        support, lower, upper,
        facecolor=to_rgba(color, options.get('alpha', 0.75)) if options.get('fill', True) else 'none',
        edgecolor=color, linewidth=options.get('linewidth', 0.8),
    )
    for value, density_value in zip(support, density):
        context.rec.mark(
            'density',
            dict(category=group.category, series=group.label, value=value, density=density_value,
                 bandwidth=bandwidth),
            group.rows,
            f'Gaussian KDE{" of log10 values" if log else ""}; bandwidth={options.get("bw_method", "scott")}; width normalized per group; cut={options.get("cut", 0.0)}',
            context.facet,
        )
    if options.get('inner', 'none') != 'none':
        boxed = split and options.get('inner') == 'box'
        offset = group.width * 0.07 * (-1 if group.hue_index == 0 else 1) if boxed else 0.0
        _inner(group, centre + offset, extent, support)
    if options.get('points', 'none') == 'all':
        overlay(group, context.spec['_manifest'].colors['ink'])
