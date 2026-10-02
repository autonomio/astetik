"""Typed boundary for the bundled pyshp reader's public geometry operations."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from importlib import import_module
from typing import Protocol, cast


class Shape(Protocol):
    parts: Sequence[int]
    points: Sequence[tuple[float, float]]


class ShapeRecord(Protocol):
    record: Sequence[object] | None
    shape: Shape | None


class ShapeReader(Protocol):
    fields: Sequence[Sequence[object]]

    def iterShapeRecords(self) -> Iterator[ShapeRecord]: ...
    def close(self) -> None: ...


class ShapefileModule(Protocol):
    def Reader(self, path: str) -> ShapeReader: ...


def geometry_reader(path: str) -> ShapeReader:
    return cast(ShapefileModule, import_module('shapefile')).Reader(path)


def geometry_code(record: ShapeRecord, field: int) -> str:
    if record.record is None:
        raise ValueError('Bundled country geometry has a missing attribute record.')
    return str(record.record[field])


def geometry_shape(record: ShapeRecord) -> Shape:
    if record.shape is None:
        raise ValueError('Bundled country geometry has a missing polygon.')
    return record.shape
