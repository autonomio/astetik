"""Only verified same-run distributions and bundles reach an exact stable release."""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / '.github/workflows/pr_publish_pypi.yml'
SHA = 'a' * 40
NAMES = ('astetik-2.0.0-py3-none-any.whl', 'astetik-2.0.0.tar.gz')
BUNDLE = 'astetik-2.0.0.release-source.sigstore.json'
WORKFLOW_REF = 'autonomio/astetik/.github/workflows/pr_publish_pypi.yml@refs/heads/master'


def _job() -> dict:
    return yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)['jobs']['publish_release_assets']


def _program() -> str:
    source = _job()['steps'][-1]['run']
    assert source.startswith('set -euo pipefail\npython -I -')
    return source.split("<<'PYCODE'\n", 1)[1].rsplit('\nPYCODE', 1)[0]


@dataclass
class AssetFixture:
    path: Path
    identity: dict[str, str]
    release: dict
    local_bytes: dict[str, bytes]
    remote_bytes: dict[int, bytes]
    calls: list[list[str]]
    uploads: list[list[str]]
    failures: list[str]

    def run(self) -> None:
        exec(compile(_program(), str(WORKFLOW), 'exec'), {'__name__': 'asset_publication_fixture'})

    def existing(self, name: str, data: bytes) -> None:
        asset_id = len(self.remote_bytes) + 1
        self.remote_bytes[asset_id] = data
        self.release['assets'].append({'name': name, 'id': asset_id})


@pytest.fixture
def assets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> AssetFixture:
    monkeypatch.chdir(tmp_path)
    identity = {
        'repository': 'https://github.com/autonomio/astetik', 'tag': 'v2.0.0',
        'commit': 'b' * 40, 'workflow_commit': SHA,
    }
    fixture = AssetFixture(
        tmp_path, identity, {'id': 17, 'tag_name': 'v2.0.0', 'draft': False, 'prerelease': False, 'assets': []},
        {NAMES[0]: b'wheel unit-fixture transport', NAMES[1]: b'sdist unit-fixture transport', BUNDLE: b'signed-bundle unit-fixture transport'},
        {}, [], [], [],
    )
    (tmp_path / 'dist').mkdir()
    (tmp_path / 'bundle').mkdir()
    for name in NAMES:
        (tmp_path / 'dist' / name).write_bytes(fixture.local_bytes[name])
    (tmp_path / 'bundle' / 'attestation.json').write_bytes(fixture.local_bytes[BUNDLE])
    for name, value in {
        'SOURCE_IDENTITY': json.dumps(identity), 'RELEASE_ID': '17',
        'GITHUB_SHA': SHA, 'GITHUB_WORKFLOW_SHA': SHA, 'GITHUB_WORKFLOW_REF': WORKFLOW_REF,
        'GITHUB_REF': 'refs/heads/master', 'GITHUB_REPOSITORY': 'autonomio/astetik',
    }.items():
        monkeypatch.setenv(name, value)

    def check_output(command: list[str], *, text: bool = False) -> str | bytes:
        fixture.calls.append(command)
        if command == ['gh', 'attestation', 'trusted-root']:
            assert not text
            return b'unit-fixture trusted-root transport'
        if command[:3] == ['gh', 'attestation', 'verify']:
            assert text
            artifact = Path(command[3])
            assert command[4:] == [
                '--repo', 'autonomio/astetik', '--bundle', 'bundle/attestation.json',
                '--custom-trusted-root', 'sigstore-trusted-root.jsonl', '--digest-alg', 'sha256',
                '--cert-identity', f'https://github.com/{WORKFLOW_REF}',
                '--cert-oidc-issuer', 'https://token.actions.githubusercontent.com',
                '--source-ref', 'refs/heads/master', '--source-digest', SHA,
                '--signer-digest', SHA, '--deny-self-hosted-runners',
                '--predicate-type', 'urn:autonomio:astetik:release-source:v1', '--format', 'json',
            ]
            assert (tmp_path / 'sigstore-trusted-root.jsonl').read_bytes() == b'unit-fixture trusted-root transport'
            if ('signature' in fixture.failures
                    or hashlib.sha256(artifact.read_bytes()).digest() != hashlib.sha256(fixture.local_bytes[artifact.name]).digest()):
                raise subprocess.CalledProcessError(1, command)
            predicate = identity | ({'commit': 'c' * 40} if 'predicate' in fixture.failures else {})
            return json.dumps([{'verificationResult': {'statement': {'predicate': predicate}}}])
        assert command[:2] == ['gh', 'api']
        if command[2].startswith('repos/autonomio/astetik/releases/assets/'):
            assert not text and command[3:] == ['--header', 'Accept: application/octet-stream']
            return fixture.remote_bytes[int(command[2].rsplit('/', 1)[1])]
        assert text and len(command) == 3
        if command[2] == 'repos/autonomio/astetik/releases/17' and 'public' in fixture.failures:
            return json.dumps(fixture.release | {'assets': []})
        assert command[2] in ('repos/autonomio/astetik/releases/tags/v2.0.0', 'repos/autonomio/astetik/releases/17')
        return json.dumps(fixture.release)

    def run(command: list[str], *, check: bool) -> subprocess.CompletedProcess:
        assert check and command[:6] == ['gh', 'release', 'upload', 'v2.0.0', '--repo', 'autonomio/astetik']
        fixture.uploads.append(command)
        for name in command[6:]:
            path = Path(name)
            fixture.existing(path.name, path.read_bytes())
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, 'check_output', check_output)
    monkeypatch.setattr(subprocess, 'run', run)
    return fixture


