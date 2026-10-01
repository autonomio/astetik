"""Public physical-axis contracts retain all observations and computed support.

Fixtures retain shipped country identifiers; mathematical displays below do not
interpret those identifiers as empirical measurements or a research study.
"""

import importlib.resources
from typing import cast

import numpy as np
import pandas as pd
import pytest

import astetik as ast
from astetik._spec_types import AxisPolicy


@pytest.fixture
def identifiers() -> pd.DataFrame:
    resource = importlib.resources.files('astetik').joinpath('extras/countries.csv')
    with resource.open('rb') as source:
        countries = pd.read_csv(source)
    selected = countries.loc[countries['alpha-3'].isin(['CAN', 'DEU', 'FIN', 'MEX', 'SWE', 'USA'])]
    frame = (
        selected[['alpha-3', 'country-code', 'region-code', 'region']]
        .rename(
            columns={'alpha-3': 'country', 'country-code': 'code', 'region-code': 'region_code'}
        )
        .reset_index(drop=True)
    )
    frame[['code', 'region_code']] = frame[['code', 'region_code']].astype(float)
    frame.attrs.update(row_keys=['country'], units={'code': '1', 'region_code': '1'})
    assert len(frame) == 6
    return frame


@pytest.fixture
def design() -> ast.Manifest:
    return ast.Manifest(categories={'Europe': 'primary', 'Americas': 'secondary'})


def test_horizontal_bars_apply_numeric_limits_to_physical_x(
    identifiers: pd.DataFrame,
    design: ast.Manifest,
) -> None:
    upper = float(identifiers['code'].max())
    result = ast.render(
        identifiers,
        {
            'kind': 'bar',
            'x': 'region',
            'y': 'code',
            'options': {'orient': 'h', 'estimator': 'mean'},
            'axes': {'x': {'limits': [0, upper]}},
        },
        design,
    )
    axis = result.figure.axes[0]
    assert axis.get_xlim() == (0, upper)
    assert axis.get_xlabel() == 'code'
    assert axis.get_ylabel() == 'region'
    assert {text.get_text() for text in axis.get_yticklabels()} == {'Europe', 'Americas'}
    assert sum(mark['values']['n'] for mark in result.marks.values()) == len(identifiers)
    assert sorted(row for mark in result.marks.values() for row in mark['source_rows']) == list(
        range(6)
    )
    assert result.table['n'].sum() == len(identifiers)


def test_horizontal_category_limits_are_not_interpreted_as_measurement_bounds(
    identifiers: pd.DataFrame,
    design: ast.Manifest,
) -> None:
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(
            identifiers,
            {
                'kind': 'box',
                'x': 'region',
                'y': 'code',
                'options': {'orient': 'h'},
                'axes': {'y': {'limits': [-1, 2]}},
            },
            design,
        )
    assert caught.value.code == 'AXIS_TYPE'
    assert caught.value.details['axis'] == 'y'


def test_horizontal_histogram_count_axis_has_a_computed_domain(identifiers: pd.DataFrame) -> None:
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(
            identifiers,
            {
                'kind': 'hist',
                'x': 'code',
                'options': {'orient': 'h'},
                'axes': {'x': {'limits': [0, 10]}},
            },
        )
    assert caught.value.code == 'DERIVED_AXIS'
    assert caught.value.details['axis'] == 'x'


@pytest.mark.parametrize('policy', [{'scale': 'log'}, {'limits': [0, 1000]}])
def test_datetime_axes_reject_numeric_policies_before_plotting(
    identifiers: pd.DataFrame,
    policy: AxisPolicy,
) -> None:
    identifiers['encoded_at'] = pd.to_datetime(identifiers['code'], unit='D', origin='unix')
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(
            identifiers,
            {'kind': 'line', 'x': 'encoded_at', 'y': 'region_code', 'axes': {'x': policy}},
        )
    assert caught.value.code == 'AXIS_TYPE'
    assert caught.value.details['axis'] == 'x'


def test_linear_datetime_axis_keeps_timestamp_identity_and_stable_order(
    identifiers: pd.DataFrame,
) -> None:
    identifiers['encoded_at'] = pd.to_datetime(identifiers['code'], unit='D', origin='unix')
    result = ast.render(identifiers, {'kind': 'line', 'x': 'encoded_at', 'y': 'region_code'})
    expected = identifiers.sort_values('encoded_at', kind='stable')
    assert [mark['source_rows'][0] for mark in result.marks.values()] == expected.index.tolist()
    assert result.table['encoded_at'].tolist() == [
        value.isoformat() for value in expected['encoded_at']
    ]
    assert result.figure.axes[0].get_xscale() == 'linear'
    assert len(result.table) == len(identifiers)


