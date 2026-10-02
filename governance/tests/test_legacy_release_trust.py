"""Legacy approval verifies fixed public bytes without sharing source and signing credentials."""
from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / '.github/workflows/sign_legacy_release.yml'
SHA = 'a' * 40
SOURCE = '11fb4ab8defa2799b0bcc4760620fb715377e93c'
NAMES = ('astetik-1.16-py2.py3-none-any.whl', 'astetik-1.16.tar.gz')
EXPECTED_DIGESTS = (
    '850fca54fa5c72b78e1f19c4cf1599d69870bb2a02bc4bf450297a5c317bb835',
    'c43fcdc927c66aee498241c1948958e87fc8df8651bd4baf4483510d639859cd',
)
EXPECTED_URLS = (
    'https://files.pythonhosted.org/packages/1e/e1/a0f19c716a4c935f1c31e2a3e18edaded99e003e2db31b807b5a1bedb597/astetik-1.16-py2.py3-none-any.whl',
    'https://files.pythonhosted.org/packages/7c/38/7de8d21c959167d760a8c6be2f9785c0f1b40b4788a4ed7dd6667221c55b/astetik-1.16.tar.gz',
)


def _workflow() -> dict:
    return yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)


def _program(job: str) -> str:
    steps = _workflow()['jobs'][job]['steps']
    command = next(step['run'] for step in steps if 'run' in step)
    assert 'python -I -' in command
    return command.split("<<'PYCODE'\n", 1)[1].rsplit('\nPYCODE', 1)[0]


@dataclass
class LegacyFixture:
    namespace: dict
    metadata: dict
    downloads: dict[str, bytes]
    release: dict
    commands: list[list[str]]
    ancestry_failure: list[str]
    tagged: list[str]
    path: Path

    def run(self) -> None:
        self.namespace['main']()


@pytest.fixture
def legacy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> LegacyFixture:
    """Inject small labelled unit bytes; retain the actual validator and SHA-256 implementation."""
    namespace = {'__name__': 'legacy_unit_fixture'}
    exec(compile(_program('verify_legacy'), str(WORKFLOW), 'exec'), namespace)
    expected = namespace['ARTIFACTS']
    assert tuple(expected) == NAMES
    assert tuple(value['sha256'] for value in expected.values()) == EXPECTED_DIGESTS
    assert tuple(value['url'] for value in expected.values()) == EXPECTED_URLS
    assert tuple(value['size'] for value in expected.values()) == (5406334, 5375929)
    assert namespace['SOURCE'] == SOURCE
    downloads = dict(zip(EXPECTED_URLS, (b'unit-fixture wheel bytes', b'unit-fixture sdist bytes'), strict=True))
    # Production constants are asserted above; only expected fixture digests/sizes are injected.
    for value in expected.values():
        data = downloads[value['url']]
        value.update(sha256=hashlib.sha256(data).hexdigest(), size=len(data))
    metadata = {'info': {'name': 'astetik', 'version': '1.16'}, 'urls': [
        {'filename': name, 'url': value['url'], 'size': value['size'],
         'digests': {'sha256': value['sha256']}, 'yanked': False}
        for name, value in expected.items()
    ]}
    release = {'id': 152049185, 'tag_name': 'v1.16', 'draft': False, 'prerelease': False,
               'html_url': 'https://github.com/autonomio/astetik/releases/tag/v1.16'}
    commands, ancestry_failure, tagged = [], [], [SOURCE]

    def check_output(command: list[str], *, text: bool) -> str:
        assert text
        commands.append(command)
        if command == ['git', 'rev-parse', 'refs/tags/v1.16^{commit}']:
            return tagged[0] + '\n'
        assert command == ['gh', 'api', 'repos/autonomio/astetik/releases/tags/v1.16']
        return json.dumps(release)

    def run(command: list[str], *, check: bool) -> subprocess.CompletedProcess:
        assert not check and command[:3] == ['git', 'merge-base', '--is-ancestor']
        commands.append(command)
        return subprocess.CompletedProcess(command, int(command[3] in ancestry_failure))

    def urlopen(url: str, *, timeout: int) -> io.BytesIO:
        assert timeout == 30
        if url == 'https://pypi.org/pypi/astetik/1.16/json':
            return io.BytesIO(json.dumps(metadata).encode())
        assert url in downloads
        return io.BytesIO(downloads[url])

    monkeypatch.setattr(namespace['subprocess'], 'check_output', check_output)
    monkeypatch.setattr(namespace['subprocess'], 'run', run)
    monkeypatch.setattr(namespace['urllib'].request, 'urlopen', urlopen)
    monkeypatch.chdir(tmp_path)
    for name, value in {
        'GITHUB_EVENT_NAME': 'workflow_dispatch', 'GITHUB_REF': 'refs/heads/master',
        'GITHUB_REPOSITORY': 'autonomio/astetik', 'GITHUB_SHA': SHA,
        'GITHUB_WORKFLOW_SHA': SHA,
        'GITHUB_WORKFLOW_REF': 'autonomio/astetik/.github/workflows/sign_legacy_release.yml@refs/heads/master',
        'RELEASE_TAG': 'v1.16', 'GITHUB_OUTPUT': str(tmp_path / 'output'),
    }.items():
        monkeypatch.setenv(name, value)
    return LegacyFixture(namespace, metadata, downloads, release, commands, ancestry_failure, tagged, tmp_path)


