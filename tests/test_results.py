"""Evidence identity, preparation integrity and publication invariants."""

import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace

import matplotlib

matplotlib.use('Agg')
import numpy as np
import pandas as pd
import polars as pl
import pytest
from matplotlib import pyplot as plt

from astetik._data import (
    data_digest,
    file_digest,
    frame_from_payload,
    frame_payload,
    json_digest,
    load_snapshot,
    normalize,
)
from astetik._errors import AstetikError
from astetik._result import EvidenceResult


def test_snapshot_is_type_index_and_order_aware_and_roundtrips():
    frame = pd.DataFrame(
        {
            'n': pd.Series([1, pd.NA], dtype='Int64'),
            'x': [float('nan'), -0.0],
            'label': ['<script>', 'β'],
        }
    )
    frame.index = pd.Index(['sample-b', 'sample-a'], name='sample')
    restored = frame_from_payload(frame_payload(frame))
    pd.testing.assert_frame_equal(restored, frame)
    assert data_digest(restored) == data_digest(frame)
    nested = pd.DataFrame({'source_rows': [[0, 2], [1]], 'facet': [{'sex': 'F'}, {'sex': 'M'}]})
    pd.testing.assert_frame_equal(frame_from_payload(frame_payload(nested)), nested)
    assert data_digest(frame.iloc[::-1]) != data_digest(frame)
    changed = frame.copy()
    changed.index.name = 'subject'
    assert data_digest(changed) != data_digest(frame)
    changed = frame.copy()
    changed['n'] = changed['n'].astype('Float64')
    assert data_digest(changed) != data_digest(frame)


def test_snapshot_preserves_categories_and_timezones():
    frame = pd.DataFrame(
        {
            'group': pd.Categorical(['b', 'a'], categories=['a', 'b'], ordered=True),
            'time': pd.date_range('2025-01-01', periods=2, tz='Europe/Helsinki'),
        }
    )
    frame.index = pd.MultiIndex.from_tuples([('a', 2), ('b', 1)], names=['subject', 'visit'])
    pd.testing.assert_frame_equal(frame_from_payload(frame_payload(frame)), frame)


def test_normalization_copies_and_retains_declared_metadata():
    data = pd.DataFrame({'subject': ['a', 'b'], 'mass': [10.0, 11.0]})
    data.attrs.update(
        row_keys=['subject'], units={'mass': 'kg'}, descriptions={'mass': 'Body mass'}
    )
    normalized = normalize(data)
    normalized.data.loc[0, 'mass'] = 50
    assert data.loc[0, 'mass'] == 10
    assert normalized.row_keys == [{'subject': 'a'}, {'subject': 'b'}]
    assert normalized.units == {'mass': 'kg'}
    assert normalized.descriptions == {'mass': 'Body mass'}
    assert normalized.source['sha256'] == data_digest(data)


def _prepared():
    data = pl.DataFrame({'subject': ['a', 'b'], 'mass': [10.0, 11.0]})
    stream = io.BytesIO()
    data.rechunk().write_ipc(
        stream, compression='uncompressed', compat_level=pl.CompatLevel.oldest()
    )
    digest = hashlib.sha256(stream.getvalue()).hexdigest()
    receipt = {
        'key': ['subject'],
        'units': {'mass': 'kg'},
        'variables': {'mass': {'description': 'Body mass'}},
        'output': {'sha256': digest},
    }
    return SimpleNamespace(
        data=data, receipt=receipt, _data_digest=digest, _receipt_digest=json_digest(receipt)
    )


def test_prepared_exact_ipc_and_receipt_integrity():
    prepared = _prepared()
    result = normalize(prepared)
    assert result.source['upstream_sha256'] == prepared._data_digest
    assert result.units == {'mass': 'kg'}
    prepared.data = prepared.data.with_columns(pl.col('mass') + 1)
    with pytest.raises(AstetikError) as failure:
        normalize(prepared)
    assert failure.value.code == 'PREPARED_CHANGED'
    prepared = _prepared()
    prepared.receipt['units']['mass'] = 'g'
    with pytest.raises(AstetikError, match='changed'):
        normalize(prepared)
    prepared = _prepared()
    prepared.receipt['extra'] = np.int64(1)
    with pytest.raises(AstetikError) as failure:
        normalize(prepared)
    assert failure.value.code == 'PREPARED_CHANGED'
    prepared = _prepared()
    prepared.receipt['output']['sha256'] = '0' * 64
    prepared._receipt_digest = json_digest(prepared.receipt)
    with pytest.raises(AstetikError, match='changed'):
        normalize(prepared)


