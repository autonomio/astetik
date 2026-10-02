"""Offline Git responses test absence, read failures, and explicit initial adoption."""
from __future__ import annotations

import importlib
import subprocess

import pytest

common = importlib.import_module('_common')


def _responses(monkeypatch: pytest.MonkeyPatch, responses: list[tuple[int, str, str]]) -> None:
    replies = iter(responses)

    def run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        code, stdout, stderr = next(replies)
        return subprocess.CompletedProcess(args, code, stdout, stderr)

    monkeypatch.setattr(common.subprocess, 'run', run)


def test_unreachable_commit_cannot_be_absent_artifact(monkeypatch: pytest.MonkeyPatch) -> None:
    _responses(monkeypatch, [(128, '', 'unknown ref')])
    with pytest.raises(SystemExit):
        common.git_base_artifact('missing', '.github/budgets.json', 'TEST')


def test_existing_artifact_read_failure_cannot_be_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    _responses(monkeypatch, [
        (0, '1' * 40, ''), (0, '.github/budgets.json\n', ''), (128, '', 'read failure'),
    ])
    with pytest.raises(SystemExit):
        common.git_base_artifact('base', '.github/budgets.json', 'TEST')


def test_absence_is_proved_by_verified_tree_inventory(monkeypatch: pytest.MonkeyPatch) -> None:
    _responses(monkeypatch, [(0, '1' * 40, ''), (0, '', '')])
    assert common.git_base_artifact('base', '.github/budgets.json', 'TEST') is None


@pytest.mark.parametrize('module_name,reader', [
    ('check_budget_ratchet', '_base_budget_from_ref'),
    ('check_coverage_ratchet', '_base_floor_from_ref'),
])
def test_initial_baseline_is_explicit_and_cannot_bypass_existing_base(
    monkeypatch: pytest.MonkeyPatch, module_name: str, reader: str,
) -> None:
    module = importlib.import_module(module_name)
    retained: str | None = None

    def artifact(*_args: object) -> str | None:
        return retained

    monkeypatch.setattr(module, 'git_base_artifact', artifact)
    monkeypatch.setattr(module, 'validate_initial_governance', lambda *_args: None)
    read = getattr(module, reader)
    with pytest.raises(SystemExit):
        read('base')
    assert read('base', bootstrap=True) == {}
    retained = '{}'
    with pytest.raises(SystemExit):
        read('base', bootstrap=True)


@pytest.mark.parametrize('introduced', [
    '.github/budgets.json\n', 'governance.yml\n', '.github/budgets.json\ngovernance.yml\n',
])
def test_initial_adoption_independently_proves_both_new_files(
    monkeypatch: pytest.MonkeyPatch, introduced: str,
) -> None:
    monkeypatch.setattr(common, 'git_base_artifact', lambda *_args: None)
    _responses(monkeypatch, [(0, introduced, '')])
    if '.github/budgets.json' in introduced and 'governance.yml' in introduced:
        common.validate_initial_governance('base', 'TEST')
    else:
        with pytest.raises(SystemExit):
            common.validate_initial_governance('base', 'TEST')


def test_existing_base_config_prevents_initial_adoption(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(common, 'git_base_artifact', lambda _ref, path, _banner: '{}' if path == 'governance.yml' else None)
    with pytest.raises(SystemExit):
        common.validate_initial_governance('base', 'TEST')
