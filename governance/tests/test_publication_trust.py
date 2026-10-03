"""Publication proves protected source identity before builds and signing."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / '.github/workflows/pr_publish_pypi.yml'


def _workflow() -> dict:
    return yaml.load(WORKFLOW.read_text(encoding='utf-8'), Loader=yaml.BaseLoader)


def _guard() -> str:
    steps = _workflow()['jobs']['build_distribution']['steps']
    return next(step['run'] for step in steps if step['name'] == 'Verify the published version tag')


def _git(path: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()


@dataclass
class PublicationFixture:
    path: Path
    head: str
    environment: dict[str, str]

    def run(self, *, isolated: bool = True) -> subprocess.CompletedProcess[str]:
        command = _guard().replace('python -I -', f'{shlex.quote(sys.executable)} -I -')
        if not isolated:
            command = command.replace(f'{shlex.quote(sys.executable)} -I -', f'{shlex.quote(sys.executable)} -')
        return subprocess.run(
            ['bash', '-c', command], cwd=self.path, env=self.environment,
            capture_output=True, text=True, check=False,
        )


@pytest.fixture
def publication(tmp_path: Path) -> PublicationFixture:
    _git(tmp_path, 'init', '-b', 'master')
    _git(tmp_path, 'config', 'user.name', 'Publication regression')
    _git(tmp_path, 'config', 'user.email', 'publication@example.invalid')
    (tmp_path / 'pyproject.toml').write_text('[project]\nversion = "2.0.0"\n')
    _git(tmp_path, 'add', 'pyproject.toml')
    _git(tmp_path, 'commit', '-m', 'Initialize publication fixture')
    head = _git(tmp_path, 'rev-parse', 'HEAD')
    _git(tmp_path, 'tag', 'v2.0.0')
    _git(tmp_path, 'update-ref', 'refs/remotes/origin/master', head)
    executable_dir = tmp_path / 'bin'
    executable_dir.mkdir()
    gh = executable_dir / 'gh'
    gh.write_text(
        f'#!{sys.executable} -I\n'
        'import os, sys\n'
        'from pathlib import Path\n'
        'if sys.argv[1:] != ["api", "repos/autonomio/astetik/releases/tags/v2.0.0"]:\n'
        '    raise SystemExit("unexpected release lookup")\n'
        'Path(os.environ["LOOKUP_WITNESS"]).write_text("read release")\n'
        'print(os.environ["RELEASE_RESPONSE"])\n'
    )
    gh.chmod(0o755)
    environment = os.environ | {
        'PATH': f'{executable_dir}{os.pathsep}{os.environ["PATH"]}',
        'GITHUB_EVENT_NAME': 'workflow_dispatch',
        'GITHUB_REF': 'refs/heads/master',
        'GITHUB_SHA': head,
        'GITHUB_REPOSITORY': 'autonomio/astetik',
        'GITHUB_WORKFLOW_REF': 'autonomio/astetik/.github/workflows/pr_publish_pypi.yml@refs/heads/master',
        'GITHUB_WORKFLOW_SHA': head,
        'GITHUB_OUTPUT': str(tmp_path / 'guard-output'),
        'RELEASE_TAG': 'v2.0.0',
        'GH_TOKEN': 'no-real-credential',
        'LOOKUP_WITNESS': str(tmp_path / 'release-lookup'),
        'RELEASE_RESPONSE': json.dumps({'id': 17, 'tag_name': 'v2.0.0', 'draft': False, 'prerelease': False}),
    }
    return PublicationFixture(tmp_path, head, environment)


def _workflow_event(publication: PublicationFixture, **changes: object) -> None:
    event = {
        'name': 'Automated Release', 'conclusion': 'success', 'head_branch': 'master',
        'head_sha': publication.head, 'head_repository': {'full_name': 'autonomio/astetik'},
    } | changes
    path = publication.path / 'event.json'
    path.write_text(json.dumps({'workflow_run': event}))
    publication.environment.update(GITHUB_EVENT_NAME='workflow_run', GITHUB_EVENT_PATH=str(path))


def test_publication_triggers_only_protected_master_with_an_explicit_opt_in() -> None:
    workflow = _workflow()
    assert set(workflow['on']) == {'workflow_run', 'workflow_dispatch'}
    assert workflow['on']['workflow_run'] == {
        'workflows': ['Automated Release'], 'types': ['completed'],
    }
    build = workflow['jobs']['build_distribution']
    for condition in (
        "vars.RELEASE_ENABLED == 'true'", "vars.PYPI_PUBLISH_ENABLED == 'true'",
        "github.ref == 'refs/heads/master'",
        "github.event_name == 'workflow_dispatch'", "github.event_name == 'workflow_run'",
        "github.event.workflow_run.conclusion == 'success'",
        "github.event.workflow_run.head_branch == 'master'",
        'github.event.workflow_run.head_repository.full_name == github.repository',
    ):
        assert condition in build['if']
    assert build['permissions'] == {'contents': 'read'}
    steps = build['steps']
    assert workflow['on']['workflow_dispatch']['inputs']['release_tag']['required'] == 'true'
    assert steps[0]['with'] == {
        'ref': '${{ github.event.workflow_run.head_sha || inputs.release_tag }}',
        'fetch-depth': '0', 'persist-credentials': 'false',
    }
    assert build['outputs'] == {
        key: '${{ steps.verify_release.outputs.' + key + ' }}'
        for key in ('source_identity', 'release_id', 'publication_required')
    }

    assert steps[0]['uses'].startswith('actions/checkout@')
    names = [step['name'] for step in steps]
    guard_index = names.index('Verify the published version tag')
    assert guard_index < names.index('Install packaging tools') < names.index('Build the distributions')
    assert all(step['if'] == "steps.verify_release.outputs.publication_required == 'true'" for step in steps[guard_index + 1:])
    assert workflow['concurrency'] == {
        'group': 'publish-${{ github.event.workflow_run.head_sha || inputs.release_tag }}',
        'cancel-in-progress': 'false',
    }
    assert 'python -I -' in _guard()
    assert all('continue-on-error' not in step for step in steps)


def test_signing_and_publication_use_same_run_artifacts_without_repository_execution() -> None:
    jobs = _workflow()['jobs']
    assert set(jobs) == {'build_distribution', 'attest_distribution', 'publish_release_assets', 'publish_to_pypi'}
    signer, publisher = jobs['attest_distribution'], jobs['publish_to_pypi']
    assert signer['needs'] == 'build_distribution'
    assert signer['permissions'] == {'contents': 'read', 'id-token': 'write', 'attestations': 'write'}
    assert signer['if'] == "needs.build_distribution.outputs.publication_required == 'true'"
    assert publisher['needs'] == 'publish_release_assets'
    assert publisher['if'] == "vars.PYPI_PUBLISH_ENABLED == 'true'"
    assert publisher['environment'] == 'pypi'
    assert publisher['permissions'] == {}
    for job in (signer, publisher):
        assert len(job['steps']) == (3 if job is signer else 2)
        download = job['steps'][0]
        assert download['uses'].startswith('actions/download-artifact@')
        assert download['with'] == {'name': 'pypi-distributions', 'path': 'dist'}
        assert all('run' not in step and 'checkout' not in step['uses'] for step in job['steps'])
    assert signer['steps'][1]['uses'].startswith('actions/attest@')
    assert signer['steps'][1]['with'] == {
        'subject-path': 'dist/*',
        'predicate-type': 'urn:autonomio:astetik:release-source:v1',
        'predicate': '${{ needs.build_distribution.outputs.source_identity }}',
    }
    assert signer['steps'][1]['id'] == 'attest'
    assert signer['steps'][2]['with'] == {
        'name': 'release-source-bundle', 'path': '${{ steps.attest.outputs.bundle-path }}',
        'if-no-files-found': 'error',
    }
    assert publisher['steps'][1]['with'] == {
        'user': '__token__', 'password': '${{ secrets.PYPI_API_TOKEN }}',
        'attestations': 'false',
    }
    assert all('PYPI_API_TOKEN' not in str(job) for name, job in jobs.items() if name != 'publish_to_pypi')


def test_isolated_guard_ignores_checkout_imports_and_reproduces_old_defect(
    publication: PublicationFixture,
) -> None:
    (publication.path / 'json.py').write_text('raise SystemExit("checkout import executed")\n')
    unsafe = publication.run(isolated=False)
    assert unsafe.returncode != 0 and 'checkout import executed' in unsafe.stderr
    assert not (publication.path / 'release-lookup').exists()
    safe = publication.run()
    assert safe.returncode == 0, safe.stderr
    assert f'Verified published v2.0.0 at {publication.head} on master history' in safe.stdout
    assert (publication.path / 'release-lookup').read_text() == 'read release'


def test_successful_release_workflow_must_identify_the_exact_build_commit(
    publication: PublicationFixture,
) -> None:
    _workflow_event(publication)
    result = publication.run()
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('field, value', [
    ('name', 'Other Workflow'), ('conclusion', 'failure'), ('head_branch', 'feature'),
    ('head_sha', '0' * 40), ('head_repository', {'full_name': 'other/astetik'}),
])
def test_untrusted_upstream_provenance_fails_before_release_lookup(
    publication: PublicationFixture, field: str, value: object,
) -> None:
    _workflow_event(publication, **{field: value})
    result = publication.run()
    assert result.returncode != 0
    assert 'Release workflow provenance must identify this master commit' in result.stderr
    assert not (publication.path / 'release-lookup').exists()


@pytest.mark.parametrize('field, value, message', [
    ('GITHUB_REF', 'refs/tags/v2.0.0', 'protected master ref'),
    ('GITHUB_REF', 'refs/heads/feature', 'protected master ref'),
    ('GITHUB_EVENT_NAME', 'release', 'master dispatch or release workflow run'),
    ('GITHUB_SHA', '0' * 40, 'protected master ref and workflow'),
    ('GITHUB_WORKFLOW_SHA', '0' * 40, 'protected master ref and workflow'),
    ('GITHUB_REPOSITORY', 'other/astetik', 'protected master ref and workflow'),
    ('GITHUB_WORKFLOW_REF', 'autonomio/astetik/.github/workflows/other.yml@refs/heads/master', 'protected master ref and workflow'),
])
def test_untrusted_workflow_context_fails_before_release_lookup(
    publication: PublicationFixture, field: str, value: str, message: str,
) -> None:
    publication.environment[field] = value
    result = publication.run()
    assert result.returncode != 0 and message in result.stderr
    assert not (publication.path / 'release-lookup').exists()


def test_a_tag_for_another_commit_fails_before_release_lookup(publication: PublicationFixture) -> None:
    (publication.path / 'later').write_text('another commit')
    _git(publication.path, 'add', 'later')
    _git(publication.path, 'commit', '-m', 'Advance fixture')
    _git(publication.path, 'update-ref', 'refs/remotes/origin/master', 'HEAD')
    publication.environment['GITHUB_SHA'] = _git(publication.path, 'rev-parse', 'HEAD')
    publication.environment['GITHUB_WORKFLOW_SHA'] = publication.environment['GITHUB_SHA']
    result = publication.run()
    assert result.returncode != 0 and 'Version tag must identify the checked-out commit' in result.stderr
    assert not (publication.path / 'release-lookup').exists()


def test_a_commit_outside_master_history_fails_before_release_lookup(
    publication: PublicationFixture,
) -> None:
    _git(publication.path, 'checkout', '--orphan', 'unrelated')
    _git(publication.path, 'commit', '-m', 'Unrelated fixture history')
    publication.environment['GITHUB_SHA'] = _git(publication.path, 'rev-parse', 'HEAD')
    publication.environment['GITHUB_WORKFLOW_SHA'] = publication.environment['GITHUB_SHA']
    _git(publication.path, 'tag', '-f', 'v2.0.0')
    result = publication.run()
    assert result.returncode != 0 and 'protected master history' in result.stderr
    assert not (publication.path / 'release-lookup').exists()


@pytest.mark.parametrize('release', [
    {'tag_name': 'v2.0.0', 'draft': True, 'prerelease': False},
    {'tag_name': 'v2.0.0', 'draft': False, 'prerelease': True},
    {'tag_name': 'v2.0.1', 'draft': False, 'prerelease': False},
])
def test_unpublished_or_mismatched_release_is_rejected(
    publication: PublicationFixture, release: dict,
) -> None:
    publication.environment['RELEASE_RESPONSE'] = json.dumps(release)
    result = publication.run()
    assert result.returncode != 0 and 'published stable GitHub release' in result.stderr
    assert (publication.path / 'release-lookup').exists()


@pytest.mark.parametrize('event_name', ['workflow_dispatch', 'workflow_run'])
def test_a_release_remains_publishable_after_master_advances(
    publication: PublicationFixture, event_name: str,
) -> None:
    if event_name == 'workflow_run':
        _workflow_event(publication)
    (publication.path / 'later').write_text('later protected commit')
    _git(publication.path, 'add', 'later')
    _git(publication.path, 'commit', '-m', 'Advance protected master')
    latest = _git(publication.path, 'rev-parse', 'HEAD')
    _git(publication.path, 'update-ref', 'refs/remotes/origin/master', latest)
    _git(publication.path, 'checkout', '--detach', publication.head)
    publication.environment['GITHUB_SHA'] = latest
    publication.environment['GITHUB_WORKFLOW_SHA'] = latest
    result = publication.run()
    assert result.returncode == 0, result.stderr
    output = dict(line.split('=', 1) for line in (publication.path / 'guard-output').read_text().splitlines())
    assert output['release_id'] == '17' and output['publication_required'] == 'true'
    assert json.loads(output['source_identity']) == {
        'repository': 'https://github.com/autonomio/astetik',
        'commit': publication.head, 'tag': 'v2.0.0', 'workflow_commit': latest,
    }


def test_dispatch_cannot_substitute_another_tag(publication: PublicationFixture) -> None:
    publication.environment['RELEASE_TAG'] = 'master'
    result = publication.run()
    assert result.returncode != 0 and 'Dispatch tag must match' in result.stderr
    assert not (publication.path / 'release-lookup').exists()
    assert not (publication.path / 'guard-output').exists()


def test_source_cannot_postdate_the_trusted_workflow_commit(
    publication: PublicationFixture,
) -> None:
    (publication.path / 'later').write_text('new source after workflow revision')
    _git(publication.path, 'add', 'later')
    _git(publication.path, 'commit', '-m', 'Advance source')
    _git(publication.path, 'update-ref', 'refs/remotes/origin/master', 'HEAD')
    _git(publication.path, 'tag', '-f', 'v2.0.0')
    result = publication.run()
    assert result.returncode != 0 and 'protected master history' in result.stderr
    assert not (publication.path / 'release-lookup').exists()
    assert not (publication.path / 'guard-output').exists()


@pytest.mark.parametrize('change', ['same', 'first-parent', 'tagged-source', 'unstable'])
def test_unchanged_dependency_merges_skip_publication_only_with_exact_history(
    publication: PublicationFixture, change: str,
) -> None:
    if change == 'tagged-source':
        (publication.path / 'pyproject.toml').write_text('[project]\nversion = "1.9.9"\n')
        _git(publication.path, 'add', 'pyproject.toml')
        _git(publication.path, 'commit', '-m', 'Different tagged source version')
        _git(publication.path, 'tag', '-f', 'v2.0.0')
    (publication.path / 'pyproject.toml').write_text('[project]\nversion = "2.0.0"\n')
    (publication.path / 'dependency').write_text('dependency-only merge fixture')
    _git(publication.path, 'add', '.')
    _git(publication.path, 'commit', '-m', 'Keep current package version')
    if change == 'tagged-source':
        (publication.path / 'dependency').write_text('another dependency merge')
        _git(publication.path, 'add', 'dependency')
        _git(publication.path, 'commit', '-m', 'Keep first-parent package version')
    if change == 'first-parent':
        (publication.path / 'pyproject.toml').write_text('[project]\nversion = "2.0.1"\n')
        _git(publication.path, 'add', 'pyproject.toml')
        _git(publication.path, 'commit', '-m', 'Change package version')
        _git(publication.path, 'tag', 'v2.0.1', publication.head)
        publication.environment['RELEASE_RESPONSE'] = json.dumps({'id': 17, 'tag_name': 'v2.0.1', 'draft': False, 'prerelease': False})
    latest = _git(publication.path, 'rev-parse', 'HEAD')
    _git(publication.path, 'update-ref', 'refs/remotes/origin/master', latest)
    publication.environment.update(GITHUB_SHA=latest, GITHUB_WORKFLOW_SHA=latest)
    _workflow_event(publication, head_sha=latest)
    if change == 'unstable':
        publication.environment['RELEASE_RESPONSE'] = json.dumps({'tag_name': 'v2.0.0', 'draft': True, 'prerelease': False})
    result = publication.run()
    if change == 'same':
        assert result.returncode == 0, result.stderr
        assert (publication.path / 'guard-output').read_text() == 'publication_required=false\n'
        assert 'unchanged version already has a stable release' in result.stdout
    else:
        assert result.returncode != 0
        assert not (publication.path / 'guard-output').exists()


@pytest.mark.parametrize('event_name', ['workflow_run', 'workflow_dispatch'])
@pytest.mark.parametrize('same_version', [True, False])
def test_missing_tag_of_unchanged_automatic_merge_skips_without_claiming_publication(
    publication: PublicationFixture, event_name: str, same_version: bool,
) -> None:
    _git(publication.path, 'tag', '-d', 'v2.0.0')
    if not same_version:
        (publication.path / 'pyproject.toml').write_text('[project]\nversion = "2.0.1"\n')
        publication.environment['RELEASE_TAG'] = 'v2.0.1'
    (publication.path / 'dependency').write_text('dependency merged before original release run')
    _git(publication.path, 'add', 'pyproject.toml', 'dependency')
    _git(publication.path, 'commit', '-m', 'Merge while release is queued')
    latest = _git(publication.path, 'rev-parse', 'HEAD')
    _git(publication.path, 'update-ref', 'refs/remotes/origin/master', latest)
    publication.environment.update(GITHUB_SHA=latest, GITHUB_WORKFLOW_SHA=latest)
    if event_name == 'workflow_run':
        _workflow_event(publication, head_sha=latest)
    result = publication.run()
    assert not (publication.path / 'release-lookup').exists()
    if event_name == 'workflow_run' and same_version:
        assert result.returncode == 0, result.stderr
        assert (publication.path / 'guard-output').read_text() == 'publication_required=false\n'
        assert 'no release tag yet; no publication' in result.stdout
    else:
        assert result.returncode != 0
        assert not (publication.path / 'guard-output').exists()
