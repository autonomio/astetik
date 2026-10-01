"""Encode and reconstruct pandas index identity without resetting row labels."""
from __future__ import annotations

from collections.abc import Hashable
from typing import Protocol, TypedDict, Unpack, cast

import pandas as pd

from ._cells import decode_cell, encode_cell
from ._nullable import nullable_float_array
from ._snapshot_types import IndexPayload


class _MultiIndexOptions(TypedDict):
    """Pandas accepts typed Index levels that its constructor stub omits."""

    levels: list[pd.Index]
    codes: list[list[int]]
    names: list[Hashable]
    sortorder: int | None
    verify_integrity: bool


class _MultiIndexConstructor(Protocol):
    def __call__(self, **kwargs: Unpack[_MultiIndexOptions]) -> pd.MultiIndex: ...


class _CategoricalConstructor(Protocol):
    def __call__(self, values: list[object], *, categories: pd.Index, ordered: bool,
                 name: Hashable) -> pd.CategoricalIndex: ...


def index_payload(index: pd.Index) -> IndexPayload:
    result: IndexPayload = {'class': type(index).__name__, 'names': [encode_cell(name) for name in index.names],
                            'values': [encode_cell(value) for value in index.tolist()]}
    if isinstance(index, pd.MultiIndex):
        result['levels'] = [index_payload(level) for level in index.levels]
        result['codes'] = [code.tolist() for code in index.codes]
        sortorder = cast(object, getattr(index, 'sortorder'))
        if sortorder is not None and (isinstance(sortorder, bool) or not isinstance(sortorder, int)):
            raise ValueError('MultiIndex sortorder must be an integer or null')
        result['sortorder'] = sortorder
    else:
        result['dtype'] = str(index.dtype)
    if isinstance(index, pd.RangeIndex):
        result['range'] = [index.start, index.stop, index.step]
    if isinstance(index, pd.CategoricalIndex):
        categories = cast(pd.Index, getattr(index, 'categories'))
        result['categories'] = [encode_cell(value) for value in categories]
        result['category_index'] = index_payload(categories)
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
        if 'levels' not in payload or 'codes' not in payload or 'sortorder' not in payload:
            raise ValueError('MultiIndex snapshots require complete levels, codes, and sortorder')
        constructor = cast(_MultiIndexConstructor, pd.MultiIndex)
        return constructor(levels=[restore_index(level) for level in payload['levels']],
                             codes=payload['codes'], names=names, sortorder=payload['sortorder'],
                             verify_integrity=True)
    if kind == 'CategoricalIndex':
        if 'category_index' not in payload:
            raise ValueError('CategoricalIndex snapshots require their complete category index')
        categorical = cast(_CategoricalConstructor, pd.CategoricalIndex)
        return categorical(values, categories=restore_index(payload['category_index']),
                           ordered=payload.get('ordered', False), name=names[0])
    if payload.get('dtype', '') in ('Float32', 'Float64'):
        return pd.Index(nullable_float_array(values, payload.get('dtype', '')), name=names[0])
    return pd.Index(values, dtype=payload.get('dtype', ''), name=names[0], tupleize_cols=False)
