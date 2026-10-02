"""Local activation requires explicit repository confirmation before mutation."""
from __future__ import annotations

import ast
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / '.github/workflows/bootstrap_repository.yml'
BOOTSTRAP_SCRIPT = REPO_ROOT / 'governance/bootstrap_repository.py'


def test_confirmation_is_a_required_manual_input() -> None:
    payload = yaml.safe_load(WORKFLOW.read_text(encoding='utf-8'))
    trigger = payload.get('on', payload.get(True))['workflow_dispatch']
    assert trigger['inputs']['confirm_repository']['required'] is True
    assert trigger['inputs']['confirm_repository']['type'] == 'string'


def test_confirmation_uses_environment_values_before_activation() -> None:
    payload = yaml.safe_load(WORKFLOW.read_text(encoding='utf-8'))
    steps = payload['jobs']['bootstrap']['steps']
    activation = [step for step in steps if 'bootstrap_repository.py' in step.get('run', '')]
    assert len(activation) == 1
    step = activation[0]
    assert step['env']['CONFIRM_REPOSITORY'] == '${{ inputs.confirm_repository }}'
    script = step['run']
    assert '"$CONFIRM_REPOSITORY" != "$GITHUB_REPOSITORY"' in script
    assert 'exit 1' in script.split('python governance/bootstrap_repository.py')[0]
    assert '${{ inputs.' not in script


def test_rename_engine_leaves_workflow_files_alone() -> None:
    tree = ast.parse(BOOTSTRAP_SCRIPT.read_text(encoding='utf-8'))
    branches = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.If)
        and any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == 'startswith'
            and any(
                isinstance(arg, ast.Constant) and arg.value == '.github/workflows/'
                for arg in call.args
            )
            for call in ast.walk(node.test)
        )
        and any(isinstance(stmt, ast.Continue) for stmt in node.body)
    ]
    assert branches
