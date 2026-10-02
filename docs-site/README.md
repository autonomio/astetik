# Astetik documentation site

This scaffold renders maintained repository Markdown through the contract in
[`Documentation-System.md`](../docs/Developer/Documentation-System.md).
`product-docs.json` owns Astetik identity, origin, base path, repository, and
source branch. `docs-map.json` owns the complete source-to-route inventory.

## Local verification

Use Node 22 and the checked-in dependency lockfile:

```bash
npm --prefix docs-site ci
npm --prefix docs-site run security:audit
npm --prefix docs-site run check
```

The security gate rejects every reported production advisory. A passing gate
records zero reported production advisories for the exact lockfile at audit time;
it does not claim absence of unknown vulnerabilities. `check` runs Markdown lint, unit tests, public-link
checks, assembly, build verification, and browser accessibility checks.
Playwright requires its Chromium browser installed with
`npm --prefix docs-site exec -- playwright install --with-deps chromium`.

If another local project uses port 3100, run browser checks with an explicit
port override: `DOCS_PORT=3113 npm --prefix docs-site run test:browser`. The
browser runner refuses to reuse an existing server.

## Local preview

```bash
npm --prefix docs-site run build
npm --prefix docs-site run serve
```

Open `http://127.0.0.1:3100/astetik/`. The configured origin is
`https://autonomio.github.io` and base path is `/astetik/`; these are canonical
build metadata. This scaffold verifies a local build and does not deploy it or
assert hosted security headers, TLS, redirects, or availability.

## Authored and generated files

Edit maintained Markdown sources, profile, route map, scripts, tests,
configuration, and CSS. Never author or commit `.generated`, `.docusaurus`,
`build`, test results, or browser reports.

Finlandica Regular is bundled locally under `src/fonts/` with its SIL Open Font
License. Light-mode roles follow the Autonomio style guide: paper `#F7F7F2`,
ink `#252D33`, muted `#626B72`, line `#D4DADD`, accent `#2A4A70`. Dark mode uses
corresponding accessible surface and text roles; geometry and interactions
retain the shared scaffold contract. Upstream license attribution is preserved
in `THIRD_PARTY_LICENSES.txt`.
