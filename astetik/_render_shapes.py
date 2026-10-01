"""Box and violin displays with explicit quantiles, whiskers, and density estimates."""

from __future__ import annotations

import numpy as np

from ._plot_backend import drawing
from ._render_category_types import CategoryGroup
from ._render_density import calculate_density
from ._types import FloatArray


def box(group: CategoryGroup) -> None:
    context, values = group.context, group.numbers
    options = context.options
    q1, median, q3 = np.quantile(values, [0.25, 0.5, 0.75], method='linear')
    iqr = q3 - q1
    whis = options.get('whis', 1.5)
    inside = values[(values >= q1 - whis * iqr) & (values <= q3 + whis * iqr)]
    low, high = inside.min(), inside.max()
    summary: dict[str, float | FloatArray] = dict(
        q1=float(q1),
        med=float(median),
        q3=float(q3),
        whislo=float(low),
        whishi=float(high),
        fliers=values[(values < low) | (values > high)],
    )
    drawing(context.ax).bxp(
        [summary],
        positions=[group.position],
        widths=group.width * 0.8,
        orientation='horizontal' if group.horizontal else 'vertical',
        patch_artist=True,
        manage_ticks=False,
        boxprops=dict(
            facecolor=group.color, edgecolor=group.color, alpha=options.get('alpha', 0.85)
        ),
        medianprops=dict(color=context.colors.manifest.colors['ink']),
        flierprops=dict(
            marker='o', markersize=3, markerfacecolor=group.color, markeredgecolor=group.color
        ),
    )
    context.rec.mark(
        'box',
        dict(
            category=group.category,
            series=group.label,
            q1=q1,
            median=median,
            q3=q3,
            lower_whisker=low,
            upper_whisker=high,
            n=len(group.rows),
        ),
        group.rows,
        f'linear quantiles; Tukey whiskers={whis}*IQR; all outliers shown',
        context.facet,
    )
    for p, value in zip(group.rows, values):
        if value < low or value > high:
            context.rec.mark(
                'outlier',
                dict(category=group.category, series=group.label, value=value),
                [int(p)],
                'identity; outside Tukey whiskers',
                context.facet,
            )


def violin(group: CategoryGroup) -> None:
    context, values = group.context, group.numbers
    options = context.options
    support, density, bandwidth = calculate_density(values, options, group.value_column)
    extent = density / density.max() * group.width * 0.45
    if options.get('split', False):
        if group.hue_count != 2:
            raise ValueError('split violins require exactly two hue categories.')
        position = group.category_index
        lower, upper = (
            (position - extent, np.full(len(extent), position))
            if group.hue_index == 0
            else (np.full(len(extent), position), position + extent)
        )
    else:
        lower, upper = group.position - extent, group.position + extent
    if group.horizontal:
        drawing(context.ax).fill_between(
            support,
            lower,
            upper,
            facecolor=group.color,
            edgecolor=group.color,
            alpha=options.get('alpha', 0.85),
        )
    else:
        drawing(context.ax).fill_betweenx(
            support,
            lower,
            upper,
            facecolor=group.color,
            edgecolor=group.color,
            alpha=options.get('alpha', 0.85),
        )
    for value, density_value in zip(support, density):
        context.rec.mark(
            'density',
            dict(
                category=group.category,
                series=group.label,
                value=value,
                density=density_value,
                bandwidth=bandwidth,
            ),
            group.rows,
            f'Gaussian KDE; bandwidth={options.get("bw_method", "scott")}; width normalized per group; cut={options.get("cut", 0.0)}',
            context.facet,
        )
