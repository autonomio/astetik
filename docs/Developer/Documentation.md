# Change documentation

Update one source-backed claim in its canonical page and prove that readers can follow its actual workflow. This guide owns contributor steps; [Documentation System](Documentation-System.md) owns composition, rendering, and routing obligations.

## Prerequisites

- A checkout with its current Python dependencies for product examples.
- Node.js 20 or newer and npm.
- Chromium installed for the site's browser checks.

## Edit and verify

1. Find the narrow source authority: public exports, signature, validator, computation, artifact writer, focused test, or actual site configuration.
2. Edit the one canonical page for the affected claim. Link secondary pages rather than repeating its full contract.
3. For a new or moved page, update the maintained [source-to-route map](../../docs-site/docs-map.json). A route change requires an explicit migration and redirect decision.
4. Parse syntax examples; run executable workflows against actual bounded data. State when a real user-owned study file is required instead of inventing one.
5. Run the locked documentation checks:

```bash
npm --prefix docs-site ci
npm --prefix docs-site exec -- playwright install --with-deps chromium
npm --prefix docs-site run security:audit
npm --prefix docs-site run check
```

When product examples or their contracts change, also run:

```bash
python -m pytest tests/test_documentation.py
```

The npm check verifies the site; Python tests verify the real scientific example and canonical source inventory.

The full check lints Markdown, runs site unit tests, checks external links, assembles mapped sources, builds Docusaurus, verifies routes/assets/search, and runs browser/accessibility tests. It writes derived site output; do not hand-edit generated pages.

## Preview the changed reader path

```bash
npm --prefix docs-site start
```

Open the printed local URL. Inspect the changed page and its next route in desktop/mobile and light/dark contexts. Check keyboard access, local search, table/code overflow, and source edit targets. For shared layout or navigation changes, use the [parity procedure](Documentation-System.md#parity-and-adoption).

## Expected output and failures

The canonical prose remains in repository Markdown; assembly and build output are derived. Missing/duplicate mappings, stale routes, broken links, invalid Markdown, failed examples, accessibility failures, and unlisted visual changes require correction before acceptance.

Do not describe configured deployment coordinates as a deployed service or claim site headers without live proof. Do not replace a runtime defect with more permissive prose; record the defect and route a separate behavior change.

Next: [Documentation System](Documentation-System.md), then [maintenance](README.md).
