"""Legacy axis spelling preserves invalid values for public schema rejection."""

from __future__ import annotations

import importlib.resources

import pandas as pd
import pytest

import astetik as ast


@pytest.fixture
def identifiers() -> pd.DataFrame:
    resource = importlib.resources.files('astetik').joinpath('extras/countries.csv')
    with resource.open('rb') as source:
        countries = pd.read_csv(source)
    frame = countries.loc[
        countries['alpha-3'].isin(['ALA', 'CAN', 'DEU', 'FIN', 'USA']),
        ['alpha-3', 'country-code', 'region-code'],
    ].reset_index(drop=True)
    frame.attrs.update(row_keys=['alpha-3'], units={'country-code': '1', 'region-code': '1'})
    assert len(frame) == 5
    return frame


@pytest.mark.parametrize('dimension', ['x', 'y'])
@pytest.mark.parametrize(
    'suffix,value,code',
    [
        ('limit', [], 'AXIS_LIMITS'),
        ('limit', False, 'AXIS_LIMITS'),
        ('limit', 0, 'AXIS_LIMITS'),
        ('limit', {}, 'AXIS_LIMITS'),
        ('limit', '', 'AXIS_LIMITS'),
        ('scale', '', 'AXIS_SCALE'),
        ('scale', False, 'AXIS_SCALE'),
        ('scale', 0, 'AXIS_SCALE'),
        ('scale', {}, 'AXIS_SCALE'),
    ],
)
def test_falsy_legacy_axis_values_reach_schema_validation(
    identifiers: pd.DataFrame, dimension: str, suffix: str, value: object, code: str
) -> None:
    original = identifiers.copy(deep=True)
    with pytest.raises(ast.AstetikError) as caught:
        ast.scat(
            identifiers,
            x='country-code',
            y='region-code',
            **{f'{dimension}_{suffix}': value},
        )
    assert caught.value.code == code
    pd.testing.assert_frame_equal(identifiers, original)


@pytest.mark.parametrize('axes', [{}, {'x': {'scale': 'log'}, 'y': {'scale': 'log'}}])
def test_null_legacy_axis_values_retain_defaults_and_existing_policies(
    identifiers: pd.DataFrame, axes: dict[str, object]
) -> None:
    default = ast.scat(identifiers, x='country-code', y='region-code', axes=axes)
    nullable = ast.scat(
        identifiers,
        x='country-code',
        y='region-code',
        axes=axes,
        x_limit=None,
        y_limit=None,
        x_scale=None,
        y_scale=None,
    )
    assert nullable.marks == default.marks
    pd.testing.assert_frame_equal(nullable.table, default.table)
    assert nullable.receipt == default.receipt
    assert nullable.figure.axes[0].get_xscale() == default.figure.axes[0].get_xscale()
    assert nullable.figure.axes[0].get_yscale() == default.figure.axes[0].get_yscale()


@pytest.mark.parametrize('dimension,column', [('x', 'country-code'), ('y', 'region-code')])
def test_valid_legacy_limits_and_scale_override_without_losing_observations(
    identifiers: pd.DataFrame, dimension: str, column: str
) -> None:
    limits = [float(identifiers[column].min()), float(identifiers[column].max())]
    policy = {'axes': {dimension: {'scale': 'log'}}}
    default = ast.scat(identifiers, x='country-code', y='region-code')
    bounded = ast.scat(
        identifiers,
        x='country-code',
        y='region-code',
        **policy,
        **{f'{dimension}_limit': limits, f'{dimension}_scale': 'linear'},
    )
    axis = bounded.figure.axes[0]
    assert (axis.get_xlim() if dimension == 'x' else axis.get_ylim()) == tuple(limits)
    assert (axis.get_xscale() if dimension == 'x' else axis.get_yscale()) == 'linear'
    assert bounded.marks == default.marks
    pd.testing.assert_frame_equal(bounded.table, default.table)
    pd.testing.assert_frame_equal(bounded.data, identifiers)
    assert sorted(mark['source_rows'][0] for mark in bounded.marks.values()) == list(range(5))
    assert bounded.receipt['source'] == default.receipt['source']
    assert bounded.receipt['observations'] == default.receipt['observations']