def test_verified_legacy_identity_and_artifacts_are_bound_to_protected_workflow(legacy: LegacyFixture) -> None:
    legacy.run()
    output = dict(line.split('=', 1) for line in (legacy.path / 'output').read_text().splitlines())
    approval = json.loads(output['approval'])
    assert approval == {
        'approval': 'retrospective approval of unchanged published distributions',
        'historical_build_provenance': False,
        'repository': 'https://github.com/autonomio/astetik', 'tag': 'v1.16',
        'source_commit': SOURCE, 'workflow_commit': SHA, 'artifacts': legacy.namespace['ARTIFACTS'],
    }
    assert output['workflow_sha'] == SHA
    for name, expected in approval['artifacts'].items():
        assert (legacy.path / 'legacy' / name).read_bytes() == legacy.downloads[expected['url']]
    assert ['git', 'merge-base', '--is-ancestor', SOURCE, SHA] in legacy.commands
    assert ['git', 'merge-base', '--is-ancestor', SHA, 'refs/remotes/origin/master'] in legacy.commands


@pytest.mark.parametrize('name, value', [
    ('GITHUB_EVENT_NAME', 'push'), ('GITHUB_REF', 'refs/tags/v1.16'),
    ('GITHUB_REPOSITORY', 'other/astetik'), ('GITHUB_WORKFLOW_REF', 'untrusted@refs/heads/master'),
    ('RELEASE_TAG', 'v1.17'), ('GITHUB_SHA', 'b' * 40), ('GITHUB_WORKFLOW_SHA', 'not-a-sha'),
])
def test_wrong_execution_identity_fails_before_network_or_output(
    legacy: LegacyFixture, monkeypatch: pytest.MonkeyPatch, name: str, value: str,
) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(SystemExit):
        legacy.run()
    assert not legacy.commands and not (legacy.path / 'legacy').exists()
    assert not (legacy.path / 'output').exists()


@pytest.mark.parametrize('ancestor', [SOURCE, SHA])
def test_source_or_workflow_outside_protected_history_fails(legacy: LegacyFixture, ancestor: str) -> None:
    legacy.ancestry_failure.append(ancestor)
    with pytest.raises(SystemExit, match='protected master history'):
        legacy.run()
    assert not (legacy.path / 'output').exists()


def test_substituted_legacy_tag_fails(legacy: LegacyFixture) -> None:
    legacy.tagged[0] = 'b' * 40
    with pytest.raises(SystemExit, match='known source commit'):
        legacy.run()
    assert not (legacy.path / 'output').exists()


@pytest.mark.parametrize('field, value', [
    ('id', 152049186), ('tag_name', 'v1.17'), ('draft', True), ('prerelease', True),
    ('html_url', 'https://github.com/other/astetik/releases/tag/v1.16'),
])
def test_wrong_published_release_is_rejected(legacy: LegacyFixture, field: str, value: object) -> None:
    legacy.release[field] = value
    with pytest.raises(SystemExit, match='exact published stable release'):
        legacy.run()
    assert not (legacy.path / 'output').exists()


@pytest.mark.parametrize('field, value', [('name', 'other'), ('version', '1.17')])
def test_wrong_index_package_identity_is_rejected(legacy: LegacyFixture, field: str, value: str) -> None:
    legacy.metadata['info'][field] = value
    with pytest.raises(SystemExit, match='package/version identity'):
        legacy.run()
    assert not (legacy.path / 'legacy').exists()


@pytest.mark.parametrize('field, value', [
    ('filename', '../other.whl'), ('url', 'https://other.invalid/file'), ('size', 0),
    ('digests', {'sha256': '0' * 64}), ('yanked', True),
])
def test_wrong_artifact_metadata_is_rejected(legacy: LegacyFixture, field: str, value: object) -> None:
    legacy.metadata['urls'][0][field] = value
    with pytest.raises(SystemExit, match='artifact'):
        legacy.run()
    assert not (legacy.path / 'legacy').exists() and not (legacy.path / 'output').exists()


