"""Offline command responses prove release absence and immutable tag identity."""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest
from _common import loads_toml

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts' / 'create_release.py'
spec = importlib.util.spec_from_file_location('create_release', SCRIPT)
assert spec is not None and spec.loader is not None
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
HEAD = '1' * 40
OTHER = '2' * 40
VERSION = loads_toml((SCRIPT.parents[1] / 'pyproject.toml').read_text())['project']['version']
TAG = f'v{VERSION}'


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
