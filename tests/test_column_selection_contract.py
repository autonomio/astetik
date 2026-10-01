"""Explicit column selectors never fall through malformed values to all columns."""

import importlib.resources

import pandas as pd
import pytest

import astetik as ast


@pytest.fixture
def identifiers() -> pd.DataFrame:
    source = importlib.resources.files('astetik').joinpath('extras/countries.csv')
    with source.open('rb') as stream:
        countries = pd.read_csv(stream)
    frame = countries.loc[
        countries['alpha-3'].isin(['CAN', 'DEU', 'FIN', 'USA']),
        ['alpha-3', 'country-code', 'region-code'],
    ].reset_index(drop=True)
    frame.attrs['row_keys'] = ['alpha-3']
    assert len(frame) == 4
    return frame


@pytest.mark.parametrize('kind', ['table', 'corr'])
@pytest.mark.parametrize('columns', [False, 0, {}, '', True, 1, ['country-code', False]])
def test_malformed_column_selection_fails_before_rendering(
    identifiers: pd.DataFrame, kind: str, columns: object
) -> None:
    before = identifiers.copy(deep=True)
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, {'kind': kind, 'columns': columns})
    assert caught.value.code == 'COLUMN_SCHEMA'
    pd.testing.assert_frame_equal(identifiers, before)


@pytest.mark.parametrize('kind', ['table', 'corr'])
@pytest.mark.parametrize('columns', [None, []])
def test_default_column_selection_keeps_exact_observation_evidence(
    identifiers: pd.DataFrame, kind: str, columns: list[str] | None
) -> None:
    default = ast.render(identifiers, {'kind': kind})
    explicit = ast.render(identifiers, {'kind': kind, 'columns': columns})
    assert explicit.marks == default.marks
    pd.testing.assert_frame_equal(explicit.table, default.table)
    pd.testing.assert_frame_equal(explicit.data, identifiers)
    assert explicit.receipt['source'] == default.receipt['source']
    assert explicit.receipt['observations'] == default.receipt['observations']
    assert explicit.receipt['input_sha256'] == default.receipt['input_sha256']


@pytest.mark.parametrize('kind', ['table', 'corr'])
def test_tuple_selection_keeps_prior_json_normalization(
    identifiers: pd.DataFrame, kind: str
) -> None:
    fields = ['country-code', 'region-code']
    selected = ast.render(identifiers, {'kind': kind, 'columns': fields})
    normalized = ast.render(identifiers, {'kind': kind, 'columns': tuple(fields)})
    assert normalized.marks == selected.marks
    pd.testing.assert_frame_equal(normalized.table, selected.table)
    assert normalized.receipt == selected.receipt
    if kind == 'table':
        assert normalized.table.columns.tolist() == fields
        pd.testing.assert_frame_equal(normalized.table, identifiers[fields])
