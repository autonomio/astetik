"""Public specification boundaries retain observations and reject silent policies.

Geographic identifiers come from the shipped country/area snapshot. Deliberately
invalid copies below exercise preparation contracts; they are not study data.
"""

import copy
import importlib.resources

import numpy as np
import pandas as pd
import pytest

import astetik as ast


@pytest.fixture
def identifiers():
    source = importlib.resources.files('astetik').joinpath('extras/countries.csv')
    with source.open('rb') as stream:
        retained = pd.read_csv(stream)
    selected = retained.loc[retained['alpha-3'].isin(['FIN', 'SWE', 'DEU', 'JPN', 'NZL', 'USA'])]
    frame = selected[['alpha-3', 'country-code', 'region-code', 'region']].rename(
        columns={'alpha-3': 'country', 'country-code': 'code', 'region-code': 'region_code'}
    )
    frame = frame.copy()
    frame[['code', 'region_code']] = frame[['code', 'region_code']].astype(float)
    frame.index = [f'retained-{position}' for position in selected.index]
    frame.attrs.update(
        row_keys=['country'],
        units={'code': '1', 'region_code': '1'},
        descriptions={'code': 'Country code', 'region_code': 'Region code'},
    )
    assert len(frame) == 6
    return frame


@pytest.fixture
def region_design():
    return ast.Manifest(
        colors={'positive': '#2D7D60'},
        categories={
            'Europe': 'primary',
            'Asia': 'secondary',
            'Oceania': 'positive',
            'Americas': 'negative',
        },
    )


def scatter_spec(**fields):
    return {'kind': 'scat', 'x': 'code', 'y': 'region_code', **fields}


@pytest.mark.parametrize(
    'document,code',
    [
        (None, 'SPEC_SCHEMA'),
        ([], 'SPEC_SCHEMA'),
        ('hist', 'SPEC_SCHEMA'),
        ({'kind': 'unknown'}, 'PLOT_KIND'),
        ({'kind': None}, 'PLOT_KIND'),
        ({'kind': 'hist', 'schema_version': '2.0'}, 'SPEC_VERSION'),
        ({'kind': 'hist', 'x': 'code', 'sampling': 'automatic'}, 'SPEC_SCHEMA'),
        ({'kind': 'hist', 'x': 'code', 'labels': {'z': 'Depth'}}, 'SPEC_SCHEMA'),
        ({'kind': 'hist', 'x': 'code', 'labels': {'x': 1}}, 'SPEC_SCHEMA'),
        ({'kind': 'hist', 'x': 'code', 'labels': []}, 'SPEC_SCHEMA'),
        ({'kind': 'hist', 'x': 'code', 'units': {'code': False}}, 'SPEC_SCHEMA'),
        ({'kind': 'hist', 'x': 'code', 'descriptions': {'code': None}}, 'SPEC_SCHEMA'),
        ({'kind': 'hist', 'x': 'code', 'options': []}, 'SPEC_SCHEMA'),
        ({'kind': 'hist', 'x': 'code', 'title': ['A title']}, 'SPEC_SCHEMA'),
        ({'kind': 'hist', 'x': 'code', 'subtitle': 5}, 'SPEC_SCHEMA'),
        ({'kind': 'hist', 'x': 'code', 'legend': 1}, 'SPEC_SCHEMA'),
        ({'kind': 'hist', 'x': 'code', 'missing': 'impute'}, 'MISSING_POLICY'),
        ({'kind': 'hist', 'x': 'code', 'missing': None}, 'MISSING_POLICY'),
        ({'kind': 'hist', 'x': 'code', 'missing': 'drop'}, 'EXCLUSION_REASON'),
        (
            {'kind': 'hist', 'x': 'code', 'missing': 'drop', 'missing_reason': ' '},
            'EXCLUSION_REASON',
        ),
        ({'kind': 'hist', 'x': 'code', 'missing_reason': 1}, 'SPEC_SCHEMA'),
        ({'kind': 'hist', 'x': 'code', 'paper': 1}, 'PAPER_PRESET'),
        ({'kind': 'hist', 'x': 'code', 'paper': 'poster'}, 'PAPER_PRESET'),
        ({'kind': 'hist', 'x': 'code', 'key': ['country', 'country']}, 'KEY_SCHEMA'),
        ({'kind': 'hist', 'x': 'code', 'key': ['country', 1]}, 'KEY_SCHEMA'),
        ({'kind': 'hist', 'x': 'code', 'key': {'country': True}}, 'KEY_SCHEMA'),
    ],
)
def test_invalid_documents_have_machine_readable_failure(identifiers, document, code):
    before = identifiers.copy(deep=True)
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, document)
    failure = caught.value.to_dict()
    assert failure['code'] == code
    assert failure['message']
    assert isinstance(failure['details'], dict)
    pd.testing.assert_frame_equal(identifiers, before)


