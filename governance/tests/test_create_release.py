"""Offline command responses prove release absence and immutable tag identity."""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest
import yaml
from _common import loads_toml

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts' / 'create_release.py'
spec = importlib.util.spec_from_file_location('create_release', SCRIPT)
assert spec is not None and spec.loader is not None
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
SKIP_UNCHANGED_RELEASE = release.skip_unchanged_release
HEAD = '1' * 40
OTHER = '2' * 40
VERSION = loads_toml((SCRIPT.parents[1] / 'pyproject.toml').read_text())['project']['version']
TAG = f'v{VERSION}'


@pytest.fixture(autouse=True)
def release_source(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Keep mocked release identity independent of the checkout's current version."""
    (tmp_path / 'pyproject.toml').write_text(f'[project]\nversion = "{TAG[1:]}"\n')
    (tmp_path / 'CHANGELOG.md').write_text(f'# {TAG}\n\nFix verified release handling.\n')
    monkeypatch.setattr(release, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(release, 'skip_unchanged_release', lambda _tag, _version: False)


def _responses(monkeypatch: pytest.MonkeyPatch, responses: list[tuple[int, str, str]]) -> list[list[str]]:
    replies = iter(responses)
    calls: list[list[str]] = []

    def run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(list(args))
        code, stdout, stderr = next(replies)
        return subprocess.CompletedProcess(args, code, stdout, stderr)

    monkeypatch.setattr(release.subprocess, 'run', run)
    return calls


def _http(status: int, payload: dict[str, object]) -> str:
    return f'HTTP/2.0 {status} status\r\nContent-Type: application/json\r\n\r\n{json.dumps(payload)}'


def test_explicit_http_404_is_missing_release(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _responses(monkeypatch, [(1, _http(404, {'message': 'Not Found'}), 'gh: HTTP 404')])
    assert release.release_exists(TAG, 'autonomio/astetik') is False
    assert calls == [['gh', 'api', '--include', f'repos/autonomio/astetik/releases/tags/{TAG}']]


@pytest.mark.parametrize('status,stderr', [
    (401, 'authentication failed'), (403, 'forbidden'),
    (500, 'server error'), (503, 'service unavailable'),
    (0, 'network unreachable'), (0, 'release not found'), (0, 'HTTP 404'),
])
def test_unknown_authentication_network_and_server_failures_block(
    monkeypatch: pytest.MonkeyPatch, status: int, stderr: str,
) -> None:
    stdout = _http(status, {'message': stderr}) if status else ''
    _responses(monkeypatch, [(1, stdout, stderr)])
    with pytest.raises(SystemExit, match='cannot verify release'):
        release.release_exists(TAG, 'autonomio/astetik')


def test_success_identifies_published_stable_release(monkeypatch: pytest.MonkeyPatch) -> None:
    _responses(monkeypatch, [(0, _http(200, {'tag_name': TAG, 'draft': False, 'prerelease': False}), '')])
    assert release.release_exists(TAG, 'autonomio/astetik') is True


@pytest.mark.parametrize('payload', [
    {'tag_name': 'v1.0.0', 'draft': False, 'prerelease': False},
    {'tag_name': TAG, 'draft': True, 'prerelease': False},
    {'tag_name': TAG, 'draft': False, 'prerelease': True},
    {'tag_name': TAG},
])
def test_success_with_wrong_or_unpublished_release_blocks(
    monkeypatch: pytest.MonkeyPatch, payload: dict[str, object],
) -> None:
    _responses(monkeypatch, [(0, _http(200, payload), '')])
    with pytest.raises(SystemExit):
        release.release_exists(TAG, 'autonomio/astetik')


@pytest.mark.parametrize('local,remote', [
    (HEAD, f'{HEAD}\trefs/tags/{TAG}\n'),
    (HEAD, f'{OTHER}\trefs/tags/{TAG}\n{HEAD}\trefs/tags/{TAG}^{{}}\n'),
    ('', f'{HEAD}\trefs/tags/{TAG}\n'),
])
def test_existing_local_and_remote_tags_must_resolve_to_exact_head(
    monkeypatch: pytest.MonkeyPatch, local: str, remote: str,
) -> None:
    replies = [(0, HEAD, ''), (0, TAG if local else '', '')]
    if local:
        replies.append((0, local, ''))
    replies.append((0, remote, ''))
    _responses(monkeypatch, replies)
    assert release.tag_exists(TAG) is True


@pytest.mark.parametrize('local,remote', [
    (OTHER, ''), (HEAD, ''), (HEAD, f'{OTHER}\trefs/tags/{TAG}\n'),
    ('', f'{HEAD}\trefs/tags/{TAG}^{{}}\n'), ('', 'unparseable evidence'),
])
def test_tag_mismatch_or_incomplete_evidence_blocks_before_any_release_read(
    monkeypatch: pytest.MonkeyPatch, local: str, remote: str,
) -> None:
    monkeypatch.setenv('GITHUB_REPOSITORY', 'autonomio/astetik')
    replies = [(0, 'https://github.com/autonomio/astetik.git', ''), (0, HEAD, ''), (0, TAG if local else '', '')]
    if local:
        replies.append((0, local, ''))
    replies.append((0, remote, ''))
    calls = _responses(monkeypatch, replies)
    with pytest.raises(SystemExit):
        release.main()
    assert all(call[0] == 'git' for call in calls)
    assert all('push' not in call and '-a' not in call for call in calls)


def test_verified_existing_tag_and_release_skip_mutation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('GITHUB_REPOSITORY', 'autonomio/astetik')
    calls = _responses(monkeypatch, [
        (0, 'https://github.com/autonomio/astetik.git', ''), (0, HEAD, ''), (0, TAG, ''), (0, HEAD, ''),
        (0, f'{HEAD}\trefs/tags/{TAG}\n', ''),
        (0, _http(200, {'tag_name': TAG, 'draft': False, 'prerelease': False}), ''),
    ])
    assert release.main() == 0
    assert len(calls) == 6
    assert all('push' not in call and 'create' not in call for call in calls)


def test_release_without_verified_tag_cannot_create_a_new_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('GITHUB_REPOSITORY', 'autonomio/astetik')
    calls = _responses(monkeypatch, [
        (0, 'https://github.com/autonomio/astetik.git', ''), (0, HEAD, ''), (0, '', ''), (0, '', ''),
        (0, _http(200, {'tag_name': TAG, 'draft': False, 'prerelease': False}), ''),
    ])
    with pytest.raises(SystemExit, match='lacks a verified tag at HEAD'):
        release.main()
    assert all('push' not in call and '-a' not in call for call in calls)


@pytest.mark.parametrize('existing_tag', [False, True])
def test_verified_absence_creates_or_resumes_only_the_verified_tag(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, existing_tag: bool,
) -> None:
    monkeypatch.setenv('GITHUB_REPOSITORY', 'autonomio/astetik')
    monkeypatch.chdir(tmp_path)
    replies = [(0, 'https://github.com/autonomio/astetik.git', ''), (0, HEAD, ''), (0, TAG if existing_tag else '', '')]
    if existing_tag:
        replies.append((0, HEAD, ''))
    replies.extend([
        (0, f'{HEAD}\trefs/tags/{TAG}\n' if existing_tag else '', ''),
        (1, _http(404, {'message': 'Not Found'}), 'gh: HTTP 404'),
        (0, '', ''), (0, '', ''),
    ])
    if not existing_tag:
        replies.extend([(0, '', ''), (0, '', '')])
    replies.append((0, '', ''))
    calls = _responses(monkeypatch, replies)
    assert release.main() == 0
    creates = [call for call in calls if call[:3] == ['gh', 'release', 'create']]
    assert len(creates) == 1
    assert '--verify-tag' in creates[0]
    assert creates[0][creates[0].index('--repo') + 1] == 'autonomio/astetik'
    assert creates[0][3] == TAG
    assert len([call for call in calls if call[:2] == ['git', 'push']]) == (0 if existing_tag else 1)
    assert (tmp_path / 'release-notes.md').is_file()


@pytest.mark.parametrize('origin', [
    'https://github.com/someone/other.git',
    'git@github.com:autonomio/other.git',
    'https://example.com/autonomio/astetik.git',
])
def test_mismatched_repository_blocks_before_tag_or_release_reads(
    monkeypatch: pytest.MonkeyPatch, origin: str,
) -> None:
    monkeypatch.setenv('GITHUB_REPOSITORY', 'autonomio/astetik')
    calls = _responses(monkeypatch, [(0, origin, '')])
    with pytest.raises(SystemExit, match='origin does not identify GITHUB_REPOSITORY'):
        release.main()
    assert calls == [['git', 'remote', 'get-url', 'origin']]


@pytest.fixture
def unchanged_release(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, str]:
    """Retain a local published tag followed by a version-exempt dependency change."""
    monkeypatch.setattr(release, 'skip_unchanged_release', SKIP_UNCHANGED_RELEASE)
    monkeypatch.setenv('GITHUB_REPOSITORY', 'autonomio/astetik')
    monkeypatch.chdir(tmp_path)
    def git(*args: str) -> str:
        return subprocess.check_output(['git', *args], text=True).strip()

    git('init', '-b', 'master')
    git('config', 'user.name', 'Release regression')
    git('config', 'user.email', 'release@example.invalid')
    git('add', 'pyproject.toml', 'CHANGELOG.md')
    git('commit', '-m', 'Prepare release regression')
    git('tag', TAG)
    published = git('rev-parse', 'HEAD')
    remote = tmp_path / 'remote.git'
    git('init', '--bare', str(remote))
    git('remote', 'add', 'origin', str(remote))
    git('push', 'origin', 'master', TAG)
    (tmp_path / 'dependency.lock').write_text('Updated dependency fixture.\n')
    git('add', 'dependency.lock')
    git('commit', '-m', 'Update dependency without changing project version')
    (tmp_path / 'dependency.lock').write_text('Another dependency fixture update.\n')
    git('add', 'dependency.lock')
    git('commit', '-m', 'Update another dependency without changing project version')
    monkeypatch.setattr(release, 'release_exists', lambda _tag, _repo: True)
    return tmp_path, published


def test_unchanged_version_merge_skips_verified_old_release_without_mutation(
    unchanged_release: tuple[Path, str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, _published = unchanged_release
    original = release.run
    calls: list[tuple[str, ...]] = []

    def run(*args: str) -> str:
        calls.append(args)
        if args == ('git', 'remote', 'get-url', 'origin'):
            return 'https://github.com/autonomio/astetik.git'
        return original(*args)

    monkeypatch.setattr(release, 'run', run)
    head = original('git', 'rev-parse', 'HEAD')
    assert release.main() == 0
    assert original('git', 'rev-parse', 'HEAD') == head
    assert not (path / 'release-notes.md').exists()
    assert all('push' not in call and 'create' not in call for call in calls)


@pytest.mark.parametrize('revision', ['HEAD^', TAG])
def test_older_tag_requires_unchanged_parent_and_tagged_versions(
    unchanged_release: tuple[Path, str], monkeypatch: pytest.MonkeyPatch, revision: str,
) -> None:
    original = release.run
    changed = original('git', 'rev-parse', revision)

    def run(*args: str) -> str:
        if args == ('git', 'show', f'{changed}:pyproject.toml'):
            return '[project]\nversion = "0.0.1"\n'
        return original(*args)

    monkeypatch.setattr(release, 'run', run)
    with pytest.raises(SystemExit, match='does not preserve the version'):
        release.skip_unchanged_release(TAG, TAG[1:])


def test_older_tag_requires_an_existing_stable_release(
    unchanged_release: tuple[Path, str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(release, 'release_exists', lambda _tag, _repo: False)
    with pytest.raises(SystemExit, match='no published release'):
        release.skip_unchanged_release(TAG, TAG[1:])


def test_older_tag_requires_its_unchanged_remote_counterpart(
    unchanged_release: tuple[Path, str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = release.run

    def run(*args: str) -> str:
        if args[:3] == ('git', 'ls-remote', '--tags'):
            return ''
        return original(*args)

    monkeypatch.setattr(release, 'run', run)
    with pytest.raises(SystemExit, match='no verified remote counterpart'):
        release.skip_unchanged_release(TAG, TAG[1:])


def test_older_tag_outside_candidate_history_cannot_be_skipped(
    unchanged_release: tuple[Path, str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = release.run
    foreign = original('git', 'commit-tree', 'HEAD^{tree}', '-m', 'Unrelated release fixture')

    def run(*args: str) -> str:
        if args == ('git', 'rev-parse', '--verify', f'refs/tags/{TAG}^{{commit}}'):
            return foreign
        return original(*args)

    monkeypatch.setattr(release, 'run', run)
    with pytest.raises(SystemExit, match='outside HEAD history'):
        release.skip_unchanged_release(TAG, TAG[1:])


def test_remote_retargeted_old_tag_cannot_be_skipped(
    unchanged_release: tuple[Path, str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = release.run

    def run(*args: str) -> str:
        if args[:3] == ('git', 'ls-remote', '--tags'):
            return f'{OTHER}\trefs/tags/{TAG}\n'
        return original(*args)

    monkeypatch.setattr(release, 'run', run)
    with pytest.raises(SystemExit, match='does not resolve to'):
        release.skip_unchanged_release(TAG, TAG[1:])


def test_missing_tag_at_unchanged_version_never_publishes_later_commit(
    unchanged_release: tuple[Path, str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, _published = unchanged_release
    original = release.run
    original('git', 'update-ref', '-d', f'refs/tags/{TAG}')
    original('git', '-C', str(path / 'remote.git'), 'update-ref', '-d', f'refs/tags/{TAG}')
    head = original('git', 'rev-parse', 'HEAD')
    calls: list[tuple[str, ...]] = []

    def run(*args: str) -> str:
        calls.append(args)
        if args == ('git', 'remote', 'get-url', 'origin'):
            return 'https://github.com/autonomio/astetik.git'
        return original(*args)

    def release_lookup(_tag: str, _repo: str) -> bool:
        pytest.fail('An unchanged missing-tag merge must not look up a release')

    monkeypatch.setattr(release, 'run', run)
    monkeypatch.setattr(release, 'release_exists', release_lookup)
    assert release.main() == 0
    assert original('git', 'rev-parse', 'HEAD') == head
    assert not original('git', 'tag', '--list', TAG)
    assert not (path / 'release-notes.md').exists()
    assert all('push' not in call and 'create' not in call and '-a' not in call for call in calls)


def test_missing_local_tag_does_not_bypass_remote_tag_identity(
    unchanged_release: tuple[Path, str],
) -> None:
    release.run('git', 'update-ref', '-d', f'refs/tags/{TAG}')
    with pytest.raises(SystemExit, match='does not resolve to the expected release commit'):
        release.skip_unchanged_release(TAG, TAG[1:])


@pytest.mark.parametrize('has_parent', [False, True])
def test_missing_tag_at_initial_or_new_version_creates_current_release(
    unchanged_release: tuple[Path, str], monkeypatch: pytest.MonkeyPatch,
    has_parent: bool,
) -> None:
    path, _published = unchanged_release
    original = release.run
    if has_parent:
        version = '99.0.0'
        (path / 'pyproject.toml').write_text(f'[project]\nversion = "{version}"\n')
        (path / 'CHANGELOG.md').write_text(f'# v{version}\n\nCreate new release fixture.\n')
        original('git', 'add', 'pyproject.toml', 'CHANGELOG.md')
        original('git', 'commit', '-m', 'Change package version')
    else:
        original('git', 'checkout', '--orphan', 'initial-release')
        original('git', 'commit', '-m', 'Initial package release fixture')
        version = TAG[1:]
        original('git', 'update-ref', '-d', f'refs/tags/{TAG}')
        original('git', '-C', str(path / 'remote.git'), 'update-ref', '-d', f'refs/tags/{TAG}')
    tag = f'v{version}'
    head = original('git', 'rev-parse', 'HEAD')
    publishes: list[tuple[str, ...]] = []

    def run(*args: str) -> str:
        if args == ('git', 'remote', 'get-url', 'origin'):
            return 'https://github.com/autonomio/astetik.git'
        if args[:3] == ('gh', 'release', 'create'):
            publishes.append(args)
            return 'release creation unit-fixture transport'
        return original(*args)

    monkeypatch.setattr(release, 'run', run)
    monkeypatch.setattr(release, 'release_exists', lambda _tag, _repo: False)
    assert release.main() == 0
    assert original('git', 'rev-parse', f'refs/tags/{tag}^{{commit}}') == head
    assert original('git', 'ls-remote', '--tags', 'origin', f'refs/tags/{tag}^{{}}').split()[0] == head
    assert len(publishes) == 1 and publishes[0][3] == tag
    assert (path / 'release-notes.md').is_file()


@pytest.mark.parametrize('has_older,expected', [(True, 'v2.0.3'), (False, None)])
def test_previous_tag_uses_only_lower_versions_on_candidate_history(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    has_older: bool, expected: str | None,
) -> None:
    monkeypatch.chdir(tmp_path)
    git = release.run
    git('git', 'init', '-b', 'master')
    git('git', 'config', 'user.name', 'Release traceability regression')
    git('git', 'config', 'user.email', 'traceability@example.invalid')
    git('git', 'add', 'pyproject.toml', 'CHANGELOG.md')
    git('git', 'commit', '-m', 'Initialize traceability regression')
    if has_older:
        git('git', 'tag', 'v2.0.3')
    # A reachable future version must also be excluded by SemVer comparison.
    git('git', 'tag', 'v9.0.0')
    (tmp_path / 'release-step').write_text('Current release fixture.\n')
    git('git', 'add', 'release-step')
    git('git', 'commit', '-m', 'Prepare current release fixture')
    current = git('git', 'rev-parse', 'HEAD')
    git('git', 'tag', 'v2.0.4')
    foreign = git('git', 'commit-tree', 'HEAD^{tree}', '-m', 'Unrelated tagged fixture')
    git('git', 'tag', 'v2.0.2', foreign)
    (tmp_path / 'release-step').write_text('Future release fixture.\n')
    git('git', 'add', 'release-step')
    git('git', 'commit', '-m', 'Prepare future release fixture')
    git('git', 'tag', 'v2.0.5')
    git('git', 'checkout', '--detach', current)
    assert release.previous_tag('v2.0.4') == expected


def test_release_concurrency_serializes_without_replacing_pending_merges() -> None:
    workflow_path = SCRIPT.parents[1] / '.github/workflows/pr_post_release.yml'
    workflow = yaml.load(workflow_path.read_text(), Loader=yaml.BaseLoader)
    assert workflow['concurrency'] == {
        'group': 'release-${{ github.ref }}', 'cancel-in-progress': 'false', 'queue': 'max',
    }
