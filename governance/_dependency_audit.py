"""Validate complete pip-audit reports before vulnerability exceptions can apply."""
from __future__ import annotations

from functools import partial

from _common import fail_setup
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

BANNER = 'DEPENDENCY VULNERABILITY GATE'
_fail_setup = partial(fail_setup, BANNER)


def validate_dependencies(audited: object) -> list[dict[str, object]]:
    """Reject skipped, malformed, duplicated, or incomplete dependency records."""
    if not isinstance(audited, list):
        _fail_setup('audited dependencies must be a list')
    seen: set[str] = set()
    for dep in audited:
        if isinstance(dep, dict) and 'skip_reason' in dep:
            _fail_setup(f'pip-audit skipped {dep.get("name", "unnamed dependency")}: {dep["skip_reason"]}')
        if not isinstance(dep, dict) or not all(
            isinstance(dep.get(key), str) and dep[key].strip() for key in ('name', 'version')
        ):
            _fail_setup('every audited dependency must contain a nonempty name and version')
        name = dep['name']
        canonical = canonicalize_name(name)
        if canonical in seen:
            _fail_setup(f'pip-audit repeated dependency {name}')
        seen.add(canonical)
        vulns = dep.get('vulns')
        if not isinstance(vulns, list):
            _fail_setup(f'pip-audit omitted the vulnerability list for {name}')
        for vuln in vulns:
            if not isinstance(vuln, dict) or not isinstance(vuln.get('id'), str) or not vuln['id'].strip():
                _fail_setup(f'pip-audit returned a malformed vulnerability for {name}')
            vid = vuln['id']
            fixes = vuln.get('fix_versions')
            if not isinstance(fixes, list) or any(not isinstance(fix, str) or not fix.strip() for fix in fixes):
                _fail_setup(f'pip-audit returned malformed fix versions for {name}: {vid}')

    return audited


def validate_report(payload: object, deps: list[str]) -> list[dict[str, object]]:
    """Require every applicable declared dependency in a validated audit inventory."""
    if not isinstance(payload, dict) or not isinstance(payload.get('dependencies'), list):
        _fail_setup('pip-audit JSON must contain a dependencies list')
    audited = payload['dependencies']
    audited = validate_dependencies(audited)
    requested: set[str] = set()
    for dep in deps:
        try:
            requirement = Requirement(dep)
        except InvalidRequirement as exc:
            _fail_setup(f'invalid declared runtime requirement: {exc}')
        if requirement.marker is None or requirement.marker.evaluate():
            requested.add(canonicalize_name(requirement.name))
    reported = {canonicalize_name(dep['name']) for dep in audited}
    if missing := requested - reported:
        _fail_setup(f'pip-audit omitted declared dependencies: {sorted(missing)}')
    return audited
