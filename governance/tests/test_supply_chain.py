"""Supply-chain law: workflow actions are pinned by commit SHA and
checkout credentials are never persisted.

One assertion per law over every workflow file, so a regression in any
one of them reds the required tests gate:

  1. Every ``uses:`` reference is pinned to a full 40-hex commit SHA
     with a trailing ``# vX.Y.Z`` comment naming the tag it was
     resolved from. A mutable tag (``@v5``) or branch reference can be
     repointed upstream after review; a commit SHA cannot.
  2. Every ``actions/checkout`` step sets ``persist-credentials:
     false``. The default persists a repo-scoped token into
     ``.git/config`` for every later step in the job; no template
     workflow pushes with that credential (bootstrap pushes through an
     explicit token remote), so nothing may keep it.
  3. Every workflow declares an explicit ``permissions:`` block at the
     workflow or job level, so no job runs on the org default grant.
  4. Every ``git fetch`` a workflow runs authenticates per command via
     an ``http.<host>.extraheader`` ``-c`` flag: with credential
     persistence off, a bare fetch works only in public repos and
     breaks in private derived repositories.

And the install law over every ``pip install`` a workflow runs:

  5. Every install is either a hash-locked compiled set
     (``--require-hashes -r requirements/ci/<set>.txt``) or the
     first-party editable install with resolution disabled
     (``--no-build-isolation --no-deps -e .``), so no job resolves a
     third-party package outside the hash-pinned sets. The declared
     runtime dependencies the ``--no-deps`` install skips come from
     the ``runtime-env`` set, which mirrors ``[project.dependencies]``.
  6. Every compiled set is hash-complete (each requirement entry
     carries at least one ``--hash=sha256``) and every ``.in`` source
     has its compiled ``.txt`` sibling and vice versa.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml
from _common import REPO_ROOT
from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

WORKFLOWS_DIR = REPO_ROOT / '.github' / 'workflows'
REQUIREMENTS_DIR = REPO_ROOT / 'requirements' / 'ci'

PINNED_USES_RE = re.compile(r'^\s*(?:- )?uses: \S+@[0-9a-f]{40}\s+# v\d+\.\d+\.\d+$')
ANY_USES_RE = re.compile(r'^\s*(?:- )?uses: ')
CHECKOUT_RE = re.compile(r'^\s*(?:- )?uses: actions/checkout@')
NEXT_STEP_RE = re.compile(r'^\s*- (?:name|uses|run|env|id|if):')
PERMISSIONS_RE = re.compile(r'^(?:permissions:|    permissions:)', re.MULTILINE)
PERSIST_LINE_RE = re.compile(r'^\s*persist-credentials: false\s*$')
# The release workflow pushes the version tag, so exactly one checkout in it
# must keep credentials. Keyed with a count rather than by filename: waiving
# the whole file would let a second checkout added later inherit the
# credential-persistence waiver silently.
CREDENTIALED_CHECKOUTS: dict[str, int] = {'pr_post_release.yml': 1}
# Deliberately exempts exactly one canonical spelling: like the byte-equal
# title rule, the law pins the form itself, so a differently-formatted
# compliant fetch fails loud and gets rewritten to canon rather than
# growing regex permutations here.
GIT_FETCH_RE = re.compile(r'^\s*git (?!-c "http\.https://github\.com/\.extraheader=\$AUTH" )[^|]*\bfetch\b')
# Anchored across the whole stripped line (an optional inline `run:`
# prefix and the interpreter/uv prefix included), so a non-compliant
# install cannot hide chained ahead of a compliant tail.
INSTALL_PREFIX = r'(?:run: )?(?:[\w./-]+ -m |uv )?'
HASHED_INSTALL_RE = re.compile(
    INSTALL_PREFIX
    + r'pip install (?:--python \S+ )?--require-hashes -r requirements/ci/[a-z-]+\.txt'
)
# Installing a distribution the workflow just built is not a dependency
# resolution: the artifact comes from `dist/`, not an index, and proving it
# installs and imports is exactly what the packaging job exists for. There is
# nothing to hash-lock.
BUILT_ARTIFACT_INSTALL_RE = re.compile(
    INSTALL_PREFIX + r'pip install (?:--no-deps )?dist/\*\.whl'
)
EDITABLE_INSTALL_RE = re.compile(
    INSTALL_PREFIX
    + r'pip install (?:--python \S+ )?--no-build-isolation --no-deps -e \.'
)
REQUIREMENT_ENTRY_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._\[\],-]*==')


def _workflow_files() -> list[Path]:
    files = sorted(WORKFLOWS_DIR.glob('*.yml'))
    assert files, f'no workflow files found under {WORKFLOWS_DIR}'
    return files


def test_every_action_reference_is_sha_pinned() -> None:
    violations: list[str] = []
    for path in _workflow_files():
        for lineno, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
            if ANY_USES_RE.match(line) and not PINNED_USES_RE.match(line):
                violations.append(f'{path.name}:{lineno}: {line.strip()}')
    assert not violations, (
        'workflow action references must be pinned to a full commit SHA '
        'with a `# vX.Y.Z` tag comment:\n' + '\n'.join(violations)
    )


def test_every_checkout_disables_credential_persistence() -> None:
    violations: list[str] = []
    waived: dict[str, int] = {}
    for path in _workflow_files():
        lines = path.read_text(encoding='utf-8').splitlines()
        for lineno, line in enumerate(lines, start=1):
            if not CHECKOUT_RE.match(line):
                continue
            step_end = lineno
            while step_end < len(lines) and not NEXT_STEP_RE.match(lines[step_end]):
                step_end += 1
            if not any(PERSIST_LINE_RE.match(entry) for entry in lines[lineno - 1:step_end]):
                allowance = CREDENTIALED_CHECKOUTS.get(path.name, 0)
                if allowance and waived.get(path.name, 0) < allowance:
                    waived[path.name] = waived.get(path.name, 0) + 1
                    continue
                violations.append(f'{path.name}:{lineno}: checkout without persist-credentials: false')
    assert not violations, '\n'.join(violations)


def test_every_git_fetch_authenticates_per_command() -> None:
    violations: list[str] = []
    for path in _workflow_files():
        for lineno, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
            if GIT_FETCH_RE.match(line):
                violations.append(f'{path.name}:{lineno}: {line.strip()}')
    assert not violations, (
        'git fetch must authenticate per command with the extraheader '
        '-c flag (persist-credentials is off; a bare fetch breaks '
        'private derived repos):\n' + '\n'.join(violations)
    )


def test_every_workflow_declares_permissions() -> None:
    # Column 0 is the workflow-level key and a four-space indent is the
    # job-level key; deeper matches (e.g. the word inside a run block)
    # do not count as a permissions declaration.
    violations: list[str] = []
    for path in _workflow_files():
        if not PERMISSIONS_RE.search(path.read_text(encoding='utf-8')):
            violations.append(f'{path.name}: no permissions block at workflow or job level')
    assert not violations, '\n'.join(violations)


def test_every_workflow_install_is_hash_locked() -> None:
    violations: list[str] = []
    for path in _workflow_files():
        for lineno, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
            if 'pip install' not in line or line.lstrip().startswith('#'):
                continue
            stripped = line.strip()
            if (
                HASHED_INSTALL_RE.fullmatch(stripped)
                or EDITABLE_INSTALL_RE.fullmatch(stripped)
                or BUILT_ARTIFACT_INSTALL_RE.fullmatch(stripped)
            ):
                continue
            violations.append(f'{path.name}:{lineno}: {stripped}')
    assert not violations, (
        'workflow installs must use a hash-locked set or the '
        'no-resolution editable form:\n' + '\n'.join(violations)
    )


def test_requirement_sets_are_hash_complete_and_paired() -> None:
    sources = sorted(REQUIREMENTS_DIR.glob('*.in'))
    compiled = sorted(REQUIREMENTS_DIR.glob('*.txt'))
    assert sources, f'no requirement sources under {REQUIREMENTS_DIR}'
    assert [p.stem for p in sources] == [p.stem for p in compiled]

    violations: list[str] = []
    for path in compiled:
        lines = path.read_text(encoding='utf-8').splitlines()
        for lineno, line in enumerate(lines, start=1):
            if not REQUIREMENT_ENTRY_RE.match(line):
                continue
            block = [line]
            for follower in lines[lineno:]:
                if not follower.startswith((' ', '\t')):
                    break
                block.append(follower)
            if '--hash=sha256' not in '\n'.join(block):
                violations.append(f'{path.name}:{lineno}: {line.split(" ")[0]} has no hash')
    assert not violations, '\n'.join(violations)


def test_every_job_running_a_repo_file_checks_out_the_repository() -> None:
    """A job that executes a tracked file must first check the repository out.

    Most guard jobs reach GitHub entirely through `gh` against
    `$GITHUB_REPOSITORY` and need no working tree, so a missing checkout is
    invisible until a step runs something from disk -- and then it fails with
    `can't open file`, which for `slice_closeout_guard` means reopening a
    correctly merged slice. No unit test can see this: the failure is in the
    job's composition, not in any module the job calls.
    """
    tracked_dirs = ('governance/', 'scripts/', 'tests/')
    offenders: list[str] = []
    for path in sorted(WORKFLOWS_DIR.glob('*.yml')):
        workflow = yaml.safe_load(path.read_text(encoding='utf-8'))
        for job_name, job in (workflow.get('jobs') or {}).items():
            steps = job.get('steps') or []
            has_checkout = any(
                isinstance(s.get('uses'), str) and s['uses'].startswith('actions/checkout@')
                for s in steps
            )
            if has_checkout:
                continue
            for step in steps:
                run = step.get('run')
                if not isinstance(run, str):
                    continue
                for line in run.split('\n'):
                    stripped = line.strip()
                    if stripped.startswith('#'):
                        continue
                    if any(f' {d}' in f' {stripped}' for d in tracked_dirs):
                        offenders.append(
                            f'{path.name}:{job_name} runs `{stripped}` with no checkout'
                        )
                        break
                else:
                    continue
                break
    assert not offenders, '\n'.join(offenders)


def test_overlapping_install_sets_share_active_versions() -> None:
    """The five frozen install sets must compose on every supported CI platform."""
    locks = sorted(REQUIREMENTS_DIR.glob('*.txt'))
    assert len(locks) == 5
    platforms = (
        ('linux', 'Linux', 'posix', 'x86_64'),
        ('darwin', 'Darwin', 'posix', 'arm64'),
        ('win32', 'Windows', 'nt', 'AMD64'),
    )
    for python_version in ('3.11', '3.12', '3.13'):
        for sys_platform, platform_system, os_name, machine in platforms:
            environment = default_environment()
            environment.update(
                python_version=python_version,
                python_full_version=f'{python_version}.0',
                sys_platform=sys_platform,
                platform_system=platform_system,
                os_name=os_name,
                platform_machine=machine,
                implementation_name='cpython',
                platform_python_implementation='CPython',
            )
            versions: dict[str, tuple[str, str]] = {}
            overlaps: set[str] = set()
            for path in locks:
                for line in path.read_text(encoding='utf-8').splitlines():
                    if not REQUIREMENT_ENTRY_RE.match(line):
                        continue
                    requirement = Requirement(line.rstrip(' \\'))
                    if requirement.marker and not requirement.marker.evaluate(environment):
                        continue
                    name = canonicalize_name(requirement.name)
                    version = str(requirement.specifier)
                    if name in versions:
                        previous_version, previous_file = versions[name]
                        assert previous_version == version, (
                            f'{python_version}/{sys_platform}: {name} conflicts: '
                            f'{previous_file} {previous_version}, {path.name} {version}'
                        )
                        overlaps.add(name)
                    else:
                        versions[name] = (version, path.name)
            assert len(overlaps) >= 3, 'install-set composition proof must not be vacuous'
