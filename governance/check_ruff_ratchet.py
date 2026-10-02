#!/usr/bin/env python3
"""Reject new Ruff debt and every unbudgeted lint failure across the full tree."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from _common import (
    REPO_ROOT,
    budgets,
    fail_setup,
    git_base_artifact,
    loads_toml,
    resolve_package_dir,
    validate_initial_governance,
    write_budget_section,
)

BANNER = 'RUFF RATCHET GATE'
DEBT_CODES = frozenset({'ANN001', 'ANN003', 'ANN201', 'ANN202', 'ANN204', 'ANN401',
                        'C901', 'PLR0912', 'PLR0913', 'PLR0915'})


def count_debt(report: object) -> tuple[dict[str, int], list[str]]:
    """Separate annotation/complexity findings from unconditional failures."""
    if not isinstance(report, list):
        fail_setup(BANNER, 'Ruff report must be a diagnostic list')
    counts: Counter[str] = Counter()
    blocked = []
    for item in report:
        if not isinstance(item, dict) or not isinstance(item.get('code'), str) or not isinstance(item.get('filename'), str):
            fail_setup(BANNER, 'invalid Ruff diagnostic')
        try:
            path = Path(item['filename']).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            fail_setup(BANNER, 'Ruff diagnostic points outside the repository')
        code = item['code']
        if code in DEBT_CODES:
            counts[f'{path}:{code}'] += 1
        else:
            blocked.append(f"{path}: {code}: {item.get('message', '')}")
    return dict(sorted(counts.items())), blocked


def evaluate(actual: dict[str, int], ceiling: object) -> list[str]:
    """Reject increased or newly introduced findings without moving the oracle."""
    if not isinstance(ceiling, dict) or any(not isinstance(k, str) or type(v) is not int or v < 0 for k, v in ceiling.items()):
        fail_setup(BANNER, 'lint.findings must contain nonnegative integer ceilings')
    return [f'{key}: {total} > {ceiling.get(key, 0)}' for key, total in actual.items() if total > ceiling.get(key, 0)]


def base_budget(ref: str, *, bootstrap: bool = False) -> dict[str, object]:
    """Read verified evidence; first adoption requires explicit proven absence."""
    text = git_base_artifact(ref, '.github/budgets.json', BANNER)
    if text is None:
        if not bootstrap:
            fail_setup(BANNER, 'base has no budgets.json; explicit --bootstrap is required')
        validate_initial_governance(ref, BANNER)
        return {}
    if bootstrap:
        fail_setup(BANNER, '--bootstrap is invalid: base already has a budget')
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        fail_setup(BANNER, f'cannot parse base budget: {error}')
    if not isinstance(value, dict) or not value:
        fail_setup(BANNER, 'base budget must be a nonempty object')
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-ref')
    parser.add_argument('--update-budget', action='store_true')
    parser.add_argument('--bootstrap', action='store_true', help='Explicit first adoption with verified missing base governance')
    args = parser.parse_args()
    if args.bootstrap and (not args.base_ref or args.update_budget):
        parser.error('--bootstrap requires --base-ref and cannot regenerate a budget')
    config = loads_toml((REPO_ROOT / 'pyproject.toml').read_text())['tool']['ruff']
    result = subprocess.run([sys.executable, '-m', 'ruff', 'check', str(resolve_package_dir(BANNER)), 'governance', 'tests', '--output-format', 'json'], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode not in (0, 1):
        fail_setup(BANNER, f'Ruff could not run: {result.stderr.strip()}')
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        fail_setup(BANNER, f'invalid Ruff output: {error}')
    retained = REPO_ROOT / 'output' / 'governance' / 'ruff.json'
    retained.parent.mkdir(parents=True, exist_ok=True)
    retained.write_text(result.stdout)
    actual, blocked = count_debt(report)
    if args.update_budget:
        if blocked:
            fail_setup(BANNER, 'unconditional failures must be fixed before baselining:\n' + '\n'.join(blocked))
        write_budget_section('lint', {'configuration': config, 'findings': actual}, BANNER)
        print(f'{BANNER} -- BASELINE ({sum(actual.values())} measured annotation/complexity findings)')
        return 0
    head = budgets(BANNER).get('lint', {})
    if not isinstance(head, dict) or head.get('configuration') != config:
        fail_setup(BANNER, 'declared lint configuration does not match pyproject.toml')
    failures = blocked + evaluate(actual, head.get('findings'))
    if args.base_ref:
        base = base_budget(args.base_ref, bootstrap=args.bootstrap)
        if base:
            old = base.get('lint')
            if not isinstance(old, dict):
                fail_setup(BANNER, 'base governance has no lint ratchet')
            if old.get('configuration') != config:
                failures.append('Ruff policy differs from the protected baseline; change it in an explicit governance migration')
            failures += evaluate(head['findings'], old.get('findings'))
    if failures:
        print(f'{BANNER} -- FAIL\n' + '\n'.join(failures), file=sys.stderr)
        return 1
    print(f'{BANNER} -- PASS ({sum(actual.values())} measured annotation/complexity findings; full report: {retained})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
