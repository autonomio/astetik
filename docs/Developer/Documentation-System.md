# Documentation system contract

This page owns Astetik's maintained documentation architecture, page composition, rendering, routing, and verification contract. It adapts the supplied repository template at revision `fa7bf92caab5bb8d7f73120d4dc3526fd86c0348`; its retained attribution and license are [THIRD_PARTY.md](../../THIRD_PARTY.md), with the site notice retained alongside the scaffold.

The source template's organization, project claims, routes, visual identity, and operating state are not Astetik product claims. Documentation adoption preserved the scientific contracts with a focused correction mapping mark provenance to original input rows. Astetik now also adopts the full local repository constitution and verification machinery; live governance and publication still require [setup readiness](../../SETUP.md).

## Prerequisites

- Node.js 20 or newer and npm.
- Locked site dependencies installed through `npm --prefix docs-site ci`.
- Current Astetik dependencies to execute product examples.
- Chromium for browser and accessibility checks.

## Quality and ownership

Maintained documentation must be correct against current source, complete across its declared corpus, coherent by reader task, runnable at the level its examples imply, accessible, discoverable, and mechanically checked in proportion to its claims.

| Layer | Owns | Excludes |
| --- | --- | --- |
| Shared scaffold | Five-section architecture, composition, assembler, interactions, generic verification | Product claims, scientific examples, deployment account, and route authority |
| Product profile and Markdown | Astetik/Autonomio identity, narrative, canonical claims, source inventory, routes | Copies of shared rendering logic or invented capabilities |
| Deployment adapter | Actual hosting, redirects, headers, preview, and rollback | Alternate prose or source-to-route authority |

Author each claim once. Secondary pages summarize and link to its canonical home. Runtime defects are separate behavior work, not an opportunity to weaken documentation claims.

## Canonical source model

| Source | Responsibility |
| --- | --- |
| Root `README.md` | Product identity, boundary, minimum first success, project information |
| `docs/README.md` | Reader task router and product execution narrative |
| `docs/Overview/` | Product/system boundary |
| `docs/Guides/` | Ordered user jobs and observable outcomes |
| `docs/Reference/` | Interfaces, schemas, defaults, outputs, and edge cases |
| `docs/Developer/` | Current contributor/maintenance processes and doc standards |
| `astetik/README.md` | Package ownership, public entry points, adjacent dependencies |
| `docs-site/docs-map.json` | Complete maintained source-to-destination/route map |

