"""Box displays with explicit quartiles and Tukey whiskers that end on observations."""

from __future__ import annotations

import numpy as np
from matplotlib.colors import to_rgba

from ._mark_backend import marks
from ._render_category_types import CategoryGroup
from ._render_groups import overlay


def quartiles(group: CategoryGroup) -> dict[str, float]:
    """Linear quartiles and the Tukey whiskers that end on observed values."""
    values, whis = group.numbers, group.context.options.get('whis', 1.5)
    q1, median, q3 = (float(v) for v in np.quantile(values, [0.25, 0.5, 0.75], method='linear'))
    inside = values[(values >= q1 - whis * (q3 - q1)) & (values <= q3 + whis * (q3 - q1))]
    return dict(q1=q1, med=median, q3=q3, whislo=float(inside.min()), whishi=float(inside.max()),
                mean=float(np.mean(values)))


def record_quartiles(group: CategoryGroup, summary: dict[str, float], shown: str) -> None:
    whis = group.context.options.get('whis', 1.5)
    group.context.rec.mark(
        'box',
        dict(category=group.category, series=group.label, q1=summary['q1'], median=summary['med'],
             q3=summary['q3'], lower_whisker=summary['whislo'], upper_whisker=summary['whishi'],
             mean=summary['mean'], n=len(group.rows)),
        group.rows,
        f'linear quantiles; Tukey whiskers={whis}*IQR; {shown}',
        group.context.facet,
    )


def box(group: CategoryGroup) -> None:
    context, values = group.context, group.numbers
    options, colors = context.options, context.spec['_manifest'].colors
    summary, every = quartiles(group), options.get('points', 'outliers') == 'all'
    beyond = (values < summary['whislo']) | (values > summary['whishi'])
    fill, width, color = options.get('fill', True), options.get('linewidth', 0.8), group.color
    stroke = dict(color=color, linewidth=width)
    marks(context.ax).bxp(
        [dict(summary, fliers=values[:0] if every else values[beyond])],
        positions=[group.position],
        widths=group.width * 0.8,
        orientation='horizontal' if group.horizontal else 'vertical',
        patch_artist=True, manage_ticks=False,
        showmeans=options.get('means', False),
        boxprops=dict(facecolor=to_rgba(color, options.get('alpha', 0.75)) if fill else 'none',
                      edgecolor=color, linewidth=width),
        medianprops=dict(color=colors['ink'] if fill else color, linewidth=width * 1.5),
        whiskerprops=stroke,
        capprops=stroke,
        flierprops=dict(marker='o', markersize=float(np.sqrt(options.get('point_size', 8.0))),
                        markerfacecolor='none', markeredgecolor=color, markeredgewidth=0.6),
        meanprops=dict(marker='D', markersize=3.5, markerfacecolor=colors['paper'],
                       markeredgecolor=colors['ink'], markeredgewidth=0.6, zorder=5.0),
    )
    record_quartiles(group, summary, 'every observation shown' if every else 'all outliers shown')
    if every:
        overlay(group, colors['ink'])
        return
    for row, value in zip(group.rows[beyond], values[beyond]):
        context.rec.mark(
            'outlier',
            dict(category=group.category, series=group.label, value=value),
            [int(row)],
            'identity; outside Tukey whiskers',
            context.facet,
        )
