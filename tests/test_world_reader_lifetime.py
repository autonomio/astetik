"""Actual bundled geometry handles close on successful and failed country renders."""

from __future__ import annotations

import importlib.resources
from collections.abc import Iterator
from dataclasses import dataclass, field
from io import IOBase
from typing import NoReturn

import pandas as pd
import pytest

import astetik as ast
from astetik import _render_world as world_module
from astetik._shape_backend import ShapeReader, ShapeRecord, geometry_reader


@dataclass
class ReaderAudit:
    opened: list[ShapeReader] = field(default_factory=list)
    closed: list[ShapeReader] = field(default_factory=list)
    handles: list[IOBase] = field(default_factory=list)


@pytest.fixture
def countries() -> pd.DataFrame:
    resource = importlib.resources.files('astetik').joinpath('extras/countries.csv')
    with resource.open('rb') as source:
        retained = pd.read_csv(source)
    frame = retained.loc[
        retained['alpha-3'].isin(['ALA', 'CAN', 'DEU', 'FIN', 'USA']),
        ['alpha-3', 'country-code'],
    ].reset_index(drop=True)
    frame.attrs.update(row_keys=['alpha-3'], units={'country-code': '1'})
    assert len(frame) == 5
    return frame


@pytest.fixture
def reader_audit(monkeypatch: pytest.MonkeyPatch) -> Iterator[ReaderAudit]:
    audit = ReaderAudit()

    def tracked_reader(path: str) -> ShapeReader:
        reader = geometry_reader(path)
        audit.opened.append(reader)
        for name in ('shp', 'shx', 'dbf'):
            handle = getattr(reader, name)
            assert isinstance(handle, IOBase)
            audit.handles.append(handle)
        close = reader.close

        def tracked_close() -> None:
            close()
            audit.closed.append(reader)

        monkeypatch.setattr(reader, 'close', tracked_close)
        return reader

    monkeypatch.setattr(world_module, 'geometry_reader', tracked_reader)
    yield audit
    for handle in audit.handles:
        handle.close()


def _render(data: pd.DataFrame) -> ast.EvidenceResult:
    return ast.render(data, {'kind': 'world', 'x': 'alpha-3', 'y': 'country-code'})


def _closed(audit: ReaderAudit) -> None:
    assert len(audit.opened) == 1
    assert audit.closed == audit.opened
    assert len(audit.handles) == 3
    assert all(handle.closed for handle in audit.handles)


def test_unmapped_retained_country_closes_geometry_before_error_returns(
    countries: pd.DataFrame, reader_audit: ReaderAudit
) -> None:
    with pytest.raises(ast.AstetikError) as caught:
        _render(countries)
    assert caught.value.code == 'PLOT_CONTRACT'
    assert 'ALA' in caught.value.details['reason']
    _closed(reader_audit)


def test_materialization_failure_closes_all_geometry_handles(
    countries: pd.DataFrame, reader_audit: ReaderAudit, monkeypatch: pytest.MonkeyPatch
) -> None:
    tracked_reader = world_module.geometry_reader

    def broken_reader(path: str) -> ShapeReader:
        reader = tracked_reader(path)
        records = reader.iterShapeRecords()

        def broken_records() -> Iterator[ShapeRecord]:
            yield next(records)
            raise ValueError('Injected geometry materialization failure.')

        monkeypatch.setattr(reader, 'iterShapeRecords', broken_records)
        return reader

    monkeypatch.setattr(world_module, 'geometry_reader', broken_reader)
    with pytest.raises(ast.AstetikError) as caught:
        _render(countries)
    assert caught.value.code == 'PLOT_CONTRACT'
    assert 'materialization failure' in caught.value.details['reason']
    _closed(reader_audit)


def test_polygon_failure_closes_geometry_reader(
    countries: pd.DataFrame, reader_audit: ReaderAudit, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failed_polygon(*_args: object, **_kwargs: object) -> NoReturn:
        raise ValueError('Injected country polygon failure.')

    monkeypatch.setattr(world_module, 'Polygon', failed_polygon)
    with pytest.raises(ast.AstetikError) as caught:
        _render(countries.loc[countries['alpha-3'] != 'ALA'].reset_index(drop=True))
    assert caught.value.code == 'PLOT_CONTRACT'
    assert 'polygon failure' in caught.value.details['reason']
    _closed(reader_audit)


def test_successful_country_marks_preserve_exact_values_and_close_reader(
    countries: pd.DataFrame, reader_audit: ReaderAudit
) -> None:
    supported = countries.loc[countries['alpha-3'] != 'ALA'].reset_index(drop=True)
    result = _render(supported)
    _closed(reader_audit)
    assert {
        mark['values']['country']: mark['values']['value'] for mark in result.marks.values()
    } == dict(zip(supported['alpha-3'], supported['country-code']))
    assert sorted(mark['source_rows'][0] for mark in result.marks.values()) == list(range(4))
    assert len(result.table) == len(supported)
    pd.testing.assert_frame_equal(result.data, supported)
