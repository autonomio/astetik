"""Checkout access and security routing remain valid without private-report activation."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY_URL = 'https://github.com/autonomio/astetik/blob/master/SECURITY.md'


def test_scorecard_job_retains_explicit_checkout_read_access() -> None:
    workflow = yaml.safe_load((ROOT / '.github/workflows/scorecard-analysis.yml').read_text())
    job = workflow['jobs']['analysis']
    assert job['permissions']['contents'] == 'read'
    assert job['permissions']['security-events'] == 'write'
    assert job['permissions']['id-token'] == 'write'
    checkout = [
        step for step in job['steps'] if step.get('uses', '').startswith('actions/checkout@')
    ]
    assert len(checkout) == 1
    assert checkout[0]['with']['persist-credentials'] is False


def test_security_contact_routes_to_policy_without_assuming_a_private_channel() -> None:
    source = (ROOT / '.github/ISSUE_TEMPLATE/config.yml').read_text()
    config = yaml.safe_load(source)
    assert config['blank_issues_enabled'] is False
    assert config['contact_links'] == [
        {
            'name': 'Security reporting policy',
            'url': POLICY_URL,
            'about': 'Follow SECURITY.md to select an available private reporting channel.',
        }
    ]
    assert '/security/advisories/new' not in source


def test_public_security_form_routes_sensitive_details_through_canonical_policy() -> None:
    source = (ROOT / '.github/ISSUE_TEMPLATE/security_report.yml').read_text()
    template = yaml.safe_load(source)
    guidance = '\n'.join(
        item['attributes']['value'] for item in template['body'] if item['type'] == 'markdown'
    )
    assert POLICY_URL in guidance
    assert 'Do not submit exploitable details or credentials through public issues.' in guidance
    assert 'otherwise' in guidance
    assert '/security/advisories/new' not in source
    acknowledgement = next(item for item in template['body'] if item.get('id') == 'acknowledgement')
    choices = acknowledgement['attributes']['options']
    assert len(choices) == 1
    assert choices[0]['required'] is True
    assert 'SECURITY.md' in choices[0]['label']
    assert 'before sharing sensitive details' in choices[0]['label']
