"""Retained country metadata replays with the exact font after relocation."""
from __future__ import annotations

import json
import shutil
from collections.abc import Iterator
from contextlib import ExitStack
from pathlib import Path
from typing import NoReturn

import pandas as pd
import pytest
from matplotlib import font_manager, get_data_path
from matplotlib import pyplot as plt
from matplotlib.backend_bases import RendererBase
from matplotlib.figure import Figure

import astetik as ast
from astetik import _replay
from astetik._data import file_digest, json_digest
from astetik._types import JsonObject


@pytest.fixture
def countries() -> pd.DataFrame:
    snapshot = pd.read_csv(Path(ast.__file__).parent / 'extras' / 'countries.csv')
    return snapshot.loc[snapshot['alpha-3'].isin(['FIN', 'SWE', 'DEU', 'USA'])].copy()


def _font_project(directory: Path, suffix: str = '.json', *, absolute: bool = False) -> Path:
    directory.mkdir()
    assets = directory / 'assets'
    assets.mkdir()
    font = assets / 'regular.ttf'
    shutil.copyfile(Path(ast.__file__).parent / 'fonts' / 'Finlandica.ttf', font)
    declared = str(font) if absolute else 'assets/regular.ttf'
    source = directory / f'design{suffix}'
    if suffix == '.json':
        source.write_text(json.dumps({'typography': {'font_path': declared}}))
    elif suffix == '.toml':
        source.write_text(f'[typography]\nfont_path = "{declared}"\n')
    else:
        source.write_text(f'typography:\n  font_path: "{declared}"\n')
    return source


def _render(countries: pd.DataFrame, manifest: ast.Manifest, paper: bool | str = True) -> ast.EvidenceResult:
    return ast.render(countries, {'kind': 'scat', 'x': 'country-code', 'y': 'country-code',
                                 'key': 'alpha-3', 'units': {'country-code': 'dimensionless'},
                                 'paper': paper}, manifest)


def _reseal(directory: Path, receipt: JsonObject) -> None:
    receipt.pop('bundle_receipt_sha256', None)
    receipt['bundle_receipt_sha256'] = json_digest(receipt)
    (directory / 'receipt.json').write_text(json.dumps(receipt))


@pytest.mark.parametrize('suffix', ['.json', '.toml', '.yaml'])
def test_loaded_relative_font_keeps_declared_identity_after_project_move(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, suffix: str,
) -> None:
    source = _font_project(tmp_path / 'original', suffix)
    moved = tmp_path / 'relocated'
    shutil.copytree(source.parent, moved)
    monkeypatch.chdir(tmp_path)
    original = ast.Manifest.load(source)
    relocated = ast.Manifest.load(moved / source.name)
    assert original.typography['font_path'] == 'assets/regular.ttf'
    assert relocated.to_dict() == original.to_dict()
    assert json_digest(relocated.to_dict()) == json_digest(original.to_dict())
    assert original.font_path == str((source.parent / 'assets' / 'regular.ttf').resolve())
    assert relocated.font_path == str((moved / 'assets' / 'regular.ttf').resolve())
    assert original.font_info['sha256'] == relocated.font_info['sha256']
    assert original.font_info['fallback'] is relocated.font_info['fallback'] is False
    updated = original.with_primary('#235B60')
    assert updated.typography['font_path'] == original.typography['font_path']
    assert updated.font_info == original.font_info


@pytest.mark.parametrize('paper', [True, 'single', 'double'])
@pytest.mark.parametrize('absolute', [False, True])
def test_custom_font_bundle_relocation_retains_identity_exact_svg_and_provenance(
    tmp_path: Path, countries: pd.DataFrame, paper: bool | str, absolute: bool,
) -> None:
    source = _font_project(tmp_path / 'project', absolute=absolute)
    manifest = ast.Manifest.load(source).with_primary('#235B60')
    with ExitStack() as cleanup:
        original = _render(countries, manifest, paper)
        cleanup.callback(plt.close, original.figure)
        original_id = original.result_id
        bundle = original.write(tmp_path / 'bundle')
        retained_svg = (bundle / 'figure.svg').read_bytes()
        retained_receipt = json.loads((bundle / 'receipt.json').read_text())
        relocated = tmp_path / 'moved' / 'bundle'
        relocated.parent.mkdir()
        shutil.move(str(bundle), relocated)
        shutil.rmtree(source.parent)
        repeated = ast.replay(relocated)
        cleanup.callback(plt.close, repeated.figure)
        assert repeated.result_id == original_id
        assert repeated.svg_bytes() == retained_svg
        assert repeated.verify()['passed']
        assert repeated.manifest == original.manifest
        assert repeated.manifest['typography']['font_path'] == manifest.typography['font_path']
        for field in ('input_sha256', 'table_sha256', 'manifest_sha256', 'marks_sha256', 'units', 'key', 'observations'):
            assert repeated.receipt[field] == retained_receipt[field]
        font = repeated.receipt['font']
        assert isinstance(font, dict)
        assert font['path'] == str((relocated / 'font.ttf').resolve())
        assert font['sha256'] == file_digest(relocated / 'font.ttf')
        assert font['fallback'] is False
        assert original.manifest['paper']['width_mm'] == (178 if paper == 'double' else 89)
        if not absolute:
            assert original.manifest['typography']['font_path'] == 'assets/regular.ttf'


