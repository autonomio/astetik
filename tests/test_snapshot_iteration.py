"""Fast snapshots retain exact native country cells, schema and empty shapes."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from astetik._cells import encode_cell
from astetik._data import data_digest, frame_from_payload, frame_payload


@pytest.mark.parametrize('view', ['native', 'nullable', 'categorical', 'duplicate', 'zero_columns', 'zero_rows'])
def test_country_row_iteration_preserves_exact_scalar_snapshot(view: str) -> None:
    data = pd.read_csv(Path(__file__).resolve().parents[1] / 'astetik' / 'extras' / 'countries.csv')
    data.index = pd.Index(data['alpha-3'], name='country_identity')
    if view == 'nullable':
        data['country-code'] = data['country-code'].astype('UInt16')
        data['region'] = data['region'].astype('string')
        data['region-code'] = data['region-code'].astype('Float32')
    elif view == 'categorical':
        data['region'] = pd.Categorical(data['region'], ordered=True)
    elif view == 'duplicate':
        data = data[['alpha-3', 'alpha-3', 'country-code']]
    elif view == 'zero_columns':
        data = data.iloc[:, :0]
    elif view == 'zero_rows':
        data = data.iloc[:0]
    expected = [[encode_cell(data.iat[row, column]) for column in range(data.shape[1])]
                for row in range(data.shape[0])]
    payload = frame_payload(data)
    assert payload['rows'] == expected
    assert len(payload['rows']) == len(data)
    restored = frame_from_payload(payload)
    pd.testing.assert_frame_equal(restored, data)
    assert frame_payload(restored) == payload
    assert data_digest(restored) == data_digest(data)
