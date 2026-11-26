"""Line series: observations joined in order, or a declared estimate with its interval."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Unpack, cast

import numpy as np
from matplotlib.artist import Artist
from matplotlib.lines import Line2D

from ._estimate import Estimate, computation, estimate
from ._mark_backend import LinePaint, Values, marks
from ._mark_colors import legend_size, series_mapping
from ._plot_backend import drawing
from ._presentation_legend import Placement, place_legend
from ._presentation_notes import end_labels
from ._presentation_ticks import count_text
from ._render_common import groups, numerical
from ._render_context import RenderContext, RowArray, measure_columns
from ._types import FloatArray, JsonScalar

_DASHES = ('solid', 'dashed', 'dotted', 'dashdot')


@dataclass(frozen=True)
class _Series:
    """One drawn line with the interval, if any, around it."""

    key: JsonScalar
    x: Values
    y: FloatArray
    low: FloatArray | None
    high: FloatArray | None
    count: int
    paint: LinePaint


def _observed(context: RenderContext, column: str, rows: RowArray, key: JsonScalar) -> Values:
    """Record each observation; the line joins them in the declared order."""
    data, x = context.data, context.column('x')
    ordered = context.options.get('sort', True)
    for position in rows:
        values: dict[str, object] = {
            x: data.iloc[position][x], column: data.iloc[position][column], 'series': key,
        }
        context.rec.mark(
            'observation',
            values,
            [int(position)],
            'identity; line connects observations in stable x order'
            if ordered
            else 'identity; input row order',
            context.facet,
        )
    return data.iloc[rows][x].to_numpy()


def _summarised(
    context: RenderContext, column: str, rows: RowArray, key: JsonScalar
) -> tuple[Values, FloatArray, FloatArray | None, FloatArray | None]:
    """One declared estimate, and its interval, for the observations sharing each x."""
    data, options, x = context.data, context.options, context.column('x')
    positions = data.iloc[rows][x].to_numpy()
    levels = np.unique(positions)
    results: list[Estimate] = []
    for level in levels:
        members = rows[positions == level]
        result = estimate(numerical(data.iloc[members][column], column), options, f'{x}={level}')
        results.append(result)
        context.rec.mark(
            'estimate',
            {x: level, column: result.centre, 'series': key, 'lower': result.low,
             'upper': result.high, 'n': result.n},
            members,
            computation(options) + '; one estimate per x',
            context.facet,
        )
    centre = np.asarray([result.centre for result in results])
    if options.get('errorbar') is None:
        return levels, centre, None, None
    low = np.asarray([result.low for result in results], dtype=float)
    return levels, centre, low, np.asarray([result.high for result in results], dtype=float)


class _Key(Protocol):
    def __call__(
        self, _x: list[float], _y: list[float], /, *, label: str, **kwargs: Unpack[LinePaint]
    ) -> Artist: ...


def _key(label: str, paint: LinePaint) -> Artist:
    """A legend key drawn with the very paint of its line."""
    return cast(_Key, Line2D)([], [], label=label, **paint)


def _paint(context: RenderContext, color: str, index: int) -> LinePaint:
    """One series' line style; ``index`` is its place among every series of the figure."""
    options = context.options
    dashed = options.get('dashes', False)
    return LinePaint(
        color=color,
        linewidth=options.get('linewidth', 1.25),
        alpha=options.get('alpha', 1.0),
        marker=options.get('marker'),
        markersize=options.get('markersize', 4.0),
        markeredgecolor=context.spec['_manifest'].colors['paper'],
        markeredgewidth=0.5,
        linestyle=_DASHES[index] if dashed else options.get('linestyle', 'solid'),
        drawstyle=options.get('drawstyle', 'default'),
    )


def _series(context: RenderContext) -> tuple[list[_Series], bool]:
    data, spec, options = context.data, context.spec, context.options
    x, columns, hue = context.column('x'), measure_columns(spec, 'y'), spec.get('hue')
    if hue and len(columns) > 1:
        raise ValueError('Multiple y columns and hue cannot be combined in one line plot.')
    grouped = bool(hue) or len(columns) > 1
    mapping = series_mapping(context, columns, grouped)
    members = [
        (label if hue else column, column, rows)
        for column in columns
        for label, rows in groups(data, context.rows, hue, spec['_hue_colors'])
    ]
    if options.get('dashes', False) and len(mapping) > len(_DASHES):
        raise ValueError(f'dashes distinguishes at most {len(_DASHES)} series.')
    result: list[_Series] = []
    for key, column, rows in members:
        paint = _paint(context, mapping[key], list(mapping).index(key))
        if options.get('estimator') is None:
            if options.get('sort', True):
                rows = rows[np.argsort(data.iloc[rows][x].to_numpy(), kind='stable')]
            positions = _observed(context, column, rows, key)
            values, low, high = numerical(data.iloc[rows][column], column), None, None
        else:
            positions, values, low, high = _summarised(context, column, rows, key)
        result.append(_Series(key, positions, values, low, high, len(rows), paint))
    return result, grouped


def _interval(context: RenderContext, item: _Series) -> None:
    if item.low is None or item.high is None:
        return
    options, color = context.options, item.paint.get('color', '')
    if options.get('interval', 'band') == 'band':
        marks(context.ax).fill_between(
            item.x, item.low, item.high, facecolor=color,
            alpha=options.get('band_alpha', 0.2), linewidth=0.0,
            step={'steps': 'pre', 'steps-pre': 'pre', 'steps-mid': 'mid',
                  'steps-post': 'post'}.get(item.paint.get('drawstyle', 'default')),
        )
        return
    width = item.paint.get('linewidth', 1.25) * 0.7
    marks(context.ax).errorbar(
        item.x, item.y, yerr=np.vstack([item.y - item.low, item.high - item.y]), fmt='none',
        ecolor=color, elinewidth=width, capsize=options.get('capsize', 2.0), capthick=width,
    )


def line(context: RenderContext) -> None:
    spec, options = context.spec, context.options
    series, grouped = _series(context)
    for item in series:
        _interval(context, item)
    for item in series:
        marks(context.ax).plot(item.x, item.y, **item.paint)
    annotate = options.get('annotate_n', False)
    notes = [f'{item.key} (n = {count_text(item.count)})' if annotate else str(item.key)
             for item in series]
    loc = options.get('legend_loc', 'best')
    ended = loc == 'end' and grouped
    if spec.get('legend', True) and ((grouped and context.lead) or annotate or ended):
        if loc == 'end':
            entries = [((item.x[-1], float(item.y[-1])), item.paint.get('color', 'ink')) for item in series]
            end_labels(context.ax, [(n, *e) for n, e in zip(notes, entries)], legend_size(context))
        else:
            handles = [_key(note, item.paint) for item, note in zip(series, notes)]
            keyed = spec['_hue_colors']
            if keyed and not annotate:
                # One legend serves every panel, so it keys every group of the figure.
                handles = [
                    _key(str(key), _paint(context, color, index))
                    for index, (key, color) in enumerate(keyed.items())
                ]
            if not grouped:
                handles = [_key(f'n = {count_text(series[0].count)}', LinePaint(linestyle='None'))]
            place_legend(context.ax, Placement(loc, handles, legend_size(context), not grouped))
    columns = measure_columns(spec, 'y')
    drawing(context.ax).set_xlabel(context.column('x'))
    drawing(context.ax).set_ylabel(columns[0] if len(columns) == 1 else 'Value')