@pytest.mark.parametrize('field', ['x', 'y', 'hue', 'row', 'col'])
def test_column_roles_do_not_coerce_non_names(identifiers, field):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, scatter_spec(**{field: 7}))
    assert caught.value.code == 'COLUMN_SCHEMA'


@pytest.mark.parametrize('columns', ['code', ['code', 'code'], ['code', 1]])
def test_column_selection_is_an_explicit_distinct_list(identifiers, columns):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, {'kind': 'table', 'columns': columns})
    assert caught.value.code == 'COLUMN_SCHEMA'


@pytest.mark.parametrize(
    'axes,code',
    [
        ([], 'SPEC_SCHEMA'),
        ({'z': {'scale': 'log'}}, 'AXIS_SCHEMA'),
        ({'x': 'log'}, 'AXIS_SCHEMA'),
        ({'x': {'offset': 1}}, 'AXIS_SCHEMA'),
        ({'x': {'scale': 'sqrt'}}, 'AXIS_SCALE'),
        ({'x': {'limits': [1]}}, 'AXIS_LIMITS'),
        ({'x': {'limits': [10, 1]}}, 'AXIS_LIMITS'),
        ({'x': {'limits': [1, 1]}}, 'AXIS_LIMITS'),
        ({'x': {'limits': ['1', '10']}}, 'AXIS_LIMITS'),
        ({'x': {'limits': [False, 10]}}, 'AXIS_LIMITS'),
        ({'x': {'limits': [0, np.inf]}}, 'SPEC_SCHEMA'),
        ({'x': {'limits': [np.nan, 10]}}, 'SPEC_SCHEMA'),
    ],
)
def test_axis_grammar_rejects_ambiguous_domains(identifiers, axes, code):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, scatter_spec(axes=axes))
    assert caught.value.code == code


@pytest.mark.parametrize(
    'kind,fields,reason',
    [
        ('hist', {'y': 'region_code'}, 'y is unsupported'),
        ('scat', {'columns': ['code']}, 'columns is unsupported'),
        ('scat', {'order': ['Europe']}, 'Category order does not apply'),
        ('scat', {'options': {'col_wrap': 2}}, 'col_wrap requires'),
        ('scat', {'options': {'hue_mode': 'continuous'}}, 'hue_mode requires'),
        ('count', {'x': 'region', 'y': 'code'}, 'y is unsupported'),
        ('count', {'x': 'region', 'order': ['Europe']}, 'every observed category'),
        ('count', {'x': 'region', 'order': ['Europe', 'Europe']}, 'distinct category'),
        ('regs', {'hue': 'region', 'options': {'draw_scatter': False}}, 'displayed observations'),
    ],
)
def test_inapplicable_fields_are_not_silently_discarded(identifiers, kind, fields, reason):
    specification = {'kind': kind, 'x': 'code', **fields}
    if kind in {'scat', 'regs'}:
        specification['y'] = 'region_code'
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, specification)
    assert caught.value.code == 'PLOT_CONTRACT'
    assert reason in caught.value.details['reason']


