"""Deterministic renderer orchestration with explicit scientific provenance."""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from ._analysis_groups import validate_order as validate_comparison_order
from ._colors import ColorSystem
from ._manifest import Manifest
from ._plot_backend import drawing, scoped_rc
from ._render_categorical import categorical
from ._render_common import color_mapping, finalize_font, levels, numerical, scalar
from ._render_comparison import comparison
from ._render_context import Recorder, RenderContext, Rendered, RendererOptions, RendererSpec
from ._render_correlation import corr
from ._render_density import kde, prepare_kde2d
from ._render_histogram import hist
from ._render_layout import facet_plan, figure_dimensions
from ._render_options import DEFAULT_OPTIONS, KINDS, SUPPORTED_OPTIONS, validate_options
from ._render_panels import compare_panels, overlap
from ._render_sectors import pie, roc
from ._render_series import line, numeric_hue, scatter
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


def _scatter_panel(context: RenderContext) -> None:
    scatter(context)
    if context.kind == 'regs' and not context.options.get('draw_scatter', True):
        for collection in list(context.ax.collections):
            collection.remove()


_HANDLERS: dict[str, Callable[[RenderContext], None]] = {
    **dict.fromkeys(('scat', 'twod', 'regs', 'association'), _scatter_panel),
    **dict.fromkeys(('line', 'longitudinal'), line),
    **dict.fromkeys(('kde', 'multikde'), kde),
    **dict.fromkeys(
        (
            'count',
            'multicount',
            'bar',
            'bartwo',
            'bargrid',
            'box',
            'violin',
            'strip',
            'swarm',
            'grid',
        ),
        categorical,
    ),
    'hist': hist,
    'corr': corr,
    'pie': pie,
    'roc': roc,
    'world': world,
    'overlap': overlap,
    'oned': _event,
    'comparison': comparison,
}


def _validate_fields(data: pd.DataFrame, spec: RendererSpec, options: RendererOptions) -> None:
    kind = spec['kind']
    incompatible = {
        'hue': {'corr', 'pie', 'world', 'roc', 'oned'},
        'y': {'corr', 'hist', 'count', 'multicount', 'oned'},
    }
    for field, kinds in incompatible.items():
        if spec.get(field) is not None and kind in kinds:
            raise ValueError(f'{field} is unsupported for {kind}.')
    if spec.get('columns') is not None and kind != 'corr':
        raise ValueError(f'columns is unsupported for {kind}; declare x and y.')
    if options.get('col_wrap') and not spec.get('col'):
        raise ValueError('col_wrap requires a col facet.')
    if kind == 'regs' and not options.get('draw_scatter', True) and spec.get('hue'):
        raise ValueError('A hue encoding requires displayed observations in regs.')
    if kind in ('compare', 'comparison') and (spec.get('row') or spec.get('col')):
        raise ValueError(f'{kind} does not support additional facets.')
    _validate_order(data, spec)


def _validate_order(data: pd.DataFrame, spec: RendererSpec) -> None:
    order = spec.get('order')
    if order is None:
        return
    kind = spec['kind']
    ordered = {
        'count',
        'multicount',
        'bar',
        'bartwo',
        'bargrid',
        'box',
        'violin',
        'strip',
        'swarm',
        'grid',
        'pie',
        'comparison',
        'compare',
        'overlap',
    }
    if kind not in ordered:
        raise ValueError(f'Category order does not apply to {kind}.')
    category = (
        (spec.get('label_col') or spec.get('hue'))
        if kind in ('compare', 'overlap')
        else spec.get('x')
    )
    if kind == 'comparison' and isinstance(category, str):
        validate_comparison_order(data[category], order)
    elif len(order) != len(set(order)):
        raise ValueError('order must list distinct category labels.')
    elif not isinstance(category, str) or set(order) != set(levels(data[category])):
        raise ValueError('order must include every observed category exactly once.')


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
    if spec['_hue_colors']:
        rec.methods['category_colours'] = {str(k): v for k, v in spec['_hue_colors'].items()}
    if kind == 'multikde' and not spec.get('row') and (spec.get('label_col') or hue):
        spec['row'] = spec.get('label_col') or hue


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
    _validate_fields(data, resolved, options)
    rec = Recorder()
    rec.methods['options'] = scalar(options)
    if analysis and kind in ('association', 'longitudinal'):
        rec.methods['analysis'] = analysis.get('methods', {})
    with scoped_rc(manifest.rc(paper)):
        _prepare_spec(data, resolved, options, rec)
        if kind == 'compare':
            figure = compare_panels(data, resolved, manifest, paper, options, rec)
        else:
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
    active: set[int] = set()
    for slot, rows, facet in facets:
        ax = axes.flat[slot]
        active.add(slot)
        if not len(rows):
            ax.text(0.5, 0.5, 'No observations', transform=ax.transAxes, ha='center', va='center')
            ax.set_axis_off()
            continue
        if facet:
            ax.set_title(' · '.join(f'{k}: {v}' for k, v in facet.items()), loc='left')
        _HANDLERS[kind](
            RenderContext(
                ax, data, rows, spec, options, ColorSystem(manifest), rec, facet, kind, analysis
            )
        )
    for slot, ax in enumerate(axes.flat):
        if slot not in active:
            ax.set_visible(False)
    return figure
