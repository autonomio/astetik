"""Declared column and observation identity checks."""

from __future__ import annotations

from typing import cast

import pandas as pd
from pandas.api.types import is_numeric_dtype

from ._spec import fail
from ._spec_types import PlotSpec


def columns(data: pd.DataFrame, spec: PlotSpec) -> list[str]:
    selected: list[str] = []
    for name in ('x', 'y', 'hue', 'row', 'col'):
        value = cast(str | list[str] | None, spec.get(name))
        selected.extend(value if isinstance(value, list) else [value] if value is not None else [])
    requested = cast(object, spec.get('columns'))
    if requested:
        if (
            not isinstance(requested, list)
            or any(not isinstance(c, str) for c in cast(list[object], requested))
            or len(cast(list[object], requested)) != len(set(cast(list[str], requested)))
        ):
            fail('COLUMN_SCHEMA', 'columns must be a list of column names.')
        selected.extend(cast(list[str], requested))
    if spec['kind'] in {'table', 'text'} and not selected:
        selected.extend(str(column) for column in data.columns)
    selected.extend(spec['key'])
    if spec['kind'] == 'corr' and not spec.get('columns'):
        selected.extend(
            str(c) for c in data.columns if is_numeric_dtype(data[c]) and c not in spec['key']
        )
    missing = sorted(set(selected) - set(data.columns))
    if missing:
        fail('COLUMN_MISSING', 'A declared column is absent.', columns=missing)
    if spec['kind'] not in {'corr', 'table', 'text'} and not spec.get('x'):
        fail('COLUMN_REQUIRED', 'Declare x for this plot.')
    if spec['kind'] in {
        'scat',
        'twod',
        'line',
        'grid',
        'box',
        'violin',
        'strip',
        'swarm',
        'bargrid',
        'bartwo',
        'compare',
        'overlap',
        'regs',
        'roc',
        'world',
        'comparison',
        'association',
        'longitudinal',
        'animate',
    } and not spec.get('y'):
        fail('COLUMN_REQUIRED', 'Declare y for this plot.')
    return list(dict.fromkeys(selected))
