"""Every public plot passes publication checks after central composition."""

import json
from hashlib import sha256
from pathlib import Path

import pandas as pd
import pytest

import astetik as ast


@pytest.fixture
def publication_data():
    return pd.DataFrame(
        {
            'id': list(range(6)),
            'x': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            'y': [1.2, 2.8, 2.2, 4.1, 5.3, 5.9],
            'group': ['A'] * 3 + ['B'] * 3,
            'truth': [0, 1, 0, 1, 0, 1],
            'score': [0.1, 0.9, 0.4, 0.7, 0.2, 0.6],
        }
    )


@pytest.fixture
def publication_manifest():
    return ast.Manifest(categories={'A': '#2A4A70', 'B': '#AC4B35', 'x': '#2D7D60', 'y': '#7D5595'})


CATALOGUE_CASES = {
    'corr': {'columns': ['x', 'y']},
    'hist': {'x': 'x'},
    'kde': {'x': 'x'},
    'pie': {'x': 'group'},
    'scat': {'x': 'x', 'y': 'y'},
    'line': {'x': 'x', 'y': 'y'},
    'roc': {'x': 'truth', 'y': 'score'},
    'oned': {'x': 'x'},
    'regs': {'x': 'x', 'y': 'y'},
    'twod': {'x': 'x', 'y': 'y'},
    'multikde': {'x': 'x', 'hue': 'group'},
    'compare': {'x': 'x', 'y': 'y', 'hue': 'group'},
    'overlap': {'x': 'x', 'y': 'y', 'hue': 'group'},
    'comparison': {
        'x': 'group',
        'y': 'y',
        'analysis': {'method': 'welch', 'groups': ['A', 'B'], 'observation_unit': 'specimen'},
    },
    'association': {
        'x': 'x',
        'y': 'y',
        'analysis': {'method': 'pearson', 'observation_unit': 'specimen'},
    },
    'longitudinal': {
        'x': 'x',
        'y': 'y',
        'analysis': {'method': 'observed', 'observation_unit': 'specimen'},
    },
    'world': {'x': 'country', 'y': 'value'},
    'animate': {'x': 'x', 'y': 'y', 'options': {'frame': 2, 'plot_type': 'bar'}},
    'table': {'columns': ['x', 'y']},
    'text': {'columns': ['x', 'y']},
}
for _kind in (
    'swarm',
    'grid',
    'box',
    'violin',
    'strip',
    'count',
    'bargrid',
    'multicount',
    'bar',
    'bartwo',
):
    CATALOGUE_CASES[_kind] = {'x': 'group', 'y': None if _kind in ('count', 'multicount') else 'y'}


def _spec(kind, **fields):
    return {
        'kind': kind,
        'paper': True,
        'key': ['id'],
        'units': {'x': 'kg', 'y': 'kg', 'truth': '1', 'score': '1', 'value': 'kg'},
        **fields,
    }


@pytest.mark.parametrize('kind', list(CATALOGUE_CASES))
def test_entire_public_catalogue_passes_composed_paper_verification(
    kind, publication_data, publication_manifest
):
    if kind == 'world':
        publication_data = pd.DataFrame(
            {'id': [0, 1], 'country': ['FIN', 'USA'], 'value': [1.25, 8.875]}
        )
    result = ast.render(
        publication_data, _spec(kind, **CATALOGUE_CASES[kind]), publication_manifest
    )
    assert result.verify()['passed']
    assert result.receipt['paper'] is True
    assert result.figure.dpi == publication_manifest.paper['dpi']
    assert result.figure.get_figwidth() * 25.4 == pytest.approx(
        publication_manifest.paper['width_mm']
    )
    expected_rows = {2} if kind == 'animate' else set(range(len(publication_data)))
    assert expected_rows == {row for mark in result.marks.values() for row in mark['source_rows']}
    assert all(mark['source_keys'] for mark in result.marks.values() if mark['source_rows'])
    assert result.receipt['observations']['used'] == len(publication_data)
    assert all(check['passed'] for check in result.receipt['checks'])


