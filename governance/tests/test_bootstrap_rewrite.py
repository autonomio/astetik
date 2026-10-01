"""Synthetic source fixtures prove factory rewrites without research observations."""
from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import pytest

bootstrap = importlib.import_module('bootstrap_repository')


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob('*') if path.is_file()
    }


@pytest.fixture
def seed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A minimal neutral source seed, never an empirical dataset."""
    package = next(iter(bootstrap.KNOWN_SEED_PACKAGES))
    (tmp_path / package).mkdir()
    (tmp_path / package / '__init__.py').write_text(
        '"""Public package surface for a neutral source fixture."""\n'
        '__all__: list[str] = []\n', encoding='utf-8',
    )
    (tmp_path / 'pyproject.toml').write_text(
        f'[project]\nname = "{package}"\nversion = "0.1.0"\n'
        f'[tool.pyright]\ninclude = ["{package}"]\n', encoding='utf-8',
    )
    (tmp_path / 'governance.yml').write_text(
        f'layout:\n  package_root: {package}\n', encoding='utf-8',
    )
    workflows = tmp_path / '.github/workflows'
    workflows.mkdir(parents=True)
    (workflows / 'contract.yml').write_text(f'name: {package}\n', encoding='utf-8')
    monkeypatch.setattr(bootstrap, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(bootstrap, 'BOOTSTRAP_SCRIPT', tmp_path / 'governance/bootstrap_repository.py')
    return tmp_path


def test_seed_rewrite_updates_package_and_leaves_workflows_static(seed: Path) -> None:
    workflow = (seed / '.github/workflows/contract.yml').read_bytes()
    bootstrap._apply_file_bootstrap('fixture-app', 'fixture_app', 'autonomio')
    assert (seed / 'fixture_app').is_dir()
    assert not any((seed / package).exists() for package in bootstrap.KNOWN_SEED_PACKAGES)
    assert 'name = "fixture-app"' in (seed / 'pyproject.toml').read_text(encoding='utf-8')
    assert 'package_root: fixture_app' in (seed / 'governance.yml').read_text(encoding='utf-8')
    assert (seed / '.github/workflows/contract.yml').read_bytes() == workflow


def test_file_bootstrap_is_idempotent_and_preserves_tuned_budgets(seed: Path) -> None:
    bootstrap._apply_file_bootstrap('fixture-app', 'fixture_app', 'autonomio')
    path = seed / '.github/budgets.json'
    budgets = json.loads(path.read_text(encoding='utf-8'))
    budgets['modules']['fixture_app/__init__.py'] = 999
    path.write_text(json.dumps(budgets), encoding='utf-8')
    before = _tree_hashes(seed)
    bootstrap._apply_file_bootstrap('fixture-app', 'fixture_app', 'autonomio')
    assert _tree_hashes(seed) == before


def test_local_labels_validate_before_github_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(bootstrap, 'REPO_ROOT', tmp_path)
    (tmp_path / 'governance.yml').write_text(
        'bootstrap:\n  labels_file: labels.json\n', encoding='utf-8',
    )
    label = {'name': 'slice', 'color': 'abcdef', 'description': 'A bounded change'}
    (tmp_path / 'labels.json').write_text(json.dumps([label]), encoding='utf-8')
    assert bootstrap._load_labels() == [label]
    (tmp_path / 'labels.json').write_text(json.dumps([label, label]), encoding='utf-8')
    with pytest.raises(SystemExit, match='unique'):
        bootstrap._load_labels()
    (tmp_path / 'governance.yml').write_text(
        'bootstrap:\n  labels_file: ../outside.json\n', encoding='utf-8',
    )
    with pytest.raises(SystemExit, match='inside'):
        bootstrap._load_labels()


def test_label_upserts_never_delete_unrelated_labels(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], str | None]] = []

    def gh(args: list[str], *, input_text: str | None = None) -> str:
        calls.append((args, input_text))
        return 'Slice\nunrelated\n' if '--jq' in args else ''

    monkeypatch.setattr(bootstrap, '_run_gh', gh)
    labels = [
        {'name': 'slice', 'color': 'abcdef', 'description': 'Existing'},
        {'name': 'new label', 'color': '123456', 'description': 'New'},
    ]
    bootstrap._copy_labels('autonomio/astetik', labels)
    assert len(calls) == 3
    assert calls[1][0][2:4] == ['PATCH', 'repos/autonomio/astetik/labels/Slice']
    assert json.loads(calls[1][1])['new_name'] == 'slice'
    assert calls[2][0][2:4] == ['POST', 'repos/autonomio/astetik/labels']
    assert not any('DELETE' in args for args, _body in calls)


def test_unsupported_codeql_cannot_weaken_a_repository(seed: Path) -> None:
    before = _tree_hashes(seed)
    with pytest.raises(SystemExit, match='must remain enabled'):
        bootstrap._apply_file_bootstrap('fixture-app', 'fixture_app', 'autonomio', 'unsupported')
    assert _tree_hashes(seed) == before
