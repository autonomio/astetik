"""Checked schema boundaries for untrusted retained input snapshots."""
from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from ._errors import AstetikError
from ._json import json_object
from ._snapshot_types import AbsentCell, Cell, ColumnPayload, FramePayload, IndexPayload, StringCell


def object_mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError('Expected an object')
    raw = cast(Mapping[object, object], value)
    if any(not isinstance(key, str) for key in raw):
        raise ValueError('Object fields must be strings')
    return cast(Mapping[str, object], raw)


def object_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError('Expected an ordered list')
    return cast(list[object], value)


def text(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError('Expected text')
    return value


def integer_list(value: object) -> list[int]:
    items = object_list(value)
    if any(isinstance(item, bool) or not isinstance(item, int) for item in items):
        raise ValueError('Expected integer values')
    return cast(list[int], items)


def boolean(value: object) -> bool:
    if not isinstance(value, bool):
        raise ValueError('Expected a boolean')
    return value


def parse_cell(value: object) -> Cell:
    raw = object_mapping(value)
    kind = text(raw['type'])
    if kind in ('NA', 'NaT', 'null'):
        return cast(AbsentCell, {'type': kind})
    item = raw['value']
    if kind == 'bool':
        return {'type': 'bool', 'value': boolean(item)}
    if kind == 'python_timedelta':
        parts = integer_list(item)
        if len(parts) != 3:
            raise ValueError('A Python duration needs three integer components')
        return {'type': 'python_timedelta', 'value': parts}
    if kind in ('list', 'tuple'):
        return {'type': kind, 'value': [parse_cell(cell) for cell in object_list(item)]}
    if kind == 'dict':
        pairs = [[parse_cell(cell) for cell in object_list(pair)] for pair in object_list(item)]
        if any(len(pair) != 2 for pair in pairs):
            raise ValueError('A mapping entry needs a key and value')
        return {'type': 'dict', 'value': pairs}
    if kind in ('int', 'float', 'str', 'bytes', 'timestamp', 'datetime', 'date', 'time', 'timedelta', 'decimal'):
        return cast(StringCell, {'type': kind, 'value': text(item)})
    raise AstetikError('INVALID_SNAPSHOT', 'Unknown scientific scalar encoding.', {'type': kind})


def parse_index(value: object) -> IndexPayload:
    raw = object_mapping(value)
    payload: IndexPayload = {'class': text(raw['class']), 'names': [parse_cell(item) for item in object_list(raw['names'])],
                             'values': [parse_cell(item) for item in object_list(raw['values'])]}
    if 'dtype' in raw:
        payload['dtype'] = text(raw['dtype'])
    if 'levels' in raw:
        payload['levels'] = [parse_index(level) for level in object_list(raw['levels'])]
    if 'codes' in raw:
        payload['codes'] = [integer_list(code) for code in object_list(raw['codes'])]
    if 'sortorder' in raw:
        sortorder = raw['sortorder']
        payload['sortorder'] = None if sortorder is None else integer_list([sortorder])[0]
    if 'category_index' in raw:
        payload['category_index'] = parse_index(raw['category_index'])
    if 'range' in raw:
        payload['range'] = integer_list(raw['range'])
    if 'categories' in raw:
        payload['categories'] = [parse_cell(item) for item in object_list(raw['categories'])]
    if 'ordered' in raw:
        payload['ordered'] = boolean(raw['ordered'])
    return payload


def parse_column(value: object) -> ColumnPayload:
    raw = object_mapping(value)
    result: ColumnPayload = {'name': parse_cell(raw['name']), 'dtype': text(raw['dtype'])}
    if 'categories' in raw:
        result['categories'] = [parse_cell(item) for item in object_list(raw['categories'])]
        result['ordered'] = boolean(raw['ordered'])
    return result


def parse_snapshot(value: object) -> FramePayload:
    raw = object_mapping(value)
    if raw.get('format') != 'astetik.data.v1':
        raise AstetikError('INVALID_SNAPSHOT', 'Use an Astetik version 1 scientific snapshot.')
    return {'format': 'astetik.data.v1', 'columns': [parse_column(item) for item in object_list(raw['columns'])],
            'column_index': parse_index(raw['column_index']), 'index': parse_index(raw['index']),
            'rows': [[parse_cell(item) for item in object_list(row)] for row in object_list(raw['rows'])],
            'attrs': json_object(raw.get('attrs', {}))}
