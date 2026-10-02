"""Manual existing-repository activation preserves every required gate."""
from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_WORKFLOW = REPO_ROOT / '.github/workflows/bootstrap_repository.yml'
BOOTSTRAP_SCRIPT = REPO_ROOT / 'governance/bootstrap_repository.py'


def _workflow() -> str:
    return BOOTSTRAP_WORKFLOW.read_text(encoding='utf-8')


def test_bootstrap_is_manual_github_only_on_protected_master() -> None:
    text = _workflow()
    payload = yaml.safe_load(text)
    triggers = payload.get('on', payload.get(True))
    assert isinstance(triggers, dict)
    assert set(triggers) == {'workflow_dispatch'}
    assert triggers['workflow_dispatch']['inputs']['confirm_repository']['required'] is True
    job = payload['jobs']['bootstrap']
    assert job['if'] == "github.ref == 'refs/heads/master'"
    assert job['environment'] == 'governance'
    assert '--github-only' in text
    assert '--files-only' not in text
    assert 'REPO_BOOTSTRAP_TOKEN is required' in text
    assert '"$CONFIRM_REPOSITORY" != "$GITHUB_REPOSITORY"' in text
    assert text.index('"$CONFIRM_REPOSITORY" != "$GITHUB_REPOSITORY"') < text.index(
        'python governance/bootstrap_repository.py'
    )
    for forbidden in ('gh issue create', 'gh pr create', 'gh pr merge', 'git push', 'git commit'):
        assert forbidden not in text


def test_bootstrap_job_has_timeout_and_serializes_runs() -> None:
    payload = yaml.safe_load(_workflow())
    assert payload['jobs']['bootstrap']['timeout-minutes'] == 30
    assert payload['concurrency'] == {
        'group': '${{ github.workflow }}', 'cancel-in-progress': False,
    }


def test_ruleset_lookup_ignores_organization_rulesets() -> None:
    script = BOOTSTRAP_SCRIPT.read_text(encoding='utf-8')
    assert "item.get('source_type') == 'Repository'" in script


def test_bootstrap_rewrite_leaves_workflow_files_static() -> None:
    script = BOOTSTRAP_SCRIPT.read_text(encoding='utf-8')
    assert "rel_path.startswith('.github/workflows/')" in script
    assert 'changed += _write_workflows(package_name)' not in script
    assert 'add_mutually_exclusive_group(required=True)' in script
    assert 'required CodeQL must remain enabled' in script
