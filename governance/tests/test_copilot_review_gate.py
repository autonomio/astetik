"""Exercise actual REST review evidence, polling failures, races, and required workflow wiring."""
from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import yaml

from governance import copilot_review_gate as gate

HEAD = 'b940ff0c87ddb3b288d9a84e473e57ff28b5f59b'
STALE = '525bd75b9c3339e9196afeb1ebbc4cd7760f678a'
PULL = 'repos/autonomio/astetik/pulls/62'
REVIEW_ID = 5382652700
WORKFLOW = Path(__file__).resolve().parents[2] / '.github/workflows/pr_checks_honesty.yml'


def review(**changes: object) -> dict[str, object]:
    """Retain the relevant fields of the actual submitted PR62 Copilot review."""
    return {'id': REVIEW_ID, 'user': {'login': gate.BOT, 'type': 'Bot'},
            'commit_id': HEAD, 'state': 'COMMENTED', 'submitted_at': '2026-10-01T16:55:02Z'} | changes


@dataclass
class Rest:
    pages: object = field(default_factory=lambda: [[review()]])
    detail: object = field(default_factory=review)
    heads: list[object] = field(default_factory=lambda: [
        {'head': {'sha': HEAD}, 'base': {'ref': 'master'}, 'state': 'open'},
    ])
    calls: list[list[str]] = field(default_factory=list)
    sleeps: list[float] = field(default_factory=list)
    now: float = 0
    latency: float = 0
    timeouts: list[float] = field(default_factory=list)
    fault: Exception | None = None
    raw_pages: str | None = None
    on_sleep: Callable[[], None] | None = None

    def run(self, command: list[str], *, capture_output: bool, text: bool,
            check: bool, timeout: float) -> subprocess.CompletedProcess[str]:
        assert capture_output and text and check and 0 < timeout <= 30
        assert command[:4] == ['gh', 'api', '--method', 'GET']
        self.calls.append(command)
        self.timeouts.append(timeout)
        self.now += self.latency
        if self.fault is not None:
            raise self.fault
        path = command[4]
        if path == PULL:
            result = self.heads.pop(0) if len(self.heads) > 1 else self.heads[0]
        elif path == f'{PULL}/reviews?per_page=100':
            assert command[5:] == ['--paginate', '--slurp']
            if self.raw_pages is not None:
                return subprocess.CompletedProcess(command, 0, self.raw_pages, '')
            result = self.pages
        else:
            assert path.startswith(f'{PULL}/reviews/')
            result = self.detail
        return subprocess.CompletedProcess(command, 0, json.dumps(result), '')

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds
        if self.on_sleep is not None:
            self.on_sleep()


@pytest.fixture
def rest(monkeypatch: pytest.MonkeyPatch) -> Rest:
    fixture = Rest()
    monkeypatch.setattr(gate.subprocess, 'run', fixture.run)
    monkeypatch.setattr(gate.time, 'monotonic', lambda: fixture.now)
    monkeypatch.setattr(gate.time, 'sleep', fixture.sleep)
    return fixture


@pytest.mark.parametrize('state', ['COMMENTED', 'APPROVED', 'CHANGES_REQUESTED'])
def test_submitted_exact_head_bot_review_passes_after_individual_recheck(
    rest: Rest, state: str, capsys: pytest.CaptureFixture[str],
) -> None:
    rest.pages, rest.detail = [[review(state=state)]], review(state=state)
    gate.wait_for_review('autonomio/astetik', '62', HEAD)
    assert [call[4] for call in rest.calls] == [
        PULL, f'{PULL}/reviews?per_page=100', f'{PULL}/reviews/{REVIEW_ID}', PULL,
    ]
    assert not rest.sleeps
    assert 'PASS' in capsys.readouterr().out


def test_all_pages_are_read_and_later_matching_review_can_pass(rest: Rest) -> None:
    rest.pages = [[review(commit_id=STALE)], [review()]]
    gate.wait_for_review('autonomio/astetik', '62', HEAD)
    assert '--paginate' in rest.calls[1] and '--slurp' in rest.calls[1]
    assert rest.calls[2][4] == f'{PULL}/reviews/{REVIEW_ID}'


@pytest.mark.parametrize('changes', [
    {'commit_id': STALE}, {'user': {'login': 'mikkokotila', 'type': 'User'}},
    {'user': {'login': gate.BOT, 'type': 'User'}},
    {'user': {'login': 'dependabot[bot]', 'type': 'Bot'}},
    {'state': 'PENDING', 'submitted_at': None}, {'state': 'DISMISSED'},
])
def test_stale_human_pending_or_dismissed_evidence_never_satisfies_completion(
    rest: Rest, changes: dict[str, object], capsys: pytest.CaptureFixture[str],
) -> None:
    rest.pages = [[review(**changes)]]
    with pytest.raises(SystemExit) as caught:
        gate.wait_for_review('autonomio/astetik', '62', HEAD, timeout=1)
    assert caught.value.code == 1
    assert rest.sleeps == [1]
    assert all('/reviews/' not in call[4] for call in rest.calls)
    captured = capsys.readouterr()
    assert 'Timed out' in captured.err and 'PASS' not in captured.out