def test_public_catalogue_test_covers_every_registered_kind():
    assert set(ast.catalog()['plots']) == set(CATALOGUE_CASES)


@pytest.mark.parametrize('horizontal', [False, True])
def test_final_bar_labels_units_and_zero_baseline_match_orientation(
    horizontal, publication_data, publication_manifest
):
    result = ast.render(
        publication_data,
        _spec(
            'bargrid',
            x='group',
            y='y',
            options={'orient': 'h' if horizontal else 'v'},
            descriptions={'group': 'Condition', 'y': 'Mass'},
        ),
        publication_manifest,
    )
    axis = result.figure.axes[0]
    assert axis.get_xlabel() == ('Mass (kg)' if horizontal else 'Condition')
    assert axis.get_ylabel() == ('Condition' if horizontal else 'Mass (kg)')
    assert (axis.get_xlim() if horizontal else axis.get_ylim())[0] == 0.0


def test_paper_facets_share_scales_and_use_manifest_panel_aspect(
    publication_data, publication_manifest
):
    result = ast.render(
        publication_data, _spec('scat', x='x', y='y', col='group'), publication_manifest
    )
    axes = result.figure.axes
    assert len(axes) == 2
    assert axes[0].get_xlim() == axes[1].get_xlim()
    assert axes[0].get_ylim() == axes[1].get_ylim()
    width, height = publication_manifest.dimensions(True)
    assert result.figure.get_figwidth() == pytest.approx(width)
    assert result.figure.get_figheight() == pytest.approx(height * 2)
    assert axes[0].get_xlabel() == 'x (kg)'
    assert axes[0].get_ylabel() == 'y (kg)'


def test_double_column_facets_wrap_at_manifest_columns(publication_data):
    manifest = ast.Manifest(paper={'preset': 'double'})
    result = ast.render(publication_data, _spec('scat', x='x', y='y', col='group'), manifest)
    width, height = manifest.dimensions(True)
    assert result.figure.get_figwidth() == pytest.approx(width)
    assert result.figure.get_figheight() == pytest.approx(height / 2)
    assert result.verify()['passed']


def test_final_compare_panels_retain_individual_measurement_units(
    publication_data, publication_manifest
):
    spec = _spec(
        'compare',
        x='x',
        y='y',
        hue='group',
        units={'x': 's', 'y': 'kg'},
        descriptions={'x': 'Time', 'y': 'Mass', 'group': 'Condition'},
    )
    result = ast.render(publication_data, spec, publication_manifest)
    assert [axis.get_xlabel() for axis in result.figure.axes] == ['Time (s)', 'Mass (kg)']
    assert [axis.get_ylabel() for axis in result.figure.axes] == ['Condition', 'Condition']


def test_final_event_plot_keeps_measured_unit(publication_data, publication_manifest):
    result = ast.render(
        publication_data, _spec('oned', x='x', descriptions={'x': 'Mass'}), publication_manifest
    )
    assert result.figure.axes[0].get_xlabel() == 'Mass (kg)'


def test_world_horizontal_colorbar_has_one_correctly_oriented_unit_label(publication_manifest):
    frame = pd.DataFrame({'id': [0, 1], 'country': ['FIN', 'USA'], 'value': [1.25, 8.875]})
    result = ast.render(
        frame,
        _spec('world', x='country', y='value', descriptions={'value': 'Mass'}),
        publication_manifest,
    )
    colorbar = result.figure.axes[-1]
    assert colorbar.get_xlabel() == 'Mass (kg)'
    assert colorbar.get_ylabel() == ''


def test_density_labels_communicate_inverse_measured_units(publication_data, publication_manifest):
    histogram = ast.render(
        publication_data, _spec('hist', x='x', options={'density': True}), publication_manifest
    )
    kde = ast.render(publication_data, _spec('kde', x='x'), publication_manifest)
    assert histogram.figure.axes[0].get_ylabel() == 'Density (1/kg)'
    assert kde.figure.axes[0].get_ylabel() == 'Density (1/kg)'


