"""Optional Polars conversion preserving numeric widths and missingness."""
from __future__ import annotations

import hashlib
import io
from typing import TYPE_CHECKING, TypeGuard

import pandas as pd

from ._errors import AstetikError
from ._snapshot import column_from_values

if TYPE_CHECKING:
    import polars as pl


def is_polars_frame(value: object) -> TypeGuard[pl.DataFrame]:
    try:
        import polars as pl
    except ImportError:
        return False
    return isinstance(value, pl.DataFrame)


def polars_digest(data: pl.DataFrame) -> str:
    """Use Wrangle's exact rechunked IPC algorithm and oldest compatibility level."""
    import polars as pl
    stream = io.BytesIO()
    try:
        data.rechunk().write_ipc(stream, compression='uncompressed', compat_level=pl.CompatLevel.oldest())
    except Exception as error:
        raise AstetikError('UNSUPPORTED_DTYPE', 'Prepared data must have serializable native Polars dtypes.') from error
    return hashlib.sha256(stream.getvalue()).hexdigest()


def from_polars(data: pl.DataFrame) -> pd.DataFrame:
    columns: list[pd.DataFrame] = []
    for column in data.iter_columns():
        values, dtype = column.to_list(), str(column.dtype)
        nullable = any(value is None for value in values)
        if dtype in ('Float32', 'Float64'):
            frame = column_from_values(values, dtype if nullable else dtype.lower())
        elif dtype in ('Int8', 'Int16', 'Int32', 'Int64', 'UInt8', 'UInt16', 'UInt32', 'UInt64'):
            frame = column_from_values(values, dtype if nullable else dtype.lower())
        elif dtype == 'Boolean':
            frame = column_from_values(values, 'boolean' if nullable else 'bool')
        else:
            frame = pd.DataFrame({0: values})
        frame.columns = [column.name]
        columns.append(frame)
    return pd.concat(columns, axis=1) if columns else pd.DataFrame()
