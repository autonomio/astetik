from __future__ import annotations

import pytest

from governance import version_gate


def _pyproject(version: str) -> str:
    return f'[project]\nname = "demo"\nversion = "{version}"\n'


def _changelog(version: str, body: str = '- Change.\n') -> str:
    return f'# v{version}\n\n{body}\n# v1.2.3\n\n- Previous.\n'


def test_gate_accepts_feat_with_minor_bump_and_changelog_content() -> None:
    failures = version_gate.gate(
        'feat: add law template',
        _pyproject('1.2.3'),
        _pyproject('1.3.0'),
        _changelog('1.2.3'),
        _changelog('1.3.0'),
    )
    assert failures == []


def test_gate_rejects_feat_with_patch_bump() -> None:
    failures = version_gate.gate(
        'feat: add law template',
        _pyproject('1.2.3'),
        _pyproject('1.2.4'),
        _changelog('1.2.3'),
        _changelog('1.2.4'),
    )
    assert any('requires at least a minor version bump' in item for item in failures)


def test_gate_requires_new_changelog_header_at_top() -> None:
    failures = version_gate.gate(
        'fix: tighten law template',
        _pyproject('1.2.3'),
        _pyproject('1.2.4'),
        _changelog('1.2.3'),
        '# v1.2.3\n\n- Previous.\n\n# v1.2.4\n\n- New but misplaced.\n',
    )
    assert any('top version header is `# v1.2.3`' in item for item in failures)


def test_gate_rejects_empty_top_changelog_section() -> None:
    failures = version_gate.gate(
        'fix: tighten law template',
        _pyproject('1.2.3'),
        _pyproject('1.2.4'),
        _changelog('1.2.3'),
        '# v1.2.4\n\n# v1.2.3\n\n- Previous.\n',
    )
    assert any('has no content before the next version header' in item for item in failures)


def test_strict_semver_rejects_prerelease_versions() -> None:
    with pytest.raises(SystemExit) as exc:
        version_gate.parse_semver('1.2.4-alpha')
    assert exc.value.code == 2


def test_gate_rejects_past_tense_changelog_bullet() -> None:
    failures = version_gate.gate(
        'fix: tighten law template',
        _pyproject('1.2.3'),
        _pyproject('1.2.4'),
        _changelog('1.2.3'),
        _changelog('1.2.4', body='- Added a new helper.\n'),
    )
    assert any('past tense' in item for item in failures)


def test_gate_rejects_changelog_placeholder() -> None:
    failures = version_gate.gate(
        'fix: tighten law template',
        _pyproject('1.2.3'),
        _pyproject('1.2.4'),
        _changelog('1.2.3'),
        _changelog('1.2.4', body='- Fix the parser (TODO: expand later).\n'),
    )
    assert any('placeholder' in item for item in failures)


def test_gate_accepts_imperative_changelog_bullet() -> None:
    failures = version_gate.gate(
        'fix: tighten law template',
        _pyproject('1.2.3'),
        _pyproject('1.2.4'),
        _changelog('1.2.3'),
        _changelog('1.2.4', body='- Fix the broken parser path.\n'),
    )
    assert failures == []


def test_header_form_whitespace_survives_next_to_the_placeholder() -> None:
    """Whitespace adjacent to `{version}` must become flexible whitespace.

    Splitting the literal on spaces and dropping empty chunks deleted the run
    either side of the placeholder, so `## {version}` compiled to a pattern
    demanding the version immediately after `##`. A repository configured that
    way matched none of its own headers and the gate reported a missing
    changelog header on every PR.
    """
    import re as _re

    for form in ('# v{version}', '## {version}', '## Version {version}',
                 '## [{version}] - ', '### v{version}:'):
        before, _, after = form.partition('{version}')
        pattern = '^' + version_gate._escape_form(before) + version_gate._VERSION_TOKEN
        pattern += version_gate._escape_form(after) if after.strip() else r'\b'
        sample = form.replace('{version}', '1.2.3')
        assert _re.match(pattern, sample), f'{form!r} does not match its own header {sample!r}'


def _historical_hatch() -> str:
    return '[project]\nname="astetik"\ndynamic=["version"]\n[tool.hatch.version]\npath="astetik/__init__.py"\n'


def test_legacy_hatch_literal_compares_without_executing_base_code() -> None:
    source = "raise RuntimeError('must never execute')\n__VERSION__ = '1.15'\n"
    assert version_gate.historical_version_path(_historical_hatch()) == 'astetik/__init__.py'
    assert version_gate.gate(
        'feat!: adopt evidence API', _historical_hatch(), _pyproject('2.0.0'),
        '', _changelog('2.0.0', '- Add the evidence API.\n'), source,
    ) == []


@pytest.mark.parametrize('source', [
    "__VERSION__ = str(1.15)", "__VERSION__ = '1.15'\n__VERSION__ = '1.16'",
    "if True:\n    __VERSION__ = '1.15'", "__VERSION__ = '1.15.dev0'",
])
def test_legacy_version_rejects_computed_ambiguous_and_conditional_values(source: str) -> None:
    with pytest.raises(SystemExit):
        version_gate.extract_version(_historical_hatch(), 'base', source)


def test_legacy_version_cannot_replace_head_static_three_part_requirement() -> None:
    with pytest.raises(SystemExit):
        version_gate.extract_version(_historical_hatch(), 'head', "__VERSION__ = '1.15'")
    with pytest.raises(SystemExit):
        version_gate.parse_semver(version_gate.extract_version(_pyproject('2.0'), 'head'))
    with pytest.raises(ValueError, match='contained'):
        version_gate.historical_version_path(_historical_hatch().replace('astetik/__init__.py', '../outside.py'))
