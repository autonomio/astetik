"""Scientific tables share design, exact snapshots and plot publication contracts."""

from __future__ import annotations

import numbers
from collections.abc import Callable
from typing import Protocol, TypedDict, Unpack, cast

import numpy as np
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.table import Table

from ._errors import AstetikError
from ._manifest import Manifest
from ._render_context import Rendered
from ._spec_json import json_object
from ._spec_types import PlotSpec
from ._types import JsonObject


class TableArguments(TypedDict):
    cellText: list[list[str]]
    colLabels: list[str]
    cellLoc: str
    colLoc: str
    loc: str
    bbox: list[float]


class TableAxes(Protocol):
    def table(self, **kwargs: Unpack[TableArguments]) -> Table: ...


def _display(value: object, digits: int) -> str:
    if isinstance(value, np.generic):
        value = cast(Callable[[], object], getattr(cast(object, value), 'item'))()
    return (
        format(value, f'.{digits}g')
        if not isinstance(value, bool) and isinstance(value, numbers.Real)
        else str(value)
    )


def _cells(
    selected: pd.DataFrame, columns: list[str], digits: int
) -> tuple[list[list[str]], list[JsonObject]]:
    cells: list[list[str]] = []
    marks: list[JsonObject] = []
    for row in range(len(selected)):
        display: list[str] = []
        for column in columns:
            display.append(_display(selected.iloc[row][column], digits))
            marks.append(
                {
                    'id': f'cell-{row}-{columns.index(column)}',
                    'kind': 'table_cell',
                    'source_rows': [row],
                    'source_field': column,
                    'values': {'column': column, 'display': display[-1]},
                    'computation': f'identity; displayed with {digits} significant digits for numerical values',
                }
            )
        cells.append(display)
    return cells, marks


def _style(table: Table, selected: pd.DataFrame, manifest: Manifest) -> None:
    table.auto_set_font_size(False)
    table.set_fontsize(manifest.typography['fontsize'])
    for (row, column), cell in table.get_celld().items():
        cell.set_facecolor(manifest.colors['paper'])
        cell.set_edgecolor(manifest.colors['line'])
        cell.set_linewidth(manifest.axes['linewidth'])
        cell.visible_edges = 'B' if row == 0 else ''
        setattr(cell.get_text(), '_astetik_text_role', 'ink')
        if row > 0 and not pd.api.types.is_numeric_dtype(selected.iloc[:, column]):
            cell.get_text().set_horizontalalignment('left')


def render_table(data: pd.DataFrame, spec: PlotSpec, manifest: Manifest, paper: bool) -> Rendered:
    digits = cast(object, spec['options'].get('digits'))
    if isinstance(digits, bool) or not isinstance(digits, int) or not 1 <= digits <= 15:
        raise AstetikError('TABLE_PRECISION', 'digits must be an integer from one to fifteen.')
    x = spec.get('x')
    columns = spec.get('columns') or (
        [x] if spec['kind'] == 'text' and x else [str(column) for column in data.columns]
    )
    selected = data[columns]
    cells, marks = _cells(selected, columns, digits)
    units, descriptions = spec.get('units', {}), spec.get('descriptions', {})
    labels = [
        descriptions.get(column, column)
        + (f' ({units[column]})' if units.get(column) not in {None, '1'} else '')
        for column in columns
    ]
    figure = Figure(figsize=manifest.dimensions(paper), layout='constrained')
    FigureCanvasAgg(figure)
    axis = figure.subplots()
    axis.set_axis_off()
    table = cast(TableAxes, axis).table(
        cellText=cells,
        colLabels=labels,
        cellLoc='right',
        colLoc='left',
        loc='center',
        bbox=[0, 0, 1, 1],
    )
    _style(table, selected, manifest)
    return Rendered(
        figure,
        selected.copy(deep=True),
        marks,
        json_object(
            {
                'table': {
                    'digits': digits,
                    'columns': columns,
                    'rows': len(data),
                    'computation': 'identity; display formatting only',
                }
            }
        ),
    )
