"""Inherited row-key declarations obey the public replay specification grammar."""

import importlib.resources

import pandas as pd
import pytest

import astetik as ast


@pytest.fixture
def countries():
    source = importlib.resources.files('astetik').joinpath('extras/countries.csv')
    with source.open('rb') as stream:
        retained = pd.read_csv(stream)
    return retained.loc[retained['alpha-3'].isin(['FIN', 'SWE']), ['alpha-3', 'region']].copy()


@pytest.mark.parametrize('field', ['key', 'row_keys'])
@pytest.mark.parametrize('label', [7, 0.5, False])
def test_nonstring_inherited_keys_fail_before_producing_unreplayable_evidence(countries, field, label):
    countries = countries.rename(columns={'alpha-3': label})
    countries.attrs[field] = [label]
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(countries, {'kind': 'count', 'x': 'region'})
    assert caught.value.code == 'INVALID_METADATA'
    assert countries.attrs[field] == [label]


@pytest.mark.parametrize('field', ['key', 'row_keys'])
def test_string_inherited_keys_match_explicit_keys_and_strictly_replay(countries, field, tmp_path):
    countries.attrs[field] = ['alpha-3']
    inherited = ast.render(countries, {'kind': 'count', 'x': 'region'})
    explicit = ast.render(countries, {'kind': 'count', 'x': 'region', 'key': ['alpha-3']})
    assert inherited.spec['key'] == ['alpha-3']
    assert inherited.marks == explicit.marks
    assert inherited.receipt['input_sha256'] == explicit.receipt['input_sha256']
    bundle = inherited.write(tmp_path / 'country-evidence')
    replayed = ast.replay(bundle)
    assert replayed.result_id == inherited.result_id
    assert replayed.marks == inherited.marks
    pd.testing.assert_frame_equal(replayed.data, inherited.data)
