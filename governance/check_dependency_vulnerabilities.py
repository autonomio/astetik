#!/usr/bin/env python3
"""Dependency vulnerability gate: declared runtime deps must carry no known CVE.

Audits `[project.dependencies]` with pip-audit. A finding blocks merge unless
it is covered by an active, time-boxed entry in `.github/vuln_exceptions.json`
(`id` + `reason` + `expiry`); an expired exception no longer covers. Skipped
dependencies and incomplete audit reports fail closed.
"""
from __future__ import annotations

import datetime
import json
import subprocess
import sys
import tempfile
from functools import partial
from pathlib import Path

from _common import REPO_ROOT, TOMLDecodeError, fail_setup, loads_toml
from _dependency_audit import validate_dependencies, validate_report

PYPROJECT = REPO_ROOT / 'pyproject.toml'
EXCEPTIONS = REPO_ROOT / '.github' / 'vuln_exceptions.json'

# Bind this gate's banner to the shared setup-failure reporter.
_fail_setup = partial(fail_setup, 'DEPENDENCY VULNERABILITY GATE')


def _runtime_dependencies() -> list[str]:
    try:
        data = loads_toml(PYPROJECT.read_text(encoding='utf-8'))
    except (OSError, TOMLDecodeError) as exc:
        _fail_setup(f'cannot read pyproject.toml: {exc}')
    project = data.get('project')
    if not isinstance(project, dict):
        _fail_setup('pyproject [project] must be a table')
    deps = project.get('dependencies', [])
    if not isinstance(deps, list):
        _fail_setup('pyproject [project.dependencies] is not a list')
    if any(not isinstance(dep, str) or not dep.strip() for dep in deps):
        _fail_setup('every runtime dependency must be a nonempty requirement string')
    return deps


def active_exceptions(raw_text: str, today: datetime.date) -> set[str]:
    """Return the set of vulnerability ids with an unexpired, reasoned
    exception. Malformed exception files fail the gate closed."""
    if not raw_text.strip():
        return set()
    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        _fail_setup(f'cannot parse {EXCEPTIONS}: {exc}')
    if not isinstance(raw, list):
        _fail_setup(f'{EXCEPTIONS} must be a JSON list of exceptions')
    active: set[str] = set()
    for item in raw:
        if not isinstance(item, dict) or not {'id', 'reason', 'expiry'} <= set(item):
            _fail_setup(f'each exception needs id, reason, expiry: {item!r}')
        try:
            expiry = datetime.date.fromisoformat(str(item['expiry']))
        except ValueError:
            _fail_setup(f'exception expiry must be ISO YYYY-MM-DD: {item!r}')
        if expiry >= today and str(item['reason']).strip():
            active.add(str(item['id']))
    return active


def _audit(deps: list[str]) -> list[dict[str, object]]:
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as handle:
        handle.write('\n'.join(deps) + '\n')
        reqs = handle.name
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip_audit', '-r', reqs,
             '--strict', '--format', 'json', '--progress-spinner', 'off'],
            check=False, capture_output=True, text=True,
        )
    finally:
        Path(reqs).unlink(missing_ok=True)
    if result.returncode not in (0, 1):  # 1 == vulnerabilities found; other == tool error
        _fail_setup(f'pip-audit could not run: {result.stderr.strip() or result.stdout.strip()}')
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        _fail_setup(f'cannot parse pip-audit JSON: {exc}')
    audited = validate_report(payload, deps)
    if result.returncode == 1 and not any(dep['vulns'] for dep in audited):
        _fail_setup('pip-audit failed without vulnerability records')
    return audited


def evaluate(audited: list[dict[str, object]], excepted: set[str]) -> list[str]:
    """Turn pip-audit's per-dependency results into blocking findings,
    dropping any vulnerability whose id has an active exception. Pure
    function so the gate's verdict is deterministically testable."""
    findings: list[str] = []
    for dep in validate_dependencies(audited):
        name = dep['name']
        for vuln in dep['vulns']:
            if vuln['id'] in excepted:
                continue
            fixes = vuln['fix_versions']
            fix = ', '.join(fixes) if fixes else 'none published'
            findings.append(f'{name}: {vuln["id"]} (fix: {fix})')
    return findings


def main() -> int:
    deps = _runtime_dependencies()
    if not deps:
        print('DEPENDENCY VULNERABILITY GATE -- PASS (no runtime dependencies declared)')
        return 0
    excepted = active_exceptions(
        EXCEPTIONS.read_text(encoding='utf-8') if EXCEPTIONS.is_file() else '',
        datetime.date.today(),
    )
    findings = evaluate(_audit(deps), excepted)
    if findings:
        print('DEPENDENCY VULNERABILITY GATE -- FAIL', file=sys.stderr)
        print('', file=sys.stderr)
        for finding in findings:
            print(f'  {finding}', file=sys.stderr)
        print('', file=sys.stderr)
        print('  Upgrade the dependency, or add a time-boxed entry to', file=sys.stderr)
        print('  .github/vuln_exceptions.json (id + reason + expiry).', file=sys.stderr)
        print(f'{len(findings)} vulnerability(ies). Merge blocked.', file=sys.stderr)
        return 1
    print('DEPENDENCY VULNERABILITY GATE -- PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