@pytest.mark.parametrize('family', ['Finlandica', 'Astetik deliberately unavailable family 98765', 'sans-serif'])
@pytest.mark.parametrize('paper', ['single', 'double'])
def test_default_and_fallback_font_decisions_survive_clones_and_bundle_replay(
    tmp_path: Path, countries: pd.DataFrame, family: str, paper: str,
) -> None:
    manifest = ast.Manifest(typography={'font': family})
    updated = manifest.with_primary('#235B60')
    assert updated.font_info == manifest.font_info
    with ExitStack() as cleanup:
        result = _render(countries, updated, paper)
        cleanup.callback(plt.close, result.figure)
        bundle = result.write(tmp_path / 'bundle')
        replayed = ast.replay(bundle)
        cleanup.callback(plt.close, replayed.figure)
        assert replayed.result_id == result.result_id
        assert replayed.svg_bytes() == result.svg_bytes()
        font = replayed.receipt['font']
        assert isinstance(font, dict)
        for field in ('requested', 'resolved', 'sha256', 'fallback'):
            assert font[field] == manifest.font_info[field]
        assert replayed.manifest['typography']['font_path'] is None
        assert font['path'] == str((bundle / 'font.ttf').resolve())
        assert replayed.verify()['passed']


def _reject_before_execution(
    bundle: Path, receipt: JsonObject, monkeypatch: pytest.MonkeyPatch, strict: bool, code: str,
) -> None:
    _reseal(bundle, receipt)

    def unexpected_execution(*_args: object, **_kwargs: object) -> NoReturn:
        raise AssertionError('Corrupted font/design reached scientific execution')

    monkeypatch.setattr(_replay, 'compile_evidence', unexpected_execution)
    with pytest.raises(ast.AstetikError) as failure:
        ast.replay(bundle, strict_environment=strict)
    assert failure.value.code == code


@pytest.fixture
def country_bundle(tmp_path: Path, countries: pd.DataFrame) -> Iterator[Path]:
    source = _font_project(tmp_path / 'project')
    with ExitStack() as cleanup:
        result = _render(countries, ast.Manifest.load(source))
        cleanup.callback(plt.close, result.figure)
        yield result.write(tmp_path / 'bundle')


@pytest.mark.parametrize('strict', [True, False])
@pytest.mark.parametrize('change, code', [
    ('font_bytes', 'BUNDLE_CHANGED'),
    ('font_missing', 'BUNDLE_CHANGED'),
    ('font_inventory', 'BUNDLE_INCOMPLETE'),
    ('font_symlink', 'BUNDLE_PATH'),
])
def test_resealed_font_artifact_corruption_fails_before_scientific_execution(
    tmp_path: Path, country_bundle: Path, monkeypatch: pytest.MonkeyPatch,
    strict: bool, change: str, code: str,
) -> None:
    receipt = json.loads((country_bundle / 'receipt.json').read_text())
    font = country_bundle / 'font.ttf'
    if change == 'font_bytes':
        font.write_bytes(font.read_bytes() + b'\0')
        receipt['output_files']['font.ttf'] = file_digest(font)
    elif change == 'font_missing':
        font.unlink()
    elif change == 'font_inventory':
        del receipt['output_files']['font.ttf']
    else:
        outside = tmp_path / 'outside.ttf'
        shutil.move(str(font), outside)
        font.symlink_to(outside)
    _reject_before_execution(country_bundle, receipt, monkeypatch, strict, code)


@pytest.mark.parametrize('strict', [True, False])
@pytest.mark.parametrize('field, value, code', [
    ('sha256', '0' * 64, 'BUNDLE_CHANGED'),
    ('sha256', 'missing', 'BUNDLE_DOCUMENT'),
    ('resolved', 'DejaVu Sans', 'MANIFEST_CONTRACT'),
    ('requested', 'DejaVu Sans', 'MANIFEST_CONTRACT'),
    ('fallback', 'false', 'BUNDLE_DOCUMENT'),
    ('fallback', True, 'MANIFEST_CONTRACT'),
    ('path', '', 'BUNDLE_DOCUMENT'),
])
def test_resealed_invalid_font_identity_fails_before_scientific_execution(
    country_bundle: Path, monkeypatch: pytest.MonkeyPatch, strict: bool,
    field: str, value: object, code: str,
) -> None:
    receipt = json.loads((country_bundle / 'receipt.json').read_text())
    receipt['font'][field] = value
    _reject_before_execution(country_bundle, receipt, monkeypatch, strict, code)


