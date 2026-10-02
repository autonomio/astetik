"""Category ordering validates JSON shape without changing observation evidence."""

import importlib.resources

import pandas as pd
import pytest

import astetik as ast


@pytest.fixture
def identifiers() -> pd.DataFrame:
    source = importlib.resources.files('astetik').joinpath('extras/countries.csv')
    with source.open('rb') as stream:
        countries = pd.read_csv(stream)
    frame = countries.loc[
        countries['alpha-3'].isin(['CAN', 'DEU', 'FIN', 'MEX', 'SWE', 'USA']),
        ['alpha-3', 'region'],
    ].reset_index(drop=True)
    frame.attrs['row_keys'] = ['alpha-3']
    assert len(frame) == 6
    return frame


@pytest.mark.parametrize(
    'order',
    [
        {'Europe': 1, 'Americas': 2},
        'Europe,Americas',
        1,
        [['Europe'], 'Americas'],
        [{'category': 'Europe'}, 'Americas'],
        [('Europe',), 'Americas'],
    ],
)
def test_malformed_order_is_rejected_before_rendering(
    identifiers: pd.DataFrame, order: object
) -> None:
    before = identifiers.copy(deep=True)
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(identifiers, {'kind': 'count', 'x': 'region', 'order': order})
    assert caught.value.code == 'SPEC_SCHEMA'
    assert 'order' in str(caught.value)
    pd.testing.assert_frame_equal(identifiers, before)


@pytest.mark.parametrize('orient', ['v', 'h'])
@pytest.mark.parametrize('order', [['Europe', 'Americas'], ('Europe', 'Americas')])
def test_valid_order_changes_positions_and_retains_exact_evidence(
    identifiers: pd.DataFrame, orient: str, order: list[str] | tuple[str, str]
) -> None:
    design = ast.Manifest(categories={'Europe': 'primary', 'Americas': 'secondary'})
    spec = {'kind': 'count', 'x': 'region', 'paper': True, 'options': {'orient': orient}}
    unordered = ast.render(identifiers, spec, design)
    ordered = ast.render(identifiers, {**spec, 'order': order}, design)
    axis = ordered.figure.axes[0]
    labels = axis.get_xticklabels() if orient == 'v' else axis.get_yticklabels()
    assert [label.get_text() for label in labels] == ['Europe', 'Americas']
    for result in (unordered, ordered):
        assert sorted(row for mark in result.marks.values() for row in mark['source_rows']) == list(
            range(len(identifiers))
        )
        assert sum(mark['values']['n'] for mark in result.marks.values()) == len(identifiers)
        pd.testing.assert_frame_equal(result.data, identifiers)
    before = {mark['values']['category']: mark for mark in unordered.marks.values()}
    after = {mark['values']['category']: mark for mark in ordered.marks.values()}
    assert after == before
    pd.testing.assert_frame_equal(
        ordered.table.drop(columns='mark_id').sort_values('category').reset_index(drop=True),
        unordered.table.drop(columns='mark_id').sort_values('category').reset_index(drop=True),
    )
    assert ordered.receipt['source'] == unordered.receipt['source']
    assert ordered.receipt['observations'] == unordered.receipt['observations']
    assert ordered.receipt['input_sha256'] == unordered.receipt['input_sha256']
    assert ordered.verify()['passed']


def test_null_order_retains_default_category_evidence(identifiers: pd.DataFrame) -> None:
    spec = {'kind': 'count', 'x': 'region'}
    default = ast.render(identifiers, spec)
    nullable = ast.render(identifiers, {**spec, 'order': None})
    assert nullable.marks == default.marks
    pd.testing.assert_frame_equal(nullable.table, default.table)
    assert nullable.receipt['source'] == default.receipt['source']
    assert nullable.receipt['observations'] == default.receipt['observations']
    assert [label.get_text() for label in nullable.figure.axes[0].get_xticklabels()] == [
        label.get_text() for label in default.figure.axes[0].get_xticklabels()
    ]
