"""Retained bundle replay verifies inventory and hashes before scientific execution."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ._bundle_font import retained_design
from ._compile import compile_evidence
from ._data import data_digest, file_digest, frame_from_payload, json_digest
from ._result import EvidenceResult, environment_fingerprint
from ._result_state import semantic_identity
from ._spec import fail, resolve
from ._spec_json import read_object
from ._types import JsonObject

REQUIRED_FILES = {
    'input.json',
    'summary.json',
    'input.csv',
    'summary.csv',
    'spec.json',
    'manifest.json',
    'marks.json',
    'figure.svg',
    'figure.pdf',
    'figure.png',
    'font.ttf',
    'font-notices.txt',
}


def _document(path: Path) -> JsonObject:
    try:
        return read_object(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        fail(
            'BUNDLE_DOCUMENT',
            'The retained JSON document cannot be read.',
            file=path.name,
            reason=str(error),
        )


def _retained(directory: Path) -> JsonObject:
    try:
        receipt = read_object((directory / 'receipt.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        fail('BUNDLE_DOCUMENT', 'The retained receipt cannot be read.', reason=str(error))
    seal = receipt.pop('bundle_receipt_sha256', None)
    if not seal or json_digest(receipt) != seal:
        fail(
            'BUNDLE_CHANGED',
            'The evidence receipt is missing or does not match its integrity seal.',
        )
    files = receipt.get('output_files', {})
    if not isinstance(files, dict) or set(files) != REQUIRED_FILES:
        fail('BUNDLE_INCOMPLETE', 'The bundle inventory must contain every retained artifact.')
    for name, digest in files.items():
        if Path(name).name != name:
            fail('BUNDLE_PATH', 'Bundle file names must be local base names.')
        path = directory / name
        if name == 'font.ttf' and path.is_symlink():
            fail('BUNDLE_PATH', 'The retained font must be a local regular artifact.', file=name)
        if not path.is_file() or file_digest(path) != digest:
            fail('BUNDLE_CHANGED', 'A retained artifact does not match its receipt.', file=name)
    return receipt


def _snapshot(path: Path, expected: object) -> pd.DataFrame:
    frame = frame_from_payload(_document(path))
    if data_digest(frame) != expected:
        fail(
            'BUNDLE_CHANGED',
            'The retained snapshot differs from its scientific receipt.',
            file=path.name,
        )
    return frame


def _csv(path: Path, frame: pd.DataFrame) -> None:
    try:
        retained = path.read_bytes()
    except OSError as error:
        fail('BUNDLE_DOCUMENT', 'The retained CSV cannot be read.', file=path.name, reason=str(error))
    expected = frame.to_csv(index=True, lineterminator='\n', float_format='%.17g').encode('utf-8')
    if retained != expected:
        fail('BUNDLE_CHANGED', 'The readable CSV differs from its scientific snapshot.', file=path.name)


def _identity(receipt: JsonObject) -> None:
    try:
        expected = semantic_identity(receipt)
    except KeyError as error:
        fail('BUNDLE_DOCUMENT', 'The retained semantic identity is incomplete.', reason=str(error))
    if receipt.get('result_id') != expected:
        fail('BUNDLE_CHANGED', 'The retained scientific receipt differs from its result identity.', field='result_id')


def _inputs(directory: Path, receipt: JsonObject) -> pd.DataFrame:
    marks = _document(directory / 'marks.json')
    if json_digest(marks) != receipt.get('marks_sha256'):
        fail(
            'BUNDLE_CHANGED',
            'Retained marks differ from their scientific receipt.',
            file='marks.json',
        )
    summary = _snapshot(directory / 'summary.json', receipt.get('table_sha256'))
    data = _snapshot(directory / 'input.json', receipt.get('input_sha256'))
    for name, frame in [('input.csv', data), ('summary.csv', summary)]:
        _csv(directory / name, frame)
    return data


def replay(directory: str | Path, *, strict_environment: object = True) -> EvidenceResult:
    """Verify a bundle's hashes before reconstructing its scientific result."""
    if not isinstance(strict_environment, bool):
        fail('REPLAY_POLICY', 'strict_environment must be a boolean.')
    path = Path(directory)
    receipt = _retained(path)
    data = _inputs(path, receipt)
    current = environment_fingerprint()
    if strict_environment and current != receipt.get('environment'):
        fail(
            'ENVIRONMENT_CHANGED',
            'Exact replay requires the retained code and environment; use strict_environment=False for explicit recomputation.',
            retained=receipt.get('environment'),
            current=current,
        )
    from ._catalog import DEFAULT_OPTIONS, KINDS, SUPPORTED_OPTIONS

    spec = resolve(
        _document(path / 'spec.json'),
        KINDS,
        DEFAULT_OPTIONS,
        SUPPORTED_OPTIONS,
    )
    manifest = retained_design(path, receipt, _document(path / 'manifest.json'))
    _identity(receipt)
    result = compile_evidence(data, spec, manifest, replayed_receipt=receipt)
    fields = (
        'input_sha256',
        'table_sha256',
        'spec_sha256',
        'manifest_sha256',
        'marks_sha256',
        'caption',
        'analysis',
        'methods',
        'observations',
        'units',
        'key',
    )
    for field in fields:
        if result.receipt.get(field) != receipt.get(field):
            fail(
                'REPLAY_DIFFERENCE',
                'Recomputed evidence differs from the retained result.',
                field=field,
            )
    if strict_environment and result.result_id != receipt.get('result_id'):
        fail(
            'REPLAY_DIFFERENCE', 'Recomputed scientific identity differs from the retained result.'
        )
    if strict_environment and result.svg_bytes() != (path / 'figure.svg').read_bytes():
        fail('REPLAY_DIFFERENCE', 'Recomputed graphics differ from the retained figure.')
    return result
