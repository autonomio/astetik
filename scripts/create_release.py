#!/usr/bin/env python3
"""Create the git tag and GitHub release for the version on master.

Every identifier is mechanical. The tag is derived from `[project].version`
and validated against `TAG_RE`; the notes are the changelog's newest section
verbatim; the traceability block is computed from git. Nothing here is
authored at release time, so there is no prose that can disagree with the
artifact it describes.

Upstream-of-this-template repositories sometimes have a model compose the
release title and body. That is deliberately not done here: it adds an API
dependency and a review surface to a step whose entire job is to publish what
the changelog already says.

Idempotent by design, and keyed on both the tag and the release rather than
the tag alone. A run that pushed the tag and then failed leaves a tag with no
release; keying only on the tag would make every re-run exit green while the
release stayed missing. Re-running resumes instead. Version-exempt dependency
merges retain an earlier release only after its source, stable release, and
unchanged parent version are verified.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Final

BANNER: Final[str] = 'CREATE RELEASE'
REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
TAG_RE: Final[re.Pattern[str]] = re.compile(r'^v\d+\.\d+\.\d+$')


def run(*args: str) -> str:
    """Run a command and return its stdout, failing loudly on a non-zero exit."""
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f'{BANNER}: {" ".join(args)} failed: {result.stderr.strip()}')
    return result.stdout.strip()


def current_version() -> str:
    """Read `[project].version` from pyproject.toml."""
    data = tomllib.loads((REPO_ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    version = data.get('project', {}).get('version')
    if not isinstance(version, str) or not version:
        raise SystemExit(f'{BANNER}: pyproject.toml has no [project].version')
    return version


def compute_tag(version: str) -> str:
    """Derive the release tag and reject anything not `vMAJOR.MINOR.PATCH`."""
    tag = f'v{version}'
    if not TAG_RE.match(tag):
        raise SystemExit(f'{BANNER}: {tag!r} does not match {TAG_RE.pattern}')
    return tag


def newest_changelog_section(version: str) -> str:
    """Return the changelog body for this version, without its header."""
    text = (REPO_ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    header = re.compile(r'^#\s+v([0-9A-Za-z.+\-]+)\b')
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if header.match(line)), None)
    if start is None:
        raise SystemExit(f'{BANNER}: CHANGELOG.md carries no version header')
    found = header.match(lines[start])
    if found is None or found.group(1) != version:
        raise SystemExit(
            f'{BANNER}: newest changelog header is {found.group(1) if found else None!r}, '
            f'expected {version!r}'
        )
    body: list[str] = []
    for line in lines[start + 1:]:
        if header.match(line):
            break
        body.append(line)
    return '\n'.join(body).strip()


def previous_tag(tag: str) -> str | None:
    """Return the release tag before this one, or None for a first release."""
    tags = [t for t in run('git', 'tag', '--list', 'v*').splitlines() if TAG_RE.match(t)]
    ordered = sorted(
        (t for t in tags if t != tag),
        key=lambda t: tuple(int(part) for part in t[1:].split('.')),
    )
    return ordered[-1] if ordered else None


def traceability(repo: str, tag: str, previous: str | None) -> str:
    """Build the merged-PR list, compare link and changelog anchor."""
    span = f'{previous}..HEAD' if previous else 'HEAD'
    subjects = run('git', 'log', span, '--merges', '--pretty=%s').splitlines()
    numbers = sorted({int(m.group(1)) for s in subjects
                      if (m := re.search(r'#(\d+)', s)) is not None})
    lines = ['', '## Traceability', '']
    if numbers:
        lines.append('Merged pull requests: ' + ', '.join(f'#{n}' for n in numbers))
    else:
        lines.append('Merged pull requests: none since the previous tag')
    if previous:
        lines.append(f'Compare: https://github.com/{repo}/compare/{previous}...{tag}')
    anchor = tag.replace('.', '')
    lines.append(f'Changelog: https://github.com/{repo}/blob/{tag}/CHANGELOG.md#{anchor}')
    return '\n'.join(lines)


def tag_exists(tag: str, *, expected_commit: str | None = None) -> bool:
    """Prove local and remote tags resolve to the expected release commit."""
    head = expected_commit or run('git', 'rev-parse', '--verify', 'HEAD')
    local = run('git', 'tag', '--list', tag)
    if local and run('git', 'rev-parse', '--verify', f'refs/tags/{tag}^{{commit}}') != head:
        raise SystemExit(f'{BANNER}: local tag {tag} does not resolve to the expected release commit')
    remote = run('git', 'ls-remote', '--tags', 'origin', f'refs/tags/{tag}', f'refs/tags/{tag}^{{}}')
    references: dict[str, str] = {}
    for line in remote.splitlines():
        fields = line.split()
        if (len(fields) != 2 or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', fields[0])
                or fields[1] not in (f'refs/tags/{tag}', f'refs/tags/{tag}^{{}}')
                or fields[1] in references):
            raise SystemExit(f'{BANNER}: malformed remote tag evidence for {tag}')
        references[fields[1]] = fields[0]
    if references:
        if f'refs/tags/{tag}' not in references:
            raise SystemExit(f'{BANNER}: remote tag {tag} lacks its reference')
        commit = references.get(f'refs/tags/{tag}^{{}}', references[f'refs/tags/{tag}'])
        if commit != head:
            raise SystemExit(f'{BANNER}: remote tag {tag} does not resolve to the expected release commit')
    if local and not references:
        raise SystemExit(f'{BANNER}: local tag {tag} has no verified remote counterpart')
    return bool(references)


def release_exists(tag: str, repo: str) -> bool:
    """Only an explicit HTTP 404 proves absence; every other read failure blocks."""
    result = subprocess.run(
        ['gh', 'api', '--include', f'repos/{repo}/releases/tags/{tag}'],
        capture_output=True, text=True, check=False,
    )
    headers, separator, body = result.stdout.replace('\r\n', '\n').partition('\n\n')
    status = re.match(r'^HTTP/\S+\s+(\d{3})\b', headers)
    if result.returncode != 0 and status is not None and status.group(1) == '404':
        return False
    if result.returncode != 0 or status is None or status.group(1) != '200' or not separator:
        raise SystemExit(f'{BANNER}: cannot verify release {tag}: {result.stderr.strip() or headers}')
    payload = json.loads(body)
    if not isinstance(payload, dict) or payload.get('tag_name') != tag:
        raise SystemExit(f'{BANNER}: release response does not identify tag {tag}')
    if payload.get('draft') is not False or payload.get('prerelease') is not False:
        raise SystemExit(f'{BANNER}: existing release {tag} is not a published stable release')
    return True


def skip_unchanged_release(tag: str, version: str) -> bool:
    """Skip an unchanged version only after proving its earlier stable release."""
    if not run('git', 'tag', '--list', tag):
        return False
    tagged = run('git', 'rev-parse', '--verify', f'refs/tags/{tag}^{{commit}}')
    head = run('git', 'rev-parse', '--verify', 'HEAD')
    if tagged == head:
        return False
    parents = run('git', 'rev-list', '--parents', '-n', '1', 'HEAD').split()
    if len(parents) < 2:
        raise SystemExit(f'{BANNER}: older release tag {tag} lacks a parent version')
    for revision in (parents[1], tagged):
        previous = tomllib.loads(run('git', 'show', f'{revision}:pyproject.toml'))
        if previous.get('project', {}).get('version') != version:
            raise SystemExit(f'{BANNER}: older release tag {tag} does not preserve the version')
    ancestry = subprocess.run(['git', 'merge-base', '--is-ancestor', tagged, head], check=False)
    if ancestry.returncode != 0:
        raise SystemExit(f'{BANNER}: older release tag {tag} is outside HEAD history')
    if not tag_exists(tag, expected_commit=tagged):
        raise SystemExit(f'{BANNER}: older release tag {tag} has no remote counterpart')
    repo = os.environ['GITHUB_REPOSITORY']
    if not release_exists(tag, repo):
        raise SystemExit(f'{BANNER}: older release tag {tag} has no published release')
    print(f'{BANNER} -- SKIP ({tag} already released; this merge keeps its version)')
    return True


def main() -> int:
    """Tag the current version and publish its GitHub release."""
    repo = os.environ.get('GITHUB_REPOSITORY')
    if not repo:
        raise SystemExit(f'{BANNER}: GITHUB_REPOSITORY is not set')

    origin = run('git', 'remote', 'get-url', 'origin')
    repository = re.fullmatch(r'(?:https://github\.com/|ssh://git@github\.com/|git@github\.com:)([^/]+/[^/]+?)(?:\.git)?/?', origin)
    if repository is None or repository.group(1).casefold() != repo.casefold():
        raise SystemExit(f'{BANNER}: origin does not identify GITHUB_REPOSITORY {repo}')

    version = current_version()
    tag = compute_tag(version)
    if skip_unchanged_release(tag, version):
        return 0

    tagged = tag_exists(tag)
    released = release_exists(tag, repo)
    if released and not tagged:
        raise SystemExit(f'{BANNER}: existing release {tag} lacks a verified tag at HEAD')
    if tagged and released:
        print(f'{BANNER} -- SKIP ({tag} is already tagged and released)')
        return 0
    if tagged and not released:
        # The tag was pushed and the release step then failed. Resuming here
        # rather than skipping is the whole point of the split check: keying
        # only on the tag would make every re-run exit green while the release
        # stayed missing, which is exactly what the docs promise is safe.
        print(f'{BANNER}: {tag} is tagged but has no release; creating it')

    notes = newest_changelog_section(version)
    if not notes:
        raise SystemExit(f'{BANNER}: changelog section for {version} is empty')
    body = notes + '\n' + traceability(repo, tag, previous_tag(tag))

    if not tagged:
        run('git', 'tag', '-a', tag, '-m', tag)
        run('git', 'push', 'origin', tag)

    notes_path = Path('release-notes.md')
    notes_path.write_text(body, encoding='utf-8')
    run('gh', 'release', 'create', tag, '--repo', repo, '--verify-tag', '--title', tag, '--notes-file', str(notes_path))
    print(f'{BANNER} -- PASS (released {tag})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
