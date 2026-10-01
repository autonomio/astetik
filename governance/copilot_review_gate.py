"""Require submitted current-head Copilot evidence within a bounded REST polling window."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime
from typing import NoReturn, cast

BOT = 'copilot-pull-request-reviewer[bot]'
SHA = re.compile(r'[0-9a-f]{40}')


def _fail(message: str, code: int = 2) -> NoReturn:
    print(f'COPILOT REVIEW GATE -- FAIL: {message}', file=sys.stderr)
    raise SystemExit(code)


def _object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError('GitHub response contains duplicate JSON fields')
    return result


def _api(path: str, deadline: float, paginate: bool = False) -> object:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        _fail('Timed out waiting for submitted current-head Copilot review', 1)
    command = ['gh', 'api', '--method', 'GET', path]
    if paginate:
        command.extend(['--paginate', '--slurp'])
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True,
                                timeout=min(30.0, remaining))
        value: object = json.loads(result.stdout, object_pairs_hook=_object, parse_constant=_fail)
    except subprocess.CalledProcessError as exc:
        _fail(f'GitHub REST request failed: {exc.stderr or exc}')
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        _fail(f'GitHub REST evidence unavailable or malformed: {exc}')
    return value


def _field(value: object, key: str) -> object:
    if not isinstance(value, dict):
        _fail('GitHub evidence must contain JSON objects')
    return cast('dict[str, object]', value).get(key)


def _head(path: str, expected: str, deadline: float) -> None:
    pull = _api(path, deadline)
    actual = _field(_field(pull, 'head'), 'sha')
    if actual != expected:
        _fail(f'PR head changed or is malformed: expected {expected}, observed {actual!r}')
    if _field(_field(pull, 'base'), 'ref') != 'master' or _field(pull, 'state') != 'open':
        _fail('Copilot completion requires an open pull request targeting master')



def _completed_report(review: object) -> None:
    """Require the provider v2 report structure; verdict text does not imply approval."""
    body = _field(review, 'body')
    prefix = (r'\A<!-- ccr-overview-v2 -->\n\n## Copilot review overview\n\n'
              r'### [^\s][^\n]*\n\n\S')
    fields = (r'(?m)^\*\*Review effort:\*\* [^\s][^\n]*\n'
              r'\*\*Findings:\*\* [0-9]+(?: <picture>[^\n]*</picture>)?[ \t]*(?:\n|\Z)')
    if (not isinstance(body, str) or re.match(prefix, body) is None
            or re.search(fields, body) is None):
        _fail('Missing or unrecognized completed Copilot report; review failure cannot pass')


def _submitted(review: object, head: str) -> int | None:
    identifier, state = _field(review, 'id'), _field(review, 'state')
    commit, submitted = _field(review, 'commit_id'), _field(review, 'submitted_at')
    login, actor = _field(_field(review, 'user'), 'login'), _field(_field(review, 'user'), 'type')
    if isinstance(identifier, bool) or not isinstance(identifier, int) or identifier <= 0:
        _fail('Malformed review identifier')
    if not isinstance(commit, str) or SHA.fullmatch(commit) is None:
        _fail('Malformed review commit identity')
    if state not in ('APPROVED', 'CHANGES_REQUESTED', 'COMMENTED', 'DISMISSED', 'PENDING'):
        _fail('Malformed review state')
    if not isinstance(login, str) or not login or not isinstance(actor, str) or not actor:
        _fail('Malformed review actor identity')
    if submitted is not None:
        if not isinstance(submitted, str):
            _fail('Malformed review submission time')
        try:
            timestamp = datetime.fromisoformat(submitted)
        except ValueError as exc:
            _fail(f'Malformed review submission time: {exc}')
        if timestamp.tzinfo is None:
            _fail('Review submission time must include its timezone')
    if state != 'PENDING' and submitted is None:
        _fail('Submitted review lacks its submission time')
    if (login == BOT and actor == 'Bot' and commit == head and submitted is not None
            and state in ('APPROVED', 'CHANGES_REQUESTED', 'COMMENTED')):
        return identifier
    return None


def _reviews(pages: object, head: str, dismissed: str) -> int | None:
    if not isinstance(pages, list) or not pages:
        _fail('Paginated reviews must be a nonempty JSON array of pages')
    # GitHub returns review pages chronologically; the last eligible response controls.
    found: tuple[int, object] | None = None
    for page in cast('list[object]', pages):
        if not isinstance(page, list):
            _fail('Every review page must be a JSON array')
        for review in cast('list[object]', page):
            candidate = _submitted(review, head)
            if candidate is not None and str(candidate) != dismissed:
                found = candidate, review
    if found is None:
        return None
    _completed_report(found[1])
    return found[0]


def wait_for_review(repo: str, number: str, head: str, dismissed: str = '',
                    timeout: object = 1200, interval: object = 30) -> None:
    """Poll only absent qualifying evidence; API errors and changed heads stop immediately."""
    if re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo) is None:
        _fail('Repository must identify one owner/name')
    if re.fullmatch(r'[1-9][0-9]*', number) is None or SHA.fullmatch(head) is None:
        _fail('PR number or expected SHA is malformed')
    if dismissed and re.fullmatch(r'[1-9][0-9]*', dismissed) is None:
        _fail('Dismissed review identity is malformed')
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 0 < timeout <= 1200:
        _fail('Completion timeout must be an integer from 1 to 1200 seconds')
    if isinstance(interval, bool) or not isinstance(interval, int) or not 0 < interval <= 60:
        _fail('Polling interval must be an integer from 1 to 60 seconds')
    path, deadline = f'repos/{repo}/pulls/{number}', time.monotonic() + timeout
    while True:
        _head(path, head, deadline)
        candidate = _reviews(_api(f'{path}/reviews?per_page=100', deadline, True), head, dismissed)
        confirmed = None
        if candidate is not None:
            review = _api(f'{path}/reviews/{candidate}', deadline)
            identity = (_field(review, 'id'), _field(review, 'commit_id'),
                        _field(_field(review, 'user'), 'login'), _field(_field(review, 'user'), 'type'))
            if identity != (candidate, head, BOT, 'Bot'):
                _fail('Selected review identity changed during verification')
            confirmed = _submitted(review, head)
            if confirmed is not None:
                _completed_report(review)
        _head(path, head, deadline)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            _fail('Timed out waiting for submitted current-head Copilot review', 1)
        if confirmed is not None:
            print(f'COPILOT REVIEW GATE -- PASS: submitted {BOT} review for {head}')
            return
        print(f'COPILOT REVIEW GATE -- WAIT: no qualifying review; {remaining:.0f}s remain', flush=True)
        time.sleep(min(interval, remaining))


def main() -> None:
    """Read the immutable event declaration and optional dismissed ID from quoted arguments."""
    if len(sys.argv) != 5:
        _fail('Usage: copilot_review_gate.py OWNER/REPO PR_NUMBER EXPECTED_HEAD_SHA DISMISSED_ID')
    wait_for_review(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])


if __name__ == '__main__':
    main()