def test_numerical_hue_requires_unit_and_preserves_its_colorbar_label(
    publication_data, publication_manifest
):
    spec = _spec(
        'scat',
        x='x',
        y='y',
        hue='score',
        units={'x': 'kg', 'y': 'kg'},
        options={'hue_mode': 'continuous'},
    )
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(publication_data, spec, publication_manifest)
    assert caught.value.code == 'UNITS_REQUIRED'
    result = ast.render(
        publication_data,
        {**spec, 'units': {'x': 'kg', 'y': 'kg', 'score': 'K'}},
        publication_manifest,
    )
    assert result.figure.axes[-1].get_ylabel() == 'score (K)'


def test_numeric_class_hue_uses_explicit_category_identity(publication_data):
    frame = publication_data.assign(class_code=[1, 1, 1, 2, 2, 2])
    manifest = ast.Manifest(categories={'1': '#2A4A70', '2': '#AC4B35'})
    result = ast.render(frame, _spec('scat', x='x', y='y', hue='class_code'), manifest)
    assert len(result.figure.axes) == 1
    assert result.figure.axes[0].get_legend() is not None
    assert result.receipt['methods']['plot']['category_colours'] == {'1': '#2A4A70', '2': '#AC4B35'}


def test_incompatible_units_cannot_be_overlaid_on_a_shared_numeric_axis(
    publication_data, publication_manifest
):
    spec = _spec('overlap', x='x', y='y', hue='group', units={'x': 'kg', 'y': 's'})
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(publication_data, spec, publication_manifest)
    assert caught.value.code == 'UNIT_COMPARABILITY'


def test_shared_line_axis_retains_common_unit(publication_data, publication_manifest):
    result = ast.render(
        publication_data,
        _spec('line', x='score', y=['x', 'y'], units={'score': '1', 'x': 'kg', 'y': 'kg'}),
        publication_manifest,
    )
    assert 'kg' in result.figure.axes[0].get_ylabel()
    spec = _spec('line', x='score', y=['x', 'y'], units={'score': '1', 'x': 'kg', 'y': 's'})
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(publication_data, spec, publication_manifest)
    assert caught.value.code == 'UNIT_COMPARABILITY'


@pytest.mark.parametrize('kind', list(CATALOGUE_CASES))
def test_every_public_kind_publishes_and_strictly_replays_complete_evidence(
    kind, publication_data, publication_manifest, tmp_path
):
    if kind == 'world':
        publication_data = pd.DataFrame(
            {'id': [0, 1], 'country': ['FIN', 'USA'], 'value': [1.25, 8.875]}
        )
    original = ast.render(
        publication_data, _spec(kind, **CATALOGUE_CASES[kind]), publication_manifest
    )
    bundle = original.write(tmp_path / kind)
    receipt = json.loads((bundle / 'receipt.json').read_text())
    assert set(receipt['output_files']) == {
        'figure.svg',
        'figure.pdf',
        'figure.png',
        'input.json',
        'input.csv',
        'summary.json',
        'summary.csv',
        'spec.json',
        'manifest.json',
        'marks.json',
        'font.ttf',
        'font-notices.txt',
    }
    assert all(
        sha256((bundle / name).read_bytes()).hexdigest() == digest
        for name, digest in receipt['output_files'].items()
    )
    assert receipt['output_files']['font.ttf'] == receipt['font']['sha256']
    assert (Path(ast.__file__).parent / 'fonts' / 'OFL.txt').read_text() in (bundle / 'font-notices.txt').read_text()
    reproduced = ast.replay(bundle, strict_environment=True)
    assert reproduced.result_id == original.result_id
    assert all(reproduced.receipt['font'][field] == original.receipt['font'][field]
               for field in ('requested', 'resolved', 'sha256', 'fallback'))
    assert reproduced.receipt['source'] == original.receipt['source']
    assert reproduced.receipt['environment'] == original.receipt['environment']
    assert reproduced.receipt['methods'] == original.receipt['methods']
    assert reproduced.marks == original.marks
    pd.testing.assert_frame_equal(reproduced.data, original.data)
    pd.testing.assert_frame_equal(reproduced.table, original.table)
    assert reproduced.verify()['passed']