def test_polars_native_input_needs_no_pyarrow():
    result = normalize(pl.DataFrame({'x': [1, 2], 'y': [2.0, 3.0]}))
    assert list(result.data.columns) == ['x', 'y']
    assert result.source['kind'] == 'polars.DataFrame'
    nullable = normalize(pl.DataFrame({'value': [None, float('nan'), 1.0]}))
    payload = frame_payload(nullable.data)
    assert payload['rows'][0][0]['type'] == 'NA'
    assert payload['rows'][1][0] == {'type': 'float', 'value': 'nan'}
    pd.testing.assert_frame_equal(frame_from_payload(payload), nullable.data)


def test_local_file_receipt_and_duplicate_csv_detection(tmp_path):
    source = tmp_path / 'input.csv'
    source.write_text('subject,value\na,1\nb,2\n')
    result = normalize(source)
    assert result.source['file_sha256'] == file_digest(source)
    source.write_text('value,value\n1,2\n')
    with pytest.raises(AstetikError) as failure:
        normalize(source)
    assert failure.value.code == 'DUPLICATE_COLUMNS'


@pytest.fixture
def result():
    figure, axis = plt.subplots(figsize=(3.5, 2.5))
    axis.plot([1, 2], [3, 4])
    axis.set_xlabel('Dose')
    axis.set_ylabel('Response')
    figure.subplots_adjust(left=0.2, bottom=0.2)
    data = pd.DataFrame({'subject': ['a', 'b'], 'x': [1, 2], 'y': [3, 4]})
    result = EvidenceResult(
        figure=figure,
        table=data[['x', 'y']],
        data=data,
        receipt={'paper': True, 'methods': {'method': 'observed'}},
        marks={'observation-0': {'origins': [{'subject': 'a'}], 'value': 3}},
        spec={'kind': 'scatter', 'x': 'x', 'y': 'y'},
        manifest={'paper': {'width_mm': 88.9, 'aspect': 1.4, 'dpi': 300, 'min_fontsize': 7}},
    )
    yield result
    plt.close(figure)


def test_bundle_replay_hashes_vector_outputs_and_no_overwrite(result, tmp_path):
    assert result.verify()['passed']
    bundle = result.write(tmp_path / 'evidence')
    receipt = json.loads((bundle / 'receipt.json').read_text())
    assert receipt['export']['png_dpi'] >= 300
    assert receipt['result_id'] == result.result_id
    checksum = receipt.pop('bundle_receipt_sha256')
    assert json_digest(receipt) == checksum
    assert {
        'figure.svg',
        'figure.pdf',
        'figure.png',
        'input.json',
        'summary.csv',
        'spec.json',
        'manifest.json',
    } <= set(receipt['output_files'])
    for name, digest in receipt['output_files'].items():
        assert file_digest(bundle / name) == digest
    pd.testing.assert_frame_equal(load_snapshot(bundle / 'input.json'), result.data)
    with pytest.raises(AstetikError) as failure:
        result.write(bundle)
    assert failure.value.code == 'OUTPUT_EXISTS'
    assert not list(tmp_path.glob('.astetik-*'))
    assert not list(tmp_path.glob('*.astetik-lock'))


def test_two_exports_have_identical_bytes(result, tmp_path):
    first, second = result.write(tmp_path / 'first'), result.write(tmp_path / 'second')
    assert {path.name: file_digest(path) for path in first.iterdir()} == {
        path.name: file_digest(path) for path in second.iterdir()
    }


@pytest.mark.parametrize(
    'target', ['table', 'data', 'receipt', 'spec', 'manifest', 'marks', 'figure']
)
def test_later_mutation_rejects_publication(result, tmp_path, target):
    if target in {'table', 'data'}:
        getattr(result, target).iloc[0, 0] = 99
    elif target == 'figure':
        result.figure.axes[0].lines[0].set_ydata([9, 8])
    else:
        getattr(result, target)['modified'] = True
    with pytest.raises(AstetikError) as failure:
        result.write(tmp_path / 'unsafe')
    assert failure.value.code == 'RESULT_CHANGED'
    assert not (tmp_path / 'unsafe').exists()