@pytest.mark.parametrize('strict', [True, False])
def test_missing_font_identity_is_rejected_in_both_replay_modes(
    country_bundle: Path, monkeypatch: pytest.MonkeyPatch, strict: bool,
) -> None:
    receipt = json.loads((country_bundle / 'receipt.json').read_text())
    del receipt['font']
    _reject_before_execution(country_bundle, receipt, monkeypatch, strict, 'BUNDLE_DOCUMENT')


@pytest.mark.parametrize('strict', [True, False])
def test_invalid_retained_manifest_remains_a_structured_failure(
    country_bundle: Path, monkeypatch: pytest.MonkeyPatch, strict: bool,
) -> None:
    receipt = json.loads((country_bundle / 'receipt.json').read_text())
    source = country_bundle / 'manifest.json'
    manifest = json.loads(source.read_text())
    manifest['typography']['unknown'] = 'ambiguous'
    source.write_text(json.dumps(manifest))
    receipt['output_files']['manifest.json'] = file_digest(source)
    _reject_before_execution(country_bundle, receipt, monkeypatch, strict, 'MANIFEST_CONTRACT')


def test_serialized_relative_font_requires_its_declared_resolution_context(tmp_path: Path) -> None:
    source = _font_project(tmp_path / 'project')
    manifest = ast.Manifest.load(source)
    with pytest.raises(ValueError, match='font file does not exist'):
        ast.Manifest.from_dict(manifest.to_dict())
    reconstructed = ast.Manifest.from_dict(manifest.to_dict(), font_source=manifest.font_info)
    assert reconstructed.to_dict() == manifest.to_dict()
    assert reconstructed.font_info == manifest.font_info


@pytest.mark.parametrize('atomic', [False, True])
def test_same_path_font_replacement_refreshes_actual_face_without_stale_registrations(
    tmp_path: Path, countries: pd.DataFrame, atomic: bool,
) -> None:
    source = _font_project(tmp_path / 'project', absolute=True)
    initial = ast.Manifest.load(source)
    font_path = Path(initial.font_path)
    replacement = Path(get_data_path()) / 'fonts' / 'ttf' / 'DejaVuSans.ttf'
    with ExitStack() as cleanup:
        original = _render(countries, initial)
        cleanup.callback(plt.close, original.figure)
        if atomic:
            staged = font_path.with_suffix('.replacement.ttf')
            shutil.copyfile(replacement, staged)
            staged.replace(font_path)
        else:
            font_path.write_bytes(replacement.read_bytes())
        revised = ast.Manifest.load(source)
        assert initial.font_info['resolved'] == 'Finlandica'
        assert revised.font_info['resolved'] == 'DejaVu Sans'
        assert revised.font_info['sha256'] == file_digest(replacement)
        assert revised.font_info['sha256'] != initial.font_info['sha256']
        assert revised.font_info['fallback'] is False
        for _ in range(2):
            assert ast.Manifest.load(source).font_info == revised.font_info
        matching = [entry for entry in font_manager.fontManager.ttflist
                    if Path(entry.fname).resolve() == font_path.resolve()]
        assert len(matching) == 1
        assert matching[0].name == 'DejaVu Sans'
        with pytest.raises(ValueError, match='Retained font identity'):
            initial.with_primary('#235B60')
        with pytest.raises(ast.AstetikError) as changed:
            original.write(tmp_path / 'stale')
        assert changed.value.code == 'RESULT_CHANGED'
        assert not (tmp_path / 'stale').exists()
        refreshed = _render(countries, revised, 'double')
        cleanup.callback(plt.close, refreshed.figure)
        bundle = refreshed.write(tmp_path / 'fresh')
        replayed = ast.replay(bundle)
        cleanup.callback(plt.close, replayed.figure)
        assert replayed.result_id == refreshed.result_id
        assert replayed.svg_bytes() == refreshed.svg_bytes()
        assert replayed.verify()['passed']
        assert replayed.receipt['font']['resolved'] == 'DejaVu Sans'
        assert replayed.receipt['font']['sha256'] == file_digest(replacement)


