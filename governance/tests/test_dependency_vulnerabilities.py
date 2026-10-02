"""Tests for the dependency-vulnerability gate's pure decision logic."""
from __future__ import annotations

import datetime
import importlib
import json
import subprocess
from pathlib import Path

import pytest

# governance/ is on sys.path via governance/tests/conftest.py.
gate = importlib.import_module('check_dependency_vulnerabilities')

_TODAY = datetime.date(2026, 6, 14)
_AUDITED = [
    {
        'name': 'jinja2',
        'version': '2.11.0',
        'vulns': [
            {'id': 'PYSEC-2021-66', 'fix_versions': ['2.11.3']},
            {'id': 'GHSA-x', 'fix_versions': []},
        ],
    }
]


def test_evaluate_reports_every_unexcepted_vuln() -> None:
    findings = gate.evaluate(_AUDITED, set())
    assert len(findings) == 2
    assert any('PYSEC-2021-66' in item for item in findings)


def test_evaluate_suppresses_an_excepted_id() -> None:
    findings = gate.evaluate(_AUDITED, {'PYSEC-2021-66'})
    assert len(findings) == 1
    assert all('PYSEC-2021-66' not in item for item in findings)


def test_evaluate_reports_missing_fix_as_none_published() -> None:
    findings = gate.evaluate(_AUDITED, {'PYSEC-2021-66'})
    assert 'none published' in findings[0]


def test_active_exceptions_honors_expiry() -> None:
    active = gate.active_exceptions('[{"id":"A","reason":"tracked","expiry":"2099-01-01"}]', _TODAY)
    assert active == {'A'}
    expired = gate.active_exceptions('[{"id":"A","reason":"tracked","expiry":"2020-01-01"}]', _TODAY)
    assert expired == set()


def test_active_exceptions_requires_a_reason() -> None:
    assert gate.active_exceptions('[{"id":"A","reason":"  ","expiry":"2099-01-01"}]', _TODAY) == set()


def test_active_exceptions_empty_text_is_empty() -> None:
    assert gate.active_exceptions('', _TODAY) == set()


def test_active_exceptions_rejects_malformed_entry() -> None:
    with pytest.raises(SystemExit):
        gate.active_exceptions('[{"id":"A"}]', _TODAY)


def test_active_exceptions_rejects_bad_expiry() -> None:
    with pytest.raises(SystemExit):
        gate.active_exceptions('[{"id":"A","reason":"x","expiry":"not-a-date"}]', _TODAY)


_ZERO_AUDIT = {'dependencies': [{'name': 'numpy', 'version': '2.0.0', 'vulns': []}], 'fixes': []}


def _fake_audit(monkeypatch, payload, returncode=0):
    """Retain the actual invocation while replacing only the external auditor response."""
    invoked = []

    def run(command, **kwargs):
        invoked.append(command)
        return subprocess.CompletedProcess(command, returncode, json.dumps(payload), 'audit diagnostic')

    monkeypatch.setattr(gate.subprocess, 'run', run)
    return invoked


@pytest.mark.parametrize('payload', [None, [], {}, {'dependencies': None}, {'dependencies': {}},
                                    {'dependencies': []}])
def test_audit_rejects_missing_or_malformed_dependency_inventory(monkeypatch, payload) -> None:
    _fake_audit(monkeypatch, payload)
    with pytest.raises(SystemExit) as caught:
        gate._audit(['numpy>=2'])
    assert caught.value.code == 2


def test_audit_uses_strict_and_removes_its_temporary_requirement_file(monkeypatch) -> None:
    invoked = _fake_audit(monkeypatch, _ZERO_AUDIT)
    assert gate._audit(['numpy>=2']) == _ZERO_AUDIT['dependencies']
    assert '--strict' in invoked[0]
    requirement_file = Path(invoked[0][invoked[0].index('-r') + 1])
    assert not requirement_file.exists()


def test_audit_rejects_omitted_declared_dependency(monkeypatch, capsys) -> None:
    _fake_audit(monkeypatch, _ZERO_AUDIT)
    with pytest.raises(SystemExit) as caught:
        gate._audit(['numpy>=2', 'pandas>=2'])
    assert caught.value.code == 2
    assert 'pandas' in capsys.readouterr().err


def test_audit_accepts_canonicalized_name_and_inactive_environment_marker(monkeypatch) -> None:
    payload = {'dependencies': [{'name': 'PyYAML', 'version': '6.0', 'vulns': []}]}
    _fake_audit(monkeypatch, payload)
    assert gate._audit(['pyyaml>=6', 'never-active; python_version < "0"']) == payload['dependencies']


def test_audit_rejects_error_exit_without_vulnerabilities(monkeypatch) -> None:
    _fake_audit(monkeypatch, _ZERO_AUDIT, returncode=1)
    with pytest.raises(SystemExit) as caught:
        gate._audit(['numpy>=2'])
    assert caught.value.code == 2


@pytest.mark.parametrize('dependency', [None, {}, {'name': 'numpy'},
    {'name': 'numpy', 'skip_reason': 'unsupported dependency source'},
    {'name': 'numpy', 'version': '2.0.0'},
    {'name': 'numpy', 'version': '2.0.0', 'vulns': None},
    {'name': 'numpy', 'version': '2.0.0', 'vulns': [None]},
    {'name': 'numpy', 'version': '2.0.0', 'vulns': [{}]},
    {'name': 'numpy', 'version': '2.0.0', 'vulns': [{'id': 'EXCEPTED'}]},
    {'name': 'numpy', 'version': '2.0.0', 'vulns': [{'id': 'EXCEPTED', 'fix_versions': [None]}]},
])
def test_evaluate_rejects_incomplete_and_skipped_records_even_if_excepted(dependency) -> None:
    with pytest.raises(SystemExit) as caught:
        gate.evaluate([dependency], {'EXCEPTED'})
    assert caught.value.code == 2


def test_evaluate_rejects_duplicate_canonical_dependency_records() -> None:
    with pytest.raises(SystemExit) as caught:
        gate.evaluate([{'name': name, 'version': '2.0.0', 'vulns': []}
                       for name in ('NumPy', 'numpy')], set())
    assert caught.value.code == 2


def test_main_passes_valid_zero_vulnerability_report(monkeypatch, tmp_path, capsys) -> None:
    _fake_audit(monkeypatch, _ZERO_AUDIT)
    monkeypatch.setattr(gate, '_runtime_dependencies', lambda: ['numpy>=2'])
    monkeypatch.setattr(gate, 'EXCEPTIONS', tmp_path / 'no-exceptions.json')
    assert gate.main() == 0
    assert 'GATE -- PASS' in capsys.readouterr().out
