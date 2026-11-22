"""Legend keys and sample-size notes for categorical displays."""

from __future__ import annotations

import numpy as np
from matplotlib.artist import Artist
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from ._mark_colors import edge_color, legend_size
from ._plot_backend import drawing
from ._presentation_legend import Placement, place_legend
from ._presentation_ticks import count_text
from ._render_category_types import CategoryGroup
from ._render_context import RenderContext
from ._types import JsonScalar

AGGREGATES = ('count', 'multicount', 'bar', 'bartwo', 'bargrid')


def _key(context: RenderContext, color: str, label: str) -> Artist:
    """A legend key painted exactly as the marks of its group."""
    options = context.options
    if context.kind in AGGREGATES:
        return Patch(
            facecolor=color, alpha=options.get('alpha', 0.85), label=label,
            edgecolor=edge_color(context, color), linewidth=options.get('edgewidth', 0.0),
        )
    if context.kind in ('box', 'violin'):
        face = to_rgba(color, options.get('alpha', 0.75)) if options.get('fill', True) else 'none'
        return Patch(
            facecolor=face, edgecolor=color, linewidth=options.get('linewidth', 0.8), label=label
        )
    return Line2D(
        [], [], linestyle='None', marker='o', markerfacecolor=color, markeredgecolor='none',
        markersize=float(np.sqrt(options.get('point_size', 18.0))),
        alpha=options.get('alpha', 0.85), label=label,
    )


def category_notes(
    context: RenderContext, members: list[CategoryGroup], categories: list[JsonScalar]
) -> None:
    """Key the hue groups; with annotate_n, state each group's or category's sample size."""
    spec, options = context.spec, context.options
    annotate, grouped = options.get('annotate_n', False), bool(spec.get('hue'))
    if grouped and spec.get('legend', True) and (context.lead or annotate):
        totals: dict[JsonScalar, int] = {}
        for group in members:
            totals[group.label] = totals.get(group.label, 0) + len(group.rows)
        handles = [
            _key(context, color, f'{label} (n = {count_text(totals.get(label, 0))})' if annotate else str(label))
            for label, color in spec['_hue_colors'].items()
        ]
        loc = options.get('legend_loc', 'best')
        place_legend(context.ax, Placement(loc, handles, legend_size(context), False))
    if annotate and not grouped and context.facet:
        raise ValueError(
            "annotate_n writes each category's sample size under its name; facets share those "
            'names. Declare hue to count the groups in each legend, or compose separate panels.'
        )
    if annotate and not grouped:
        sizes = {group.category: len(group.rows) for group in members}
        labels = [f'{value}\nn = {count_text(sizes.get(value, 0))}' for value in categories]
        positions = np.arange(len(categories))
        if options.get('orient', 'v') == 'h':
            drawing(context.ax).set_yticks(positions, labels)
        else:
            drawing(context.ax).set_xticks(positions, labels)
