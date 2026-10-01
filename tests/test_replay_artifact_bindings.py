"""Resealed artifact inventories cannot conceal contradictory scientific sidecars."""

import importlib.resources
import json

import pandas as pd
import pytest

import astetik as ast
from astetik._data import canonical_json, file_digest, json_digest


@pytest.fixture
def bundle(tmp_path):
    source = importlib.resources.files('astetik').joinpath('extras/countries.csv')
    with source.open('rb') as stream:
        countries = pd.read_csv(stream)
    frame = countries.loc[
        countries['alpha-3'].isin(['CAN', 'DEU', 'FIN', 'MEX', 'SWE', 'USA']),
        ['alpha-3', 'region'],
    ].reset_index(drop=True)
    result = ast.render(frame, {'kind': 'count', 'x': 'region', 'key': ['alpha-3']})
    return result.write(tmp_path / 'evidence'), result


def reseal(directory, changed_file):
    receipt = json.loads((directory / 'receipt.json').read_text())
    receipt['output_files'][changed_file] = file_digest(directory / changed_file)
    receipt.pop('bundle_receipt_sha256')
    receipt['bundle_receipt_sha256'] = json_digest(receipt)
    (directory / 'receipt.json').write_text(canonical_json(receipt) + '\n')


@pytest.mark.parametrize('filename', ['marks.json', 'summary.json'])
@pytest.mark.parametrize('strict', [True, False])
def test_resealed_scientific_sidecars_must_match_semantic_receipt(bundle, filename, strict):
    directory, original = bundle
    path = directory / filename
    document = json.loads(path.read_text())
    if filename == 'marks.json':
        next(iter(document.values()))['values']['n'] += 1000
    else:
        position = next(
            index
            for index, column in enumerate(document['columns'])
            if column['name']['value'] == 'n'
        )
        cell = document['rows'][0][position]
        cell['value'] = str(int(cell['value']) + 1000)
    path.write_text(canonical_json(document) + '\n')
    reseal(directory, filename)
    with pytest.raises(ast.AstetikError) as caught:
        ast.replay(directory, strict_environment=strict)
    assert caught.value.code == 'BUNDLE_CHANGED'
    assert caught.value.details['file'] == filename
    assert sum(mark['values']['n'] for mark in original.marks.values()) == 6


@pytest.mark.parametrize('strict', [True, False])
def test_unmodified_scientific_sidecars_replay_exactly(bundle, strict):
    directory, original = bundle
    restored = ast.replay(directory, strict_environment=strict)
    assert restored.marks == original.marks
    pd.testing.assert_frame_equal(restored.table, original.table)
    pd.testing.assert_frame_equal(restored.data, original.data)
    assert restored.receipt['methods'] == original.receipt['methods']
    assert restored.svg_bytes() == original.svg_bytes()