@pytest.mark.parametrize(
    'kind,options',
    [
        ('hist', {'bins': True}),
        ('hist', {'bins': 0}),
        ('hist', {'bins': [10, 10, 1000]}),
        ('hist', {'density': 'yes'}),
        ('hist', {'kde': True, 'density': False}),
        ('kde', {'bw_method': 0}),
        ('kde', {'bw_method': 'automatic'}),
        ('kde', {'gridsize': 15}),
        ('kde', {'cut': -1}),
        ('scat', {'point_size': False}),
        ('scat', {'alpha': 1.1}),
        ('scat', {'hue_mode': 'infer'}),
        ('line', {'sort': 1}),
        ('line', {'linewidth': 0}),
        ('strip', {'jitter': 0.5}),
        ('bar', {'estimator': 'trimmed_mean'}),
        ('bar', {'errorbar': 'ci'}),
        ('regs', {'fit_reg': False, 'draw_scatter': False}),
    ],
)
def test_numerical_policies_cannot_be_guessed(identifiers, kind, options):
    specification = {'kind': kind, 'x': 'code', 'options': options}
    if kind not in {'hist', 'kde'}:
        specification['y'] = 'region_code'
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, specification)
    assert caught.value.code == 'PLOT_CONTRACT'
    assert caught.value.details['kind'] == kind
    assert caught.value.details['reason']


def test_unknown_plot_options_include_recovery_grammar(identifiers):
    with pytest.raises(ast.AstetikError) as caught:
        ast.plot(identifiers, 'hist', x='code', options={'trim': 0.1}, mystery=True)
    assert caught.value.code == 'PLOT_OPTIONS'
    assert caught.value.details['fields'] == ['mystery', 'trim']
    assert caught.value.details['allowed'] == ast.catalog()['plots']['hist']['options']


def test_user_text_is_retained_without_interpretation(identifiers):
    text = '__import__("os").system("forbidden")'
    result = ast.plot(
        identifiers, 'scat', x='code', y='region_code', title=text, subtitle='${HOME}'
    )
    assert result.spec['title'] == text
    assert result.spec['subtitle'] == '${HOME}'
    assert text + '\n${HOME}' in [item.get_text() for item in result.figure.texts]
    assert result.receipt['observations']['used'] == 6


def test_non_json_callbacks_are_rejected_without_execution(identifiers):
    calls = []

    class Callback:
        def __call__(self):
            calls.append('call')
            raise AssertionError('Specifications must not call objects.')

        def __float__(self):
            calls.append('float')
            raise AssertionError('Specifications must not coerce objects.')

    callback = Callback()
    for document in (
        {'kind': 'hist', 'x': 'code', 'options': {'bins': callback}},
        scatter_spec(title=callback),
        scatter_spec(axes={'x': {'limits': [callback, 1000]}}),
    ):
        with pytest.raises(ast.AstetikError) as caught:
            ast.render(identifiers, document)
        assert caught.value.code == 'SPEC_SCHEMA'
    assert calls == []


def test_untrusted_data_properties_are_not_evaluated():
    calls = []

    class Callback:
        @property
        def data(self):
            calls.append('data')
            raise AssertionError('Input detection must not execute descriptors.')

        @property
        def receipt(self):
            calls.append('receipt')
            raise AssertionError('Input detection must not execute descriptors.')

    with pytest.raises(ast.AstetikError) as caught:
        ast.render(Callback(), {'kind': 'hist', 'x': 'code'})
    assert caught.value.code == 'INVALID_DATA'
    assert calls == []


@pytest.mark.parametrize(
    'field,value',
    [
        ('row_keys', {'country': True}),
        ('row_keys', ['absent']),
        ('units', ['1']),
        ('descriptions', 'Country metadata'),
        ('units', {'code': 1}),
        ('descriptions', {'code': False}),
    ],
)
def test_preparation_metadata_must_match_its_declared_schema(identifiers, field, value):
    identifiers.attrs[field] = value
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, scatter_spec())
    assert caught.value.code == 'INVALID_METADATA'


@pytest.mark.parametrize('invalid_key', ['absent', ['country', 'absent']])
def test_declared_keys_cannot_reference_missing_columns(identifiers, invalid_key):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, scatter_spec(key=invalid_key))
    assert caught.value.code == 'COLUMN_MISSING'
    assert caught.value.details['columns'] == ['absent']


