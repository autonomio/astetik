"""Exact scalar, index, and tabular snapshot wire schemas."""
from __future__ import annotations

from typing import Literal, NotRequired, TypeAlias, TypedDict

from ._types import JsonObject


class AbsentCell(TypedDict):
    """Pandas missing markers and Python null retain distinct identities."""

    type: Literal['NA', 'NaT', 'null']


class StringCell(TypedDict):
    """Exact textual encoding of native scalar values."""

    type: Literal['int', 'float', 'str', 'bytes', 'timestamp', 'datetime', 'date', 'time', 'timedelta', 'decimal']
    value: str


class BoolCell(TypedDict):
    """Boolean values stay distinct from integer values."""

    type: Literal['bool']
    value: bool


class DurationCell(TypedDict):
    """Python durations retain days, seconds, and microseconds."""

    type: Literal['python_timedelta']
    value: list[int]


class SequenceCell(TypedDict):
    """Native list and tuple containers retain their original distinction."""

    type: Literal['list', 'tuple']
    value: list[Cell]


class MappingCell(TypedDict):
    """Mappings retain typed keys in canonical key order."""

    type: Literal['dict']
    value: list[list[Cell]]


Cell: TypeAlias = AbsentCell | StringCell | BoolCell | DurationCell | SequenceCell | MappingCell


# `class` is a reserved Python identifier; the functional form preserves the wire key.
IndexPayload = TypedDict('IndexPayload', {
    'class': str, 'names': list[Cell], 'values': list[Cell],
    'dtype': NotRequired[str], 'levels': NotRequired[list['IndexPayload']],
    'codes': NotRequired[list[list[int]]], 'sortorder': NotRequired[int | None],
    'category_index': NotRequired['IndexPayload'],
    'range': NotRequired[list[int]], 'categories': NotRequired[list[Cell]],
    'ordered': NotRequired[bool],
})


class ColumnPayload(TypedDict):
    """A typed label and dtype, with explicit categorical metadata."""

    name: Cell
    dtype: str
    categories: NotRequired[list[Cell]]
    ordered: NotRequired[bool]


class FramePayload(TypedDict):
    """A lossless, ordered scientific input snapshot."""

    format: Literal['astetik.data.v1']
    columns: list[ColumnPayload]
    column_index: IndexPayload
    index: IndexPayload
    rows: list[list[Cell]]
    attrs: JsonObject