def test_invalid_same_path_font_replacement_rejects_before_rendering(
    tmp_path: Path, countries: pd.DataFrame,
) -> None:
    source = _font_project(tmp_path / 'project')
    initial = ast.Manifest.load(source)
    original_bytes = Path(initial.font_path).read_bytes()
    Path(initial.font_path).write_bytes(b'not a valid font')
    with pytest.raises(ValueError, match='Cannot read typography font'):
        ast.Manifest.load(source)
    with pytest.raises(ast.AstetikError) as failure:
        ast.render(countries, {'kind': 'scat', 'x': 'country-code', 'y': 'country-code'}, source)
    assert failure.value.code == 'MANIFEST_CONTRACT'
    Path(initial.font_path).write_bytes(original_bytes)
    restored = ast.Manifest.load(source)
    assert restored.font_info == initial.font_info
    matching = [entry for entry in font_manager.fontManager.ttflist
                if Path(entry.fname).resolve() == Path(initial.font_path).resolve()]
    assert len(matching) == 1
    with ExitStack() as cleanup:
        result = _render(countries, restored)
        cleanup.callback(plt.close, result.figure)
        assert result.verify()['passed']


@pytest.mark.parametrize('warm', ['face', 'properties'])
def test_font_cached_externally_before_manifest_registration_refreshes_exact_bytes(
    tmp_path: Path, countries: pd.DataFrame, warm: str,
) -> None:
    source = _font_project(tmp_path / 'project', absolute=True)
    font_path = source.parent / 'assets' / 'regular.ttf'
    if warm == 'face':
        assert font_manager.get_font(str(font_path)).family_name == 'Finlandica'
    else:
        assert font_manager.FontProperties(fname=str(font_path)).get_name() == 'Finlandica'
    font_manager.fontManager.addfont(str(font_path))
    replacement = Path(get_data_path()) / 'fonts' / 'ttf' / 'DejaVuSans.ttf'
    font_path.write_bytes(replacement.read_bytes())
    manifest = ast.Manifest.load(source)
    assert manifest.font_info['resolved'] == 'DejaVu Sans'
    assert manifest.font_info['sha256'] == file_digest(replacement)
    matching = [entry for entry in font_manager.fontManager.ttflist
                if Path(entry.fname).resolve() == font_path.resolve()]
    assert len(matching) == 1
    assert matching[0].name == 'DejaVu Sans'
    with ExitStack() as cleanup:
        result = _render(countries, manifest)
        cleanup.callback(plt.close, result.figure)
        bundle = result.write(tmp_path / 'bundle')
        repeated = ast.replay(bundle)
        cleanup.callback(plt.close, repeated.figure)
        assert repeated.result_id == result.result_id
        assert repeated.svg_bytes() == result.svg_bytes()
        assert repeated.verify()['passed']


@pytest.mark.parametrize('registered', [False, True])
def test_registered_font_aliases_are_removed_when_target_bytes_change(
    tmp_path: Path, countries: pd.DataFrame, registered: bool,
) -> None:
    source = _font_project(tmp_path / 'project', absolute=True)
    font_path = source.parent / 'assets' / 'regular.ttf'
    if registered:
        ast.Manifest.load(source)
    alias = tmp_path / 'different-name.ttf'
    alias.symlink_to(font_path)
    assert font_manager.get_font(str(alias)).family_name == 'Finlandica'
    font_manager.fontManager.addfont(str(alias))
    replacement = Path(get_data_path()) / 'fonts' / 'ttf' / 'DejaVuSans.ttf'
    font_path.write_bytes(replacement.read_bytes())
    revised = ast.Manifest.load(source)
    assert revised.font_info['resolved'] == 'DejaVu Sans'
    assert revised.font_info['sha256'] == file_digest(replacement)
    matching = [entry for entry in font_manager.fontManager.ttflist
                if Path(entry.fname).resolve() == font_path.resolve()]
    assert len(matching) == 1
    assert matching[0].fname == str(font_path.resolve())
    assert matching[0].name == 'DejaVu Sans'
    with ExitStack() as cleanup:
        result = _render(countries, revised)
        cleanup.callback(plt.close, result.figure)
        assert result.verify()['passed']
        bundle = result.write(tmp_path / 'bundle')
        repeated = ast.replay(bundle)
        cleanup.callback(plt.close, repeated.figure)
        assert repeated.svg_bytes() == result.svg_bytes()
        assert repeated.result_id == result.result_id


@pytest.mark.parametrize('paper', [False, True, 'single', 'double'])
def test_existing_manifest_with_replaced_font_refuses_before_native_draw(
    tmp_path: Path, countries: pd.DataFrame, monkeypatch: pytest.MonkeyPatch,
    paper: bool | str,
) -> None:
    source = _font_project(tmp_path / 'project')
    initial = ast.Manifest.load(source)
    replacement = Path(get_data_path()) / 'fonts' / 'ttf' / 'DejaVuSans.ttf'
    Path(initial.font_path).write_bytes(replacement.read_bytes())

    def reject_draw(_figure: Figure, _renderer: RendererBase) -> NoReturn:
        raise AssertionError('A stale manifest reached native drawing')

    monkeypatch.setattr(Figure, 'draw', reject_draw)
    with pytest.raises(ast.AstetikError) as failure:
        _render(countries, initial, paper)
    assert failure.value.code == 'MANIFEST_CONTRACT'
