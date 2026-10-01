"""Stable scientific snapshots and verified optional preparation inputs."""
from __future__ import annotations

import math
from pathlib import Path
from typing import cast

import pandas as pd

from ._cells import encode_cell as _cell
from ._data_types import InputFrame, Normalized, RowIdentity, SourceInfo
from ._errors import AstetikError
from ._json import canonical_json as canonical_json
from ._json import json_digest as json_digest
from ._json import json_object, json_value
from ._polars import from_polars, is_polars_frame, polars_digest
from ._prepared import prepared_input
from ._snapshot import data_digest as data_digest
from ._snapshot import frame_from_payload as frame_from_payload
from ._snapshot import frame_payload as frame_payload
from ._snapshot import load_snapshot as load_snapshot
from ._snapshot_types import Cell
from ._source_file import file_digest as file_digest
from ._source_file import read_file
from ._types import JsonObject, JsonScalar


def _input(value: object) -> InputFrame:
    prepared = prepared_input(value)
    if prepared is not None:
        return prepared
    if isinstance(value, pd.DataFrame):
        before = data_digest(value)
        payload = frame_payload(value)
        if json_digest(payload) != before or data_digest(value) != before:
            raise AstetikError('SOURCE_CHANGED', 'The input table changed while its snapshot was being taken.')
        frame = frame_from_payload(payload)
        return InputFrame(frame, {'kind': 'pandas.DataFrame'}, keys=frame.attrs.get('row_keys', frame.attrs.get('key', [])),
                          units=frame.attrs.get('units', {}), descriptions=frame.attrs.get('descriptions', {}))
    if is_polars_frame(value):
        return InputFrame(from_polars(value.clone()), {'kind': 'polars.DataFrame', 'upstream_sha256': polars_digest(value),
                          'native_schema': {name: str(dtype) for name, dtype in value.schema.items()}})
    if isinstance(value, (str, Path)):
        return read_file(value)
    raise AstetikError('INVALID_DATA', 'Use pandas, Polars, Wrangle Prepared, or a local data file.')


def _metadata(input_frame: InputFrame) -> tuple[list[JsonScalar], JsonObject, JsonObject]:
    raw_keys: object = list[JsonScalar]() if input_frame.keys is None else input_frame.keys
    if isinstance(raw_keys, str):
        raw_keys = [raw_keys]
    if not isinstance(raw_keys, list):
        raise AstetikError('INVALID_METADATA', 'Declare row_keys as a list and units/descriptions as mappings.')
    keys = json_value(cast(list[object], raw_keys))
    if not isinstance(keys, list) or any(isinstance(key, (dict, list)) for key in keys):
        raise AstetikError('INVALID_METADATA', 'Declared row keys must be scalar column labels.')
    labels = cast(list[JsonScalar], keys)
    if any(key not in input_frame.data.columns for key in labels):
        raise AstetikError('INVALID_METADATA', 'Declared row keys must exist in the input table.')
    units: object = dict[str, object]() if input_frame.units is None else input_frame.units
    descriptions: object = dict[str, object]() if input_frame.descriptions is None else input_frame.descriptions
    if not isinstance(units, dict) or not isinstance(descriptions, dict):
        raise AstetikError('INVALID_METADATA', 'Declare row_keys as a list and units/descriptions as mappings.')
    return labels, json_object(cast(dict[object, object], units)), json_object(cast(dict[object, object], descriptions))


def _identity(value: object) -> JsonScalar | Cell:
    cell = _cell(value)
    kind = cell['type']
    if kind == 'str':
        return cast(str, cell.get('value'))
    if kind == 'bool':
        return cast(bool, cell.get('value'))
    if kind == 'int':
        return int(cast(str, cell.get('value')))
    if kind == 'float':
        number = float.fromhex(cast(str, cell.get('value')))
        if math.isfinite(number):
            return number
    if kind == 'null':
        return None
    return cell


def _column_position(frame: pd.DataFrame, key: JsonScalar) -> int:
    position = frame.columns.get_loc(key)
    if not isinstance(position, int):
        raise AstetikError('INVALID_METADATA', 'Row keys require unambiguous column labels.')
    return position


def normalize(value: object) -> Normalized:
    input_frame = _input(value)
    frame = input_frame.data
    if frame.columns.has_duplicates:
        raise AstetikError('DUPLICATE_COLUMNS', 'Scientific input column labels must be unique.')
    keys, units, descriptions = _metadata(input_frame)
    identities = ([{key: _identity(frame.iat[position, _column_position(frame, key)]) for key in keys} for position in range(len(frame))]
                  if keys else [_identity(label) for label in frame.index])
    if input_frame.receipt is not None:
        frame.attrs.update(key=keys, units=units, descriptions=descriptions)
    source: SourceInfo = {**input_frame.origin, 'sha256': data_digest(frame), 'rows': len(frame), 'key': keys,
                          'schema': [{'name': str(name), 'dtype': str(dtype)} for name, dtype in frame.dtypes.items()]}
    return Normalized(frame, source, input_frame.receipt, cast(list[RowIdentity], identities), units, descriptions)
