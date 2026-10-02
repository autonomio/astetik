"""Read local immutable CSV or Parquet bytes and detect concurrent changes."""
from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path

import pandas as pd

from ._data_types import InputFrame
from ._errors import AstetikError
from ._polars import from_polars


def file_digest(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _parquet(content: bytes) -> tuple[pd.DataFrame, str]:
    try:
        return pd.read_parquet(io.BytesIO(content)), 'pandas'
    except ImportError:
        import polars as pl
        return from_polars(pl.read_parquet(io.BytesIO(content))), 'polars'


def read_file(value: str | Path) -> InputFrame:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise AstetikError('SOURCE_NOT_FOUND', 'Use an existing local CSV or Parquet file.', {'path': str(path)})
    reader = 'pandas'
    try:
        content = path.read_bytes()
        before = hashlib.sha256(content).hexdigest()
        if path.suffix.lower() == '.csv':
            header = next(csv.reader(io.StringIO(content.decode('utf-8'))), list[str]())
            if len(header) != len(set(header)):
                raise AstetikError('DUPLICATE_COLUMNS', 'CSV column labels must be unique.')
            frame = pd.read_csv(io.BytesIO(content))
        elif path.suffix.lower() == '.parquet':
            frame, reader = _parquet(content)
        else:
            raise AstetikError('UNSUPPORTED_FORMAT', 'Use local CSV or Parquet files.')
    except AstetikError:
        raise
    except (OSError, ValueError, ImportError, UnicodeError) as error:
        raise AstetikError('INVALID_SOURCE', 'The source could not be read.', {'path': str(path)}) from error
    if file_digest(path) != before:
        raise AstetikError('SOURCE_CHANGED', 'The file changed while it was being read.', {'path': str(path)})
    return InputFrame(frame, {'kind': 'file', 'path': str(path), 'file_sha256': before,
                              'reader': reader, 'format': path.suffix.lower().lstrip('.')})
