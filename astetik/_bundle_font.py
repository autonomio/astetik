"""Bind replay to the retained font bytes and declared design identity."""
from __future__ import annotations

from pathlib import Path

from ._data import file_digest
from ._font_source import font_identity
from ._manifest import Manifest
from ._spec import fail
from ._types import JsonObject


def retained_design(directory: Path, receipt: JsonObject, document: JsonObject) -> Manifest:
    """Resolve only the bundle's local font, preserving its original decision."""
    source = directory / 'font.ttf'
    if source.is_symlink() or source.resolve().parent != directory.resolve():
        fail('BUNDLE_PATH', 'The retained font must be a local regular artifact.', file=source.name)
    try:
        identity = font_identity(receipt.get('font'))
    except ValueError as error:
        fail('BUNDLE_DOCUMENT', 'The retained font identity is invalid.', reason=str(error))
    if not source.is_file() or file_digest(source) != identity['sha256']:
        fail('BUNDLE_CHANGED', 'The retained font differs from its scientific receipt.', file=source.name)
    identity['path'] = str(source.resolve())
    try:
        return Manifest.from_dict(document, font_source=identity)
    except (ValueError, TypeError, OSError) as error:
        fail('MANIFEST_CONTRACT', 'The retained design manifest is invalid.', reason=str(error))
