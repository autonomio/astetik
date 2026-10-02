"""Exact row identity, exclusion accounting and retained preparation metadata."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd

from ._cells import encode_cell
from ._columns import columns
from ._data_types import Normalized, RowIdentity
from ._snapshot_types import Cell
from ._spec import fail
from ._spec_json import clone_json
from ._spec_types import PlotSpec
from ._types import JsonObject, JsonScalar, JsonValue


@dataclass
class Observations:
    frame: pd.DataFrame
    fields: list[str]
    units: dict[str, str]
    descriptions: dict[str, str]
    row_keys: list[RowIdentity]
    excluded: list[RowIdentity]
    positions: list[int]


def _identity(value: object) -> JsonScalar | Cell:
    if isinstance(value, np.generic):
        value = cast(Callable[[], object], getattr(cast(object, value), 'item'))()
    if isinstance(value, (str, int, float, bool)):
        if not isinstance(value, float) or np.isfinite(value):
            return cast(JsonScalar, value)
    return encode_cell(value)


def _key_record(frame: pd.DataFrame, position: int, key: list[str]) -> RowIdentity:
    record: dict[JsonScalar, JsonScalar | Cell] = {
        field: _identity(frame.iloc[position][field]) for field in key
    }
    return record


def row_keys(frame: pd.DataFrame, key: list[str], retained: list[RowIdentity]) -> list[RowIdentity]:
    if not key:
        return retained
    absent = set(key) - set(frame.columns)
    if absent:
        fail('COLUMN_MISSING', 'A declared key column is absent.', columns=sorted(absent))
    if frame[key].isna().any().any() or frame.duplicated(key).any():
        fail('KEY_INVALID', 'Observation keys must be complete and unique.', key=key)
    return [_key_record(frame, position, key) for position in range(len(frame))]


def _text_metadata(section: dict[str, object]) -> dict[str, str]:
    if any(not isinstance(value, str) for value in section.values()):
        fail('INVALID_METADATA', 'Units and descriptions must contain text values.')
    return {name: cast(str, value) for name, value in section.items()}


def prepare(normalized: Normalized, spec: PlotSpec, *, inherited_key: bool) -> Observations:
    frame = normalized.data.copy(deep=True)
    if inherited_key:
        spec['key'] = cast(list[str], normalized.source.get('key', []))
    keys = row_keys(frame, spec['key'], normalized.row_keys)
    fields = columns(frame, spec)
    units = _text_metadata({**normalized.units, **spec.get('units', {})})
    descriptions = _text_metadata({**normalized.descriptions, **spec.get('descriptions', {})})
    spec['units'], spec['descriptions'] = units, descriptions
    conflict = {
        key: [value, units[key]] for key, value in normalized.units.items() if value != units[key]
    }
    if conflict:
        fail(
            'UNIT_CONFLICT',
            'Convert units through preparation before changing their labels.',
            units=conflict,
        )
    incomplete = frame[fields].isna().any(axis=1)
    excluded: list[RowIdentity] = []
    if incomplete.any():
        if spec['missing'] == 'error':
            fail(
                'MISSING_DATA',
                'Declare an exclusion policy or prepare complete observations.',
                columns=frame[fields].columns[frame[fields].isna().any()].tolist(),
                rows=int(incomplete.sum()),
            )
        excluded = [keys[int(index)] for index in np.flatnonzero(incomplete)]
        frame = frame.loc[~incomplete].copy()
    positions = [int(position) for position in np.flatnonzero(~incomplete)]
    return Observations(
        frame.reset_index(drop=True), fields, units, descriptions, keys, excluded, positions
    )


def remap(value: JsonValue, positions: list[int]) -> JsonValue:
    """Translate renderer row references into the retained input positions."""
    if isinstance(value, dict):
        return {
            key: (
                [positions[cast(int, row)] for row in item]
                if key in {'source_rows', 'category_source_rows'} and isinstance(item, list)
                else remap(item, positions)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [remap(item, positions) for item in value]
    return value


def marks_from(rendered: list[JsonObject], observations: Observations) -> dict[str, JsonObject]:
    marks: dict[str, JsonObject] = {}
    for index, original in enumerate(rendered):
        mark = cast(JsonObject, clone_json(original))
        identifier = str(mark.pop('id', f'mark-{index}'))
        if identifier in marks:
            fail('MARK_ID', 'Renderer generated duplicate mark identifiers.')
        rows = cast(list[int], mark.get('source_rows', mark.get('rows', [])))
        mark = cast(JsonObject, remap(mark, observations.positions))
        mark['source_rows'] = [observations.positions[row] for row in rows]
        mark['source_keys'] = clone_json(
            [observations.row_keys[observations.positions[row]] for row in rows]
        )
        marks[identifier] = mark
    return marks
