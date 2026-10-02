"""Animation frames share one retained source, including preparation evidence."""
from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import polars as pl
import pytest
from matplotlib import pyplot as plt

import astetik as ast
from astetik import _animation, _compile
from astetik._data import data_digest, file_digest, json_digest, normalize
from astetik._data_types import Normalized
from astetik._json import json_object
from astetik._manifest import Manifest
from astetik._polars import polars_digest
from astetik._render_context import Rendered
from astetik._spec_types import PlotSpec
from astetik._types import JsonObject


def _countries() -> pd.DataFrame:
    source = pd.read_csv(Path(__file__).resolve().parents[1] / 'astetik' / 'extras' / 'countries.csv')
    frame = source.loc[source['region'].eq('Europe')].iloc[:3].copy()
    frame.attrs.update(
        key=['alpha-3'],
        units={'country-code': 'identifier', 'region-code': 'identifier'},
        descriptions={'country-code': 'Retained country code', 'region-code': 'Retained region code'},
    )
    return frame


def _prepared(frame: pd.DataFrame) -> SimpleNamespace:
    table = pl.DataFrame(frame.to_dict(orient='list'))
    digest = polars_digest(table)
    receipt = {
        'key': frame.attrs['key'], 'units': frame.attrs['units'],
        'variables': {name: {'description': description} for name, description in frame.attrs['descriptions'].items()},
        'output': {'sha256': digest},
    }
    return SimpleNamespace(data=table, receipt=receipt, _data_digest=digest, _receipt_digest=json_digest(receipt))


@pytest.mark.parametrize('input_kind', ['path', 'pandas', 'prepared'])
def test_animation_normalizes_once_and_retains_source_changed_between_frames(
    input_kind: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    countries = _countries()
    path = tmp_path / 'retained-countries.csv'
    countries.to_csv(path, index=False)
    prepared = _prepared(countries)
    inputs: dict[str, object] = {'path': path, 'pandas': countries, 'prepared': prepared}
    source = inputs[input_kind]
    retained = normalize(source)
    options = {'key': ['alpha-3'], 'units': countries.attrs['units']} if input_kind == 'path' else {}
    normalization_count = 0
    render_count = 0
    render_frame = _compile._render

    def counted_normalize(value: object) -> Normalized:
        nonlocal normalization_count
        normalization_count += 1
        return normalize(value)

    def mutate_after_first_render(
        frame: pd.DataFrame, spec: PlotSpec, design: Manifest, analysis: JsonObject | None,
    ) -> Rendered:
        nonlocal render_count
        result = render_frame(frame, spec, design, analysis)
        render_count += 1
        if render_count == 1:
            if input_kind == 'path':
                countries.iloc[::-1].to_csv(path, index=False)
            elif input_kind == 'pandas':
                countries.iloc[:] = countries.iloc[::-1].to_numpy()
                countries.attrs['key'] = ['name']
                countries.attrs['units']['country-code'] = 'changed metadata'
            else:
                prepared.data = prepared.data.reverse()
                prepared.receipt['key'] = ['name']
                prepared.receipt['units']['country-code'] = 'changed metadata'
        return result

    monkeypatch.setattr(_animation, 'normalize', counted_normalize)
    monkeypatch.setattr(_compile, 'normalize', counted_normalize)
    monkeypatch.setattr(_compile, '_render', mutate_after_first_render)
    animation = ast.Animation(source, 'country-code', 'region-code', label_col='alpha-3', **options)
    with ExitStack() as cleanup:
        for result in animation.frames:
            cleanup.callback(plt.close, result.figure)
        assert normalization_count == 1
        assert render_count == len(retained.data)
        assert animation.receipt['input_sha256'] == data_digest(retained.data)
        pd.testing.assert_frame_equal(animation.data, retained.data)
        for position, result in enumerate(animation.frames):
            pd.testing.assert_frame_equal(result.data, retained.data)
            assert result.receipt['input_sha256'] == animation.receipt['input_sha256']
            assert result.receipt['source'] == retained.source
            assert result.receipt['upstream_receipt'] == retained.upstream_receipt
            assert result.receipt['key'] == ['alpha-3']
            assert result.receipt['units'] == {'country-code': 'identifier', 'region-code': 'identifier'}
            assert result.spec['title'] == retained.data.iloc[position]['alpha-3']
            for mark in result.marks.values():
                assert mark['source_rows'] == [position]
                assert mark['source_keys'] == [{'alpha-3': retained.data.iloc[position]['alpha-3']}]
        if input_kind == 'path':
            assert animation.frames[0].receipt['source']['file_sha256'] != file_digest(path)
        else:
            assert animation.frames[0].receipt['descriptions'] == retained.descriptions


def test_retained_normalized_handle_does_not_expand_public_input_types() -> None:
    retained = normalize(_countries())
    with pytest.raises(ast.AstetikError) as failure:
        ast.render(retained, {'kind': 'count', 'x': 'region'})
    assert failure.value.code == 'INVALID_DATA'


@pytest.mark.parametrize(('field', 'value', 'code'), [
    ('key', False, 'KEY_SCHEMA'), ('key', 0, 'KEY_SCHEMA'), ('key', {}, 'KEY_SCHEMA'),
    ('units', False, 'SPEC_SCHEMA'), ('units', 0, 'SPEC_SCHEMA'), ('units', [], 'SPEC_SCHEMA'),
])
def test_animation_rejects_falsy_invalid_metadata_declarations(field: str, value: object, code: str) -> None:
    options = {field: value}
    with pytest.raises(ast.AstetikError) as failure:
        ast.Animation(_countries().iloc[:1], 'country-code', 'region-code', **options)
    assert failure.value.code == code


@pytest.mark.parametrize('key', [None, []])
@pytest.mark.parametrize('units', [None, {}])
def test_animation_preserves_explicit_empty_key_and_unit_mappings(
    key: list[str] | None, units: dict[str, str] | None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _countries().iloc[:1]
    declarations: list[JsonObject] = []
    resolve = _animation.resolve_spec

    def capture_declaration(value: object) -> PlotSpec:
        declarations.append(json_object(value))
        return resolve(value)

    monkeypatch.setattr(_animation, 'resolve_spec', capture_declaration)
    animation = ast.Animation(data, 'country-code', 'region-code', key=key, units=units)
    result = animation.poster
    with ExitStack() as cleanup:
        cleanup.callback(plt.close, result.figure)
        assert result.receipt['key'] == (['alpha-3'] if key is None else [])
        assert result.spec['key'] == result.receipt['key']
        assert result.receipt['units'] == data.attrs['units']
        assert declarations[0]['units'] == (data.attrs['units'] if units is None else {})
        assert declarations[0]['key'] == (['alpha-3'] if key is None else [])
        assert result.receipt['source']['key'] == ['alpha-3']
        for mark in result.marks.values():
            assert mark['source_keys'] == [{'alpha-3': data.iloc[0]['alpha-3']}]
