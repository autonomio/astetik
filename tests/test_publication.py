"""Real country bundles arbitrate concurrent writers without persistent locks."""
from __future__ import annotations

import errno
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from hashlib import sha256
from pathlib import Path
from threading import Barrier, Lock
from typing import NoReturn

import pytest
from matplotlib import get_data_path
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

import astetik as ast
from astetik import _result, _result_atomic, _result_export
from astetik._result import EvidenceResult
from astetik._result_atomic import publish_new
from astetik._result_export import Bundle
from astetik._result_types import VerificationReport
from astetik.docs.first_figure import first_figure


def test_concurrent_publication_installs_one_complete_country_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = first_figure()
    reversed_rows = ast.render(original.data.iloc[::-1].copy(), original.spec, original.manifest)
    destination = tmp_path / 'countries'
    barrier = Barrier(2, timeout=10)
    rendering = Lock()
    verify, stage = EvidenceResult.verify, _result_export._stage

    # Matplotlib is serialized; both staged publishers still race at the rename.
    def guarded_verify(result: EvidenceResult) -> VerificationReport:
        with rendering:
            return verify(result)

    def guarded_stage(bundle: Bundle, directory: Path, report: VerificationReport) -> None:
        with rendering:
            stage(bundle, directory, report)

    def competing_rename(source: Path, target: Path) -> None:
        barrier.wait()
        publish_new(source, target)

    monkeypatch.setattr(EvidenceResult, 'verify', guarded_verify)
    monkeypatch.setattr(_result_export, '_stage', guarded_stage)
    monkeypatch.setattr(_result, '_publish_new', competing_rename)
    with ExitStack() as cleanup:
        cleanup.callback(plt.close, original.figure)
        cleanup.callback(plt.close, reversed_rows.figure)
        with ThreadPoolExecutor(max_workers=2) as workers:
            futures = [workers.submit(result.write, destination) for result in (original, reversed_rows)]
        failures = [future.exception() for future in futures]
        assert sum(failure is None for failure in failures) == 1
        loser = next(failure for failure in failures if failure is not None)
        assert isinstance(loser, ast.AstetikError)
        assert loser.code == 'OUTPUT_EXISTS'
        winner = (original, reversed_rows)[failures.index(None)]
        assert futures[failures.index(None)].result() == destination
        assert json.loads((destination / 'receipt.json').read_text())['result_id'] == winner.result_id
        replayed = ast.replay(destination, strict_environment=True)
        cleanup.callback(plt.close, replayed.figure)
        assert replayed.result_id == winner.result_id
        assert replayed.marks == winner.marks
        assert replayed.verify()['passed']
        assert not list(tmp_path.glob('.astetik-*'))
        assert not list(tmp_path.glob('*.astetik-lock'))


def test_process_exit_after_real_staging_leaves_unused_destination_publishable(tmp_path: Path) -> None:
    destination = tmp_path / 'countries'
    script = tmp_path / 'interrupted_writer.py'
    script.write_text("""import os
import sys
from pathlib import Path
from astetik import _result_export
from astetik.docs.first_figure import first_figure

stage = _result_export._stage

def terminate_after_staging(bundle, directory, report):
    stage(bundle, directory, report)
    print('INJECTED_CRASH_AFTER_STAGING', flush=True)
    os._exit(71)

_result_export._stage = terminate_after_staging
first_figure().write(Path(sys.argv[1]))
""")
    process = subprocess.run([sys.executable, '-I', str(script), str(destination)], capture_output=True, text=True, check=False)
    assert process.returncode == 71, process.stdout + process.stderr
    assert process.stdout.strip() == 'INJECTED_CRASH_AFTER_STAGING'
    assert not destination.exists()
    abandoned = list(tmp_path.glob('.astetik-*'))
    assert len(abandoned) == 1
    assert (abandoned[0] / 'receipt.json').is_file()
    result = first_figure()
    with ExitStack() as cleanup:
        cleanup.callback(plt.close, result.figure)
        assert result.write(destination) == destination
        replayed = ast.replay(destination, strict_environment=True)
        cleanup.callback(plt.close, replayed.figure)
        assert replayed.result_id == result.result_id
        assert abandoned[0].is_dir()
        assert not list(tmp_path.glob('*.astetik-lock'))


