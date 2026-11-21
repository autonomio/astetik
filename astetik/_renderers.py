"""Deterministic renderer orchestration with explicit scientific provenance."""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from ._colors import ColorSystem
from ._manifest import Manifest
from ._plot_backend import drawing, scoped_rc
from ._presentation_grid import SHARED
from ._presentation_headings import heading
from ._render_categorical import categorical
from ._render_common import color_mapping, finalize_font, levels, numerical, scalar
from ._render_comparison import comparison
from ._render_context import (
    Recorder,
    RenderContext,
    Rendered,
    RendererOptions,
    RendererSpec,
)
from ._render_correlation import corr
from ._render_density import kde, prepare_kde2d
from ._render_fields import validate_fields
from ._render_figure import compose
from ._render_histogram import hist
from ._render_layout import facet_plan, figure_dimensions
from ._render_line import line
from ._render_options import DEFAULT_OPTIONS, KINDS, SUPPORTED_OPTIONS, validate_options
from ._render_panels import compare_panels, overlap
from ._render_scatter import numeric_hue, scatter
from ._render_sectors import pie, roc
from ._render_world import world
from ._spec_types import PlotSpec
from ._types import JsonObject

__all__ = ['DEFAULT_OPTIONS', 'KINDS', 'SUPPORTED_OPTIONS', 'Rendered', 'render_plot']


def _event(context: RenderContext) -> None:
    values = numerical(context.data.iloc[context.rows][context.column('x')], context.column('x'))
    drawing(context.ax).eventplot(
        values, colors=context.colors.primary, linewidths=context.options.get('linewidth', 1.25)
    )
    drawing(context.ax).set_yticks([])
    drawing(context.ax).set_xlabel(context.column('x'))
    for p, value in zip(context.rows, values):
        context.rec.mark(
            'observation', {'value': value}, [int(p)], 'identity; event plot', context.facet
        )


_CATEGORICAL = (
    'count', 'multicount', 'bar', 'bartwo', 'bargrid', 'box', 'violin', 'strip', 'swarm', 'grid'
)
_HANDLERS: dict[str, Callable[[RenderContext], None]] = {
    **dict.fromkeys(('scat', 'twod', 'regs', 'association'), scatter),
    **dict.fromkeys(('line', 'longitudinal'), line),
    **dict.fromkeys(('kde', 'multikde'), kde),
    **dict.fromkeys(_CATEGORICAL, categorical),
    'hist': hist,
    'corr': corr,
    'pie': pie,
    'roc': roc,
    'world': world,
    'overlap': overlap,
    'oned': _event,
    'comparison': comparison,
}


def _prepare_spec(
    data: pd.DataFrame, spec: RendererSpec, options: RendererOptions, rec: Recorder
) -> None:
    hue, kind, manifest = spec.get('hue'), spec['kind'], spec['_manifest']
    continuous = kind in ('scat', 'twod', 'regs', 'association') and numeric_hue(
        data, spec, options
    )
    spec['_hue_colors'] = (
        color_mapping(manifest, levels(data[hue]), spec['_paper']) if hue and not continuous else {}
    )
    order = spec.get('hue_order')
    if order is not None:
        if not spec['_hue_colors']:
            raise ValueError('hue_order applies to categorical hue groups.')
        spec['_hue_colors'] = {label: spec['_hue_colors'][label] for label in order}
    if spec['_hue_colors']:
        rec.methods['category_colours'] = {str(k): v for k, v in spec['_hue_colors'].items()}
    if kind == 'multikde' and not spec.get('row') and (spec.get('label_col') or hue):
        spec['row'] = spec.get('label_col') or hue


def _draw_panel(data: pd.DataFrame, view: RendererSpec, ax: Axes, rec: Recorder) -> None:
    """Draw one complete specification on one axes of a composed figure."""
    kind = view['kind']
    options = validate_options(kind, cast(JsonObject, view.get('options', {})))
    validate_fields(data, view, options)
    rec.methods['options'] = scalar(options)
    _prepare_spec(data, view, options, rec)
    colors, rows = ColorSystem(view['_manifest']), np.arange(len(data))
    _HANDLERS[kind](RenderContext(ax, data, rows, view, options, colors, rec, {}, kind))


def render_plot(
    data: pd.DataFrame,
    spec: PlotSpec,
    manifest: Manifest,
    paper: bool,
    analysis: JsonObject | None = None,
) -> Rendered:
    """Render one validated scientific specification without global state."""
    resolved = cast(RendererSpec, dict(spec, _manifest=manifest, _paper=paper, _hue_colors={}))
    kind = resolved['kind']
    if kind not in DEFAULT_OPTIONS:
        raise ValueError(f'Unknown plot kind {kind!r}.')
    options = validate_options(kind, cast(JsonObject, spec.get('options', {})))
    data = data.reset_index(drop=True)
    if data.empty:
        raise ValueError('Rendering requires at least one observation.')
    validate_fields(data, resolved, options)
    rec = Recorder()
    rec.methods['options'] = scalar(options)
    if analysis and kind in ('association', 'longitudinal'):
        rec.methods['analysis'] = analysis.get('methods', {})
    with scoped_rc(manifest.rc(paper)):
        if kind == 'panels':
            figure = compose(data, resolved, options, rec, _draw_panel)
        elif kind == 'compare':
            _prepare_spec(data, resolved, options, rec)
            figure = compare_panels(data, resolved, manifest, paper, options, rec)
        else:
            _prepare_spec(data, resolved, options, rec)
            figure = _render_facets(data, resolved, options, rec, analysis)
        finalize_font(figure, manifest)
        return Rendered(figure, rec.table(), rec.marks, rec.methods)


def _render_facets(
    data: pd.DataFrame,
    spec: RendererSpec,
    options: RendererOptions,
    rec: Recorder,
    analysis: JsonObject | None,
) -> Figure:
    manifest, paper, kind = spec['_manifest'], spec['_paper'], spec['kind']
    nrows, ncols, facets = facet_plan(data, spec, options, manifest, paper)
    if kind in ('kde', 'multikde') and spec.get('y'):
        spec['_kde2d'], spec['_kde2d_domain'] = prepare_kde2d(data, spec, options, facets)
    figure = Figure(figsize=figure_dimensions(manifest, paper, nrows, ncols), layout='constrained')
    FigureCanvasAgg(figure)
    setattr(figure, '_astetik_font_size', manifest.rc(paper).get('font.size', 9))
    axes = figure.subplots(nrows, ncols, squeeze=False, sharex=True, sharey=True)
    setattr(figure, SHARED, True)
    active: set[int] = set()
    colors = ColorSystem(manifest)
    for slot, rows, facet in facets:
        ax = axes.flat[slot]
        if not len(rows):
            active.add(slot)
            ax.text(0.5, 0.5, 'No observations', transform=ax.transAxes, ha='center', va='center')
            ax.set_axis_off()
            continue
        if facet:
            heading(ax, ' \N{MIDDLE DOT} '.join(str(value) for value in facet.values()))
        _HANDLERS[kind](
            RenderContext(
                ax, data, rows, spec, options, colors, rec, facet, kind, analysis, not active
            )
        )
        active.add(slot)
    for slot, ax in enumerate(axes.flat):
        if slot not in active:
            ax.set_visible(False)
    return figure
