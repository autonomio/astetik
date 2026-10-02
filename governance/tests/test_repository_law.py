"""Honesty gate: config, written laws, and enforced ruleset agree exactly.

Three descriptions of the same fact, from three files that a change can touch
independently:

  * `governance.yml` -- the gates configured to run *and* to block
  * `CLAUDE.md` -- the laws, each workflow-gate law carrying its
    required-status-check context as a trailing `*(context)*` annotation
  * `.github/rulesets/master.json` -- the checks `master` actually requires

This gate asserts a bijection across all three. Pairwise would not be enough
in principle, but three-way agreement is: any single-file edit that moves one
description away from the other two fails here, and is named on both sides.

Exactly one law is the server-side branch-protection law, which has no status
check and therefore no config entry.
"""
from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
LAWS_DOC = REPO_ROOT / 'CLAUDE.md'
RULESET = REPO_ROOT / '.github/rulesets/master.json'
CONFIG = REPO_ROOT / 'governance.yml'

# The one law that maps to server-side branch protection, not a status check.
BRANCH_PROTECTION_ANNOTATION = 'branch protection, server-side'

_LAW_LINE = re.compile(r'^\d+\.\s')
_ANNOTATION = re.compile(r'\*\((?P<annotation>.+)\)\*\s*$')


def _laws_section() -> list[str]:
    # Only the "## The laws" section is parsed, so a numbered list elsewhere
    # in the document cannot be mistaken for a law.
    out: list[str] = []
    in_section = False
    for line in LAWS_DOC.read_text(encoding='utf-8').splitlines():
        if line.startswith('## '):
            in_section = line.strip() == '## The laws'
            continue
        if in_section:
            out.append(line)
    return out


def _law_annotations() -> list[str]:
    annotations: list[str] = []
    for line in _laws_section():
        if not _LAW_LINE.match(line):
            continue
        m = _ANNOTATION.search(line)
        assert m is not None, f'law without a trailing *(annotation)*: {line!r}'
        annotations.append(m.group('annotation').strip())
    return annotations


def _ruleset_contexts() -> set[str]:
    payload = json.loads(RULESET.read_text(encoding='utf-8'))
    checks = next(r for r in payload['rules'] if r['type'] == 'required_status_checks')
    return {entry['context'] for entry in checks['parameters']['required_status_checks']}


def _config_contexts() -> set[str]:
    # A gate owes a law and a required check only when it both runs and
    # blocks. `enabled: false` withdraws it from all three descriptions at
    # once, which is what makes partial adoption a config edit.
    gates = yaml.safe_load(CONFIG.read_text(encoding='utf-8')).get('gates', {})
    return {
        body['context']
        for body in gates.values()
        if body.get('enabled', True) is not False and body.get('required') is True
    }


def test_exactly_one_branch_protection_law() -> None:
    branch = [a for a in _law_annotations() if a == BRANCH_PROTECTION_ANNOTATION]
    assert len(branch) == 1, f'expected exactly one branch-protection law, got {len(branch)}'


def test_laws_and_ruleset_are_in_bijection() -> None:
    law_contexts = {a for a in _law_annotations() if a != BRANCH_PROTECTION_ANNOTATION}
    ruleset_contexts = _ruleset_contexts()
    assert law_contexts == ruleset_contexts, (
        'laws <-> ruleset drift -- '
        f'in laws only: {sorted(law_contexts - ruleset_contexts)}; '
        f'in ruleset only: {sorted(ruleset_contexts - law_contexts)}'
    )


def test_config_and_laws_are_in_bijection() -> None:
    config_contexts = _config_contexts()
    law_contexts = {a for a in _law_annotations() if a != BRANCH_PROTECTION_ANNOTATION}
    assert config_contexts == law_contexts, (
        'config <-> laws drift -- '
        f'in config only: {sorted(config_contexts - law_contexts)}; '
        f'in laws only: {sorted(law_contexts - config_contexts)}'
    )


def test_config_and_ruleset_are_in_bijection() -> None:
    config_contexts = _config_contexts()
    ruleset_contexts = _ruleset_contexts()
    assert config_contexts == ruleset_contexts, (
        'config <-> ruleset drift -- '
        f'in config only: {sorted(config_contexts - ruleset_contexts)}; '
        f'in ruleset only: {sorted(ruleset_contexts - config_contexts)}'
    )


def test_honesty_workflow_runs_only_deterministic_law_checks() -> None:
    """Honesty enforces the repository bijection without an external model dependency."""
    workflow = yaml.load(
        (REPO_ROOT / '.github/workflows/pr_checks_honesty.yml').read_text(encoding='utf-8'),
        Loader=yaml.BaseLoader,
    )
    assert workflow['name'] == 'pr_checks_honesty'
    assert set(workflow['on']) == {'pull_request'}
    trigger = workflow['on']['pull_request']
    assert trigger['branches'] == ['master']
    assert {'opened', 'synchronize', 'reopened', 'ready_for_review'} <= set(trigger['types'])
    assert workflow['permissions'] == {'contents': 'read'}
    assert set(workflow['jobs']) == {'pr_checks_honesty'}
    job = workflow['jobs']['pr_checks_honesty']
    assert job['name'] == 'pr_checks_honesty' and 'if' not in job
    steps = job['steps']
    assert len(steps) == 4
    assert all('if' not in step and 'continue-on-error' not in step for step in steps)
    assert steps[0]['uses'].startswith('actions/checkout@')
    assert steps[0]['with']['persist-credentials'] == 'false'
    assert steps[1]['uses'].startswith('actions/setup-python@')
    assert steps[1]['with']['python-version'] == '3.13'
    installation = [shlex.split(line) for line in steps[2]['run'].splitlines() if line.strip()]
    assert installation == [
        ['python', '-m', 'pip', 'install', '--require-hashes', '-r', path]
        for path in (
            'requirements/ci/dev-env.txt', 'requirements/ci/runtime-env.txt',
            'requirements/ci/build-tools.txt',
        )
    ] + [['python', '-m', 'pip', 'install', '--no-build-isolation', '--no-deps', '-e', '.']]
    assert shlex.split(steps[3]['run']) == [
        'pytest', 'governance/tests/test_repository_law.py', '-v', '--tb=short',
    ]