@pytest.mark.parametrize('mutation', ['duplicate', 'missing'])
def test_incomplete_or_duplicate_keys_cannot_be_hidden_by_exclusion(identifiers, mutation):
    if mutation == 'duplicate':
        identifiers.iloc[1, identifiers.columns.get_loc('country')] = identifiers.iloc[0]['country']
    else:
        identifiers.iloc[1, identifiers.columns.get_loc('country')] = None
    identifiers.iloc[1, identifiers.columns.get_loc('code')] = np.nan
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, scatter_spec(missing='drop', missing_reason='Code unavailable.'))
    assert caught.value.code == 'KEY_INVALID'
    assert caught.value.details['key'] == ['country']


def test_metadata_unit_override_requires_actual_preparation(identifiers):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, scatter_spec(units={'code': 'kg'}))
    assert caught.value.code == 'UNIT_CONFLICT'
    assert caught.value.details['units'] == {'code': ['1', 'kg']}


def test_descriptions_and_labels_override_without_relabelling_units(identifiers):
    result = ast.render(
        identifiers,
        scatter_spec(
            paper=True,
            descriptions={'code': 'Numeric country identifier'},
            labels={'y': 'Geographic region identifier'},
        ),
    )
    assert result.receipt['units'] == {'code': '1', 'region_code': '1'}
    assert result.receipt['descriptions']['code'] == 'Numeric country identifier'
    assert result.figure.axes[0].get_xlabel() == 'Numeric country identifier'
    assert result.figure.axes[0].get_ylabel() == 'Geographic region identifier'
    assert identifiers.attrs['descriptions']['code'] == 'Country code'


def test_missingness_is_limited_to_declared_fields_and_replayed_exactly(
    identifiers, region_design, tmp_path
):
    identifiers['unused'] = np.nan
    identifiers.iloc[1, identifiers.columns.get_loc('code')] = np.nan
    identifiers.iloc[4, identifiers.columns.get_loc('region_code')] = np.nan
    before = identifiers.copy(deep=True)
    specification = scatter_spec(paper=True, hue='region')
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, specification, region_design)
    assert caught.value.code == 'MISSING_DATA'
    assert caught.value.details['rows'] == 2
    assert caught.value.details['columns'] == ['code', 'region_code']
    specification.update(
        missing='drop', missing_reason='Identifier absent from the retained snapshot.'
    )
    result = ast.render(identifiers, specification, region_design)
    expected_positions = [0, 2, 3, 5]
    expected_keys = [
        {'country': identifiers.iloc[position]['country']} for position in expected_positions
    ]
    accounting = result.receipt['observations']
    assert accounting == {
        'input': 6,
        'used': 4,
        'excluded': [{'country': identifiers.iloc[position]['country']} for position in [1, 4]],
        'missing_policy': 'drop',
        'reason': specification['missing_reason'],
    }
    by_position = {mark['source_rows'][0]: mark for mark in result.marks.values()}
    assert sorted(by_position) == expected_positions
    assert [
        by_position[position]['source_keys'][0] for position in expected_positions
    ] == expected_keys
    for position, mark in by_position.items():
        assert mark['values']['code'] == identifiers.iloc[position]['code']
        assert mark['values']['region_code'] == identifiers.iloc[position]['region_code']
    assert sorted(row for rows in result.table['source_rows'] for row in rows) == expected_positions
    pd.testing.assert_frame_equal(identifiers, before)
    pd.testing.assert_frame_equal(result.data, before)
    assert result.spec['key'] == ['country']
    assert 'key' not in specification
    bundle = result.write(tmp_path / 'retained-identifiers')
    repeated = ast.replay(bundle)
    assert repeated.receipt['observations'] == accounting
    assert repeated.receipt['units'] == result.receipt['units']
    assert repeated.marks == result.marks
    assert repeated.svg_bytes() == result.svg_bytes()
    pd.testing.assert_frame_equal(repeated.data, before)


