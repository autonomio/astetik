"""Histogram rendering with explicit scientific provenance."""

from __future__ import annotations

import numpy as np
from matplotlib.artist import Artist

from ._histogram_bins import bin_edges, bin_values
from ._histogram_draw import Canvas, Style
from ._histogram_options import stat_label, statistic
from ._histogram_series import Series, overlays, record
from ._mark_colors import legend_size, resolve_color, series_mapping
from ._plot_backend import drawing
from ._presentation_ticks import count_text
from ._render_common import groups, numerical
from ._render_context import RenderContext, measure_columns


def _style(context: RenderContext, horizontal: bool, log: bool) -> Style:
    options, manifest = context.options, context.spec['_manifest']
    step, fill = options.get('element', 'bars') == 'step', options.get('fill', True)
    edge = options.get('edgecolor', 'auto')
    return Style(
        horizontal=horizontal,
        log=log,
        step=step,
        fill=fill,
        alpha=options.get('alpha', 0.85),
        shrink=options.get('shrink', 1.0),
        edgecolor=(manifest.colors['paper'] if fill and not step else None)
        if edge == 'auto'
        else resolve_color(manifest, edge, 'edgecolor'),
        edgewidth=options.get('edgewidth', 0.4),
        linewidth=options.get('linewidth', 1.25),
        paper=manifest.colors['paper'],
        legendsize=legend_size(context),
        integer=statistic(options) == 'count' and not options.get('common_norm', False),
        cumulative=options.get('cumulative', False),
    )


def _plan(context: RenderContext) -> tuple[Canvas, list[Series], bool]:
    data, spec, options = context.data, context.spec, context.options
    columns, hue = measure_columns(spec, 'x'), spec.get('hue')
    if hue and len(columns) > 1:
        raise ValueError('Multiple histogram columns and hue cannot be combined.')
    horizontal = options.get('orient', 'v') == 'h'
    log = spec.get('axes', {}).get('y' if horizontal else 'x', {}).get('scale') == 'log'
    if log and options.get('kde', False):
        raise ValueError('A KDE overlay requires a linear measurement axis.')
    grouped = bool(hue) or len(columns) > 1
    multiple = options.get('multiple', 'layer')
    if multiple != 'layer' and not grouped:
        raise ValueError(f'multiple={multiple!r} requires hue groups or several columns.')
    # All compared distributions share bin boundaries resolved from the full input.
    edges = bin_edges(np.concatenate([numerical(data[c], c) for c in columns]), options, log)
    mapping = series_mapping(context, columns, grouped)
    members = [
        (label if hue else column, column, rows, numerical(data.iloc[rows][column], column))
        for column in columns
        for label, rows in groups(data, context.rows, hue, spec['_hue_colors'])
    ]
    pooled = sum(len(values) for *_, values in members)
    bottom = np.zeros(len(edges) - 1)
    series: list[Series] = []
    for key, column, rows, values in members:
        total = pooled if options.get('common_norm', False) else len(values)
        counts, heights = bin_values(
            values, edges, statistic(options), total, options.get('cumulative', False)
        )
        series.append(
            Series(
                key, column, rows, values, mapping[key], counts, heights, bottom,
                len(values) / total,
            )
        )
        if multiple == 'stack':
            bottom = bottom + heights
    return Canvas(context.ax, _style(context, horizontal, log), edges), series, grouped


def hist(context: RenderContext) -> None:
    spec, options = context.spec, context.options
    canvas, series, grouped = _plan(context)
    stat, multiple = statistic(options), options.get('multiple', 'layer')
    annotate = options.get('annotate_n', False)
    top = max(float((item.bottom + item.heights).max()) for item in series)
    for index, item in enumerate(series):
        slot = (index, len(series)) if multiple == 'dodge' else (0, 1)
        canvas.fill(item.heights, item.bottom, item.color, slot)
    handles: list[Artist] = []
    for item in series:
        canvas.outline(item.heights, item.bottom, item.color)
        record(context, item, canvas.edges)
        overlays(context, canvas, item, top)
    context.rec.methods['histogram'] = dict(
        bins=canvas.edges.tolist(),
        density=stat == 'density',
        statistic=stat,
        cumulative=options.get('cumulative', False),
        common_norm=options.get('common_norm', False),
        multiple=multiple,
        log_bins=canvas.style.log and not isinstance(options.get('bins'), list),
        shared_bins=True,
        final_bin_right_closed=True,
    )
    if grouped and annotate:
        handles = [
            canvas.series_handle(item.color, f'{item.key} (n = {count_text(len(item.values))})')
            for item in series
        ]
    elif grouped:
        # One legend serves every panel, so it keys every group of the figure.
        keyed = spec['_hue_colors'] or {item.key: item.color for item in series}
        handles = [canvas.series_handle(color, str(key)) for key, color in keyed.items()]
    ink = spec['_manifest'].colors['ink']
    handles += [canvas.reference_handle(name, ink) for name in options.get('reference', [])]
    pooled = sum(len(item.values) for item in series)
    notes = [f'n = {count_text(pooled)}'] if annotate and not grouped else []
    if annotate and not spec.get('legend', True):
        raise ValueError('annotate_n is written in the legend; enable legend.')
    # Panels repeat one legend only when its entries differ between them.
    if spec.get('legend', True) and (annotate or context.lead):
        canvas.legend(options.get('legend_loc', 'best'), handles, notes)
    value, measure = stat_label(options, 'Density'), series[0].column
    drawing(context.ax).set_xlabel(value if canvas.style.horizontal else measure)
    drawing(context.ax).set_ylabel(measure if canvas.style.horizontal else value)
    canvas.value_axis()
