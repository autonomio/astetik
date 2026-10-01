"""Lossless scientific data snapshots with deterministic schema-aware hashes."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ._cells import decode_cell, encode_cell
from ._errors import AstetikError
from ._json import json_digest, json_object
from ._snapshot_index import index_payload, restore_index
from ._snapshot_parse import parse_snapshot
from ._snapshot_types import ColumnPayload, FramePayload


def column_from_values(values: list[object], dtype: str | pd.CategoricalDtype) -> pd.DataFrame:
    if dtype in ('Float32', 'Float64'):
        mask = np.asarray([value is pd.NA or value is None for value in values], dtype=bool)
        numeric = np.asarray([0 if masked else value for value, masked in zip(values, mask)],
                             dtype=np.float32 if dtype == 'Float32' else np.float64)
        return pd.DataFrame({0: pd.arrays.FloatingArray(numeric, mask)})
    return pd.DataFrame({0: values}, dtype=dtype)


def frame_payload(data: pd.DataFrame) -> FramePayload:
    """Retain dtypes, index identity, missingness, labels, and exact native cells."""
    columns: list[ColumnPayload] = []
    for position, name in enumerate(data.columns):
        series = data.iloc[:, position]
        column: ColumnPayload = {'name': encode_cell(name), 'dtype': str(series.dtype)}
        if isinstance(series.dtype, pd.CategoricalDtype):
            column['categories'] = [encode_cell(value) for value in series.cat.categories]
            column['ordered'] = bool(series.cat.ordered)
        columns.append(column)
    return {'format': 'astetik.data.v1', 'columns': columns,
            'column_index': index_payload(data.columns), 'index': index_payload(data.index),
            'rows': [[encode_cell(data.iat[row, col]) for col in range(data.shape[1])] for row in range(data.shape[0])],
            'attrs': json_object({name: data.attrs[name] for name in ('key', 'row_keys', 'units', 'descriptions') if name in data.attrs})}


def frame_from_payload(value: object) -> pd.DataFrame:
    try:
        payload = parse_snapshot(value)
        series: list[pd.DataFrame] = []
        for position, column in enumerate(payload['columns']):
            values = [decode_cell(row[position]) for row in payload['rows']]
            dtype: str | pd.CategoricalDtype = column['dtype']
            if 'categories' in column:
                dtype = pd.CategoricalDtype([decode_cell(item) for item in column['categories']], ordered=column.get('ordered', False))
            series.append(column_from_values(values, dtype))
        frame = pd.concat(series, axis=1) if series else pd.DataFrame(index=range(len(payload['rows'])))
        frame.columns = restore_index(payload['column_index'])
        frame.index = restore_index(payload['index'])
        frame.attrs.update(payload['attrs'])
        if frame_payload(frame) != value:
            raise AstetikError('INVALID_SNAPSHOT', 'The scientific snapshot does not round-trip exactly.')
        return frame
    except AstetikError:
        raise
    except (KeyError, TypeError, ValueError, IndexError, OverflowError) as error:
        raise AstetikError('INVALID_SNAPSHOT', 'The typed scientific snapshot is malformed.', {'reason': str(error)}) from error


def load_snapshot(path: str | Path) -> pd.DataFrame:
    import json
    try:
        payload: object = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise AstetikError('INVALID_SNAPSHOT', 'Use an existing typed input.json snapshot.') from error
    return frame_from_payload(payload)


def data_digest(data: pd.DataFrame) -> str:
    return json_digest(frame_payload(data))
