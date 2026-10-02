"""Descriptive displays reject malformed analysis declarations before inference."""

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
        ['alpha-3', 'region', 'country-code', 'region-code'],
    ].reset_index(drop=True)
    frame.attrs['row_keys'] = ['alpha-3']
    assert len(frame) == 4
    return frame


@pytest.mark.parametrize('kind', ['count', 'table', 'corr'])
@pytest.mark.parametrize('analysis', [False, 0, [], '', True, 1, 'welch'])
def test_descriptive_analysis_requires_an_object(
    identifiers: pd.DataFrame, kind: str, analysis: object
) -> None:
    spec = {'kind': kind, 'analysis': analysis}
    if kind == 'count':
        spec['x'] = 'region'
    before = identifiers.copy(deep=True)
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, spec)
    assert caught.value.code == 'ANALYSIS_SCHEMA'
    pd.testing.assert_frame_equal(identifiers, before)


@pytest.mark.parametrize('kind', ['count', 'table', 'corr'])
@pytest.mark.parametrize('analysis', [None, {}])
def test_descriptive_default_analysis_retains_exact_evidence(
    identifiers: pd.DataFrame, kind: str, analysis: dict[str, object] | None
) -> None:
    spec = {'kind': kind}
    if kind == 'count':
        spec['x'] = 'region'
    default = ast.render(identifiers, spec)
    explicit = ast.render(identifiers, {**spec, 'analysis': analysis})
    assert explicit.receipt['analysis'] is None
    assert explicit.receipt['methods']['analysis'] is None
    assert explicit.marks == default.marks
    pd.testing.assert_frame_equal(explicit.table, default.table)
    assert explicit.receipt['source'] == default.receipt['source']
    assert explicit.receipt['observations'] == default.receipt['observations']
    assert explicit.receipt['input_sha256'] == default.receipt['input_sha256']
