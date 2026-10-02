import json
import subprocess
import sys

import matplotlib as mpl
import numpy as np
import pandas as pd
import pytest
from scipy import stats

import astetik as ast
from astetik._data import data_digest


@pytest.fixture
def frame():
    return pd.DataFrame(
        {
            'sample': [f's{i}' for i in range(16)],
            'group': ['Control'] * 8 + ['Treatment'] * 8,
            'time': list(range(8)) * 2,
            'mass': [4, 5, 6, 5, 7, 5, 6, 8, 7, 8, 9, 8, 10, 8, 9, 11],
        }
    )


@pytest.fixture
def design():
    return ast.Manifest(categories={'Control': '#2A4A70', 'Treatment': '#A54532'})


def comparison_spec():
    return {
        'kind': 'comparison',
        'x': 'group',
        'y': 'mass',
        'paper': True,
        'key': ['sample'],
        'units': {'mass': 'g'},
        'analysis': {
            'method': 'welch',
            'groups': ['Control', 'Treatment'],
            'observation_unit': 'sample',
        },
    }


def test_complete_comparison_and_independent_reference(frame, design, tmp_path):
    before, settings = data_digest(frame), dict(mpl.rcParams)
    result = ast.render(frame, comparison_spec(), design)
    assert data_digest(frame) == before
    assert dict(mpl.rcParams) == settings
    reference = stats.ttest_ind(
        frame.loc[frame.group == 'Treatment', 'mass'],
        frame.loc[frame.group == 'Control', 'mass'],
        equal_var=False,
    )
    contrast = result.receipt['analysis']['contrast']
    assert contrast['statistic'] == pytest.approx(reference.statistic)
    assert contrast['p_value'] == pytest.approx(reference.pvalue)
    interval = reference.confidence_interval()
    assert [contrast['lower'], contrast['upper']] == pytest.approx([interval.low, interval.high])
    assert result.verify()['passed']
    first = result.inspect(next(iter(result.marks)))
    assert first['source_rows'] and first['source_keys']
    bundle = result.write(tmp_path / 'paper')
    assert all((bundle / f'figure.{ext}').exists() for ext in ['svg', 'pdf', 'png'])
    repeated = ast.replay(bundle)
    assert repeated.receipt['table_sha256'] == result.receipt['table_sha256']
    assert result.diff(repeated)['values']['changed'] is False


def test_association_uses_declared_method(frame, design):
    spec = {
        'kind': 'association',
        'x': 'time',
        'y': 'mass',
        'paper': True,
        'key': 'sample',
        'units': {'time': 'day', 'mass': 'g'},
        'analysis': {'method': 'pearson', 'observation_unit': 'sample'},
    }
    result = ast.render(frame, spec, design)
    assert result.receipt['analysis']['statistics']['estimate'] == pytest.approx(
        stats.pearsonr(frame.time, frame.mass).statistic
    )
    assert 'does not establish causation' in result.receipt['caption']
    spec['analysis']['method'] = 'spearman'
    second = ast.render(frame, spec, design)
    assert result.diff(second)['methods']['changed']
    assert second.receipt['analysis']['statistics']['lower'] is None


def test_observed_longitudinal_and_legacy_line(frame, design):
    spec = {
        'kind': 'longitudinal',
        'x': 'time',
        'y': 'mass',
        'hue': 'group',
        'key': 'sample',
        'units': {'time': 'day', 'mass': 'g'},
        'paper': True,
        'analysis': {'method': 'observed', 'observation_unit': 'sample'},
    }
    result = ast.render(frame, spec, design)
    assert len(result.marks) == len(frame)
    legacy = ast.line(
        frame, x='mass', y='time', hue='group', units=spec['units'], paper=True, manifest=design
    )
    assert legacy.spec['x'] == 'time' and legacy.spec['y'] == 'mass'


