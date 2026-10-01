"""Exact runtime, dependency and rendering-engine provenance."""
from __future__ import annotations

import importlib.metadata
import platform
import sys
from pathlib import Path

from matplotlib import ft2font

from ._data import file_digest
from ._errors import AstetikError
from ._json import json_digest, json_object
from ._types import JsonObject


def environment() -> JsonObject:
    versions: dict[str, str | None] = {}
    for name in ('astetik', 'pandas', 'numpy', 'matplotlib', 'scipy', 'polars', 'pyshp', 'Pillow'):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    root = Path(__file__).resolve().parent
    try:
        modules = {path.name: file_digest(path) for path in sorted(root.glob('*.py'))}
    except OSError as error:
        raise AstetikError('RUNTIME_FINGERPRINT', 'Runtime source modules could not be fingerprinted.',
                           {'reason': str(error)}) from error
    runtime: object = vars(sys.modules[__package__]).get('__version__') if __package__ in sys.modules else None
    return json_object({'python': platform.python_version(), 'implementation': platform.python_implementation(),
                        'platform': platform.system(), 'machine': platform.machine(), 'versions': versions,
                        'runtime_package_version': runtime, 'freetype_version': ft2font.__freetype_version__,
                        'freetype_build_type': ft2font.__freetype_build_type__,
                        'code_files_sha256': modules, 'code_sha256': json_digest(modules)})
