"""Existing-repository file activation is idempotent and preserves gate contracts."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVED_SLUG = 'astetik'
DERIVED_PACKAGE = 'astetik'
_SEED_PACKAGE = 'new' + '_repository_' + 'template'
_IGNORE = shutil.ignore_patterns(
    '.git', '.venv', '.venv-lint', '.venv-ruleset', '.venv-ruleset-audit',
    '__pycache__', 'node_modules', '.pytest_cache', '.ruff_cache', 'htmlcov',
    '.hypothesis', 'build', 'dist', '.docusaurus', '.generated',
    'test-results', 'playwright-report', 'output',
    '.venv*')
# `bootstrap_repository.py` names every placeholder because it is the thing
# that replaces them, and generated site output is rebuilt from sources that
# were themselves rewritten. Neither ships a placeholder to a reader.
_PLACEHOLDER_EXEMPT = ('governance/bootstrap_repository.py',)
# Selected by suffix rather than discovered by catching a decode error:
# the test-fallback gate forbids try/except in tests, and rightly -- a
# swallowed decode error would silently shrink what this test checks.
_TEXT_SUFFIXES = frozenset({
    '.py', '.md', '.yml', '.yaml', '.json', '.toml', '.txt', '.cff', '.cfg', '.ini',
})
# Placeholders the rename engine is responsible for filling in. Any survivor
# ships to the derived repository verbatim.
# Assembled, not written literally: this file is inside the rewrite sweep, so
# a literal placeholder here would be filled in and the check would stop
# looking for the thing it exists to find.
PLACEHOLDERS = tuple(
    '{' + name + '}'
    for name in ('REPOSITORY_NAME', 'DISPLAY_NAME', 'REPOSITORY_OWNER',
                 'ONE_SENTENCE_DESCRIPTION')
)


def _tree_hashes(root: Path) -> dict[str, str]:
    from hashlib import sha256
    return {
        path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in root.rglob('*')
        if path.is_file() and '__pycache__' not in path.parts
    }


@pytest.fixture(scope='module')
def bootstrapped(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A throwaway copy, activated without changing existing package identity."""
    repo = tmp_path_factory.mktemp('derived') / 'repo'
    # Installed documentation resolves immutable blobs from retained history;
    # candidate files still include the current uncommitted test and source edits.
    subprocess.run(
        ['git', 'clone', '--shared', '--no-checkout', str(REPO_ROOT), str(repo)],
        check=True,
    )
    shutil.copytree(REPO_ROOT, repo, ignore=_IGNORE, dirs_exist_ok=True)
    before = _tree_hashes(repo)
    result = subprocess.run(
        [
            sys.executable, 'governance/bootstrap_repository.py', '--files-only',
            '--repo-name', DERIVED_SLUG, '--owner', 'autonomio',
        ],
        cwd=repo, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'already specialized' in result.stdout
    assert _tree_hashes(repo) == before
    return repo


def test_bootstrapped_repository_passes_its_own_suite(bootstrapped: Path) -> None:
    """The whole point: the activated local candidate must satisfy its own contracts."""
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', 'governance/tests', '-q', '-p', 'no:cacheprovider',
         '--deselect', 'governance/tests/test_bootstrapped_repo_is_green.py'],
        cwd=bootstrapped, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, (
        'a bootstrapped repository fails its own governance suite:\n'
        + result.stdout + result.stderr
    )


def test_retained_budgets_fit_the_modules_they_budget(bootstrapped: Path) -> None:
    """Every regenerated line budget must exceed the file it budgets.

    The defect this pins was a literal: bootstrap wrote 120 for every gate
    module while one of them was 172 lines, so the module-budget gate failed
    on the derived repository's first run.
    """
    budgets = json.loads(
        (bootstrapped / '.github' / 'budgets.json').read_text(encoding='utf-8')
    )['modules']
    over: list[str] = []
    for rel, budget in budgets.items():
        path = bootstrapped / rel
        if not path.is_file():
            continue
        significant = sum(
            1 for line in path.read_text(encoding='utf-8').splitlines()
            if line.strip() and not line.strip().startswith('#')
        )
        if significant > budget:
            over.append(f'{rel}: {significant} lines vs budget {budget}')
    assert not over, 'regenerated budgets smaller than the files they budget: ' + '; '.join(over)


def test_no_sha_pinned_file_is_rewritten_by_bootstrap(bootstrapped: Path) -> None:
    """A byte pin must not cover a file specialization edits.

    Read from the derived copy rather than from here: the question is whether
    the pin still holds *after* the rename engine has run, which is exactly
    the question the template alone cannot ask.
    """
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', 'governance/tests/test_agent_rulebook.py',
         '-q', '-p', 'no:cacheprovider'],
        cwd=bootstrapped, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, (
        'a SHA-pinned artifact was rewritten by bootstrap:\n' + result.stdout[-2000:]
    )


def test_no_placeholder_token_survives_bootstrap(bootstrapped: Path) -> None:
    """Every `{PLACEHOLDER}` must be filled in, in every text file.

    `CITATION.cff` shipped literal `display-name placeholder` to every derived
    repository because `.cff` was missing from the rewrite sweep.
    """
    survivors: list[str] = []
    for path in sorted(bootstrapped.rglob('*')):
        rel = path.relative_to(bootstrapped).as_posix()
        if not path.is_file() or rel in _PLACEHOLDER_EXEMPT:
            continue
        if any(part in {'.git', '__pycache__', 'node_modules', 'build',
                        '.docusaurus', '.hypothesis'} for part in path.parts):
            continue
        if path.suffix not in _TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding='utf-8')
        for token in PLACEHOLDERS:
            if token in text:
                survivors.append(f'{rel}: {token}')
    assert not survivors, 'placeholders bootstrap left behind: ' + '; '.join(survivors)


def test_the_seed_package_is_gone(bootstrapped: Path) -> None:
    """The existing package survives; an original factory seed is absent."""
    assert (bootstrapped / DERIVED_PACKAGE).is_dir()
    assert not (bootstrapped / _SEED_PACKAGE).exists()