def test_asset_job_is_separate_from_source_execution_signing_and_pypi() -> None:
    job = _job()
    assert job['needs'] == ['build_distribution', 'attest_distribution']
    assert job['environment'] == 'release'
    assert job['permissions'] == {'contents': 'write', 'attestations': 'read'}
    assert all('checkout' not in step.get('uses', '') for step in job['steps'])
    assert job['steps'][0]['with'] == {'name': 'pypi-distributions', 'path': 'dist'}
    assert job['steps'][1]['with'] == {'name': 'release-source-bundle', 'path': 'bundle'}
    program = _program()
    assert 'pip' not in program and 'build' not in program and '--clobber' not in program
    assert program.index("'attestation', 'verify'") < program.index("'release', 'upload'")


@pytest.mark.parametrize('existing', [0, 1, 3])
def test_publication_uploads_only_missing_identical_assets_and_verifies_public_bytes(
    assets: AssetFixture, existing: int,
) -> None:
    names = [*NAMES, BUNDLE]
    for name in names[:existing]:
        assets.existing(name, assets.local_bytes[name])
    assets.run()
    expected = ['dist/' + name for name in names[existing:]]
    assert assets.uploads == ([['gh', 'release', 'upload', 'v2.0.0', '--repo', 'autonomio/astetik', *expected]] if expected else [])
    assert sorted(assets.remote_bytes.values()) == sorted(assets.local_bytes.values())
    assert [call[3] for call in assets.calls if call[:3] == ['gh', 'attestation', 'verify']] == ['dist/' + name for name in NAMES]
    assert assets.calls[-3:][0][2] == 'repos/autonomio/astetik/releases/assets/1'


@pytest.mark.parametrize('failure', ['signature', 'predicate', 'digest', 'existing', 'inventory', 'bundle'])
def test_invalid_proof_or_asset_inventory_cannot_upload(assets: AssetFixture, failure: str) -> None:
    assets.failures.append(failure)
    if failure == 'digest':
        (assets.path / 'dist' / NAMES[0]).write_bytes(b'tampered wheel')
    if failure == 'existing':
        assets.existing(NAMES[0], b'different already published wheel')
    if failure == 'inventory':
        (assets.path / 'dist' / 'unexpected.whl').write_bytes(b'extra')
    if failure == 'bundle':
        (assets.path / 'bundle' / 'another.json').write_bytes(b'extra')
    with pytest.raises((SystemExit, subprocess.CalledProcessError)):
        assets.run()
    assert not assets.uploads


@pytest.mark.parametrize('field,value', [
    ('GITHUB_REF', 'refs/tags/v2.0.0'), ('GITHUB_REPOSITORY', 'other/astetik'),
    ('GITHUB_SHA', '0' * 40), ('GITHUB_WORKFLOW_SHA', '0' * 40),
    ('GITHUB_WORKFLOW_REF', 'autonomio/astetik/.github/workflows/other.yml@refs/heads/master'),
])
def test_wrong_workflow_context_cannot_read_or_publish(
    assets: AssetFixture, monkeypatch: pytest.MonkeyPatch, field: str, value: str,
) -> None:
    monkeypatch.setenv(field, value)
    with pytest.raises(SystemExit, match='verified protected master workflow'):
        assets.run()
    assert not assets.calls and not assets.uploads


@pytest.mark.parametrize('field,value', [
    ('id', 18), ('tag_name', 'v2.0.1'), ('draft', True), ('prerelease', True),
])
def test_wrong_stable_release_identity_cannot_upload(assets: AssetFixture, field: str, value: object) -> None:
    assets.release[field] = value
    with pytest.raises(SystemExit, match='exact verified stable release'):
        assets.run()
    assert len(assets.calls) == 1 and not assets.uploads


def test_missing_public_assets_fail_before_downstream_index_publication(assets: AssetFixture) -> None:
    assets.failures.append('public')
    with pytest.raises(SystemExit, match='Published asset inventory'):
        assets.run()
    assert len(assets.uploads) == 1
