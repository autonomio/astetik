"""Scientific axis labels and units derived from the declared plotted roles."""

from __future__ import annotations

from collections.abc import Mapping

from ._spec_types import PlotSpec

_HORIZONTAL = {
    'bar',
    'bartwo',
    'bargrid',
    'count',
    'multicount',
    'box',
    'violin',
    'strip',
    'swarm',
    'hist',
}


def label(
    column: str | list[str] | None, units: Mapping[str, str], descriptions: Mapping[str, str]
) -> str:
    if column is None:
        return ''
    if isinstance(column, list):
        column = ', '.join(column)
    text = descriptions.get(column) or str(column)
    unit = units.get(column)
    return f'{text} ({unit})' if unit and unit != '1' else text


def density_label(spec: PlotSpec, units: Mapping[str, str]) -> str:
    column = spec.get('x')
    unit = units.get(column) if column else None
    return 'Density' + (f' (1/{unit})' if unit not in {None, '1'} else '')


def axis_labels(
    spec: PlotSpec, units: Mapping[str, str], descriptions: Mapping[str, str]
) -> tuple[str, str, bool]:
    kind, options = spec['kind'], spec['options']
    labels = spec.get('labels', {})
    x = labels.get('x', label(spec.get('x'), units, descriptions))
    y = labels.get('y', label(spec.get('y'), units, descriptions))
    if kind in {'count', 'multicount'}:
        y = labels.get('y', 'Count')
    elif kind == 'hist':
        y = labels.get('y', density_label(spec, units) if options.get('density') else 'Count')
    elif kind in {'kde', 'multikde'} and not spec.get('y'):
        y = labels.get(
            'y',
            'Cumulative probability' if options.get('cumulative') else density_label(spec, units),
        )
    elif kind == 'roc':
        x, y = 'False positive rate', 'True positive rate'
    elif kind == 'animate':
        x, y = 'Series', labels.get('y', value_label(spec.get('y'), units))
    elif kind == 'corr':
        x = y = ''
    horizontal = options.get('orient') == 'h' and kind in _HORIZONTAL
    return (y, x, horizontal) if horizontal else (x, y, horizontal)


def value_label(column: str | list[str] | None, units: Mapping[str, str]) -> str:
    field = column[0] if isinstance(column, list) else column
    unit = units.get(field) if field else None
    return 'Value' + (f' ({unit})' if unit and unit != '1' else '')
