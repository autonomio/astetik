"""Encode and reconstruct pandas index identity without resetting row labels."""
from __future__ import annotations

from collections.abc import Hashable
from typing import Protocol, cast

import pandas as pd

from ._cells import decode_cell, encode_cell
from ._nullable import nullable_float_array
from ._snapshot_types import IndexPayload


class _CategoricalConstructor(Protocol):
    def __call__(self, values: list[object], *, categories: list[object], ordered: bool,
                 name: Hashable) -> pd.CategoricalIndex: ...


def index_payload(index: pd.Index) -> IndexPayload:
    result: IndexPayload = {'class': type(index).__name__, 'names': [encode_cell(name) for name in index.names],
                            'values': [encode_cell(value) for value in index.tolist()]}
    if isinstance(index, pd.MultiIndex):
        result['level_dtypes'] = [str(level.dtype) for level in index.levels]
    else:
        result['dtype'] = str(index.dtype)
    if isinstance(index, pd.RangeIndex):
        result['range'] = [index.start, index.stop, index.step]
    if isinstance(index, pd.CategoricalIndex):
        categories = cast(pd.Index, getattr(index, 'categories'))
        result['categories'] = [encode_cell(value) for value in categories]
        result['ordered'] = bool(getattr(index, 'ordered'))
    return result


def index_name(value: object) -> Hashable:
    if not isinstance(value, Hashable):
        raise ValueError('Index names must be hashable')
    return value


def restore_index(payload: IndexPayload) -> pd.Index:
    names = [index_name(decode_cell(name)) for name in payload['names']]
    values = [decode_cell(value) for value in payload['values']]
    kind = payload['class']
    if kind == 'RangeIndex':
        start, stop, step = payload.get('range', [])
        return pd.RangeIndex(start, stop, step, name=names[0])
    if kind == 'MultiIndex':
        if not values:
            return pd.MultiIndex.from_arrays([[] for _ in names], names=names)
        if any(not isinstance(value, tuple) for value in values):
            raise ValueError('MultiIndex values must be tuples')
        return pd.MultiIndex.from_tuples(cast(list[tuple[Hashable, ...]], values), names=names)
    if kind == 'CategoricalIndex':
        constructor = cast(_CategoricalConstructor, pd.CategoricalIndex)
        return constructor(values, categories=[decode_cell(value) for value in payload.get('categories', [])],
                           ordered=payload.get('ordered', False), name=names[0])
    if payload.get('dtype', '') in ('Float32', 'Float64'):
        return pd.Index(nullable_float_array(values, payload.get('dtype', '')), name=names[0])
    return pd.Index(values, dtype=payload.get('dtype', ''), name=names[0], tupleize_cols=False)