def test_missing_review_waits_then_accepts_later_submission(rest: Rest) -> None:
    rest.pages = [[]]

    def submit() -> None:
        rest.pages = [[review()]]

    rest.on_sleep = submit
    gate.wait_for_review('autonomio/astetik', '62', HEAD, timeout=60)
    assert rest.sleeps == [30]
    assert len(rest.calls) == 7


@pytest.mark.parametrize('pages', [
    {}, [], None, [None], [{'id': REVIEW_ID}], [[None]],
    [[review(id=True)]], [[review(id=1.5)]], [[review(commit_id=None)]],
    [[review(state='UNKNOWN')]], [[review(user=None)]],
    [[review(user={'login': None, 'type': 'Bot'})]],
    [[review(submitted_at=7)]], [[review(submitted_at='invalid')]],
    [[review(submitted_at='2026-10-01T16:55:02')]], [[review(submitted_at=None)]],
    [[review(), {'state': 'COMMENTED'}]],
])
def test_malformed_complete_payload_fails_immediately_even_after_valid_candidate(
    rest: Rest, pages: object,
) -> None:
    rest.pages = pages
    with pytest.raises(SystemExit) as caught:
        gate.wait_for_review('autonomio/astetik', '62', HEAD)
    assert caught.value.code == 2
    assert not rest.sleeps
    assert len(rest.calls) == 2


@pytest.mark.parametrize('payload', ['invalid', '[NaN]', '[[{"id":1,"id":2}]]'])
def test_invalid_nonfinite_and_duplicate_json_api_payloads_fail_closed(
    rest: Rest, payload: str,
) -> None:
    rest.raw_pages = payload
    with pytest.raises(SystemExit) as caught:
        gate.wait_for_review('autonomio/astetik', '62', HEAD)
    assert caught.value.code == 2
    assert not rest.sleeps


@pytest.mark.parametrize('fault', [
    subprocess.CalledProcessError(1, ['gh', 'api'], stderr='HTTP 403'),
    subprocess.CalledProcessError(1, ['gh', 'api'], stderr='HTTP 404'),
    subprocess.CalledProcessError(1, ['gh', 'api'], stderr='HTTP 429'),
    subprocess.TimeoutExpired(['gh', 'api'], 30), OSError('gh unavailable'),
])
def test_api_failures_are_not_retried(rest: Rest, fault: Exception) -> None:
    rest.fault = fault
    with pytest.raises(SystemExit) as caught:
        gate.wait_for_review('autonomio/astetik', '62', HEAD)
    assert caught.value.code == 2
    assert len(rest.calls) == 1 and not rest.sleeps


@pytest.mark.parametrize('pull', [
    {}, {'head': None}, {'head': {'sha': STALE}, 'base': {'ref': 'master'}, 'state': 'open'},
    {'head': {'sha': HEAD}, 'base': {'ref': 'developer'}, 'state': 'open'},
    {'head': {'sha': HEAD}, 'base': {'ref': 'master'}, 'state': 'closed'},
])
def test_actual_head_target_and_state_are_checked_before_fetching_reviews(
    rest: Rest, pull: object,
) -> None:
    rest.heads = [pull]
    with pytest.raises(SystemExit) as caught:
        gate.wait_for_review('autonomio/astetik', '62', HEAD)
    assert caught.value.code == 2
    assert len(rest.calls) == 1 and not rest.sleeps


def test_push_during_review_verification_fails_before_success(rest: Rest) -> None:
    rest.heads.append({'head': {'sha': STALE}, 'base': {'ref': 'master'}, 'state': 'open'})
    with pytest.raises(SystemExit) as caught:
        gate.wait_for_review('autonomio/astetik', '62', HEAD)
    assert caught.value.code == 2
    assert rest.calls[-2][4] == f'{PULL}/reviews/{REVIEW_ID}'
    assert not rest.sleeps


def test_dismissal_between_list_and_selected_review_recheck_cannot_pass(rest: Rest) -> None:
    rest.detail = review(state='DISMISSED')
    with pytest.raises(SystemExit) as caught:
        gate.wait_for_review('autonomio/astetik', '62', HEAD, timeout=1)
    assert caught.value.code == 1
    assert rest.calls[2][4] == f'{PULL}/reviews/{REVIEW_ID}'
    assert rest.sleeps == [1]


def test_authoritative_dismissal_event_excludes_stale_api_review(rest: Rest) -> None:
    with pytest.raises(SystemExit) as caught:
        gate.wait_for_review('autonomio/astetik', '62', HEAD, str(REVIEW_ID), timeout=1)
    assert caught.value.code == 1
    assert all('/reviews/' not in call[4] for call in rest.calls)
    assert rest.sleeps == [1]


def test_dismissed_event_allows_a_different_submitted_review(rest: Rest) -> None:
    replacement = review(id=REVIEW_ID + 1)
    rest.pages, rest.detail = [[review(), replacement]], replacement
    gate.wait_for_review('autonomio/astetik', '62', HEAD, str(REVIEW_ID))
    assert rest.calls[2][4] == f'{PULL}/reviews/{REVIEW_ID + 1}'