@pytest.mark.parametrize(
    'change,code',
    [
        ({'analysis': {}}, 'METHOD_REQUIRED'),
        ({'key': []}, 'KEY_REQUIRED'),
        ({'units': {}}, 'UNITS_REQUIRED'),
        ({'options': {'outliers': True}}, 'PLOT_OPTIONS'),
        ({'axes': {'y': {'limits': [5, 8]}}}, 'AXIS_TRUNCATION'),
    ],
)
def test_consequential_ambiguity_is_a_structured_failure(frame, design, change, code):
    spec = {**comparison_spec(), **change}
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(frame, spec, design)
    assert caught.value.code == code


def test_missingness_and_nonstandard_index_are_accounted(frame, design):
    frame.index = [f'original-{i}' for i in range(len(frame))]
    frame.loc['original-2', 'mass'] = np.nan
    spec = comparison_spec()
    with pytest.raises(ast.AstetikError, match='exclusion policy'):
        ast.render(frame, spec, design)
    spec.update(missing='drop', missing_reason='Outcome was not recorded.')
    result = ast.render(frame, spec, design)
    assert result.receipt['observations']['used'] == 15
    assert len(result.receipt['observations']['excluded']) == 1
    assert len(result.data) == 16
    assert result.inspect(next(iter(result.marks)))['source_rows'] == [0]


def test_paired_design_requires_complete_subjects(design):
    frame = pd.DataFrame(
        {
            'subject': [1, 2, 3, 4] * 2,
            'group': ['Control'] * 4 + ['Treatment'] * 4,
            'mass': [4, 5, 7, 8, 5, 7, 8, 12],
        }
    )
    spec = comparison_spec()
    spec['key'] = ['subject', 'group']
    spec['analysis'].update(method='paired_t', subject='subject')
    result = ast.render(frame, spec, design)
    reference = stats.ttest_rel(frame.mass.iloc[4:].to_numpy(), frame.mass.iloc[:4].to_numpy())
    assert result.receipt['analysis']['contrast']['statistic'] == pytest.approx(reference.statistic)
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(frame.iloc[:-1], spec, design)
    assert caught.value.code == 'PAIRING_INCOMPLETE'


def test_catalog_and_cli_machine_errors(tmp_path):
    assert all(item['paper'] for item in ast.catalog()['plots'].values())
    assert ast.select('comparison')['scientific_method_required']
    data = tmp_path / 'data.csv'
    data.write_text('a\n1\n2\n')
    spec = tmp_path / 'spec.json'
    spec.write_text(json.dumps({'kind': 'hist', 'x': 'absent'}))
    process = subprocess.run(
        [
            sys.executable,
            '-m',
            'astetik._cli',
            'render',
            '--data',
            str(data),
            '--spec',
            str(spec),
            '--output',
            str(tmp_path / 'failed'),
        ],
        capture_output=True,
        text=True,
    )
    assert process.returncode == 2
    assert json.loads(process.stderr)['code'] == 'COLUMN_MISSING'
    assert not (tmp_path / 'failed').exists()


def test_datetime_trajectory_retains_exact_time_and_ignores_unplotted_metadata(tmp_path):
    frame = pd.DataFrame(
        {
            'sample': ['s1', 's2', 's3', 's4'],
            'time': pd.date_range('2026-01-01', periods=4, tz='UTC'),
            'value': [1.0, 2.0, 1.5, 2.5],
            'unplotted': [np.nan] * 4,
        }
    )
    spec = {
        'kind': 'longitudinal',
        'x': 'time',
        'y': 'value',
        'key': 'sample',
        'paper': True,
        'units': {'time': 'UTC', 'value': 'g'},
        'analysis': {'method': 'observed', 'observation_unit': 'sample'},
    }
    result = ast.render(frame, spec)
    assert result.receipt['analysis']['summary'][0]['time'] == frame.time.iloc[0].isoformat()
    bundle = result.write(tmp_path / 'temporal')
    pd.testing.assert_frame_equal(ast.replay(bundle).data, frame)


