"""Source-backed documentation, portable site contracts, and the real example."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from contextlib import ExitStack
from importlib.resources import files
from pathlib import Path, PurePosixPath

import pandas as pd
from matplotlib import pyplot as plt

import astetik
from astetik.docs.first_figure import first_figure

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'docs-site'
COUNTRIES_SHA256 = 'c2f45363b0c59039cc29c1233e8e3bc879c78046f219e487fa543459580d7c5f'
REGION_COUNTS = {'Africa': 60, 'Americas': 57, 'Asia': 51, 'Europe': 51, 'Oceania': 29}


def _document(name: str) -> dict:
    return json.loads((SITE / name).read_text(encoding='utf-8'))


def _canonical_sources() -> set[str]:
    # Package redirects, scaffold README and governance files are deliberately
    # outside the maintained public corpus; all docs/ Markdown is canonical.
    return {'README.md', 'astetik/README.md'} | {
        path.relative_to(ROOT).as_posix() for path in (ROOT / 'docs').rglob('*.md')
    }


def test_canonical_markdown_inventory_is_complete_and_routes_are_unique():
    docs_map = _document('docs-map.json')
    sections, documents = docs_map['sections'], docs_map['documents']
    assert [section['label'] for section in sections] == [
        'Overview',
        'Guides',
        'Reference',
        'Developer',
        'Packages',
    ]
    for name in ('dir', 'slug', 'position'):
        assert len({section[name] for section in sections}) == 5
    assert sorted(section['position'] for section in sections) == [1, 2, 3, 4, 5]
    assert {document['source'] for document in documents} == _canonical_sources()
    for name in ('source', 'dest', 'slug'):
        values = [document[name] for document in documents]
        assert len(values) == len(set(values)), f'Duplicate document {name}'
    routes = [item['slug'] for item in [*sections, *documents]]
    assert len(routes) == len(set(routes))
    for document in documents:
        source = (ROOT / document['source']).resolve()
        assert source.is_relative_to(ROOT) and source.is_file()
        destination = PurePosixPath(document['dest'])
        assert not destination.is_absolute() and '..' not in destination.parts
        assert destination.suffix == '.md'
        slug = document['slug']
        assert slug == '/' or (
            slug.startswith('/')
            and not slug.endswith('/')
            and all(part not in {'', '.', '..'} for part in slug.split('/')[1:])
            and not any(character in slug for character in '?#')
        )


def test_public_python_fences_parse_as_standalone_modules():
    count = 0
    for source in sorted(_canonical_sources()):
        content = (ROOT / source).read_text(encoding='utf-8')
        for fence in re.finditer(r'^(`{3,}|~{3,})python\s*\n(.*?)^\1\s*$', content, re.M | re.S):
            code = fence.group(2)
            line = content[: fence.start()].count('\n') + 1
            ast.parse(code, filename=f'{source}:{line}')
            count += 1
    assert count > 0, 'No public Python examples were checked'


def test_real_example_retains_exact_input_counts_origins_and_replays(tmp_path):
    resource = files('astetik').joinpath('extras', 'countries.csv')
    snapshot = resource.read_bytes()
    assert hashlib.sha256(snapshot).hexdigest() == COUNTRIES_SHA256
    source = pd.read_csv(resource)
    assert len(source) == 249 and source['alpha-3'].is_unique
    assert source.loc[source['region'].isna(), 'alpha-3'].tolist() == ['ATA']

    result = first_figure()
    with ExitStack() as cleanup:
        cleanup.callback(plt.close, result.figure)
        observations = result.receipt['observations']
        assert observations == {
            'input': 249,
            'used': 248,
            'excluded': [{'alpha-3': 'ATA'}],
            'missing_policy': 'drop',
            'reason': 'The bundled Antarctica record has no region label.',
        }
        assert result.receipt['key'] == ['alpha-3']
        assert result.receipt['source']['file_sha256'] == COUNTRIES_SHA256
        assert result.receipt['source']['format'] == 'csv'
        assert result.receipt['source']['rows'] == 249
        assert len(result.data) == 249
        assert result.receipt['analysis'] is None  # Descriptive metadata, not inference.
        assert result.table['category'].tolist() == list(REGION_COUNTS)
        assert dict(zip(result.table['category'], result.table['n'])) == REGION_COUNTS
        assert dict(zip(result.table['category'], result.table['estimate'])) == REGION_COUNTS
        assert len(result.marks) == 5

        covered = []
        for identifier, mark in result.marks.items():
            category = mark['values']['category']
            rows = source.index[source['region'].eq(category)].tolist()
            assert mark['source_rows'] == rows
            assert mark['source_keys'] == [{'alpha-3': source.iloc[row]['alpha-3']} for row in rows]
            assert mark['values']['n'] == REGION_COUNTS[category]
            assert mark['values']['estimate'] == REGION_COUNTS[category]
            assert mark['computation'] == 'row count'
            assert result.inspect(identifier) == mark
            table_rows = result.table.loc[
                result.table['mark_id'].eq(identifier), 'source_rows'
            ].iloc[0]
            assert table_rows == rows, 'Retained summary origins must use original input positions'
            covered.extend(rows)
        assert len(covered) == len(set(covered)) == 248
        assert set(covered) == set(source.index[source['region'].notna()])
        assert result.verify()['passed']

        bundle = result.write(tmp_path / 'real-metadata')
        retained = json.loads((bundle / 'receipt.json').read_text(encoding='utf-8'))
        assert retained['source']['file_sha256'] == COUNTRIES_SHA256
        assert all((bundle / name).is_file() for name in retained['output_files'])
        replayed = astetik.replay(bundle, strict_environment=True)
        cleanup.callback(plt.close, replayed.figure)
        assert replayed.result_id == result.result_id
        assert replayed.receipt['observations'] == observations
        assert replayed.marks == result.marks
        pd.testing.assert_frame_equal(replayed.data, result.data)
        pd.testing.assert_frame_equal(replayed.table, result.table)
        assert replayed.verify()['passed']


def test_site_verification_contract_and_astetik_identity():
    profile = _document('product-docs.json')
    assert profile['productId'] == 'astetik'
    assert profile['productName'] == 'Astetik'
    assert profile['sourceRepoUrl'] == 'https://github.com/autonomio/astetik'
    assert profile['sourceBranch'] == 'master'
    assert profile['siteUrl'] == 'https://autonomio.github.io'
    assert profile['basePath'] == '/astetik/'
    assert (SITE / 'package-lock.json').is_file()
    scripts = _document('package.json')['scripts']
    assert 'lint-markdown.mjs' in scripts['lint']
    assert 'check-external-links.mjs' in scripts['check:external-links']
    assert 'audit-security.mjs' in scripts['security:audit']
    assert 'assemble-docs.mjs' in scripts['prepare-docs']
    for command in (
        'npm run lint',
        'npm run test:unit',
        'npm run check:external-links',
        'npm run prepare-docs',
        'docusaurus build --no-minify',
        'npm run verify:build',
        'npm run test:browser',
    ):
        assert command in scripts['check']
    assert scripts['test:browser'] == 'playwright test'
    workflow = (ROOT / '.github/workflows/pr_checks_lint.yml').read_text(encoding='utf-8')
    for command in (
        'npm --prefix docs-site ci',
        'npm --prefix docs-site run security:audit',
        'npm --prefix docs-site run check',
    ):
        assert command in workflow
    assert 'playwright install' in workflow and 'chromium' in workflow
    config = (SITE / 'docusaurus.config.js').read_text(encoding='utf-8')
    assert "onBrokenLinks: 'throw'" in config
    assert "onBrokenMarkdownLinks: 'throw'" in config
    assert 'productDocs.sourceBranch' in config
    css = (SITE / 'src/css/custom.css').read_text(encoding='utf-8')
    assert "font-family: 'Finlandica'" in css
    assert '../fonts/Finlandica.ttf' in css
    assert 'fonts.googleapis.com' not in css
    assert (SITE / 'src/fonts/OFL.txt').is_file()
    assert (SITE / 'src/fonts/Finlandica.ttf').read_bytes() == (
        ROOT / 'astetik/fonts/Finlandica.ttf'
    ).read_bytes()


def test_no_template_branding_remains_outside_required_license_notice():
    ignored = {
        'node_modules',
        'build',
        '.generated',
        '.docusaurus',
        'test-results',
        'playwright-report',
    }
    text_extensions = {'.js', '.mjs', '.json', '.css', '.md', '.yml', '.yaml', '.txt'}
    sources = [
        path
        for path in SITE.rglob('*')
        if path.is_file()
        and path.suffix in text_extensions
        and not ignored.intersection(path.relative_to(SITE).parts)
    ]
    sources.extend(ROOT / source for source in _canonical_sources())
    notice = SITE / 'THIRD_PARTY_LICENSES.txt'
    assert 'Copyright (c) 2024 Vaquum' in notice.read_text(encoding='utf-8')
    assert 'Permission is hereby granted' in notice.read_text(encoding='utf-8')
    for path in sources:
        if path == notice:
            continue
        content = path.read_text(encoding='utf-8').casefold()
        for brand in (
            'vaquum',
            'limen',
            'new_repository_template',
            'new-repository-template',
            'ibm plex',
        ):
            assert brand not in content, (
                f'Template branding {brand!r} remains in {path.relative_to(ROOT)}'
            )