Every maintained public source maps exactly once to a stable public route with one primary page role. The root repository-policy and metadata corpus is explicitly outside this public map; [maintenance](README.md#scope-and-authority) owns its inventory and links. These sources remain repository-file links rather than duplicated site prose. Generated category indexes provide navigation. The five categories are Overview, Guides, Reference, Developer, and Packages; their navigation starts collapsed. Derived `.generated`, `.docusaurus`, and `build` output must not be hand-authored or committed.

## Product narrative

The [hub](../README.md#product-sequence) owns the actual sequence: installed input, declaration, manifest resolution, optional explicit computation, rendering/inspection, publication, and bounded replay. Each step names an implemented boundary and links its canonical guide or reference. It ends at recorded artifact/computation responsibility, not a claim of universal scientific validity.

## Page composition

Composition specifies information order. Explicitly identify an inapplicable element rather than silently omitting it.

| Role | Required information order |
| --- | --- |
| Product home | Identity/value; owned/excluded boundary; capabilities; install/first success; outputs; risk boundary; task routes; contribution/support/security/citation/license |
| Docs hub | Product in one page; reader jobs; product sequence; complete five-section map; boundary; next routes |
| Guide | Job/outcome/scope; prerequisites; ordered procedure; observable result; failures/edge cases; next task |
| Reference | Surface/boundary; names/imports; signatures/defaults/units/side effects; concrete example; errors/dependencies; adjacent surfaces; next reference/workflow |
| Developer | Purpose/authority; prerequisites; ownership; executable process; proof/failures; maintenance boundary; related routes |
| Package README | Path/responsibility; public docs; boundary; entry points; adjacent dependencies; useful source orientation; caveats; next routes |

## Writing and source authority

Lead with current behavior and reader impact. Use American English, literal units and signatures, relative maintained-source links, and explicit next routes. Use Python fences for parseable Python, not mixed prompts or pseudo-code. Declare optional dependencies before importing them.

Authority is the narrowest current source: exports for imports; signatures and validators for arguments/schema; computation plus focused tests for numerical claims; writers for artifacts; project metadata for dependencies; workflows for actual gates; route map/assembler/build for routes; CSS for visual values; live adapter responses for deployed headers.

Examples must satisfy the promise they make. Syntax examples parse; import examples import; commands use actual argument order; executable workflows run against bounded actual data; output fields come from implementations. If measured research data is absent, require a user-owned study input explicitly. The bundled country snapshot supports metadata examples, not invented empirical measurements or a current ISO authority claim.

Do not present local measurements as stable API guarantees, future behavior as current, or a template reference's project claims as Astetik claims.

## Autonomio visual adaptation

The site's visual authority is [custom.css](../../docs-site/src/css/custom.css). The supplied Autonomio style guide informs Finlandica Regular, restrained color, alignment, whitespace, and authority through content. Web pixel geometry is not a chart-publication sizing rule; figure design belongs in the [manifest](../Reference/Manifest.md).

| Site token | Light | Dark | Role |
| --- | --- | --- | --- |
| `--astetik-paper` | `#F7F7F2` | `#252D33` | Page/navigation surface |
| `--astetik-paper-2` | `#EEF0EB` | `#303B45` | Secondary/code surface |
| `--astetik-ink` | `#252D33` | `#F7F7F2` | Main foreground |
| `--astetik-ink-soft` | `#626B72` | `#D4DADD` | Secondary foreground |
| `--astetik-rule` | `#D4DADD` | `#47525C` | Dividers |
| `--astetik-accent` | `#2A4A70` | `#A7C5E8` | Interaction/accent |

| Element | Current site geometry |
| --- | --- |
| Body | Self-hosted Finlandica; 17 px; line height 1.55 |
| Code | System monospace; 14.5 px; line height 1.65 |
| Reading column | Maximum 680 px |
| H1 | 44 px; regular weight 400; line height 1.1; maximum 28 ch |
| Section headings | 13 px; regular weight 400; uppercase/tracking treatment |
| Navbar/sidebar | 56 px navbar; 320 px desktop sidebar |
| Corners/shadows | Zero radius and no decorative shadow |
| Responsive boundary | 996 px; mobile layout has bounded readable width |

Dark-mode values are the implemented site adaptation, not values quoted from the PDF. Preserve reader usability, keyboard focus, tables/code overflow handling, light/dark contrast, and mobile navigation. Changing shared geometry requires visual evidence.

## Scoped scaffold overrides

Astetik's documentation maintainers own these source-controlled adaptations and their browser proofs:

| Scope | Reason and boundary | Evidence |
| --- | --- | --- |
| [MDX table component](../../docs-site/src/theme/MDXComponents/index.js) | Add keyboard focus only to horizontally overflowing tables; preserve ordinary table semantics and visible focus | Mobile contract-page test focuses a table and scrolls it with ArrowRight; Axe and the surface matrix pass |
| [Skip-to-content wrapper](../../docs-site/src/theme/SkipToContent/index.js) | Keep the main target programmatically focusable because Chromium loses focus when the upstream handler removes its tabindex; preserve the original skip-link component | Keyboard test activates the skip link and verifies main focus, then selects a local search result |
| [Browser test configuration](../../docs-site/playwright.config.js) | `DOCS_PORT` selects an isolated local test port; default 3100, integer range 1024–65535; no deployed route change | Full browser suite runs on the selected port with existing-server reuse disabled |

These changes affect documented accessibility or local verification. Reverting them requires equivalent keyboard and accessibility proof.

## Profile, routes, and assembly

[product-docs.json](../../docs-site/product-docs.json) owns identity, repository URL, `sourceBranch`, site origin, and base path. Astetik's source branch is `master`; edit targets must point to each real source file under that branch. The configured `https://autonomio.github.io` origin with `/astetik/` base path is a build coordinate, not proof of a deployed site.

The [route map](../../docs-site/docs-map.json) owns exactly one source, destination, and canonical leading-slash route per page. Routes have no optional trailing slash. A route change requires link migration, an explicit redirect decision, sitemap update, and a declared expected difference.

The assembler validates profile/map, recreates ignored generated source, writes source-true front matter/edit URLs, rewrites mapped relative links, preserves repository-file links, normalizes Markdown for MDX, and creates category/robots output. Blog and standalone-page authority are excluded from the maintained root documentation path.

## Security audit boundary

`npm --prefix docs-site run security:audit` runs npm's production audit and applies the actual rules in [audit-report.mjs](../../docs-site/scripts/audit-report.mjs) and dependency-root reachability in [audit-scope.mjs](../../docs-site/scripts/audit-scope.mjs).

Every reported production advisory blocks, including **info** and **low** severity. Dependency-root attribution is diagnostic; it grants no exception. Invalid reports, unknown severity, incomplete audit execution, and unresolved declared roots fail. A pass means npm reported zero production advisories for the exact installed lockfile at audit time; it does not establish that unknown vulnerabilities are absent.

Dependency repairs use supported upstream releases and compatible security backports. Narrow an override to the affected major when a backport exists; retain registry integrity hashes and verify the complete site after lockfile changes. The package manifest and lockfile own exact versions.

## Required proof

From the repository root:

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

The configured [lint workflow](../../.github/workflows/pr_checks_lint.yml) runs the locked documentation install, Chromium installation, audit, and full check. Package and governance checks are owned by [maintenance](README.md); their local configuration does not establish live required checks.

| Concern | Mechanism |
| --- | --- |
| Profile, uniqueness, source inventory, routing | Assembler validation and site unit tests |
| Markdown | Locked Markdown lint |
| External links | Public-address-safe HEAD/GET checks; three attempts with 500/1000 ms delays |
| Local assembled links | Docusaurus broken-link failure |
| Production dependency advisories | Zero-advisory production audit |
| Build, route set, sitemap, robots, search, asset budgets | Production build and build verifier |
| Desktop/mobile, light/dark, navigation, search, edit targets | Playwright |
| Keyboard and WCAG A/AA checks | Browser tests and Axe |
| Scientific product examples | Actual bounded fixture checks against Python source |
| Deployed redirects/headers/status | Deployment-specific live checks; not established by a static build |

External-link verification accepts only an actual 2xx response. A transient HEAD status or unsupported HEAD method (405) is verified through GET using the same public-DNS validation, pinned addresses, and five-redirect limit. Definitive 4xx failures stop immediately; unresolved transient or network failures stop after three attempts, with real 500 and 1000 ms delays. Diagnostics retain method, status, request ID and Retry-After, while omitting URL credentials, queries and unrelated headers.

A static build proves generated artifacts and configured canonical metadata. It does not prove live TLS, security headers, redirect behavior, or availability. Deployment acceptance requires those adapter-specific proofs separately.

## Parity and adoption

Freeze the baseline source inventory, route set, lockfiles/tool versions, profile, behavior, representative screenshots, and known defects. Build the candidate with the same origin/base path and viewport matrix. Compare preserved navigation, search, edit targets, metadata, routes, CSS geometry, and non-target content.

At minimum review product home, category index, guide, reference, developer, and package pages at desktop 1440-by-900 and mobile 390-by-844, both light and dark. Every intended difference names route, viewport, theme, old/new behavior, authority, evidence, and rollback effect. Unexpected deltas require correction.

Astetik's declared adoption differences are its product/source inventory, actual scientific narrative and data, Autonomio branding and Finlandica visual treatment, `master` edit targets, and repository-specific build coordinates. The supplied template's old project evidence is not retained as product content. Notebook-era documentation and images remain in Git history rather than forming a second maintained API authority.

Review a candidate preview before any cutover. Retain the prior production artifact through smoke checks when production deployment actually exists. This iteration's local build alone does not establish that a cutover happened.

## Maintenance boundary

A page or shared-system change must leave source authority, routes, links, tests, and documentation accurate. A local override requires an owner, reason, tracked scope, and evidence that it preserves the claimed checks. No change to this contract silently authorizes runtime changes, remote governance activation, messages, or publication.

Next: [documentation contributor workflow](Documentation.md), [docstring standard](Writing-Docstrings.md), or [maintenance](README.md).