def test_receipt_and_inventory_tampering_cannot_be_replayed(frame, design, tmp_path):
    bundle = ast.render(frame, comparison_spec(), design).write(tmp_path / 'original')
    receipt_path = bundle / 'receipt.json'
    receipt = json.loads(receipt_path.read_text())
    receipt['caption'] = 'Unsupported scientific claim.'
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ast.AstetikError) as caught:
        ast.replay(bundle)
    assert caught.value.code == 'BUNDLE_CHANGED'


def test_legacy_module_uses_same_paper_contract():
    from astetik.plots.hist import hist

    result = hist(
        pd.DataFrame({'mass': [1.0, 2.0, 3.0]}), x='mass', units={'mass': 'g'}, paper=True
    )
    assert isinstance(result, ast.EvidenceResult)
    assert result.verify()['passed']


def test_physical_horizontal_axes_do_not_scale_categories():
    frame = pd.DataFrame({'group': ['a', 'b'], 'mass': [1.0, 2.0]})
    design = ast.Manifest(categories={'a': '#2A4A70', 'b': '#A54532'})
    spec = {
        'kind': 'bar',
        'x': 'group',
        'y': 'mass',
        'paper': True,
        'units': {'mass': 'g'},
        'options': {'orient': 'h'},
        'axes': {'y': {'scale': 'log'}},
    }
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(frame, spec, design)
    assert caught.value.code == 'AXIS_TYPE'


def test_object_measurements_require_preparation():
    with pytest.raises(ast.AstetikError) as caught:
        ast.hist(pd.DataFrame({'mass': ['1', '2', '3']}), x='mass', paper=True)
    assert caught.value.code == 'MEASUREMENT_DTYPE'


def test_axis_limits_include_uncertainty_intervals(design):
    frame = pd.DataFrame(
        {
            'sample': ['a', 'b', 'c', 'd'],
            'group': ['Control'] * 2 + ['Treatment'] * 2,
            'mass': [0.0, 1.0, 2.0, 3.0],
        }
    )
    spec = comparison_spec()
    spec['axes'] = {'y': {'limits': [-1, 4]}}
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(frame, spec, design)
    assert caught.value.code == 'AXIS_TRUNCATION'
    assert 'computed intervals' in str(caught.value)


def test_numeric_category_codes_do_not_become_numeric_axes():
    frame = pd.DataFrame({'group': [1, 2], 'mass': [1.0, 2.0]})
    spec = {'kind': 'bar', 'x': 'group', 'y': 'mass', 'axes': {'x': {'scale': 'log'}}}
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(frame, spec)
    assert caught.value.code == 'AXIS_TYPE'


def test_protocol_rejects_unused_method_fields_and_pooled_facets(frame, design):
    spec = comparison_spec()
    spec['analysis']['subject'] = 'sample'
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(frame, spec, design)
    assert caught.value.code == 'ANALYSIS_FIELDS'
    spec = comparison_spec()
    spec['col'] = 'group'
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(frame, spec, design)
    assert caught.value.code == 'ANALYSIS_FACETS'


def test_receipt_resealing_does_not_make_forged_claim_replayable(frame, design, tmp_path):
    from astetik._data import json_digest

    bundle = ast.render(frame, comparison_spec(), design).write(tmp_path / 'forged')
    path = bundle / 'receipt.json'
    receipt = json.loads(path.read_text())
    receipt.pop('bundle_receipt_sha256')
    receipt['caption'] = 'A fabricated claim.'
    receipt['bundle_receipt_sha256'] = json_digest(receipt)
    path.write_text(json.dumps(receipt))
    with pytest.raises(ast.AstetikError) as caught:
        ast.replay(bundle)
    assert caught.value.code == 'REPLAY_DIFFERENCE'


def test_replay_requires_exact_environment_unless_explicitly_recomputed(frame, design, tmp_path):
    from astetik._data import json_digest

    bundle = ast.render(frame, comparison_spec(), design).write(tmp_path / 'old-environment')
    path = bundle / 'receipt.json'
    receipt = json.loads(path.read_text())
    receipt.pop('bundle_receipt_sha256')
    receipt['environment']['python'] = '0.0.0'
    receipt['bundle_receipt_sha256'] = json_digest(receipt)
    path.write_text(json.dumps(receipt))
    with pytest.raises(ast.AstetikError) as caught:
        ast.replay(bundle)
    assert caught.value.code == 'ENVIRONMENT_CHANGED'
    assert (
        ast.replay(bundle, strict_environment=False).receipt['table_sha256']
        == receipt['table_sha256']
    )


