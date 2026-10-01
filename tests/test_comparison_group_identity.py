"""Comparison identities preserve retained metadata without claiming a research study."""

from __future__ import annotations

import importlib.resources
from pathlib import Path

import pandas as pd
import pytest
from scipy import stats

import astetik as ast


@pytest.fixture
def countries() -> pd.DataFrame:
    resource = importlib.resources.files('astetik').joinpath('extras/countries.csv')
    with resource.open('rb') as source:
        retained = pd.read_csv(source)
    frame = retained.loc[
        retained['alpha-3'].isin(['CAN', 'COL', 'DEU', 'FIN', 'MEX', 'NOR', 'SWE', 'USA']),
        ['alpha-3', 'country-code', 'region-code', 'region'],
    ].reset_index(drop=True)
    frame.attrs.update(row_keys=['alpha-3'], units={'country-code': '1', 'region-code': '1'})
    assert len(frame) == 8
    return frame


def _spec(groups: list[object], **fields: object) -> dict[str, object]:
    return {
        'kind': 'comparison',
        'x': 'group',
        'y': 'country-code',
        'analysis': {
            'method': 'welch',
            'groups': groups,
            'observation_unit': 'retained identifier',
        },
        **fields,
    }


def _accounting(result: ast.EvidenceResult, data: pd.DataFrame) -> None:
    observed = [mark for mark in result.marks.values() if mark['kind'] == 'observation']
    estimates = [mark for mark in result.marks.values() if mark['kind'] == 'estimate']
    assert sorted(mark['source_rows'][0] for mark in observed) == list(range(len(data)))
    assert sum(mark['values']['n'] for mark in estimates) == len(data)
    assert all(len(mark['source_rows']) == mark['values']['n'] for mark in estimates)
    assert sorted(row for mark in estimates for row in mark['source_rows']) == list(
        range(len(data))
    )
    assert sum(row['n'] for row in result.receipt['analysis']['summary']) == len(data)
    assert result.receipt['observations']['used'] == len(data)
    assert len(result.table.loc[result.table['mark_kind'] == 'observation']) == len(data)
    pd.testing.assert_frame_equal(result.data, data)


@pytest.mark.parametrize('encoding', ['numeric-string', 'boolean-number', 'boolean-string'])
@pytest.mark.parametrize('shadow_first', [False, True])
def test_undeclared_typed_group_cannot_hide_behind_encounter_order(
    countries: pd.DataFrame, encoding: str, shadow_first: bool
) -> None:
    countries['group'] = (
        countries['region-code']
        if encoding == 'numeric-string'
        else countries['region'].eq('Europe')
    ).astype(object)
    position = countries.index[countries['alpha-3'] == 'MEX'][0]
    original = countries.loc[position, 'group']
    countries.loc[position, 'group'] = (
        int(original) if encoding == 'boolean-number' else str(original)
    )
    if shadow_first:
        countries = pd.concat(
            [countries.iloc[[position]], countries.drop(index=position)]
        ).reset_index(drop=True)
    groups = [19.0, 150.0] if encoding == 'numeric-string' else [False, True]
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(countries, _spec(groups))
    assert caught.value.code == 'GROUPS_MISMATCH'
    assert len(caught.value.details['observed']) == 3


@pytest.mark.parametrize('groups', [[True, 1], [False, 0], [19, 19.0]])
def test_python_equal_declarations_remain_rejected(
    countries: pd.DataFrame, groups: list[object]
) -> None:
    countries['group'] = countries['region-code']
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(countries, _spec(groups))
    assert caught.value.code == 'GROUPS_REQUIRED'


def test_boolean_order_cannot_relabel_groups_as_numbers(countries: pd.DataFrame) -> None:
    countries['group'] = countries['region'].eq('Europe')
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(countries, _spec([False, True], order=[0, 1]))
    assert caught.value.code == 'PLOT_CONTRACT'
    assert 'order' in caught.value.details['reason']


@pytest.mark.parametrize(
    'native_type,groups,order',
    [('float', [19, 150], [150, 19]), ('int', [19.0, 150.0], [150.0, 19.0])],
)
def test_json_number_representations_share_identity_and_exact_sample_accounting(
    countries: pd.DataFrame, native_type: str, groups: list[object], order: list[object]
) -> None:
    countries['group'] = countries['region-code'].astype(native_type)
    design = ast.Manifest(
        categories={
            str(value): role
            for value, role in zip(groups, ['primary', 'secondary'])
        }
    )
    result = ast.render(countries, _spec(groups, order=order, paper=True), design)
    _accounting(result, countries)
    first = countries.loc[countries['group'] == groups[0], 'country-code']
    second = countries.loc[countries['group'] == groups[1], 'country-code']
    reference = stats.ttest_ind(second, first, equal_var=False)
    contrast = result.receipt['analysis']['contrast']
    assert contrast['statistic'] == pytest.approx(reference.statistic)
    assert contrast['p_value'] == pytest.approx(reference.pvalue)
    assert [contrast['lower'], contrast['upper']] == pytest.approx(reference.confidence_interval())
    assert [label.get_text() for label in result.figure.axes[0].get_xticklabels()] == [
        str(value) for value in order
    ]


def test_valid_boolean_groups_retain_exact_evidence_under_strict_replay(
    countries: pd.DataFrame, tmp_path: Path
) -> None:
    countries['group'] = countries['region'].eq('Europe')
    result = ast.render(
        countries,
        _spec([False, True], paper=True),
        ast.Manifest(categories={'False': 'primary', 'True': 'secondary'}),
    )
    _accounting(result, countries)
    bundle = result.write(tmp_path / 'boolean-groups')
    replayed = ast.replay(bundle)
    assert replayed.result_id == result.result_id
    assert replayed.marks == result.marks
    assert replayed.svg_bytes() == result.svg_bytes()
    pd.testing.assert_frame_equal(replayed.table, result.table)


def test_paired_retained_fields_preserve_the_existing_t_formula(countries: pd.DataFrame) -> None:
    paired = countries.melt(
        id_vars='alpha-3',
        value_vars=['country-code', 'region-code'],
        var_name='field',
        value_name='value',
    )
    paired.attrs.update(row_keys=['alpha-3', 'field'], units={'value': '1'})
    result = ast.render(
        paired,
        {
            'kind': 'comparison',
            'x': 'field',
            'y': 'value',
            'paper': True,
            'analysis': {
                'method': 'paired_t',
                'groups': ['country-code', 'region-code'],
                'subject': 'alpha-3',
                'observation_unit': 'retained identifier',
            },
        },
        ast.Manifest(categories={'country-code': 'primary', 'region-code': 'secondary'}),
    )
    reference = stats.ttest_rel(countries['region-code'], countries['country-code'])
    contrast = result.receipt['analysis']['contrast']
    assert contrast['statistic'] == pytest.approx(reference.statistic)
    assert contrast['p_value'] == pytest.approx(reference.pvalue)
    assert [contrast['lower'], contrast['upper']] == pytest.approx(reference.confidence_interval())
    assert contrast['n'] == len(countries)
    _accounting(result, paired)
