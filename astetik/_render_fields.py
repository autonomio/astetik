"""Refuse specification fields a plot kind cannot use, before anything is drawn."""

from __future__ import annotations

import pandas as pd

from ._analysis_groups import validate_order as validate_comparison_order
from ._render_common import levels
from ._render_context import RendererOptions, RendererSpec

_ORDERED = {
    'count', 'multicount', 'bar', 'bartwo', 'bargrid', 'box', 'violin', 'strip', 'swarm', 'grid',
    'pie', 'comparison', 'compare', 'overlap',
}


_HUE_ORDERED = {
    'hist', 'kde', 'line', 'longitudinal', 'scat', 'twod', 'regs', 'association', 'count',
    'multicount', 'bar', 'bartwo', 'bargrid', 'box', 'violin', 'strip', 'swarm', 'grid',
}


def validate_fields(data: pd.DataFrame, spec: RendererSpec, options: RendererOptions) -> None:
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
    hue, order = spec.get('hue'), spec.get('hue_order')
    if order is not None:
        if kind not in _HUE_ORDERED or not hue:
            raise ValueError(f'hue_order orders the hue groups of a plot; this {kind} has none.')
        if len(order) != len(set(order)) or set(order) != set(levels(data[hue])):
            raise ValueError('hue_order must include every observed hue group exactly once.')


def _validate_order(data: pd.DataFrame, spec: RendererSpec) -> None:
    order = spec.get('order')
    if order is None:
        return
    kind = spec['kind']
    if kind not in _ORDERED:
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
