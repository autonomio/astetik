"""Bars for a declared estimate, with its interval and, when asked, the observations."""

from __future__ import annotations

import numpy as np

from ._estimate import Estimate, computation, estimate
from ._mark_backend import marks
from ._mark_colors import edge_color
from ._render_category_types import CategoryGroup
from ._render_groups import overlay


def aggregate(group: CategoryGroup) -> list[float]:
    """Draw one bar and return every value its numeric axis must include."""
    context = group.context
    options, ink = context.options, context.spec['_manifest'].colors['ink']
    if group.values is None:
        result, text = Estimate(float(len(group.rows)), None, None, len(group.rows)), 'row count'
    else:
        name = group.category if group.label is None else f'{group.category}, {group.label}'
        result, text = estimate(group.values, options, name), computation(options)
    ax, thickness = marks(context.ax), group.width * 0.88
    bar = ax.barh if group.horizontal else ax.bar
    bar(
        group.position, result.centre, thickness, color=group.color,
        alpha=options.get('alpha', 0.85), edgecolor=edge_color(context, group.color),
        linewidth=options.get('edgewidth', 0.0),
    )
    extent = [result.centre]
    if result.low is not None and result.high is not None:
        spread = np.asarray([[result.centre - result.low], [result.high - result.centre]])
        width = options.get('linewidth', 0.8)
        position, centre = np.asarray([group.position]), np.asarray([result.centre])
        if group.horizontal:
            ax.errorbar(centre, position, xerr=spread, fmt='none', ecolor=ink, elinewidth=width,
                        capsize=options.get('capsize', 2.0), capthick=width, zorder=4.0)
        else:
            ax.errorbar(position, centre, yerr=spread, fmt='none', ecolor=ink, elinewidth=width,
                        capsize=options.get('capsize', 2.0), capthick=width, zorder=4.0)
        extent = [result.low, result.high]
    if options.get('points', 'none') == 'all' and group.values is not None:
        extent += overlay(group, ink)
    context.rec.mark(
        'aggregate',
        dict(category=group.category, series=group.label, estimate=result.centre, n=result.n,
             error=result.error, lower=result.low, upper=result.high),
        group.rows,
        text,
        context.facet,
    )
    return extent
