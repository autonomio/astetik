"""Design invariants protect scientific meaning across plots and exports."""

import hashlib
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import pytest
from matplotlib import pyplot as plt
from matplotlib.colors import to_hex

from astetik._colors import ColorSystem
from astetik._manifest import Manifest


def test_manifest_is_immutable_and_roundtrips_without_sharing_input():
    document = {'colors': {'primary': '#234B66'}, 'axes': {'spines': ['bottom']}}
    manifest = Manifest.from_dict(document)
    document['colors']['primary'] = '#000000'
    document['axes']['spines'].append('top')
    assert manifest.colors['primary'] == '#234B66'
    assert manifest.axes['spines'] == ('bottom',)
    with pytest.raises(TypeError):
        manifest.colors['primary'] = '#000000'
    with pytest.raises(FrozenInstanceError):
        manifest.schema_version = '2.0'
    assert Manifest.from_dict(manifest.to_dict()).to_dict() == manifest.to_dict()


@pytest.mark.parametrize(
    'document, expected',
    [
        ({'schema_version': '2.0'}, 'schema_version'),
        ({'colour': {}}, 'Unknown manifest'),
        ({'colors': {'primary': 'navy'}}, 'hexadecimal'),
        ({'colors': {'primary': '#FFFFFE'}}, '3:1'),
        ({'colors': {'ink': '#DDDDDD'}}, '4.5:1'),
        ({'colors': {'muted': '#CCCCCC'}}, '4.5:1'),
        ({'colors': {'negative': '#2A4A70'}}, 'distinct'),
        ({'colors': {'neutral': '#A54532'}}, 'neutral'),
        ({'categories': {'control': '#2A4A70', 'treatment': '#2B4B71'}}, 'too similar'),
        ({'categories': {'control': '#FFFFFE'}}, '3:1'),
        ({'paper': {'dpi': 299}}, '300'),
        ({'paper': {'dpi': True}}, '300'),
        ({'paper': {'min_fontsize': 6.9}}, '7'),
        ({'paper': {'width_mm': float('nan')}}, 'finite'),
        ({'typography': {'ticksize': False}}, 'finite'),
        ({'axes': {'grid': 'yes'}}, 'boolean'),
        ({'axes': {'spines': ['left', 'left']}}, 'duplicate'),
    ],
)
def test_manifest_rejects_unsafe_or_ambiguous_design(document, expected):
    with pytest.raises(ValueError, match=expected):
        Manifest.from_dict(document)


def test_paper_presets_fix_export_dimensions_and_font_floor():
    single, double = Manifest(), Manifest(paper={'preset': 'double'})
    assert single.dimensions(paper=True)[0] == pytest.approx(89 / 25.4)
    assert double.dimensions(paper=True)[0] == pytest.approx(178 / 25.4)
    assert single.dimensions(paper=True, panels=2)[1] == pytest.approx(
        2 * single.dimensions(paper=True)[1]
    )
    assert double.dimensions(paper=True, panels=2)[1] == pytest.approx(
        single.dimensions(paper=True)[1]
    )
    small = Manifest(typography={'ticksize': 4, 'fontsize': 5}, paper={'min_fontsize': 8})
    assert small.rc(paper=True)['xtick.labelsize'] == 8
    assert small.rc(paper=True)['font.size'] == 8
    assert small.rc()['xtick.labelsize'] == 4
    with pytest.raises(ValueError, match='positive integer'):
        single.dimensions(panels=True)


def test_style_is_scoped_and_bundled_font_is_recorded():
    before = dict(matplotlib.rcParams)
    manifest = Manifest()
    assert dict(matplotlib.rcParams) == before
    assert manifest.font_info['resolved'] == 'Finlandica'
    assert manifest.font_info['fallback'] is False
    assert (
        manifest.font_info['sha256']
        == hashlib.sha256(Path(manifest.font_path).read_bytes()).hexdigest()
    )
    with matplotlib.rc_context(manifest.rc(paper=True)):
        figure, axes = plt.subplots()
        assert figure.get_figwidth() == pytest.approx(89 / 25.4)
        assert axes.spines['top'].get_visible() is False
        assert axes.spines['right'].get_visible() is False
        assert matplotlib.rcParams['pdf.fonttype'] == 42
        plt.close(figure)
    assert dict(matplotlib.rcParams) == before


def test_explicit_missing_font_has_recorded_deterministic_fallback():
    manifest = Manifest(typography={'font': 'Astetik intentionally missing font 9876'})
    assert manifest.font_info['requested'] == 'Astetik intentionally missing font 9876'
    assert manifest.font_info['resolved'] == 'DejaVu Sans'
    assert manifest.font_info['fallback'] is True


def test_with_primary_does_not_modify_original_and_updates_linked_positive():
    original = Manifest()
    updated = original.with_primary('#235b60')
    assert updated.colors['primary'] == '#235B60'
    assert updated.colors['positive'] == '#235B60'
    assert original.colors['primary'] == '#2A4A70'


def test_category_identity_survives_reorder_and_subset():
    system = ColorSystem(Manifest())
    all_colors = system.categorical(['alpha', 'beta', 'gamma'])
    assert all_colors == system.categorical(['gamma', 'alpha', 'beta'])
    assert system.categorical(['beta']) == {'beta': all_colors['beta']}
    assert len(set(all_colors.values())) == 3


def test_paper_categories_are_explicit_and_reusable():
    system = ColorSystem(Manifest(categories={'control': '#2A4A70', 'treatment': '#A54532'}))
    assert system.categorical(['treatment', 'control'], strict=True) == {
        'treatment': '#A54532',
        'control': '#2A4A70',
    }
    with pytest.raises(ValueError, match=r'manifest\.categories'):
        system.categorical(['control', 'unknown'], strict=True)


