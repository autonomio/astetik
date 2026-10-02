"""Axis policies account for observations, computed support and zero baselines."""

from __future__ import annotations

from typing import cast

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from pandas.api.types import is_numeric_dtype

from ._measurements import y_fields
from ._spec import fail
from ._spec_types import AxisPolicy, Dimension, PlotSpec
from ._types import FloatArray


def variables(spec: PlotSpec) -> tuple[dict[Dimension, list[str | None]], set[Dimension], bool]:
    kind, x, ys = spec['kind'], spec.get('x'), y_fields(spec)
    fields: dict[Dimension, list[str | None]] = {'x': [x] if x else [], 'y': list(ys)}
    derived: set[Dimension] = set()
    if kind in {'count', 'multicount', 'hist'} or (kind in {'kde', 'multikde'} and not ys):
        fields['y'] = []
        derived.add('y')
    if kind == 'overlap':
        fields = (
            {'x': [x, *ys], 'y': [None]}
            if spec['options'].get('orient') == 'h'
            else {'x': [None], 'y': [x, *ys]}
        )
    if kind == 'compare':
        fields = {'x': [x, *ys], 'y': [None]}
    categorical = {
        'bar',
        'bartwo',
        'bargrid',
        'box',
        'violin',
        'strip',
        'swarm',
        'grid',
        'count',
        'multicount',
        'comparison',
    }
    if kind in categorical:
        fields['x'] = [None]
    if kind == 'animate':
        fields = {'x': [], 'y': [x, *ys]}
        derived.add('x')
    horizontal = spec['options'].get('orient') == 'h' and kind in categorical | {'hist'}
    if horizontal:
        fields = {'x': fields['y'], 'y': fields['x']}
        derived = {'x' if dimension == 'y' else 'y' for dimension in derived}
    if kind in {'corr', 'roc', 'pie', 'world', 'table', 'text'}:
        derived.update({'x', 'y'})
    if kind == 'oned':
        derived.add('y')
    return fields, derived, horizontal


def _custom(policy: AxisPolicy) -> bool:
    return policy.get('scale', 'linear') != 'linear' or policy.get('limits') is not None


def _field(data: pd.DataFrame, field: str | None, policy: AxisPolicy, dimension: Dimension) -> None:
    if field is None or not is_numeric_dtype(data[field]):
        if _custom(policy):
            fail(
                'AXIS_TYPE',
                'Numeric scale/limits cannot be applied to a categorical or datetime axis.',
                axis=dimension,
            )
        return
    values = data[field].to_numpy(float)
    if policy.get('scale') == 'log' and (values <= 0).any():
        fail('LOG_DOMAIN', 'Logarithmic axes require strictly positive values.', column=field)
    limits = policy.get('limits')
    if limits and (min(values) < limits[0] or max(values) > limits[1]):
        fail(
            'AXIS_TRUNCATION',
            'Axis limits would conceal observations.',
            column=field,
            observed=[float(min(values)), float(max(values))],
        )


def validate(data: pd.DataFrame, spec: PlotSpec) -> None:
    fields, derived, horizontal = variables(spec)
    policies = spec.get('axes', {})
    for dimension, policy in policies.items():
        if dimension in derived:
            if _custom(policy):
                fail(
                    'DERIVED_AXIS',
                    'This axis has a fixed or computed domain; custom scale/limits are unsupported.',
                    axis=dimension,
                )
            continue
        for field in fields[dimension]:
            _field(data, field, policy, dimension)
    if spec['kind'] in {
        'bar',
        'bartwo',
        'bargrid',
        'count',
        'multicount',
        'hist',
        'overlap',
        'animate',
    }:
        dimension: Dimension = (
            'x'
            if horizontal or (spec['kind'] == 'overlap' and spec['options'].get('orient') == 'h')
            else 'y'
        )
        if policies.get(dimension, {}).get('scale') == 'log':
            fail(
                'BAR_BASELINE',
                'Bars require a visible zero baseline; use a point or line representation for a logarithmic value axis.',
            )


def validate_rendered(figure: Figure, spec: PlotSpec) -> None:
    """Include computed intervals, fitted values, density support and baselines."""
    for dimension, policy in spec.get('axes', {}).items():
        limits = policy.get('limits')
        if limits is None and policy.get('scale') != 'log':
            continue
        for axis in figure.axes:
            if not axis.get_visible() or hasattr(axis, '_colorbar'):
                continue
            bounds = cast(
                FloatArray, axis.dataLim.intervalx if dimension == 'x' else axis.dataLim.intervaly
            )
            if policy.get('scale') == 'log' and np.isfinite(bounds).all() and bounds[0] <= 0:
                fail(
                    'LOG_DOMAIN',
                    'Logarithmic axes cannot conceal nonpositive computed values or intervals.',
                    axis=dimension,
                )
            if (
                limits is not None
                and np.isfinite(bounds).all()
                and (bounds[0] < limits[0] - 1e-12 or bounds[1] > limits[1] + 1e-12)
            ):
                fail(
                    'AXIS_TRUNCATION',
                    'Axis limits would conceal rendered observations or computed intervals.',
                    axis=dimension,
                    rendered=[float(v) for v in bounds],
                )