def test_selected_review_id_must_match_individual_endpoint(rest: Rest) -> None:
    rest.detail = review(id=REVIEW_ID + 1)
    with pytest.raises(SystemExit) as caught:
        gate.wait_for_review('autonomio/astetik', '62', HEAD)
    assert caught.value.code == 2 and not rest.sleeps


@pytest.mark.parametrize('changes', [
    {'commit_id': STALE}, {'user': {'login': 'dependabot[bot]', 'type': 'Bot'}},
    {'user': {'login': gate.BOT, 'type': 'User'}},
])
def test_selected_review_immutable_identity_change_fails_without_retry(
    rest: Rest, changes: dict[str, object],
) -> None:
    rest.detail = review(**changes)
    with pytest.raises(SystemExit) as caught:
        gate.wait_for_review('autonomio/astetik', '62', HEAD)
    assert caught.value.code == 2 and not rest.sleeps
    assert len(rest.calls) == 3


@pytest.mark.parametrize('latency, timeout, timeouts', [(1, 3, [3, 2, 1]), (0.5, 2, [2, 1.5, 1, 0.5])])
def test_api_request_time_consumes_the_same_completion_deadline(
    rest: Rest, latency: float, timeout: int, timeouts: list[float],
) -> None:
    rest.latency = latency
    with pytest.raises(SystemExit) as caught:
        gate.wait_for_review('autonomio/astetik', '62', HEAD, timeout=timeout, interval=1)
    assert caught.value.code == 1
    assert rest.timeouts == timeouts
    assert rest.now == timeout and not rest.sleeps


@pytest.mark.parametrize('arguments', [
    {'repo': 'invalid'}, {'number': '0'}, {'head': 'invalid'}, {'dismissed': '-1'},
    {'timeout': 1201}, {'timeout': True}, {'interval': 61}, {'interval': 0},
])
def test_input_declarations_cannot_extend_or_bypass_the_bound(
    rest: Rest, arguments: dict[str, object],
) -> None:
    values = {'repo': 'autonomio/astetik', 'number': '62', 'head': HEAD} | arguments
    with pytest.raises(SystemExit) as caught:
        gate.wait_for_review(**values)
    assert caught.value.code == 2 and not rest.calls


def test_main_invokes_exact_quoted_event_declaration(rest: Rest, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate.sys, 'argv', ['gate', 'autonomio/astetik', '62', HEAD, ''])
    gate.main()
    assert len(rest.calls) == 4


def assert_workflow_contract(document: str) -> None:
    payload = yaml.load(document, Loader=yaml.BaseLoader)
    triggers = payload['on']
    assert triggers['pull_request']['branches'] == ['master']
    assert {'synchronize', 'edited'} <= set(triggers['pull_request']['types'])
    assert triggers['pull_request_review']['types'] == ['submitted', 'dismissed']
    assert payload['permissions'] == {'contents': 'read', 'pull-requests': 'read'}
    assert payload['concurrency'] == {
        'group': 'pr_checks_honesty-${{ github.event.pull_request.number }}',
        'cancel-in-progress': 'true',
    }
    job = payload['jobs']['pr_checks_honesty']
    assert job['name'] == 'pr_checks_honesty' and 'if' not in job
    assert job['timeout-minutes'] == '25'
    steps = job['steps']
    assert steps[0]['with']['persist-credentials'] == 'false'
    guards = [step for step in steps if step.get('run', '').startswith('python governance/copilot_review_gate.py')]
    assert len(guards) == 1
    guard = guards[0]
    assert 'if' not in guard and 'continue-on-error' not in guard
    assert guard['env'] == {
        'GH_TOKEN': '${{ github.token }}', 'REPOSITORY': '${{ github.repository }}',
        'PR_NUMBER': '${{ github.event.pull_request.number }}',
        'EXPECTED_HEAD': '${{ github.event.pull_request.head.sha }}',
        'DISMISSED_REVIEW': "${{ github.event.action == 'dismissed' && github.event.review.id || '' }}",
    }
    assert '"$REPOSITORY" "$PR_NUMBER" "$EXPECTED_HEAD" "$DISMISSED_REVIEW"' in guard['run']
    assert any('test_repository_law.py' in step.get('run', '') for step in steps)


def test_required_workflow_checks_completion_and_refreshes_all_review_events() -> None:
    assert_workflow_contract(WORKFLOW.read_text())



def test_removed_gate_or_reviewer_based_skip_cannot_pass_workflow_contract() -> None:
    text = WORKFLOW.read_text()
    for mutation in [
        text.replace('      - name: Require submitted current-head Copilot review',
                     "      - if: github.event.review.user.type == 'Bot'\n        name: Require submitted current-head Copilot review"),
        text.replace('          python governance/copilot_review_gate.py', '          true'),
    ]:
        with pytest.raises(AssertionError):
            assert_workflow_contract(mutation)
