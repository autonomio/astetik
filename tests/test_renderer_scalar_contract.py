"""Renderer provenance rejects ambiguous keys and retains valid country metadata."""

from __future__ import annotations

import importlib.resources
from copy import deepcopy
from pathlib import Path
from types import MappingProxyType

import numpy as np
import pandas as pd
import pytest

import astetik as ast
from astetik._render_context import Recorder


@pytest.fixture
def countries() -> pd.DataFrame:
    resource = importlib.resources.files('astetik').joinpath('extras/countries.csv')
    with resource.open('rb') as source:
        retained = pd.read_csv(source)
    frame = retained.loc[
        retained['alpha-3'].isin(['ALA', 'CAN', 'DEU', 'FIN', 'USA']),
        ['alpha-3', 'name', 'country-code'],
    ].reset_index(drop=True)
    frame.attrs.update(row_keys=['alpha-3'], units={'country-code': '1'})
    assert len(frame) == 5
    return frame


@pytest.mark.parametrize(
    'metadata',
    [
        {1: 'CAN', '1': 'FIN'},
        {1: 'CAN'},
        {None: 'CAN'},
        {False: 'CAN', 'False': 'FIN'},
        {('country',): 'CAN'},
        {np.int64(1): 'CAN', '1': 'FIN'},
        {'nested': {1: 'CAN', '1': 'FIN'}},
        {'nested': [{1: 'CAN', '1': 'FIN'}]},
        {'nested': ({1: 'CAN', '1': 'FIN'},)},
        MappingProxyType({1: 'CAN', '1': 'FIN'}),
    ],
)
def test_recording_rejects_nonstring_keys_without_partial_evidence(metadata: object) -> None:
    recorder = Recorder()
    recorder.mark('observation', {'country': 'CAN'}, [0], 'identity')
    previous_marks = deepcopy(recorder.marks)
    previous_table = recorder.table()
    with pytest.raises(ValueError, match='string keys'):
        recorder.mark('observation', {'retained_metadata': metadata}, [1], 'identity')
    assert recorder.marks == previous_marks
    pd.testing.assert_frame_equal(recorder.table(), previous_table)


def test_nested_string_keys_preserve_country_values_and_native_scalar_normalization(
    countries: pd.DataFrame,
) -> None:
    metadata = MappingProxyType(
        {
            'countries': tuple(
                MappingProxyType(
                    {'country': row['alpha-3'], 'name': row['name'], 'code': row['country-code']}
                )
                for _, row in countries.iterrows()
            ),
            '0': None,
            '1': True,
        }
    )
    recorder = Recorder()
    mark = recorder.mark('metadata', {'retained_metadata': metadata}, list(range(5)), 'identity')
    expected = {
        'countries': [
            {'country': row['alpha-3'], 'name': row['name'], 'code': int(row['country-code'])}
            for _, row in countries.iterrows()
        ],
        '0': None,
        '1': True,
    }
    assert mark['values'] == {'retained_metadata': expected}
    assert recorder.table().iloc[0]['retained_metadata'] == expected
    assert mark['source_rows'] == list(range(5))
    assert isinstance(metadata['countries'], tuple)
    assert metadata['0'] is None and metadata['1'] is True


def test_public_country_marks_and_bundle_replay_remain_exact(
    countries: pd.DataFrame, tmp_path: Path
) -> None:
    result = ast.render(
        countries,
        {'kind': 'hist', 'x': 'country-code', 'paper': True, 'options': {'bins': 4}},
    )
    assert sum(mark['values']['n'] for mark in result.marks.values()) == len(countries)
    assert sorted(row for mark in result.marks.values() for row in mark['source_rows']) == list(
        range(5)
    )
    bundle = result.write(tmp_path / 'country-evidence')
    replayed = ast.replay(bundle)
    assert replayed.result_id == result.result_id
    assert replayed.marks == result.marks
    pd.testing.assert_frame_equal(replayed.table, result.table)
    pd.testing.assert_frame_equal(replayed.data, countries)
    assert replayed.svg_bytes() == result.svg_bytes()