@pytest.mark.parametrize('url', EXPECTED_URLS)
def test_changed_download_bytes_fail_real_sha256(legacy: LegacyFixture, url: str) -> None:
    legacy.downloads[url] = b'X' + legacy.downloads[url][1:]
    with pytest.raises(SystemExit, match='distribution digest or size'):
        legacy.run()
    assert not (legacy.path / 'output').exists()


def test_signer_and_publisher_retain_only_verified_same_run_bytes() -> None:
    workflow = _workflow()
    assert set(workflow['on']) == {'workflow_dispatch'}
    assert workflow['on']['workflow_dispatch']['inputs']['release_tag'] == {
        'description': 'Approve unchanged PyPI 1.16 artifacts retrospectively',
        'required': 'true', 'type': 'choice', 'options': ['v1.16'],
    }
    jobs = workflow['jobs']
    verifier, signer, publisher = (jobs[name] for name in ('verify_legacy', 'sign_legacy', 'publish_legacy'))
    for job in (verifier, signer, publisher):
        assert "github.ref == 'refs/heads/master'" in job['if']
        assert "github.repository == 'autonomio/astetik'" in job['if']
        assert all('continue-on-error' not in step for step in job['steps'])
    assert verifier['permissions'] == {'contents': 'read'}
    assert verifier['steps'][0]['with'] == {
        'ref': '${{ github.sha }}', 'fetch-depth': '0', 'persist-credentials': 'false',
    }
    assert signer['environment'] == publisher['environment'] == 'release'
    assert signer['needs'] == 'verify_legacy'
    assert publisher['needs'] == ['verify_legacy', 'sign_legacy']
    assert signer['permissions'] == {'contents': 'read', 'id-token': 'write', 'attestations': 'write'}
    assert publisher['permissions'] == {'contents': 'write'}
    assert len(signer['steps']) == 3
    assert set(signer['steps'][0]) == {'name', 'run'}
    assert all('run' not in step and 'checkout' not in step['uses'] for step in signer['steps'][1:])
    assert all('checkout' not in step.get('uses', '') for step in publisher['steps'])
    assert publisher['steps'][0]['with'] == {
        'name': 'legacy-verified-distributions', 'path': 'legacy',
    }
    assert signer['steps'][1]['uses'] == 'actions/attest@daf44fb950173508f38bd2406030372c1d1162b1'
    assert signer['steps'][1]['with'] == {
        'subject-checksums': 'legacy-reviewed.sha256',
        'predicate-type': 'urn:autonomio:astetik:legacy-approval:v1',
        'predicate': '${{ needs.verify_legacy.outputs.approval }}',
    }
    assert all('download-artifact' not in step.get('uses', '') for step in signer['steps'])
    assert signer['steps'][2]['with']['path'] == '${{ steps.attest.outputs.bundle-path }}'
    assert publisher['steps'][1]['with'] == {'name': 'legacy-approval-bundle', 'path': 'bundle'}
    source = _program('publish_legacy')
    for flag in ('--cert-identity', '--cert-oidc-issuer', '--source-ref', '--source-digest',
                 '--signer-digest', '--predicate-type', '--deny-self-hosted-runners'):
        assert flag in source
    assert '--signer-workflow' not in source and '--clobber' not in source
    assert "'gh', 'release', 'upload', 'v1.16'" in source
    assert 'pip' not in source and 'build' not in source
    assert source.index("'attestation', 'verify'") < source.index("'release', 'upload'")


