"""Categorical renderer orchestration with fixed domains and observation cells."""

from __future__ import annotations

from collections.abc import Iterator

from ._category_notes import AGGREGATES, category_notes
from ._mark_colors import resolve_color
from ._plot_backend import draw_canvas, drawing
from ._render_bars import aggregate
from ._render_category_types import CategoryGroup
from ._render_common import (
    category_axes,
    equal,
    figure_for,
    finalize_font,
    levels,
    numerical,
    scalar,
    zero_baseline,
)
from ._render_context import RenderContext
from ._render_groups import observations
from ._render_shapes import box
from ._render_violin import violin
from ._types import JsonScalar


def _base_color(context: RenderContext) -> str:
    """One declared colour restyles ungrouped marks; groups keep their manifest bindings."""
    color = context.options.get('color')
    if color is None:
        return context.colors.primary
    if context.spec.get('hue'):
        raise ValueError('color applies to one series; bind groups in manifest.categories.')
    return resolve_color(context.spec['_manifest'], color, 'color')


def _groups(context: RenderContext, categories: list[JsonScalar]) -> Iterator[CategoryGroup]:
    spec, data, options = context.spec, context.data, context.options
    category, hue = context.column('x'), spec.get('hue')
    hlevels = list(spec['_hue_colors']) if hue else [None]
    width, base = options.get('width', 0.8) / len(hlevels), _base_color(context)
    for ci, cat in enumerate(categories):
        cr = context.rows[equal(data.iloc[context.rows][category], cat)]
        for hi, label in enumerate(hlevels):
            rows = cr[equal(data.iloc[cr][hue], label)] if hue else cr
            if not len(rows):
                continue
            value = spec.get('y')
            numbers = (
                numerical(data.iloc[rows][context.column('y')], context.column('y'))
                if value
                else None
            )
            yield CategoryGroup(
                context,
                cat,
                label,
                rows,
                numbers,
                ci + (hi - (len(hlevels) - 1) / 2) * width,
                width,
                spec['_hue_colors'].get(label, base),
                options.get('orient', 'v') == 'h',
                ci,
                hi,
                len(hlevels),
            )


def _prepare_swarm(context: RenderContext) -> None:
    values = numerical(context.data[context.column('y')], context.column('y'))
    low, high = values.min(), values.max()
    padding = (high - low) * 0.05 if high > low else 0.5
    if context.options.get('orient', 'v') == 'h':
        context.ax.set_xlim(low - padding, high + padding)
    else:
        context.ax.set_ylim(low - padding, high + padding)
    figure = figure_for(context.ax)
    finalize_font(figure, context.spec['_manifest'])
    draw_canvas(figure)


def categorical(context: RenderContext) -> None:
    category = context.column('x')
    categories = context.spec.get('order') or levels(context.data[category])
    horizontal = context.options.get('orient', 'v') == 'h'
    category_axes(context.ax, categories, horizontal)
    if context.kind == 'swarm':
        _prepare_swarm(context)
    baseline: list[float] = []
    members = list(_groups(context, categories))
    for group in members:
        if context.kind in AGGREGATES:
            baseline.extend(aggregate(group))
        else:
            {'box': box, 'violin': violin}.get(context.kind, observations)(group)
    category_axes(context.ax, categories, horizontal)
    if context.kind in AGGREGATES:
        zero_baseline(context.ax, horizontal, baseline or [0.0])
    measure = str(context.spec.get('y') or 'Count')
    drawing(context.ax).set_xlabel(measure if horizontal else category)
    drawing(context.ax).set_ylabel(category if horizontal else measure)
    category_notes(context, members, categories)
    context.rec.methods['categorical'] = dict(
        order=[scalar(v) for v in categories], orient=context.options.get('orient', 'v')
    )