@pytest.mark.parametrize('value', [np.inf, -np.inf])
def test_nonfinite_values_require_preparation_even_with_missing_drop(identifiers, value):
    identifiers.iloc[1, identifiers.columns.get_loc('code')] = value
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(
            identifiers, scatter_spec(missing='drop', missing_reason='Incomplete identifiers.')
        )
    assert caught.value.code == 'NONFINITE_DATA'
    assert caught.value.details['column'] == 'code'


def test_all_missing_selected_values_cannot_produce_an_empty_result(identifiers):
    identifiers['code'] = np.nan
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, scatter_spec(missing='drop', missing_reason='Code unavailable.'))
    assert caught.value.code == 'EMPTY_DATA'


def test_string_identifiers_are_not_implicitly_converted_into_measurements(identifiers):
    identifiers['code'] = identifiers['code'].astype(str)
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, scatter_spec())
    assert caught.value.code == 'MEASUREMENT_DTYPE'
    assert caught.value.details['column'] == 'code'


def test_explicit_histogram_edges_cannot_exclude_observations(identifiers):
    bounds = [identifiers.code.min() + 1, identifiers.code.max()]
    with pytest.raises(ast.AstetikError) as caught:
        ast.plot(identifiers, 'hist', x='code', bins=bounds)
    assert caught.value.code == 'PLOT_CONTRACT'
    assert 'cover every observation' in caught.value.details['reason']


def test_final_bin_includes_right_endpoint_and_retains_exact_keys(identifiers):
    low, high = identifiers.code.min(), identifiers.code.max()
    middle = (low + high) / 2
    result = ast.plot(identifiers, 'hist', x='code', bins=[low, middle, high])
    assert sum(mark['values']['n'] for mark in result.marks.values()) == len(identifiers)
    positions = [row for mark in result.marks.values() for row in mark['source_rows']]
    assert sorted(positions) == list(range(len(identifiers)))
    high_position = int(np.flatnonzero(identifiers.code.to_numpy() == high)[0])
    last = list(result.marks.values())[-1]
    assert high_position in last['source_rows']
    assert {'country': identifiers.iloc[high_position]['country']} in last['source_keys']
    assert result.receipt['methods']['plot']['histogram']['final_bin_right_closed'] is True


def test_axis_limits_fail_before_hiding_a_retained_observation(identifiers):
    bounds = [float(identifiers.code.min() + 1), float(identifiers.code.max())]
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, scatter_spec(axes={'x': {'limits': bounds}}))
    assert caught.value.code == 'AXIS_TRUNCATION'
    assert caught.value.details['column'] == 'code'
    assert caught.value.details['observed'] == [identifiers.code.min(), identifiers.code.max()]


def test_explicit_log_domain_preserves_all_observations_and_caller_spec(identifiers):
    specification = scatter_spec(axes={'x': {'scale': 'log'}}, options={'point_size': 24})
    before = copy.deepcopy(specification)
    result = ast.render(identifiers, specification)
    assert result.figure.axes[0].get_xscale() == 'log'
    assert sorted(mark['source_rows'][0] for mark in result.marks.values()) == list(range(6))
    assert specification == before
    assert result.spec['axes'] == {'x': {'scale': 'log'}}
    assert result.receipt['observations']['excluded'] == []


@pytest.mark.parametrize('value', [0, -1])
def test_logarithmic_domains_do_not_remove_nonpositive_values(identifiers, value):
    identifiers.iloc[0, identifiers.columns.get_loc('code')] = value
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, scatter_spec(axes={'x': {'scale': 'log'}}))
    assert caught.value.code == 'LOG_DOMAIN'
    assert caught.value.details['column'] == 'code'


