"""Numeric plot declarations reject booleans without changing retained values."""

from __future__ import annotations

import importlib.resources

import pandas as pd
import pytest

import astetik as ast
from astetik._types import JsonObject


@pytest.fixture
def countries() -> pd.DataFrame:
    resource = importlib.resources.files('astetik').joinpath('extras/countries.csv')
    with resource.open('rb') as source:
        retained = pd.read_csv(source)
    frame = retained.loc[
        retained['alpha-3'].isin(['ALA', 'CAN', 'DEU', 'FIN', 'USA']),
        ['alpha-3', 'country-code', 'region-code', 'region'],
    ].reset_index(drop=True)
    frame.attrs.update(row_keys=['alpha-3'], units={'country-code': '1', 'region-code': '1'})
    assert len(frame) == 5
    return frame


def _spec(kind: str, field: str, value: object) -> dict[str, object]:
    spec: dict[str, object] = {'kind': kind, 'x': 'country-code', 'options': {field: value}}
    if kind in ('violin', 'strip', 'grid'):
        spec.update(x='region', y='country-code')
    if field == 'col_wrap':
        spec.update(y='region-code', col='region')
    return spec


@pytest.mark.parametrize(
    'kind,field',
    [
        ('kde', 'cut'),
        ('multikde', 'cut'),
        ('violin', 'cut'),
        ('strip', 'jitter'),
        ('grid', 'jitter'),
        ('scat', 'col_wrap'),
    ],
)
@pytest.mark.parametrize('value', [False, True])
def test_boolean_is_not_a_scientific_numeric_option(
    countries: pd.DataFrame, kind: str, field: str, value: bool
) -> None:
    original = countries.copy(deep=True)
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(countries, _spec(kind, field, value))
    assert caught.value.code == 'PLOT_CONTRACT'
    assert field in caught.value.details['reason']
    pd.testing.assert_frame_equal(countries, original)


@pytest.mark.parametrize('kind,field', [('kde', 'cut'), ('violin', 'cut'), ('strip', 'jitter')])
def test_numeric_zero_representations_preserve_computed_values_and_origins(
    countries: pd.DataFrame, kind: str, field: str
) -> None:
    integer = ast.render(countries, _spec(kind, field, 0))
    floating = ast.render(countries, _spec(kind, field, 0.0))
    def retained(result: ast.EvidenceResult) -> dict[str, JsonObject]:
        return {
            name: {key: value for key, value in mark.items() if key != 'computation'}
            for name, mark in result.marks.items()
        }
    assert retained(floating) == retained(integer)
    pd.testing.assert_frame_equal(
        floating.table.drop(columns='computation'), integer.table.drop(columns='computation')
    )
    assert type(integer.spec['options'][field]) is int
    assert type(floating.spec['options'][field]) is float
    pd.testing.assert_frame_equal(floating.data, countries)
    assert floating.svg_bytes() == integer.svg_bytes()
    assert floating.receipt['observations']['used'] == len(countries)
    assert floating.receipt['input_sha256'] == integer.receipt['input_sha256']


def test_integer_column_wrap_retains_every_country_in_its_facet(countries: pd.DataFrame) -> None:
    result = ast.render(countries, _spec('scat', 'col_wrap', 1))
    assert len(result.figure.axes) == 2
    positions = [axis.get_position().bounds for axis in result.figure.axes]
    assert positions[0][0] == pytest.approx(positions[1][0])
    assert positions[0][1] != pytest.approx(positions[1][1])
    assert sorted(mark['source_rows'][0] for mark in result.marks.values()) == list(range(5))
    assert len(result.table) == len(countries)
    pd.testing.assert_frame_equal(result.data, countries)
