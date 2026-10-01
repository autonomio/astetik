"""Standalone snapshot loading rejects ambiguous retained country evidence."""

import importlib.resources

import pandas as pd
import pytest

from astetik._data import canonical_json, frame_payload, load_snapshot
from astetik._errors import AstetikError


@pytest.fixture
def retained(tmp_path):
    source = importlib.resources.files('astetik').joinpath('extras/countries.csv')
    with source.open('rb') as stream:
        countries = pd.read_csv(stream)
    frame = countries.loc[countries['alpha-3'].isin(['FIN', 'SWE']), ['alpha-3', 'region']]
    path = tmp_path / 'input.json'
    path.write_text(canonical_json(frame_payload(frame)), encoding='utf-8')
    return path, frame


@pytest.mark.parametrize('nested', [False, True])
def test_standalone_snapshot_rejects_duplicate_fields_before_reconstruction(retained, nested):
    path, _ = retained
    text = path.read_text(encoding='utf-8')
    if nested:
        text = text.replace('"class":', '"class":"forged-index","class":', 1)
    else:
        text = '{"format":"forged-format",' + text[1:]
    path.write_text(text, encoding='utf-8')
    with pytest.raises(AstetikError) as caught:
        load_snapshot(path)
    assert caught.value.code == 'INVALID_SNAPSHOT'


@pytest.mark.parametrize('constant', ['NaN', 'Infinity', '-Infinity'])
def test_standalone_snapshot_rejects_nonfinite_values_even_in_overwritten_fields(retained, constant):
    path, _ = retained
    text = path.read_text(encoding='utf-8')
    path.write_text('{"attrs":{"discarded":' + constant + '},' + text[1:], encoding='utf-8')
    with pytest.raises(AstetikError) as caught:
        load_snapshot(path)
    assert caught.value.code == 'INVALID_SNAPSHOT'


def test_standalone_snapshot_retains_unmodified_country_evidence(retained):
    path, original = retained
    pd.testing.assert_frame_equal(load_snapshot(path), original)
