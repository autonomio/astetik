"""Retained country evidence rejects ambiguous JSON even after inventory resealing."""

from __future__ import annotations

import hashlib
import importlib.resources
import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

import astetik as ast


@pytest.fixture(scope='module')
def retained_bundle(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, ast.EvidenceResult]:
    source = importlib.resources.files('astetik').joinpath('extras/countries.csv')
    with source.open('rb') as stream:
        countries = pd.read_csv(stream)
    frame = countries.loc[
        countries['alpha-3'].isin(['ALA', 'CAN', 'DEU', 'FIN', 'USA']),
        ['alpha-3', 'name', 'country-code'],
    ].reset_index(drop=True)
    frame.attrs.update(row_keys=['alpha-3'], units={'country-code': '1'})
    assert len(frame) == 5
    assert 'Åland Islands' in frame['name'].tolist()
    result = ast.render(
        frame,
        {
            'kind': 'hist',
            'x': 'country-code',
            'paper': True,
            'options': {'bins': 4},
            'axes': {'x': {'scale': 'linear'}, 'y': {'scale': 'linear'}},
        },
    )
    return result.write(tmp_path_factory.mktemp('retained-json') / 'bundle'), result


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def _reseal(bundle: Path, name: str) -> None:
    if name == 'receipt.json':
        return
    path = bundle / 'receipt.json'
    receipt = json.loads(path.read_text(encoding='utf-8'))
    receipt['output_files'][name] = hashlib.sha256((bundle / name).read_bytes()).hexdigest()
    receipt.pop('bundle_receipt_sha256')
    receipt['bundle_receipt_sha256'] = hashlib.sha256(_canonical(receipt).encode('utf-8')).hexdigest()
    path.write_text(_canonical(receipt) + '\n', encoding='utf-8')


def _inject_duplicate(path: Path, section: str | None, field: str, shadow: str | int) -> None:
    original = path.read_text(encoding='utf-8')
    marker = '{' if section is None else f'"{section}":{{'
    assert marker in original
    changed = original.replace(marker, marker + f'"{field}":{json.dumps(shadow)},', 1)
    assert json.loads(changed) == json.loads(original), 'Default JSON parsing hides the shadow value'
    path.write_text(changed, encoding='utf-8')


@pytest.mark.parametrize(
    'mutation',
    [
        ('receipt.json', None, 'kind', 'forged'),
        ('receipt.json', 'observations', 'used', 0),
        ('spec.json', None, 'kind', 'forged'),
        ('spec.json', 'options', 'bins', 0),
        ('manifest.json', None, 'schema_version', 'unsupported'),
        ('manifest.json', 'colors', 'primary', '#FFFFFF'),
        ('receipt.json', None, r'ki\u006ed', 'forged'),
        ('manifest.json', 'colors', r'pr\u0069mary', '#FFFFFF'),
    ],
)
def test_duplicate_document_fields_cannot_be_replayed_after_resealing(
    retained_bundle: tuple[Path, ast.EvidenceResult],
    tmp_path: Path,
    mutation: tuple[str, str | None, str, str | int],
) -> None:
    source, _ = retained_bundle
    bundle = Path(shutil.copytree(source, tmp_path / 'duplicate'))
    name, section, field, shadow = mutation
    _inject_duplicate(bundle / name, section, field, shadow)
    _reseal(bundle, name)
    with pytest.raises(ast.AstetikError) as caught:
        ast.replay(bundle)
    assert caught.value.code == 'BUNDLE_DOCUMENT'
    assert 'Duplicate JSON field' in caught.value.details['reason']


@pytest.mark.parametrize('name', ['receipt.json', 'spec.json', 'manifest.json'])
@pytest.mark.parametrize('constant', ['NaN', 'Infinity', '-Infinity'])
def test_nonfinite_constants_cannot_hide_behind_last_value_wins(
    retained_bundle: tuple[Path, ast.EvidenceResult], tmp_path: Path, name: str, constant: str
) -> None:
    source, _ = retained_bundle
    bundle = Path(shutil.copytree(source, tmp_path / 'nonfinite'))
    path = bundle / name
    original = path.read_text(encoding='utf-8')
    field = 'schema_version' if name == 'manifest.json' else 'kind'
    changed = '{"' + field + '":' + constant + ',' + original[1:]
    assert json.loads(changed) == json.loads(original)
    path.write_text(changed, encoding='utf-8')
    _reseal(bundle, name)
    with pytest.raises(ast.AstetikError) as caught:
        ast.replay(bundle)
    assert caught.value.code == 'BUNDLE_DOCUMENT'
    assert 'Nonfinite JSON constant' in caught.value.details['reason']
    assert constant in caught.value.details['reason']


def test_finite_unicode_bundle_preserves_exact_strict_replay(
    retained_bundle: tuple[Path, ast.EvidenceResult],
) -> None:
    bundle, original = retained_bundle
    replayed = ast.replay(bundle)
    assert replayed.result_id == original.result_id
    assert replayed.marks == original.marks
    pd.testing.assert_frame_equal(replayed.table, original.table)
    pd.testing.assert_frame_equal(replayed.data, original.data)
    assert replayed.receipt['source'] == original.receipt['source']
    assert replayed.svg_bytes() == (bundle / 'figure.svg').read_bytes()