def test_inspection_returns_copy_and_diff_has_semantic_groups(result):
    mark = result.inspect('observation-0')
    mark['origins'][0]['subject'] = 'changed'
    assert result.inspect('observation-0')['origins'][0]['subject'] == 'a'
    assert not any(item['changed'] for item in result.diff(result).values())
    assert set(result.diff(result)) == {'inputs', 'methods', 'values', 'design'}
    with pytest.raises(AstetikError) as failure:
        result.inspect('missing')
    assert failure.value.code == 'UNKNOWN_MARK'


def test_verify_reports_small_type_and_clipped_label():
    figure = plt.figure(figsize=(3.5, 2.5))
    figure.text(1.1, 0.5, 'Outside paper', fontsize=5)
    artifact = EvidenceResult(
        figure=figure,
        table=pd.DataFrame({'x': [1]}),
        data=pd.DataFrame({'x': [1]}),
        receipt={'paper': True},
        marks={},
        spec={},
        manifest={},
    )
    report = artifact.verify()
    failures = {check['check'] for check in report['checks'] if not check['passed']}
    assert {'minimum_type_size', 'label_clipping'} <= failures
    assert not report['passed']
    plt.close(figure)


def test_normalization_does_not_invoke_object_properties():
    class Callback:
        @property
        def data(self):
            raise AssertionError('Untrusted properties must not execute')

    with pytest.raises(AstetikError) as failure:
        normalize(Callback())
    assert failure.value.code == 'INVALID_DATA'


def test_verify_detects_adjacent_tick_label_collisions():
    figure, axes = plt.subplots(figsize=(3.5, 2.5))
    axes.plot([0, 1, 2], [1, 2, 3])
    axes.set_xticks(
        [0, 1, 2],
        [
            'Long scientific category one',
            'Long scientific category two',
            'Long scientific category three',
        ],
    )
    figure.subplots_adjust(left=0.2, right=0.8, bottom=0.25)
    result = EvidenceResult(
        figure=figure,
        table=pd.DataFrame({'x': [1]}),
        data=pd.DataFrame({'x': [1]}),
        receipt={'paper': True},
        marks={},
        spec={},
        manifest={},
    )
    report = result.verify()
    collision = next(
        check for check in report['checks'] if check['check'] == 'tick_label_collisions'
    )
    assert not collision['passed']
    assert len(collision['issues']) == 2
    assert collision['issues'][0]['axis'] == 'x'
    plt.close(figure)