@pytest.mark.parametrize('failure', [None, 'digest', 'predicate', 'signature'])
def test_publisher_verifies_actual_bytes_and_predicate_before_upload(
    legacy: LegacyFixture, monkeypatch: pytest.MonkeyPatch, failure: str | None,
) -> None:
    legacy.run()
    output = dict(line.split('=', 1) for line in (legacy.path / 'output').read_text().splitlines())
    approval = json.loads(output['approval'])
    monkeypatch.setenv('WORKFLOW_SHA', SHA)
    monkeypatch.setenv('APPROVAL', output['approval'])
    bundle_dir = legacy.path / 'bundle'
    bundle_dir.mkdir()
    (bundle_dir / 'attestation.json').write_bytes(b'unit-fixture signed bundle transport')
    if failure == 'digest':
        (legacy.path / 'legacy' / NAMES[0]).write_bytes(b'tampered after verification')
    signed_predicate = json.loads(json.dumps(approval))
    if failure == 'predicate':
        signed_predicate['historical_build_provenance'] = True
    signatures, uploads = [], []

    def check_output(command: list[str], *, text: bool) -> str:
        assert text
        if command[:2] == ['gh', 'api']:
            assert command == ['gh', 'api', 'repos/autonomio/astetik/releases/tags/v1.16']
            return json.dumps(legacy.release)
        assert command[:3] == ['gh', 'attestation', 'verify']
        signatures.append(command)
        assert command[4:] == [
            '--repo', 'autonomio/astetik', '--bundle', 'bundle/attestation.json',
            '--cert-identity', 'https://github.com/autonomio/astetik/.github/workflows/sign_legacy_release.yml@refs/heads/master',
            '--cert-oidc-issuer', 'https://token.actions.githubusercontent.com',
            '--signer-digest', SHA, '--source-digest', SHA, '--source-ref', 'refs/heads/master',
            '--deny-self-hosted-runners', '--predicate-type', 'urn:autonomio:astetik:legacy-approval:v1',
            '--format', 'json',
        ]
        if failure == 'signature':
            raise subprocess.CalledProcessError(1, command)
        return json.dumps([{'verificationResult': {'statement': {'predicate': signed_predicate}}}])

    def run(command: list[str], *, check: bool) -> subprocess.CompletedProcess:
        assert check
        uploads.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, 'check_output', check_output)
    monkeypatch.setattr(subprocess, 'run', run)
    program = compile(_program('publish_legacy'), str(WORKFLOW), 'exec')
    if failure:
        with pytest.raises((SystemExit, subprocess.CalledProcessError)):
            exec(program, {'__name__': 'legacy_publish_unit_fixture'})
        assert not uploads
        return
    exec(program, {'__name__': 'legacy_publish_unit_fixture'})
    assert [command[3] for command in signatures] == [f'legacy/{name}' for name in NAMES]
    assert uploads == [[
        'gh', 'release', 'upload', 'v1.16', '--repo', 'autonomio/astetik',
        *(f'legacy/{name}' for name in NAMES), 'legacy/astetik-1.16.legacy-approval.sigstore.json',
    ]]
    for name, expected in approval['artifacts'].items():
        assert (legacy.path / 'legacy' / name).read_bytes() == legacy.downloads[expected['url']]
    assert (legacy.path / 'legacy' / 'astetik-1.16.legacy-approval.sigstore.json').read_bytes() == (bundle_dir / 'attestation.json').read_bytes()


@pytest.mark.parametrize('failure', ['checksum', 'signature', 'predicate'])
def test_documented_verifier_stops_on_first_failed_check(tmp_path: Path, failure: str) -> None:
    source = (ROOT / 'docs/Developer/Release-Policy.md').read_text()
    recipe = next(block.split('```', 1)[0] for block in source.split('```bash\n')[1:]
                  if 'gh release download v1.16' in block)
    executable_dir = tmp_path / 'bin'
    executable_dir.mkdir()
    witness = tmp_path / 'calls'
    for name, program in {
        'gh': 'echo "gh $*" >> "$WITNESS"\n'
              'if [ "$1" = run ]; then echo "$SHA"; fi\n'
              'if [ "$1 $2" = "attestation verify" ] && [ "$FAILURE" = signature ]; then exit 1; fi\n',
        'shasum': 'echo checksum >> "$WITNESS"\nif [ "$FAILURE" = checksum ]; then exit 1; fi\n',
        'jq': 'echo predicate >> "$WITNESS"\nif [ "$FAILURE" = predicate ]; then exit 1; fi\n',
    }.items():
        executable = executable_dir / name
        executable.write_text('#!/bin/sh\n' + program + 'exit 0\n')
        executable.chmod(0o755)
    result = subprocess.run(
        ['bash', '-c', recipe], cwd=tmp_path, text=True, capture_output=True, check=False,
        env=os.environ | {'PATH': f'{executable_dir}{os.pathsep}{os.environ["PATH"]}',
                          'WITNESS': str(witness), 'FAILURE': failure, 'SHA': SHA, 'RUN_ID': 'unit-fixture'},
    )
    assert result.returncode != 0, result.stderr
    calls = witness.read_text()
    assert calls.count('attestation verify') <= 1
    assert NAMES[1] not in calls
    if failure == 'checksum':
        assert 'attestation' not in calls
    if failure == 'signature':
        assert 'predicate' not in calls.splitlines()


def test_changed_distribution_transfer_cannot_change_fixed_signed_subjects(tmp_path: Path) -> None:
    signer = _workflow()['jobs']['sign_legacy']
    (tmp_path / 'legacy').mkdir()
    for name in NAMES:
        (tmp_path / 'legacy' / name).write_bytes(b'unit-fixture corrupted transfer')
    result = subprocess.run(
        ['bash', '-euo', 'pipefail', '-c', signer['steps'][0]['run']], cwd=tmp_path,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / 'legacy-reviewed.sha256').read_text() == ''.join(
        f'{digest}  {name}\n' for name, digest in zip(NAMES, EXPECTED_DIGESTS, strict=True)
    )
    assert '${{' not in signer['steps'][0]['run'] and '$' not in signer['steps'][0]['run']