def test_table_implicit_columns_include_measurements_despite_declared_key():
    frame = pd.DataFrame({'sample': ['s1', 's2'], 'mass': [1.0, 2.0]})
    with pytest.raises(ast.AstetikError) as caught:
        ast.table(frame, key='sample', paper=True)
    assert caught.value.code == 'UNITS_REQUIRED'
    assert ast.table(
        frame, key='sample', units={'mass': 'g'}, paper=True
    ).table.columns.tolist() == ['sample', 'mass']


def test_boolean_hue_is_a_category():
    frame = pd.DataFrame(
        {'a': [1.0, 2.0, 3.0, 4.0], 'b': [2.0, 3.0, 2.0, 5.0], 'flag': [True, False, True, False]}
    )
    design = ast.Manifest(categories={'True': '#2A4A70', 'False': '#A54532'})
    result = ast.scat(
        frame, x='a', y='b', hue='flag', units={'a': 'g', 'b': 'm'}, paper=True, manifest=design
    )
    assert len(result.figure.axes) == 1


def test_central_axis_styling_preserves_scientific_category_names(frame, design):
    comparison = ast.render(frame, comparison_spec(), design)
    assert [tick.get_text() for tick in comparison.figure.axes[0].get_xticklabels()] == [
        'Control',
        'Treatment',
    ]
    bar = ast.bar(frame, x='group', y='mass', paper=True, manifest=design, units={'mass': 'g'})
    assert [tick.get_text() for tick in bar.figure.axes[0].get_xticklabels()] == [
        'Control',
        'Treatment',
    ]
    correlation = ast.corr(
        frame, columns=['time', 'mass'], paper=True, units={'time': 'day', 'mass': 'g'}
    )
    assert [tick.get_text() for tick in correlation.figure.axes[0].get_xticklabels()] == [
        'time',
        'mass',
    ]
    assert [tick.get_text() for tick in correlation.figure.axes[0].get_yticklabels()] == [
        'time',
        'mass',
    ]


def test_ambient_matplotlib_settings_do_not_change_scientific_output(frame, design, tmp_path):
    original = ast.render(frame, comparison_spec(), design)
    original.write(tmp_path / 'ordinary')
    ambient = {
        'axes.grid': True,
        'font.family': 'monospace',
        'savefig.bbox': 'tight',
        'patch.edgecolor': 'magenta',
        'savefig.facecolor': 'red',
        'figure.dpi': 137,
        'axes.xmargin': 0.2,
        'svg.image_inline': False,
        'savefig.transparent': True,
    }
    with mpl.rc_context(ambient):
        changed = ast.render(frame, comparison_spec(), design)
        changed.write(tmp_path / 'ambient')
        assert changed.result_id == original.result_id
        assert changed._svg() == original._svg()
    for name in ('figure.svg', 'figure.pdf', 'figure.png'):
        assert (tmp_path / 'ordinary' / name).read_bytes() == (
            tmp_path / 'ambient' / name
        ).read_bytes()


def test_paper_type_floor_applies_to_titles_and_table_cells():
    from matplotlib.text import Text

    design = ast.Manifest(
        typography={'fontsize': 5, 'titlesize': 5, 'ticksize': 5}, paper={'min_fontsize': 9}
    )
    frame = pd.DataFrame({'mass': [1.0, 2.0]})
    for result in (
        ast.hist(frame, x='mass', title='Mass', units={'mass': 'g'}, paper=True, manifest=design),
        ast.table(frame, title='Mass', units={'mass': 'g'}, paper=True, manifest=design),
    ):
        assert result.verify()['passed']
        assert all(text.get_fontsize() >= 9 for text in result.figure.findobj(match=Text))
