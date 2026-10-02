"""Native measurement dtype, unit and shared-axis comparability contracts."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from ._manifest import Manifest
from ._observation import Observations
from ._spec import fail
from ._spec_types import PlotSpec


def y_fields(spec: PlotSpec) -> list[str]:
    y = spec.get('y')
    return y if isinstance(y, list) else [y] if y else []


def measures(data: pd.DataFrame, spec: PlotSpec, fields: list[str]) -> list[str]:
    kind, x, ys = spec['kind'], spec.get('x'), y_fields(spec)
    both = {
        'scat',
        'twod',
        'regs',
        'association',
        'line',
        'longitudinal',
        'overlap',
        'compare',
        'animate',
        'hist',
        'kde',
        'multikde',
        'oned',
    }
    ordinate = {
        'bar',
        'bartwo',
        'bargrid',
        'box',
        'violin',
        'strip',
        'swarm',
        'grid',
        'comparison',
        'world',
        'pie',
        'roc',
    }
    if kind in both:
        selected = ([x] if x else []) + ys
    elif kind in ordinate:
        selected = ys
    elif kind in {'table', 'text', 'corr'}:
        selected = (spec.get('columns') if kind == 'corr' else None) or [
            column
            for column in fields
            if is_numeric_dtype(data[column]) and column not in spec['key']
        ]
    else:
        selected = []
    return list(dict.fromkeys(selected))


def continuous_hue(data: pd.DataFrame, spec: PlotSpec, design: Manifest) -> str | None:
    hue = spec.get('hue')
    if not hue or spec['kind'] not in {'scat', 'twod', 'regs', 'association'}:
        return None
    mode = spec['options'].get('hue_mode', 'auto')
    bound = all(str(value) in design.categories for value in data[hue].unique())
    continuous = mode == 'continuous' or (
        mode == 'auto'
        and is_numeric_dtype(data[hue])
        and not is_bool_dtype(data[hue])
        and not bound
    )
    if continuous and not is_numeric_dtype(data[hue]):
        fail('MEASUREMENT_DTYPE', 'Continuous hue requires native numerical values.', column=hue)
    return hue if continuous else None


def validate(observations: Observations, spec: PlotSpec, design: Manifest) -> None:
    data, units = observations.frame, observations.units
    if data.empty:
        fail('EMPTY_DATA', 'A scientific result needs observations.')
    for column in observations.fields:
        if (
            is_numeric_dtype(data[column])
            and not np.isfinite(data[column].to_numpy(dtype=float)).all()
        ):
            fail(
                'NONFINITE_DATA',
                'Infinite numeric values need explicit preparation.',
                column=column,
            )
    selected = measures(data, spec, observations.fields)
    for column in selected:
        datetime_time = (
            column == spec.get('x')
            and spec['kind'] in {'line', 'longitudinal'}
            and pd.api.types.is_datetime64_any_dtype(data[column])
        )
        if not is_numeric_dtype(data[column]) and not datetime_time:
            fail(
                'MEASUREMENT_DTYPE',
                'Convert measurements to a native numerical dtype during preparation.',
                column=column,
            )
    hue = continuous_hue(data, spec, design)
    if hue:
        selected.append(hue)
    if spec['paper']:
        unresolved = [column for column in selected if not units.get(column, '').strip()]
        if unresolved:
            fail(
                'UNITS_REQUIRED',
                'Declare units for paper output; use 1 for dimensionless quantities.',
                columns=unresolved,
            )
    _comparable(spec, units)


def _comparable(spec: PlotSpec, units: dict[str, str]) -> None:
    kind, ys, x = spec['kind'], y_fields(spec), spec.get('x')
    if (kind == 'line' and len(ys) > 1) or kind in {'overlap', 'animate'}:
        comparable = ys if kind == 'line' else ([x] if x else []) + ys
        if len({units.get(column) for column in comparable}) > 1:
            fail(
                'UNIT_COMPARABILITY',
                'Measurements sharing an axis require the same units; convert during preparation.',
                columns=comparable,
            )
