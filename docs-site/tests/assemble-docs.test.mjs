import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

import {
  normalizeForMdx,
  rewriteOutsideCode,
  validateDocuments,
  validateProfile,
  validateSections,
} from '../scripts/assemble-docs.mjs';
import {
  assertPublicUrl,
  extractExternalLinks,
  isPublicAddress,
} from '../scripts/check-external-links.mjs';
import {
  lintExitCode,
  markdownSources,
} from '../scripts/lint-markdown.mjs';
import {
  isPathInside,
  resolveRepositoryPath,
} from '../scripts/repository-paths.mjs';
import {canonicalSitemapUrl, siteRoute} from '../scripts/site-urls.mjs';

const profile = JSON.parse(readFileSync(new URL('../product-docs.json', import.meta.url)));
const mark = (value) => value.replaceAll('{TOKEN}', 'REWRITTEN');


test('rewrites prose but preserves fenced and inline code', () => {
  const source = [
    'before {TOKEN}',
    '```text',
    'inside {TOKEN}',
    '```',
    '~~~text',
    'inside tilde {TOKEN}',
    '~~~',
    'after `{TOKEN}` and {TOKEN}',
  ].join('\n');

  assert.equal(
    rewriteOutsideCode(source, mark),
    [
      'before REWRITTEN',
      '```text',
      'inside {TOKEN}',
      '```',
      '~~~text',
      'inside tilde {TOKEN}',
      '~~~',
      'after `{TOKEN}` and REWRITTEN',
    ].join('\n')
  );
});

test('preserves the tail of an unclosed fence', () => {
  const source = 'before {TOKEN}\n```text\ninside {TOKEN}';

  assert.equal(
    rewriteOutsideCode(source, mark),
    'before REWRITTEN\n```text\ninside {TOKEN}'
  );
});

test('preserves the tail of unmatched inline code', () => {
  const source = 'before {TOKEN} and `{TOKEN}';

  assert.equal(
    rewriteOutsideCode(source, mark),
    'before REWRITTEN and `{TOKEN}'
  );
});

test('preserves multi-backtick inline code while transforming surrounding prose', () => {
  const source = 'before {TOKEN}, ``inside $& $$ ` {TOKEN}``, after {TOKEN}';

  assert.equal(
    rewriteOutsideCode(source, mark),
    'before REWRITTEN, ``inside $& $$ ` {TOKEN}``, after REWRITTEN'
  );
});

test('extracts unique Markdown and HTML external links', () => {
  const source = [
    '[Repository](https://github.com/autonomio/example)',
    '<a href="https://docs.example.com/example/">Docs</a>',
    '<img src="https://docs.example.com/example/logo.png" alt="Logo" />',
    '[Duplicate](https://github.com/autonomio/example)',
    '`[Inline example](http://127.0.0.1/private)`',
    '~~~markdown',
    '[Fenced example](http://169.254.169.254/latest/meta-data)',
    '~~~',
  ].join('\n');

  assert.deepEqual(
    [...extractExternalLinks(source)].sort(),
    [
      'https://docs.example.com/example/',
      'https://docs.example.com/example/logo.png',
      'https://github.com/autonomio/example',
    ]
  );
});

test('rewrites prose links without mutating code examples', () => {
  const source = [
    '[Docs](docs/README.md)',
    '[``Docs with `ticks` ``](docs/README.md)',
    '<a href="docs/README.md">Docs</a>',
    '```markdown',
    '[Docs](docs/README.md)',
    '```',
    '`[Docs](docs/README.md)`',
    '``[Docs](docs/README.md) with `ticks` ``',
  ].join('\n');

  const normalized = normalizeForMdx(source, 'README.md');
  assert.match(normalized, /^\[Docs\]\(overview\/docs-hub\.md\)$/m);
  assert.match(
    normalized,
    /^\[``Docs with `ticks` ``\]\(overview\/docs-hub\.md\)$/m
  );
  assert.match(
    normalized,
    /^<a href="\/(?:[^"]*\/)?overview\/docs-hub">Docs<\/a>$/m
  );
  assert.match(normalized, /^`\[Docs\]\(docs\/README\.md\)`$/m);
  assert.match(normalized, /^``\[Docs\]\(docs\/README\.md\) with `ticks` ``$/m);
  assert.match(
    normalized,
    /```markdown\n\[Docs\]\(docs\/README\.md\)\n```/
  );
});