def test_failed_atomic_publication_cleans_only_its_own_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = first_figure()
    destination = tmp_path / 'countries'

    def failed_rename(_source: Path, target: Path) -> NoReturn:
        raise OSError(errno.EIO, 'Injected publication failure', str(target))

    monkeypatch.setattr(_result, '_publish_new', failed_rename)
    with ExitStack() as cleanup:
        cleanup.callback(plt.close, result.figure)
        with pytest.raises(ast.AstetikError) as failure:
            result.write(destination)
        assert failure.value.code == 'EXPORT_FAILED'
        assert not destination.exists()
        assert not list(tmp_path.glob('.astetik-*'))
        assert not list(tmp_path.glob('*.astetik-lock'))


def test_windows_existing_destination_has_the_same_no_overwrite_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / 'countries'
    destination.mkdir()
    staged = tmp_path / 'staged'
    staged.mkdir()

    def existing_destination(_source: Path, target: Path) -> NoReturn:
        raise FileExistsError(errno.EEXIST, 'Destination already exists', str(target))

    monkeypatch.setattr(_result_atomic.sys, 'platform', 'win32')
    monkeypatch.setattr(_result_atomic.os, 'rename', existing_destination)
    with pytest.raises(ast.AstetikError) as failure:
        publish_new(staged, destination)
    assert failure.value.code == 'OUTPUT_EXISTS'
    assert destination.is_dir()


def test_compiled_country_bundle_retains_exact_selected_font(tmp_path: Path) -> None:
    result = first_figure()
    with ExitStack() as cleanup:
        cleanup.callback(plt.close, result.figure)
        directory = result.write(tmp_path / 'countries')
        font = result.receipt['font']
        assert isinstance(font, dict)
        assert (directory / 'font.ttf').read_bytes() == Path(str(font['path'])).read_bytes()
        receipt = json.loads((directory / 'receipt.json').read_text())
        assert receipt['output_files']['font.ttf'] == font['sha256']
        notices = (directory / 'font-notices.txt').read_bytes()
        fonts = Path(get_data_path()) / 'fonts' / 'ttf'
        assert (Path(ast.__file__).parent / 'fonts' / 'OFL.txt').read_bytes() in notices
        assert (fonts / 'LICENSE_DEJAVU').read_bytes() in notices
        assert (fonts / 'LICENSE_STIX').read_bytes() in notices
        assert b'Finlandica bundled with Astetik' in notices
        assert b'DejaVu fonts bundled with Matplotlib' in notices
        assert b'STIX fonts bundled with Matplotlib' in notices
        assert b'They do not cover user-supplied fonts.' in notices
        assert receipt['output_files']['font-notices.txt'] == sha256(notices).hexdigest()


def test_font_changed_during_real_export_cannot_publish_stale_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = first_figure()
    font = original.receipt['font']
    assert isinstance(font, dict)
    font_path = tmp_path / 'selected-font.ttf'
    original_bytes = Path(str(font['path'])).read_bytes()
    font_path.write_bytes(original_bytes)
    declaration = ast.Manifest.from_dict(original.manifest).to_dict()
    declaration['typography']['font_path'] = str(font_path)
    actual_graphics = _result_export.graphics

    def replace_after_graphics(figure: Figure, directory: Path, dpi: int) -> None:
        actual_graphics(figure, directory, dpi)
        font_path.write_bytes(original_bytes + b'\0')

    with ExitStack() as cleanup:
        cleanup.callback(plt.close, original.figure)
        result = ast.render(original.data, original.spec, ast.Manifest.from_dict(declaration))
        cleanup.callback(plt.close, result.figure)
        monkeypatch.setattr(_result_export, 'graphics', replace_after_graphics)
        destination = tmp_path / 'countries'
        with pytest.raises(ast.AstetikError) as failure:
            result.write(destination)
        assert failure.value.code == 'RESULT_CHANGED'
        assert not destination.exists()
        assert not list(tmp_path.glob('.astetik-*'))