def test_density_limits_accept_all_computed_support_and_account_for_every_fit_row(
    identifiers: pd.DataFrame,
) -> None:
    unbounded = ast.render(identifiers, {'kind': 'kde', 'x': 'code', 'options': {'cut': 1}})
    bounds = [float(unbounded.table['x'].min()), float(unbounded.table['x'].max())]
    assert bounds[0] < identifiers['code'].min() and bounds[1] > identifiers['code'].max()
    bounded = ast.render(
        identifiers,
        {'kind': 'kde', 'x': 'code', 'options': {'cut': 1}, 'axes': {'x': {'limits': bounds}}},
    )
    assert bounded.figure.axes[0].get_xlim() == tuple(bounds)
    assert bounded.marks == unbounded.marks
    pd.testing.assert_frame_equal(bounded.table, unbounded.table)
    assert all(mark['source_rows'] == list(range(6)) for mark in bounded.marks.values())


@pytest.mark.parametrize(
    'policy,code', [({'limits': [0, 1000]}, 'AXIS_TRUNCATION'), ({'scale': 'log'}, 'LOG_DOMAIN')]
)
def test_comparison_axis_includes_intervals_beyond_positive_observed_values(
    identifiers: pd.DataFrame,
    design: ast.Manifest,
    policy: AxisPolicy,
    code: str,
) -> None:
    specification = {
        'kind': 'comparison',
        'x': 'region',
        'y': 'code',
        'analysis': {
            'method': 'welch',
            'groups': ['Europe', 'Americas'],
            'observation_unit': 'country identifier',
        },
    }
    complete = ast.render(identifiers, specification, design)
    estimates = complete.table.loc[complete.table['mark_kind'] == 'estimate']
    assert estimates['lower'].min() < 0
    assert estimates['upper'].max() > 1000
    assert estimates['n'].sum() == len(identifiers)
    assert len(complete.table) == len(identifiers) + 2
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, {**specification, 'axes': {'y': policy}}, design)
    assert caught.value.code == code
    assert caught.value.details['axis'] == 'y'


def test_bar_limits_cannot_hide_zero_when_all_observations_are_positive(
    identifiers: pd.DataFrame,
    design: ast.Manifest,
) -> None:
    lower, upper = float(identifiers['code'].min()), float(identifiers['code'].max())
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(
            identifiers,
            {'kind': 'bar', 'x': 'region', 'y': 'code', 'axes': {'y': {'limits': [lower, upper]}}},
            design,
        )
    assert caught.value.code == 'AXIS_TRUNCATION'
    assert caught.value.details['axis'] == 'y'
    assert cast(list[float], caught.value.details['rendered'])[0] == 0


def test_missing_policy_precedes_log_checks_and_preserves_original_row_accounting(
    identifiers: pd.DataFrame,
) -> None:
    identifiers.loc[0, 'code'] = 0
    identifiers.loc[0, 'region_code'] = np.nan
    specification = {
        'kind': 'scat',
        'x': 'code',
        'y': 'region_code',
        'axes': {'x': {'scale': 'log'}},
    }
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, specification)
    assert caught.value.code == 'MISSING_DATA'
    result = ast.render(
        identifiers,
        {
            **specification,
            'missing': 'drop',
            'missing_reason': 'Deliberately invalid identifier fixture lacks a region code.',
        },
    )
    assert result.figure.axes[0].get_xscale() == 'log'
    assert result.receipt['observations']['used'] == 5
    assert result.receipt['observations']['excluded'] == [
        {'country': identifiers.loc[0, 'country']}
    ]
    assert sorted(mark['source_rows'][0] for mark in result.marks.values()) == list(range(1, 6))
    assert sorted(rows[0] for rows in result.table['source_rows']) == list(range(1, 6))
    assert {mark['source_keys'][0]['country'] for mark in result.marks.values()} == set(
        identifiers.loc[1:, 'country']
    )
    pd.testing.assert_frame_equal(result.data, identifiers)


def test_facets_share_declared_domains_without_duplication_or_local_clipping(
    identifiers: pd.DataFrame,
    design: ast.Manifest,
) -> None:
    result = ast.render(
        identifiers,
        {
            'kind': 'scat',
            'x': 'code',
            'y': 'region_code',
            'col': 'region',
            'axes': {'x': {'limits': [0, 1000]}, 'y': {'limits': [0, 150]}},
        },
        design,
    )
    assert len(result.figure.axes) == 2
    assert all(axis.get_xlim() == (0, 1000) for axis in result.figure.axes)
    assert all(axis.get_ylim() == (0, 150) for axis in result.figure.axes)
    assert sorted(mark['source_rows'][0] for mark in result.marks.values()) == list(range(6))
    assert len(result.table) == len(identifiers)
    assert {tuple(mark['facet'].values()) for mark in result.marks.values()} == {
        ('Europe',),
        ('Americas',),
    }
