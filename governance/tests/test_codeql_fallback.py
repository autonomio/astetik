"""Required CodeQL cannot be removed by existing-repository activation."""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_bootstrap_has_no_codeql_disabling_capability() -> None:
    bootstrap = importlib.import_module('bootstrap_repository')
    assert not hasattr(bootstrap, 'disable_codeql')
    assert not hasattr(bootstrap, '_drop_codeql_law')
    source = (REPO_ROOT / '.github/workflows/bootstrap_repository.yml').read_text(encoding='utf-8')
    assert '--codeql' not in source
    assert 'Detect CodeQL availability' not in source
    assert 'github-only' in source


def test_unsupported_codeql_fails_before_file_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bootstrap = importlib.import_module('bootstrap_repository')
    monkeypatch.setattr(bootstrap, 'REPO_ROOT', tmp_path)
    snapshot = tmp_path / 'required-policy.txt'
    snapshot.write_text('CodeQL required', encoding='utf-8')
    with pytest.raises(SystemExit, match='must remain enabled'):
        bootstrap._apply_file_bootstrap('astetik', 'astetik', 'autonomio', 'unsupported')
    assert snapshot.read_text(encoding='utf-8') == 'CodeQL required'
    assert sorted(path.name for path in tmp_path.iterdir()) == ['required-policy.txt']