test('routes portable repository URLs locally without changing retained references or examples', () => {
  const base = `${profile.sourceRepoUrl}/blob/${profile.sourceBranch}`;
  const current = `${base}/docs/README.md#product-sequence`;
  const retained = `${profile.sourceRepoUrl}/blob/854caea917ce1f52b796a570d197d37c4a925244/docs/README.md`;
  const foreign = 'https://github.com/autonomio/chances/blob/master/docs/README.md';
  const source = [
    `[Docs](${current})`,
    `<a href="${current}">Docs</a>`,
    `[Retained](${retained})`,
    `[Other](${foreign})`,
    `[Metadata](${base}/pyproject.toml)`,
    `\`[Example](${current})\``,
    '```markdown',
    `[Example](${current})`,
    '```',
  ].join('\n');
  const normalized = normalizeForMdx(source, 'docs/Guides/First-Figure.md');
  assert.match(normalized, /^\[Docs\]\(\.\.\/overview\/docs-hub\.md#product-sequence\)$/m);
  assert.ok(normalized.includes(`<a href="${profile.basePath}overview/docs-hub#product-sequence">Docs</a>`));
  for (const [label, target] of [['Retained', retained], ['Other', foreign], ['Metadata', `${base}/pyproject.toml`]]) {
    assert.ok(normalized.includes(`[${label}](${target})`));
  }
  assert.ok(normalized.includes(`\`[Example](${current})\``));
  assert.ok(normalized.includes(`\`\`\`markdown\n[Example](${current})\n\`\`\``));
});

test('rewrites unmapped repository files using the declared source branch', () => {
  const source = '[Package metadata](pyproject.toml)';
  assert.equal(
    normalizeForMdx(source, 'README.md'),
    `[Package metadata](${profile.sourceRepoUrl}/blob/${profile.sourceBranch}/pyproject.toml)`
  );
});

test('keeps repository link resolution inside the repository root', () => {
  assert.equal(isPathInside('/repo', '/repo'), true);
  assert.equal(isPathInside('/repo', '/repo/docs/README.md'), true);
  assert.equal(isPathInside('/repo', '/repo-neighbor/README.md'), false);
  assert.equal(isPathInside('/repo', '/outside/README.md'), false);
  assert.throws(
    () => resolveRepositoryPath('/repo', '../outside/README.md'),
    /documentation source is outside the repository/
  );
});

test('builds canonical sitemap URLs for root and nested docs paths', () => {
  assert.equal(
    canonicalSitemapUrl('https://docs.example.com', '/'),
    'https://docs.example.com/sitemap.xml'
  );
  assert.equal(
    canonicalSitemapUrl('https://docs.example.com/', '/product/'),
    'https://docs.example.com/product/sitemap.xml'
  );
  assert.equal(siteRoute('/', '/guide'), '/guide');
  assert.equal(siteRoute('/', '/'), '/');
  assert.equal(siteRoute('/product/', '/guide'), '/product/guide');
  assert.equal(siteRoute('/product/', '/'), '/product/');
});

test('derives Markdown lint sources from the route map', () => {
  const map = {
    documents: [
      {source: 'README.md'},
      {source: 'docs/README.md'},
      {source: 'README.md'},
    ],
  };

  assert.deepEqual(
    markdownSources(map),
    ['CHANGELOG.md', 'README.md', 'docs/README.md']
  );
});

test('fails markdown lint when the subprocess exits by signal', () => {
  assert.equal(lintExitCode(null), 1);
  assert.equal(lintExitCode(2), 2);
});

test('validates every category field before generation', () => {
  const sections = Array.from({length: 5}, (_, index) => ({
    dir: `section-${index}`,
    label: `Section ${index}`,
    position: index + 1,
    slug: `/section-${index}`,
    description: `Section ${index} description.`,
  }));

  assert.doesNotThrow(() => validateSections(sections));
  assert.throws(
    () => validateSections([{...sections[0], label: ''}, ...sections.slice(1)]),
    /section.label must be a non-empty string/
  );
  assert.throws(
    () => validateSections([{...sections[0], position: 0}, ...sections.slice(1)]),
    /section.position must be a positive integer/
  );
  assert.throws(
    () => validateSections([{...sections[0], slug: '/section/'}, ...sections.slice(1)]),
    /section.slug must be \/ or a canonical leading-slash route/
  );
});

test('validates canonical document routes before generation', () => {
  const documents = [
    {source: 'README.md', dest: 'index.md', slug: '/'},
    {source: 'docs/README.md', dest: 'overview.md', slug: '/overview'},
  ];

  assert.doesNotThrow(() => validateDocuments(documents));
  assert.throws(
    () => validateDocuments([{...documents[0], slug: 'overview'}]),
    /document.slug must be \/ or a canonical leading-slash route/
  );
  assert.throws(
    () => validateDocuments([{...documents[0], slug: '/overview/'}]),
    /document.slug must be \/ or a canonical leading-slash route/
  );
});

test('validates documentation build coordinates before generation', () => {
  const profile = {
    productId: 'product',
    productName: 'Product',
    tagline: 'Product documentation.',
    siteUrl: 'https://docs.example.com',
    basePath: '/product/',
    sourceRepoUrl: 'https://github.com/autonomio/product',
    sourceBranch: 'master',
  };

  assert.doesNotThrow(() => validateProfile(profile));
  assert.doesNotThrow(() => validateProfile({...profile, basePath: '/'}));
  assert.doesNotThrow(() => validateProfile({...profile, sourceBranch: 'release/docs'}));
  assert.throws(
    () => validateProfile({...profile, sourceBranch: '../master'}),
    /sourceBranch must be a valid repository branch/
  );
  assert.throws(
    () => validateProfile({...profile, sourceBranch: ''}),
    /sourceBranch must be a non-empty string/
  );
  assert.throws(
    () => validateProfile({...profile, siteUrl: 'https://docs.example.com/'}),
    /siteUrl must be an HTTP\(S\) origin without a trailing slash/
  );
  assert.throws(
    () => validateProfile({...profile, basePath: 'product/'}),
    /basePath must be \/ or have leading and trailing slashes/
  );
});

test('rejects external-link destinations that can reach private networks', async () => {
  assert.equal(isPublicAddress('8.8.8.8'), true);
  assert.equal(isPublicAddress('127.0.0.1'), false);
  assert.equal(isPublicAddress('169.254.169.254'), false);
  assert.equal(isPublicAddress('10.20.30.40'), false);
  assert.equal(isPublicAddress('192.0.2.1'), false);
  assert.equal(isPublicAddress('::1'), false);
  assert.equal(isPublicAddress('fe80::1'), false);

  await assert.rejects(
    assertPublicUrl('http://localhost/private'),
    /non-public destination/
  );
  await assert.rejects(
    assertPublicUrl('http://169.254.169.254/latest/meta-data'),
    /non-public destination/
  );
  await assert.rejects(
    assertPublicUrl('https://user:secret@example.com/'),
    /must not contain credentials/
  );
});