def test_hash_collision_requires_explicit_distinct_mapping():
    # Fixed examples occupy the same stable category slot.
    with pytest.raises(ValueError, match='too similar'):
        ColorSystem(Manifest()).categorical(['C', 'alpha'])
    system = ColorSystem(Manifest(categories={'C': '#2A4A70', 'alpha': '#A54532'}))
    assert len(set(system.categorical(['C', 'alpha']).values())) == 2


def test_colormaps_have_exact_semantic_endpoints_and_fixed_neutral_midpoint():
    manifest = Manifest()
    system = ColorSystem(manifest)
    sequential, diverging = system.sequential(), system.diverging()
    assert to_hex(sequential(0.0)).upper() == manifest.colors['paper']
    assert to_hex(sequential(1.0)).upper() == manifest.colors['primary']
    assert to_hex(diverging(0.0)).upper() == manifest.colors['negative']
    assert to_hex(diverging(0.5)).upper() == manifest.colors['neutral']
    assert to_hex(diverging(1.0)).upper() == manifest.colors['positive']


def test_json_and_toml_load_equivalent_manifest(tmp_path):
    source = tmp_path / 'manifest.json'
    source.write_text(json.dumps({'schema_version': '1.0', 'paper': {'preset': 'double'}}))
    toml = tmp_path / 'manifest.toml'
    toml.write_text('schema_version = "1.0"\n[paper]\npreset = "double"\n')
    assert Manifest.load(source).to_dict() == Manifest.load(toml).to_dict()
    source.write_text('{"colors":{"primary":"#2A4A70","primary":"#234B66"}}')
    with pytest.raises(ValueError, match='Duplicate'):
        Manifest.load(source)
    source.write_text('{"paper":{"aspect":NaN}}')
    with pytest.raises(ValueError, match='Nonfinite'):
        Manifest.load(source)


def test_yaml_load_refuses_python_objects_and_duplicates(tmp_path):
    yaml = pytest.importorskip('yaml')
    source = tmp_path / 'manifest.yaml'
    source.write_text('schema_version: "1.0"\npaper:\n  preset: double\n')
    assert Manifest.load(source).paper['width_mm'] == 178
    source.write_text('colors:\n  primary: "#2A4A70"\n  primary: "#234B66"\n')
    with pytest.raises(ValueError, match='Duplicate'):
        Manifest.load(source)
    source.write_text('!!python/object/apply:os.system ["echo forbidden"]')
    with pytest.raises(yaml.constructor.ConstructorError):
        Manifest.load(source)


def test_paper_and_exploration_keep_single_category_identity():
    system = ColorSystem(Manifest())
    assert system.categorical(['alpha'], strict=True) == system.categorical(['alpha'])
    with pytest.raises(ValueError, match='ambiguous string'):
        system.categorical([1, '1'])


def test_repeated_manifest_construction_does_not_accumulate_font_registrations():
    from matplotlib import font_manager

    Manifest()
    count = len(font_manager.fontManager.ttflist)
    Manifest()
    Manifest()
    assert len(font_manager.fontManager.ttflist) == count


def test_semantic_category_bindings_survive_serialization_and_resolve_on_use(tmp_path):
    manifest = Manifest(categories={'control': 'primary', 'treatment': 'secondary'})
    assert dict(manifest.categories) == {'control': 'primary', 'treatment': 'secondary'}
    document = manifest.to_dict()
    source = tmp_path / 'design.json'
    source.write_text(json.dumps(document))
    restored = Manifest.load(source)
    assert restored.to_dict() == document
    assert ColorSystem(restored).categorical(['treatment', 'control'], strict=True) == {
        'treatment': manifest.colors['secondary'],
        'control': manifest.colors['primary'],
    }


def test_primary_change_propagates_through_role_bound_categories_and_continuous_scales():
    original = Manifest(
        categories={'control': 'primary', 'treatment': 'secondary', 'reference': '#A54532'}
    )
    updated = original.with_primary('#235B60')
    mapping = ColorSystem(updated).categorical(['control', 'treatment', 'reference'], strict=True)
    assert mapping == {
        'control': '#235B60',
        'treatment': original.colors['secondary'],
        'reference': '#A54532',
    }
    assert original.categories['control'] == updated.categories['control'] == 'primary'
    assert original.colors['primary'] == '#2A4A70'
    assert to_hex(ColorSystem(updated).sequential()(1.0)).upper() == '#235B60'
    assert to_hex(ColorSystem(updated).diverging()(1.0)).upper() == '#235B60'
    literal = Manifest(categories={'reference': '#2A4A70'}).with_primary('#235B60')
    assert ColorSystem(literal).categorical(['reference']) == {'reference': '#2A4A70'}


@pytest.mark.parametrize(
    'bindings, message',
    [
        ({'control': 'unknown_role'}, 'existing semantic'),
        ({'control': 'paper'}, '3:1'),
        ({'control': 'primary', 'treatment': 'positive'}, 'too similar'),
        ({'control': 'primary', 'treatment': '#2A4A70'}, 'too similar'),
    ],
)
def test_semantic_category_bindings_validate_resolved_colours(bindings, message):
    with pytest.raises(ValueError, match=message):
        Manifest(categories=bindings)


def test_primary_change_revalidates_bound_category_distinction():
    original = Manifest(categories={'control': 'primary', 'treatment': '#235B60'})
    with pytest.raises(ValueError, match='too similar'):
        original.with_primary('#235B60')
