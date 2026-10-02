"""Normalized source identity and scientific metadata domains."""
from __future__ import annotations

from dataclasses import dataclass
from typing import NotRequired, TypeAlias, TypedDict

import pandas as pd

from ._snapshot_types import Cell
from ._types import JsonObject, JsonScalar

RowIdentity: TypeAlias = JsonScalar | Cell | dict[JsonScalar, JsonScalar | Cell]


class SchemaField(TypedDict):
    """Human-readable labels and exact storage dtypes in an input receipt."""

    name: str
    dtype: str


class SourceOrigin(TypedDict):
    """Validated input origin before the retained pandas snapshot is hashed."""

    kind: str
    upstream_sha256: NotRequired[str]
    receipt_sha256: NotRequired[str]
    native_schema: NotRequired[dict[str, str]]
    path: NotRequired[str]
    file_sha256: NotRequired[str]
    reader: NotRequired[str]
    format: NotRequired[str]


class SourceInfo(SourceOrigin):
    """Full provenance for the exact normalized input."""

    sha256: str
    rows: int
    schema: list[SchemaField]
    key: list[JsonScalar]


@dataclass(frozen=True)
class Normalized:
    """An isolated scientific input plus its source and optional preparation evidence."""

    data: pd.DataFrame
    source: SourceInfo
    upstream_receipt: JsonObject | None
    row_keys: list[RowIdentity]
    units: JsonObject
    descriptions: JsonObject


@dataclass(frozen=True)
class InputFrame:
    """Input-reader output before metadata and snapshot identity are checked."""

    data: pd.DataFrame
    origin: SourceOrigin
    receipt: JsonObject | None = None
    keys: object = None
    units: object = None
    descriptions: object = None
