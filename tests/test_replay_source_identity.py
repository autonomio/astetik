"""Retained file-origin declarations stay bound while evidence bundles relocate."""

from __future__ import annotations

import importlib.resources
import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

import astetik as ast
from astetik._data import canonical_json, json_digest


@pytest.fixture(scope='module')
def file_bundle(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, ast.EvidenceResult, bytes]:
    source = importlib.resources.files('astetik').joinpath('extras/countries.csv')
    with source.open('rb') as stream:
        countries = pd.read_csv(stream)
    frame = countries.loc[
        countries['alpha-3'].isin(['CAN', 'DEU', 'FIN', 'MEX', 'SWE', 'USA']),
        ['alpha-3', 'region', 'country-code'],
    ].reset_index(drop=True)
    directory = tmp_path_factory.mktemp('retained-file-origin')
    origin = directory / 'countries.csv'
    frame.to_csv(origin, index=False, lineterminator='\n', float_format='%.17g')
    content = origin.read_bytes()
    result = ast.render(origin, {'kind': 'count', 'x': 'region', 'key': ['alpha-3']})
    return result.write(directory / 'evidence'), result, content


def _reseal_receipt(directory: Path, receipt: dict[str, object]) -> None:
    receipt.pop('bundle_receipt_sha256')
    receipt['bundle_receipt_sha256'] = json_digest(receipt)
    (directory / 'receipt.json').write_text(canonical_json(receipt) + '\n', encoding='utf-8')


@pytest.mark.parametrize('strict', [True, False])
@pytest.mark.parametrize(('field', 'value'), [
    ('kind', 'pandas.DataFrame'),
    ('path', 'forged-origin.csv'),
    ('file_sha256', '0' * 64),
    ('sha256', '0' * 64),
    ('rows', 0),
    ('reader', 'polars'),
    ('format', 'parquet'),
    ('key', ['alpha-3']),
    ('schema', []),
])
def test_resealed_source_claim_cannot_retain_original_result_identity(
    file_bundle: tuple[Path, ast.EvidenceResult, bytes], tmp_path: Path,
    field: str, value: object, strict: bool,
) -> None:
    original, result, _ = file_bundle
    directory = Path(shutil.copytree(original, tmp_path / 'forged-origin'))
    receipt = json.loads((directory / 'receipt.json').read_text(encoding='utf-8'))
    assert receipt['source'][field] != value
    receipt['source'][field] = value
    _reseal_receipt(directory, receipt)
    with pytest.raises(ast.AstetikError) as caught:
        ast.replay(directory, strict_environment=strict)
    assert caught.value.code == 'BUNDLE_CHANGED'
    assert caught.value.details['field'] == 'result_id'
    assert receipt['result_id'] == result.result_id


def test_identical_country_files_at_distinct_origins_have_distinct_result_identity(
    file_bundle: tuple[Path, ast.EvidenceResult, bytes], tmp_path: Path,
) -> None:
    _, original, content = file_bundle
    other_source = tmp_path / 'same-country-observations.csv'
    other_source.write_bytes(content)
    other = ast.render(other_source, original.spec, original.manifest)
    pd.testing.assert_frame_equal(other.data, original.data)
    pd.testing.assert_frame_equal(other.table, original.table)
    assert other.marks == original.marks
    assert other.receipt['input_sha256'] == original.receipt['input_sha256']
    assert other.receipt['source']['file_sha256'] == original.receipt['source']['file_sha256']
    assert other.receipt['source']['path'] != original.receipt['source']['path']
    assert other.result_id != original.result_id


def test_relocated_bundle_retains_exact_origin_when_original_file_is_unavailable(
    file_bundle: tuple[Path, ast.EvidenceResult, bytes], tmp_path: Path,
) -> None:
    source, original, _ = file_bundle
    moved = Path(shutil.copytree(source, tmp_path / 'different-project' / 'countries'))
    origin = Path(original.receipt['source']['path'])
    origin.unlink()
    assert not origin.exists()
    for strict in (True, False):
        restored = ast.replay(moved, strict_environment=strict)
        assert restored.receipt['source'] == original.receipt['source']
        assert restored.result_id == original.result_id
        assert restored.marks == original.marks
        pd.testing.assert_frame_equal(restored.data, original.data)
        pd.testing.assert_frame_equal(restored.table, original.table)
        assert restored.svg_bytes() == original.svg_bytes()
        for filename, frame in [('input.csv', original.data), ('summary.csv', original.table)]:
            expected = frame.to_csv(index=True, lineterminator='\n', float_format='%.17g')
            assert (moved / filename).read_bytes() == expected.encode('utf-8')