def test_verify_detects_table_text_spill_and_collision():
    figure, axes = plt.subplots(figsize=(3.5, 2.5))
    axes.set_axis_off()
    table = axes.table(
        cellText=[['Scientific measurement label A', 'Scientific measurement label B']],
        colWidths=[0.15, 0.15],
        loc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    result = EvidenceResult(
        figure=figure,
        table=pd.DataFrame({'x': [1]}),
        data=pd.DataFrame({'x': [1]}),
        receipt={'paper': True},
        marks={},
        spec={},
        manifest={},
    )
    checks = {check['check']: check for check in result.verify()['checks']}
    assert not checks['table_cell_text_fit']['passed']
    assert not checks['table_cell_text_collisions']['passed']
    assert checks['table_cell_text_collisions']['issues'][0]['cells'] == [[0, 0], [0, 1]]
    plt.close(figure)


def test_actual_font_checksum_changes_semantic_result_identity():
    from matplotlib import font_manager

    data = pd.DataFrame({'x': [1]})
    paths = [
        font_manager.findfont(font_manager.FontProperties(family='DejaVu Sans', style=style))
        for style in ('normal', 'oblique')
    ]
    artifacts = []
    for path in paths:
        figure = plt.figure(figsize=(3.5, 2.5))
        figure.text(
            0.2, 0.5, 'Scientific evidence', fontproperties=font_manager.FontProperties(fname=path)
        )
        font = {
            'path': path,
            'sha256': file_digest(path),
            'resolved': 'DejaVu Sans',
            'requested': 'DejaVu Sans',
        }
        artifact = EvidenceResult(
            figure=figure,
            table=data,
            data=data,
            receipt={'font': font},
            marks={},
            spec={},
            manifest={},
        )
        assert artifact.verify()['passed']
        artifacts.append(artifact)
    assert artifacts[0].result_id != artifacts[1].result_id
    for artifact in artifacts:
        plt.close(artifact.figure)


def test_optional_parquet_input_uses_native_reader_without_pyarrow(tmp_path):
    source = tmp_path / 'data.parquet'
    pl.DataFrame({'subject': ['a', 'b'], 'mass': [1.0, 2.0]}).write_parquet(source)
    result = normalize(source)
    assert result.data['mass'].tolist() == [1.0, 2.0]
    assert result.source['format'] == 'parquet'
    assert result.source['file_sha256'] == file_digest(source)


def test_environment_records_exact_rendering_versions_and_runtime_sources():
    import importlib.metadata

    from matplotlib import ft2font

    import astetik._result as results

    environment = results._environment()
    for name in ('scipy', 'pyshp', 'Pillow', 'matplotlib', 'pandas', 'numpy'):
        assert environment['versions'][name] == importlib.metadata.version(name)
    assert environment['freetype_version'] == ft2font.__freetype_version__
    assert environment['code_sha256'] == json_digest(environment['code_files_sha256'])
    for name, digest in environment['code_files_sha256'].items():
        assert file_digest(Path(results.__file__).parent / name) == digest
    assert {'_data.py', '_result.py', '_api.py', '_renderers.py', '_analysis.py'} <= set(
        environment['code_files_sha256']
    )


def test_runtime_code_fingerprint_changes_semantic_identity(monkeypatch):
    import astetik._result as results

    environment = results._environment()
    data = pd.DataFrame({'x': [1]})
    figure = plt.figure(figsize=(3.5, 2.5))
    figure.text(0.2, 0.5, 'Scientific evidence')
    arguments = dict(
        figure=figure, table=data, data=data, receipt={}, marks={}, spec={}, manifest={}
    )
    before = EvidenceResult(**arguments)
    monkeypatch.setattr(results, '_environment', lambda: {**environment, 'code_sha256': '0' * 64})
    after = EvidenceResult(**arguments)
    assert before.result_id != after.result_id
    assert (
        before.receipt['environment']['code_sha256'] != after.receipt['environment']['code_sha256']
    )
    plt.close(figure)


def test_missing_greek_glyphs_fail_publication_with_precise_recovery(tmp_path):
    from matplotlib import font_manager

    import astetik._result as results

    font_path = Path(results.__file__).parent / 'fonts' / 'Finlandica.ttf'
    data = pd.DataFrame({'x': [1]})
    figure = plt.figure(figsize=(3.5, 2.5))
    figure.text(
        0.2,
        0.5,
        'Response α β Δ',
        fontproperties=font_manager.FontProperties(fname=str(font_path)),
        fontsize=10,
    )
    font = {'path': str(font_path), 'sha256': file_digest(font_path), 'resolved': 'Finlandica'}
    with pytest.warns(UserWarning, match='Glyph'):
        artifact = EvidenceResult(
            figure=figure,
            table=data,
            data=data,
            receipt={'paper': True, 'font': font},
            marks={},
            spec={},
            manifest={},
        )
        report = artifact.verify()
        coverage = next(check for check in report['checks'] if check['check'] == 'glyph_coverage')
        assert not coverage['passed']
        assert coverage['issues'][0]['text'] == 'Response α β Δ'
        missing = {item['codepoint'] for item in coverage['issues'][0]['missing']}
        assert {'U+03B1', 'U+03B2', 'U+0394'} <= missing
        assert 'typography.font_path' in coverage['recovery']
        with pytest.raises(AstetikError) as failure:
            artifact.write(tmp_path / 'missing-glyphs')
    assert failure.value.code == 'VERIFICATION_FAILED'
    assert not (tmp_path / 'missing-glyphs').exists()
    plt.close(figure)


def test_explicit_dejavu_sans_covers_scientific_greek_labels():
    import astetik as ast

    data = pd.DataFrame({'x': [1.0, 2.0, 3.0], 'y': [2.0, 3.0, 4.0]})
    artifact = ast.render(
        data,
        {
            'kind': 'scat',
            'x': 'x',
            'y': 'y',
            'paper': True,
            'title': 'Response α β Δ',
            'units': {'x': '1', 'y': '1'},
        },
        {'typography': {'font': 'DejaVu Sans'}},
    )
    coverage = next(
        check for check in artifact.verify()['checks'] if check['check'] == 'glyph_coverage'
    )
    assert coverage['passed']
    assert artifact.verify()['passed']
    assert artifact.receipt['font']['resolved'] == 'DejaVu Sans'
    assert artifact.manifest['typography']['font'] == 'DejaVu Sans'
    plt.close(artifact.figure)
