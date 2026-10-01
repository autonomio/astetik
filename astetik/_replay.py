"""Retained bundle replay verifies inventory and hashes before scientific execution."""

from __future__ import annotations

from pathlib import Path

from ._compile import compile_evidence
from ._data import file_digest, json_digest, load_snapshot
from ._result import EvidenceResult, environment_fingerprint
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
}


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
        if not path.is_file() or file_digest(path) != digest:
            fail('BUNDLE_CHANGED', 'A retained artifact does not match its receipt.', file=name)
    return receipt


def replay(directory: str | Path, *, strict_environment: object = True) -> EvidenceResult:
    """Verify a bundle's hashes before reconstructing its scientific result."""
    if not isinstance(strict_environment, bool):
        fail('REPLAY_POLICY', 'strict_environment must be a boolean.')
    path = Path(directory)
    receipt = _retained(path)
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
        read_object((path / 'spec.json').read_text(encoding='utf-8')),
        KINDS,
        DEFAULT_OPTIONS,
        SUPPORTED_OPTIONS,
    )
    manifest = read_object((path / 'manifest.json').read_text(encoding='utf-8'))
    result = compile_evidence(
        load_snapshot(path / 'input.json'), spec, manifest, replayed_receipt=receipt
    )
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