@pytest.mark.parametrize(
    'kind,fields,axes,code',
    [
        ('hist', {'x': 'code'}, {'y': {'scale': 'log'}}, 'DERIVED_AXIS'),
        ('hist', {'x': 'code'}, {'y': {'limits': [0, 10]}}, 'DERIVED_AXIS'),
        ('count', {'x': 'region'}, {'x': {'scale': 'log'}}, 'AXIS_TYPE'),
        ('bar', {'x': 'region', 'y': 'code'}, {'y': {'scale': 'log'}}, 'BAR_BASELINE'),
        (
            'bar',
            {'x': 'region', 'y': 'code', 'options': {'orient': 'h'}},
            {'x': {'scale': 'log'}},
            'BAR_BASELINE',
        ),
        ('pie', {'x': 'region'}, {'x': {'limits': [0, 1]}}, 'DERIVED_AXIS'),
        ('table', {'columns': ['country']}, {'y': {'scale': 'log'}}, 'DERIVED_AXIS'),
    ],
)
def test_axis_roles_preserve_categories_computed_domains_and_bar_baselines(
    identifiers, kind, fields, axes, code
):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, {'kind': kind, **fields, 'axes': axes})
    assert caught.value.code == code


@pytest.mark.parametrize('policy,code', [('limits', 'AXIS_TRUNCATION'), ('scale', 'LOG_DOMAIN')])
def test_computed_density_support_is_included_in_axis_policy(identifiers, policy, code):
    axes = (
        {'limits': [float(identifiers.code.min()), float(identifiers.code.max())]}
        if policy == 'limits'
        else {'scale': 'log'}
    )
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(
            identifiers, {'kind': 'kde', 'x': 'code', 'options': {'cut': 3}, 'axes': {'x': axes}}
        )
    assert caught.value.code == code
    assert caught.value.details['axis'] == 'x'
    if policy == 'limits':
        assert caught.value.details['rendered'][0] < identifiers.code.min()
        assert caught.value.details['rendered'][1] > identifiers.code.max()


@pytest.mark.parametrize('policy', [None, 0, 1, 'false'])
def test_replay_environment_policy_is_boolean_before_bundle_access(tmp_path, policy):
    with pytest.raises(ast.AstetikError) as caught:
        ast.replay(tmp_path / 'absent', strict_environment=policy)
    assert caught.value.code == 'REPLAY_POLICY'


def test_inference_requires_a_research_protocol_kind(identifiers):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(
            identifiers,
            {
                'kind': 'hist',
                'x': 'code',
                'analysis': {'method': 'welch', 'observation_unit': 'country/area'},
            },
        )
    assert caught.value.code == 'ANALYSIS_KIND'


@pytest.mark.parametrize(
    'plan,code',
    [
        (None, 'ANALYSIS_SCHEMA'),
        ([], 'ANALYSIS_SCHEMA'),
        ({'method': 'pearson', 'observation_unit': 'country/area', 'seed': 7}, 'ANALYSIS_SCHEMA'),
        ({'method': 'automatic', 'observation_unit': 'country/area'}, 'METHOD_REQUIRED'),
        ({'method': 'pearson', 'observation_unit': ' '}, 'OBSERVATION_UNIT_REQUIRED'),
        (
            {'method': 'pearson', 'observation_unit': 'country/area', 'confidence': True},
            'CONFIDENCE',
        ),
        ({'method': 'pearson', 'observation_unit': 'country/area', 'confidence': 0}, 'CONFIDENCE'),
        ({'method': 'pearson', 'observation_unit': 'country/area', 'confidence': 1}, 'CONFIDENCE'),
        (
            {'method': 'spearman', 'observation_unit': 'country/area', 'confidence': 0.95},
            'ANALYSIS_FIELDS',
        ),
    ],
)
def test_analysis_plan_fields_are_validated_before_inference(identifiers, plan, code):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, {**scatter_spec(), 'kind': 'association', 'analysis': plan})
    assert caught.value.code == code
    if code == 'ANALYSIS_FIELDS':
        assert caught.value.details['fields'] == ['confidence']
    if code == 'ANALYSIS_SCHEMA' and isinstance(plan, dict):
        assert caught.value.details['fields'] == ['seed']


@pytest.mark.parametrize('options', [{'sort': False}, {'drawstyle': 'steps'}])
def test_observed_trajectory_does_not_reinterpret_connection_method(identifiers, options):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(
            identifiers,
            {
                **scatter_spec(),
                'kind': 'longitudinal',
                'options': options,
                'analysis': {'method': 'observed', 'observation_unit': 'country/area'},
            },
        )
    assert caught.value.code == 'TRAJECTORY_METHOD'
