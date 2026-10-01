#!/usr/bin/env python3
"""Package audit: the sdist and wheel content contract.

Checks what the built distributions actually contain, which no other gate
does. `twine check` validates metadata and `check-manifest` compares the sdist
to version control; neither asserts that the files a consumer needs are
present and the ones they must not receive are absent.

Three rules:

  - every path in REQUIRED_SDIST_PATHS is in the sdist;
  - no path matching FORBIDDEN_PREFIXES is in either distribution;
  - every declared dependency carries a lower AND an upper bound.

The bound rule is the one that catches real breakage: an unbounded dependency
lets a resolver silently change what ships between two builds of the same
version.
"""
from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Final

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib

import re

BANNER: Final[str] = 'PACKAGE AUDIT'
REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
DIST: Final[Path] = REPO_ROOT / 'dist'
# Either a range with both ends, or an exact pin -- `==` is the tightest
# bound there is, not an absent one.
BOUNDED_RE: Final[re.Pattern[str]] = re.compile(r'>=[^,;]+,\s*<[^,;]+|==[^,;]+')


def version_part(spec: str) -> str:
    """Return the requirement without its PEP 508 environment marker.

    A marker carries its own `==`, so matching bounds against the whole
    string reports `pkg; python_version==\"3.12\"` as bounded -- the exact
    class of unbounded dependency this check exists to catch.
    """
    return spec.split(';', 1)[0].strip()

REQUIRED_SDIST_PATHS: Final[frozenset[str]] = frozenset({
    'README.md',
    'LICENSE',
    'CHANGELOG.md',
    'CONTRIBUTING.md',
    'SECURITY.md',
    'CITATION.cff',
    'pyproject.toml',
    'THIRD_PARTY.md',
})
REQUIRED_WHEEL_PATHS: Final[frozenset[str]] = frozenset({
    'astetik/__init__.py', 'astetik/_api.py', 'astetik/_result.py',
    'astetik/extras/countries.csv', 'astetik/docs/first_figure.py',
    'astetik/fonts/Finlandica.ttf', 'astetik/fonts/OFL.txt',
    'astetik/extras/countries.shp', 'astetik/extras/countries.shx',
    'astetik/extras/countries.dbf',
})
FORBIDDEN_PREFIXES: Final[tuple[str, ...]] = (
    'governance/',
    '.github/',
    'docs-site/',
    'fuzz/',
)


def sdist_members(path: Path) -> set[str]:
    """Return sdist paths with the leading `name-version/` component removed."""
    with tarfile.open(path, 'r:gz') as tar:
        return {m.name.split('/', 1)[1] for m in tar.getmembers() if '/' in m.name}


def wheel_members(path: Path) -> set[str]:
    """Return every path inside a wheel."""
    with zipfile.ZipFile(path) as zf:
        return set(zf.namelist())


def unbounded(specs: list[str]) -> list[str]:
    """Return the specs that carry neither a two-ended range nor an exact pin.

    Split from the pyproject reader so the rule itself is testable without a
    project on disk -- a test that reimplements the check instead of calling
    it proves nothing about the call site.
    """
    return [spec for spec in specs if not BOUNDED_RE.search(version_part(spec))]


def unbounded_dependencies() -> list[str]:
    """Return declared dependencies missing a lower or an upper bound."""
    data = tomllib.loads((REPO_ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    project = data.get('project', {})
    declared: list[str] = list(project.get('dependencies', []))
    for extra in (project.get('optional-dependencies') or {}).values():
        declared.extend(extra)
    return unbounded(declared)


def main() -> int:
    """Run the audit over the built distributions."""
    failures: list[str] = []

    sdists = sorted(DIST.glob('*.tar.gz'))
    wheels = sorted(DIST.glob('*.whl'))
    if not sdists or not wheels:
        print(f'{BANNER} -- FAIL', file=sys.stderr)
        print(f'  no distributions in {DIST}; run `python -m build` first', file=sys.stderr)
        return 2

    members = sdist_members(sdists[-1])
    for required in sorted(REQUIRED_SDIST_PATHS):
        if required not in members:
            failures.append(f'sdist is missing {required}')
    for prefix in FORBIDDEN_PREFIXES:
        for name in sorted(members):
            if name.startswith(prefix):
                failures.append(f'sdist ships {name}, which is enforcement plane, not source')
                break
    wheel_paths = wheel_members(wheels[-1])
    for required in sorted(REQUIRED_WHEEL_PATHS):
        if required not in wheel_paths:
            failures.append(f'wheel is missing {required}')
    for name in sorted(wheel_paths):
        for prefix in FORBIDDEN_PREFIXES:
            if name.startswith(prefix):
                failures.append(f'wheel ships {name}')

    for spec in unbounded_dependencies():
        failures.append(f'dependency {spec!r} lacks a lower and upper bound')

    if failures:
        print(f'{BANNER} -- FAIL', file=sys.stderr)
        print('', file=sys.stderr)
        for failure in failures:
            print(f'  - {failure}', file=sys.stderr)
        print('', file=sys.stderr)
        print(f'{len(failures)} violation(s). Merge blocked.', file=sys.stderr)
        return 1

    print(f'{BANNER} -- PASS ({len(members)} sdist paths, {len(wheels)} wheel)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
