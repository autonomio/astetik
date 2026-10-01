"""Ruff debt cannot expand or disguise unconditional lint failures."""
from pathlib import Path

import pytest
from _common import REPO_ROOT
from check_ruff_ratchet import count_debt, evaluate


def test_only_annotation_and_complexity_debt_is_budgetable():
    report = [{'code': 'ANN001', 'filename': str(REPO_ROOT / 'astetik/_api.py'), 'message': 'annotation'},
              {'code': 'E722', 'filename': str(REPO_ROOT / 'astetik/_api.py'), 'message': 'bare except'}]
    actual, failures = count_debt(report)
    assert actual == {'astetik/_api.py:ANN001': 1}
    assert failures == ['astetik/_api.py: E722: bare except']


def test_findings_cannot_move_to_a_new_path_or_increase():
    assert evaluate({'a:ANN001': 2}, {'a:ANN001': 1}) == ['a:ANN001: 2 > 1']
    assert evaluate({'b:ANN001': 1}, {'a:ANN001': 1}) == ['b:ANN001: 1 > 0']
    assert evaluate({'a:ANN001': 1}, {'a:ANN001': 1}) == []
    assert evaluate({}, {'a:ANN001': 1}) == []


@pytest.mark.parametrize('bad', [None, [], {'a:ANN001': True}, {'a:ANN001': -1}])
def test_malformed_ceilings_fail_closed(bad):
    with pytest.raises(SystemExit, match='2'):
        evaluate({}, bad)


@pytest.mark.parametrize('bad', [{}, [{'code': None, 'filename': 'a.py'}], [{'code': 'ANN001', 'filename': str(Path('/outside/a.py'))}]])
def test_malformed_reports_fail_closed(bad):
    with pytest.raises(SystemExit, match='2'):
        count_debt(bad)


@pytest.mark.parametrize('retained', ['', '{}', '[]', '{broken'])
def test_corrupt_base_is_never_first_adoption(monkeypatch, retained):
    import check_ruff_ratchet as gate
    monkeypatch.setattr(gate, 'git_base_artifact', lambda *args: retained)
    with pytest.raises(SystemExit, match='2'):
        gate.base_budget('verified-base')


def test_first_adoption_requires_absent_budget_and_governance(monkeypatch):
    import check_ruff_ratchet as gate
    monkeypatch.setattr(gate, 'git_base_artifact', lambda *args: None)
    with pytest.raises(SystemExit, match='2'):
        gate.base_budget('verified-base')
    validated = []
    monkeypatch.setattr(gate, 'validate_initial_governance', lambda *args: validated.append(args))
    assert gate.base_budget('verified-base', bootstrap=True) == {}
    assert validated == [('verified-base', gate.BANNER)]
    def reject_adoption(*args):
        raise SystemExit(2)
    monkeypatch.setattr(gate, 'validate_initial_governance', reject_adoption)
    with pytest.raises(SystemExit, match='2'):
        gate.base_budget('verified-base', bootstrap=True)


def test_bootstrap_cannot_bypass_existing_budget(monkeypatch):
    import check_ruff_ratchet as gate
    monkeypatch.setattr(gate, 'git_base_artifact', lambda *args: '{"lint": {"findings": {}}}')
    with pytest.raises(SystemExit, match='2'):
        gate.base_budget('verified-base', bootstrap=True)
