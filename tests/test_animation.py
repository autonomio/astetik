import pandas as pd
import pytest

import astetik as ast


def test_paper_poster_and_animation_have_original_row_provenance(tmp_path):
    data = pd.DataFrame({'a': [1.0, 2.0], 'b': [3.0, 4.0], 'year': [2020, 2021]})
    manifest = ast.Manifest(categories={'a': '#2A4A70', 'b': '#A54532'})
    result = ast.animate(
        data, x='a', y='b', paper=True, manifest=manifest, units={'a': 'g', 'b': 'g'}, frame=1
    )
    assert {mark['source_rows'][0] for mark in result.marks.values()} == {1}
    assert {mark['source_field'] for mark in result.marks.values()} == {'a', 'b'}
    animation = ast.Animation(
        data, 'a', 'b', 'year', paper=True, manifest=manifest, units={'a': 'g', 'b': 'g'}, frame=1
    )
    assert animation.poster.receipt['methods']['plot']['poster']['frame'] == 1
    directory = animation.write(tmp_path / 'animated')
    assert (directory / 'animation.gif').is_file()
    assert (directory / 'frame-0000' / 'receipt.json').is_file()
    with pytest.raises(ast.AstetikError) as caught:
        animation.write(directory)
    assert caught.value.code == 'OUTPUT_EXISTS'


def test_animation_never_executes_user_callbacks():
    def forbidden(*args, **kwargs):
        raise AssertionError('must not execute')

    with pytest.raises(ast.AstetikError, match='registered'):
        ast.Animation(pd.DataFrame({'a': [1.0], 'b': [2.0]}), 'a', 'b', plot_type=forbidden)


def test_animation_receipt_changes_block_publication(tmp_path):
    animation = ast.Animation(pd.DataFrame({'a': [1.0], 'b': [2.0]}), 'a', 'b')
    animation.receipt['poster_frame'] = 99
    with pytest.raises(ast.AstetikError) as caught:
        animation.write(tmp_path / 'altered')
    assert caught.value.code == 'RESULT_CHANGED'
    assert not (tmp_path / 'altered').exists()
