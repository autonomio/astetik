"""Native scientific scalar codecs; never invoke an input-provided serializer."""
from __future__ import annotations

import base64
from collections.abc import Callable, Hashable
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import cast

import numpy as np
import pandas as pd

from ._errors import AstetikError
from ._json import canonical_json
from ._numpy_types import NumpyDateTime, NumpyDuration, NumpyScalar
from ._snapshot_types import (
    AbsentCell,
    BoolCell,
    Cell,
    DurationCell,
    MappingCell,
    SequenceCell,
    StringCell,
)


def _numpy_value(value: object) -> object:
    if isinstance(value, np.datetime64):
        return pd.Timestamp(cast(NumpyDateTime, value))
    if isinstance(value, np.timedelta64):
        return pd.Timedelta(cast(NumpyDuration, value))
    if isinstance(value, np.generic):
        item = cast(Callable[[NumpyScalar], object], getattr(np.generic, 'item'))
        return item(cast(NumpyScalar, value))
    return value


def _missing(value: object) -> AbsentCell | None:
    for marker, tag in ((pd.NA, 'NA'), (pd.NaT, 'NaT'), (None, 'null')):
        if value is marker:
            return {'type': cast(AbsentCell, {'type': tag})['type']}
    return None


def _primitive(value: object) -> StringCell | BoolCell | None:
    if isinstance(value, bool):
        return {'type': 'bool', 'value': value}
    if isinstance(value, int):
        return {'type': 'int', 'value': str(value)}
    if isinstance(value, float):
        return {'type': 'float', 'value': float.hex(value)}
    if isinstance(value, str):
        return {'type': 'str', 'value': value}
    if isinstance(value, bytes):
        return {'type': 'bytes', 'value': base64.b64encode(value).decode('ascii')}
    return None


def _temporal(value: object) -> StringCell | DurationCell | None:
    if isinstance(value, pd.Timestamp):
        return {'type': 'timestamp', 'value': value.isoformat()}
    if isinstance(value, datetime):
        return {'type': 'datetime', 'value': value.isoformat()}
    if isinstance(value, date):
        return {'type': 'date', 'value': value.isoformat()}
    if isinstance(value, time):
        return {'type': 'time', 'value': value.isoformat()}
    if isinstance(value, pd.Timedelta):
        return {'type': 'timedelta', 'value': str(value.value)}
    if isinstance(value, timedelta):
        return {'type': 'python_timedelta', 'value': [value.days, value.seconds, value.microseconds]}
    if isinstance(value, Decimal):
        return {'type': 'decimal', 'value': str(value)}
    return None


def encode_cell(value: object) -> Cell:
    value = _numpy_value(value)
    for encoder in (_missing, _primitive, _temporal):
        encoded = encoder(value)
        if encoded is not None:
            return encoded
    if type(value) is list:
        return {'type': 'list', 'value': [encode_cell(item) for item in cast(list[object], value)]}
    if type(value) is dict:
        pairs = [[encode_cell(key), encode_cell(item)] for key, item in cast(dict[object, object], value).items()]
        pairs.sort(key=lambda pair: canonical_json(pair[0]))
        return {'type': 'dict', 'value': pairs}
    if isinstance(value, tuple):
        return {'type': 'tuple', 'value': [encode_cell(item) for item in cast(tuple[object, ...], value)]}
    raise AstetikError('UNSUPPORTED_DTYPE', 'Snapshots accept native scientific scalar values.', {'type': type(value).__name__})


def _decode_text(cell: StringCell) -> object:
    decoders: dict[str, Callable[[str], object]] = {
        'int': int, 'float': float.fromhex, 'str': lambda value: value,
        'bytes': lambda value: base64.b64decode(value, validate=True),
        'timestamp': pd.Timestamp, 'datetime': datetime.fromisoformat,
        'date': date.fromisoformat, 'time': time.fromisoformat,
        'timedelta': lambda value: pd.Timedelta(int(value), unit='ns'), 'decimal': Decimal,
    }
    return decoders[cell['type']](cell['value'])


def _hashable(value: object) -> Hashable:
    if not isinstance(value, Hashable):
        raise ValueError('Scientific mapping keys must be hashable')
    return value


def decode_cell(cell: Cell) -> object:
    kind = cell['type']
    if kind in ('NA', 'NaT', 'null'):
        return {'NA': pd.NA, 'NaT': pd.NaT, 'null': None}[kind]
    if kind == 'bool':
        return cast(BoolCell, cell)['value']
    if kind == 'python_timedelta':
        parts = cast(DurationCell, cell)['value']
        return timedelta(days=parts[0], seconds=parts[1], microseconds=parts[2])
    if kind in ('tuple', 'list'):
        values = [decode_cell(item) for item in cast(SequenceCell, cell)['value']]
        return tuple(values) if kind == 'tuple' else values
    if kind == 'dict':
        return {_hashable(decode_cell(key)): decode_cell(item) for key, item in cast(MappingCell, cell)['value']}
    return _decode_text(cast(StringCell, cell))
