"""Installed Markdown must retain usable links without the source checkout."""

from __future__ import annotations

import importlib.metadata as metadata
import os
import re
import subprocess
import sys
from functools import cache
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

from _common import loads_toml

REPO_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_PATH = re.compile(r'/autonomio/astetik/blob/([0-9a-f]{40})/(.+)')


def _targets(document: str) -> set[str]:
    """Collect inline, reference, HTML, and autolink destinations outside code."""
    prose = re.sub(r'(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$', '', document)
    prose = re.sub(r'`+[^`]*`+', '', prose)
    patterns = (
        r'\[[^\]]*\]\(\s*<?([^\s)>]+)',
        r'(?m)^\s*\[[^\]]+\]:\s*<?([^\s>]+)',
        r'(?:href|src)=["\']([^"\']+)["\']',
        r'<(https?://[^\s>]+)>',
    )
    return {target for pattern in patterns for target in re.findall(pattern, prose)}


def _heading_ids(document: str) -> set[str]:
    """Resolve the ordinary GitHub Markdown heading anchors used by package docs."""
    headings = re.findall(r'(?m)^#{1,6}\s+(.+?)\s*#*$', document)
    return {re.sub(r'[^\w -]', '', heading.lower()).replace(' ', '-') for heading in headings}


@cache
def _committed_blob(commit: str, source: str) -> bytes:
    """Read the exact retained Git blob without relying on the mutable checkout."""
    revision = f'{commit}:{source}'
    kind = subprocess.check_output(
        ['git', 'cat-file', '-t', revision],
        cwd=REPO_ROOT,
        text=True,
    ).strip()
    assert kind == 'blob', f'{revision}: documentation must reference a committed file'
    return subprocess.check_output(['git', 'show', revision], cwd=REPO_ROOT)


def _assert_target(document: Path, target: str, package_root: Path, version: str) -> None:
    parts = urlsplit(target)
    assert not parts.query, f'{document}: unverified query in {target}'
    if parts.scheme or parts.netloc:
        assert parts.scheme == 'https' and parts.netloc == 'github.com', (
            f'{document}: expected a canonical Autonomio repository URL, got {target}'
        )
        match = REPOSITORY_PATH.fullmatch(parts.path)
        assert match, f'{document}: expected an immutable repository commit in {target}'
        commit, source_name = match.groups()
        relative = PurePosixPath(unquote(source_name))
        assert not relative.is_absolute() and '..' not in relative.parts, (
            f'{document}: {target} escapes its repository'
        )
        contents = _committed_blob(commit, relative.as_posix())
        project = loads_toml(_committed_blob(commit, 'pyproject.toml').decode('utf-8'))
        assert project['project']['version'] == version, (
            f'{document}: linked documentation does not match installed version {version}'
        )
        suffix = relative.suffix
    else:
        source = (document.parent / unquote(parts.path)).resolve() if parts.path else document
        assert source.is_relative_to(package_root), f'{document}: {target} escapes its distribution'
        assert source.is_file(), f'{document}: missing link destination {target}'
        contents = source.read_bytes()
        suffix = source.suffix
    if parts.fragment:
        assert suffix.lower() == '.md', f'{document}: unverifiable fragment in {target}'
        assert unquote(parts.fragment) in _heading_ids(contents.decode('utf-8')), (
            f'{document}: missing heading in {target}'
        )


def test_built_installed_markdown_links_survive_checkout_absence(tmp_path: Path) -> None:
    """Build and install the actual wheel, then resolve every shipped Markdown link."""
    wheels = tmp_path / 'wheels'
    subprocess.run(
        [sys.executable, '-m', 'hatchling', 'build', '-t', 'wheel', '-d', str(wheels)],
        cwd=REPO_ROOT,
        env=os.environ | {'SOURCE_DATE_EPOCH': '1704067200'},
        check=True,
    )
    artifacts = list(wheels.glob('*.whl'))
    assert len(artifacts) == 1
    installed = tmp_path / 'installed'
    subprocess.run(
        [
            sys.executable,
            '-m',
            'pip',
            '--disable-pip-version-check',
            'install',
            '--no-index',
            '--no-deps',
            '--no-compile',
            '--target',
            str(installed),
            str(artifacts[0]),
        ],
        cwd=tmp_path,
        check=True,
    )
    versions = [
        distribution.version
        for distribution in metadata.distributions(path=[str(installed)])
        if distribution.metadata['Name'] == 'astetik'
    ]
    assert len(versions) == 1
    package_root = installed / 'astetik'
    documents = sorted(package_root.rglob('*.md'))
    names = {path.relative_to(package_root).as_posix() for path in documents}
    assert {'README.md', 'docs/README.md', 'docs/migration.md'} <= names
    assert not (installed / 'docs').exists()
    for document in documents:
        targets = _targets(document.read_text(encoding='utf-8'))
        for target in sorted(targets):
            _assert_target(document, target, package_root, versions[0])
