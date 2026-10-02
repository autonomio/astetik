"""Original input positions survive exclusions in every evidence surface."""

from contextlib import ExitStack

import pandas as pd
import pytest
from matplotlib import pyplot as plt

import astetik as ast


def test_excluded_kde_rows_match_method_marks_and_summary():
    data = pd.DataFrame(
        {
            'id': [f'row-{i}' for i in range(7)],
            'x': [0.0, None, 1.0, 2.0, 3.0, 4.0, 5.0],
            'y': [0.0, 1.0, 1.0, 4.0, 2.0, 5.0, 3.0],
        },
        index=[10, 20, 30, 40, 50, 60, 70],
    )
    result = ast.render(
        data,
        {
            'kind': 'kde',
            'x': 'x',
            'y': 'y',
            'key': 'id',
            'missing': 'drop',
            'missing_reason': 'One coordinate was unrecorded.',
            'options': {'gridsize': 16},
        },
    )
    with ExitStack() as cleanup:
        cleanup.callback(plt.close, result.figure)
        expected = [0, 2, 3, 4, 5, 6]
        assert result.receipt['observations']['excluded'] == [{'id': 'row-1'}]
        fits = result.receipt['methods']['plot']['kde_fits']
        assert len(fits) == 1 and fits[0]['source_rows'] == expected
        assert len(result.marks) == len(result.table) == 16**2
        for mark in result.marks.values():
            assert mark['source_rows'] == expected
            assert mark['source_keys'] == [{'id': f'row-{i}'} for i in expected]
        assert all(rows == expected for rows in result.table['source_rows'])


def test_pie_denominator_and_category_origins_use_original_rows():
    data = pd.DataFrame(
        {
            'id': ['first', 'missing', 'second', 'third'],
            'group': ['A', 'A', 'A', 'B'],
            'value': [1.0, None, 2.0, 3.0],
        }
    )
    result = ast.render(
        data,
        {
            'kind': 'pie',
            'x': 'group',
            'y': 'value',
            'key': 'id',
            'missing': 'drop',
            'missing_reason': 'One sector contribution was unrecorded.',
        },
        ast.Manifest(categories={'A': 'primary', 'B': 'secondary'}),
    )
    with ExitStack() as cleanup:
        cleanup.callback(plt.close, result.figure)
        assert result.receipt['observations']['excluded'] == [{'id': 'missing'}]
        for identifier, mark in result.marks.items():
            expected = [0, 2] if mark['values']['category'] == 'A' else [3]
            assert mark['source_rows'] == [0, 2, 3]
            assert mark['values']['category_source_rows'] == expected
            assert mark['values']['fraction'] == 0.5
            summary = result.table.loc[result.table['mark_id'].eq(identifier)].iloc[0]
            assert summary['source_rows'] == [0, 2, 3]
            assert summary['category_source_rows'] == expected


def test_animation_pie_nested_origins_identify_original_poster_row():
    data = pd.DataFrame(
        {
            'id': ['first', 'missing', 'poster', 'last'],
            'a': [1.0, None, 2.0, 3.0],
            'b': [3.0, 4.0, 2.0, 1.0],
        }
    )
    result = ast.render(
        data,
        {
            'kind': 'animate',
            'x': 'a',
            'y': 'b',
            'key': 'id',
            'units': {'a': 'g', 'b': 'g'},
            'missing': 'drop',
            'missing_reason': 'An animation quantity was unrecorded.',
            'options': {'frame': 1, 'plot_type': 'pie'},
        },
        ast.Manifest(categories={'a': 'primary', 'b': 'secondary'}),
    )
    with ExitStack() as cleanup:
        cleanup.callback(plt.close, result.figure)
        for mark in result.marks.values():
            assert mark['source_rows'] == [2]
            assert mark['source_keys'] == [{'id': 'poster'}]
            assert mark['values']['category_source_rows'] == [2]
        assert all(rows == [2] for rows in result.table['source_rows'])
        assert all(rows == [2] for rows in result.table['category_source_rows'])


@pytest.mark.parametrize('kind', ['table', 'text'])
def test_user_source_rows_column_is_literal_data(kind):
    data = pd.DataFrame(
        {
            'id': ['first', 'excluded', 'last'],
            'name': ['A', None, 'B'],
            'source_rows': [[88, 89], [55], [77]],
            'category_source_rows': [[9], [8], [7]],
        }
    )
    columns = ['name', 'source_rows', 'category_source_rows']
    result = ast.render(
        data,
        {
            'kind': kind,
            'x': 'name',
            'columns': columns,
            'key': 'id',
            'missing': 'drop',
            'missing_reason': 'One name was unrecorded.',
        },
    )
    with ExitStack() as cleanup:
        cleanup.callback(plt.close, result.figure)
        pd.testing.assert_frame_equal(
            result.table, data.loc[[0, 2], columns].reset_index(drop=True)
        )
        assert result.data['source_rows'].tolist() == [[88, 89], [55], [77]]
        assert {tuple(mark['source_rows']) for mark in result.marks.values()} == {(0,), (2,)}
        assert {mark['source_keys'][0]['id'] for mark in result.marks.values()} == {'first', 'last'}
