"""Categorical renderer orchestration with fixed domains and observation cells."""

from __future__ import annotations

from collections.abc import Iterator

from ._plot_backend import draw_canvas, drawing
from ._render_category_types import CategoryGroup
from ._render_common import (
    category_axes,
    equal,
    figure_for,
    finalize_font,
    legend,
    levels,
    numerical,
    scalar,
    zero_baseline,
)
from ._render_context import RenderContext
from ._render_groups import aggregate, observations
from ._render_shapes import box, violin
from ._types import JsonScalar

_AGGREGATES = ('count', 'multicount', 'bar', 'bartwo', 'bargrid')


def _groups(context: RenderContext, categories: list[JsonScalar]) -> Iterator[CategoryGroup]:
    spec, data, options = context.spec, context.data, context.options
    category, hue = context.column('x'), spec.get('hue')
    hlevels = levels(data[hue]) if hue else [None]
    width = options.get('width', 0.8) / len(hlevels)
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
                spec['_hue_colors'].get(label, context.colors.primary),
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
    for group in _groups(context, categories):
        if context.kind in _AGGREGATES:
            baseline.extend(aggregate(group))
        else:
            {'box': box, 'violin': violin}.get(context.kind, observations)(group)
    category_axes(context.ax, categories, horizontal)
    if baseline:
        zero_baseline(context.ax, horizontal, baseline)
    elif context.kind in _AGGREGATES:
        zero_baseline(context.ax, horizontal, [0.0])
    value = context.spec.get('y')
    x_label, y_label = (
        (str(value) if value else 'Count', category)
        if horizontal
        else (category, str(value) if value else 'Count')
    )
    drawing(context.ax).set_xlabel(x_label)
    drawing(context.ax).set_ylabel(y_label)
    legend(context.ax, context.spec, context.spec['_hue_colors'])
    context.rec.methods['categorical'] = dict(
        order=[scalar(v) for v in categories], orient=context.options.get('orient', 'v')
    )
