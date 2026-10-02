# Maintenance

This page owns the contributor task router and verification path. [CLAUDE.md](../../CLAUDE.md) owns the constitution; [Configuration](Configuration.md) owns mechanical settings. Local governance adoption is distinct from activated remote enforcement.

## Prerequisites

Use Python 3.13 for governance and a source checkout with development/Polars dependencies and the hash-pinned gate toolchain. The installed library's public floor remains Python 3.11; product compatibility is checked separately on 3.11, 3.12, and 3.13.
Documentation work also requires Node.js 20 or newer, npm, and Chromium.

## Scope and authority

Read [AGENTS.md](../../AGENTS.md), then the delegated constitution. Keep changes inside the declared task/slice. The actual project metadata, gate source/tests, workflows, and budgets determine installed and checked behavior.

The root policy/metadata corpus is repository-facing, outside the public docs map: `AGENTS.md`, `CLAUDE.md`, `GOVERNANCE.md`, `CONTRIBUTING.md`, `SETUP.md`, `SECURITY.md`, `SUPPORT.md`, `CODE_OF_CONDUCT.md`, `MAINTAINERS.md`, `AUTHORS`, `CITATION.cff`, `NOTICE`, `THIRD_PARTY.md`, `AUTONOMIO_REPO_SPECIFICS.md`, and `AUTONOMIO_PR_GUIDELINE.md`. These are linked as repository sources, not duplicated into public pages. Product/Developer Markdown under the maintained public corpus is mapped once.

## Start by contributor task

| Task | Canonical route |
| --- | --- |
| Set up or contribute | [Contributing](../../CONTRIBUTING.md) |
| Use Astetik as an agent | [Scientific agent workflow](Agent-Workflow.md) |
| Change gates or ratchets | [Configuration](Configuration.md) |
| Change documentation | [Documentation workflow](Documentation.md) |
| Review docstrings | [Writing docstrings](Writing-Docstrings.md) |
| Inspect distributions | [Packaging](Packaging.md) |
| Decide or execute a release | [Versioning](Semantic-Versioning.md), [release policy](Release-Policy.md), [making a release](Making-Release.md) |
| Evaluate security controls | [Security assurance case](Security-Assurance-Case.md) |
| Record accepted limitations | [Technical debt](Technical-Debt.md) |
| Activate remote governance | [Setup readiness](../../SETUP.md) |

## Verify package changes

```bash
python -m pytest tests -q --maxfail=1
python -m pytest governance/tests -q
python governance/check_ruff_ratchet.py --base-ref origin/master
python scripts/build_catalog.py --check
python -m build
```

Run the relevant full configured gates as described in [contribution](../../CONTRIBUTING.md), including docstrings/module budgets, typing/fail-loud ratchets, coverage/runtime, and packaging. The [verified first-adoption case](Configuration.md#first-adoption-proof) requires explicit bootstrap arguments when the protected base has no governance; Git-dependent checks require the real base and PR declarations; a local unit command cannot prove merge eligibility.
Behavior changes need meaningful regression protection and current canonical documentation. A green suite proves tested contracts, not universal scientific correctness.
For catalogue changes, regenerate `astetik/docs/plots.json` with `python scripts/build_catalog.py`, inspect scientific meaning, then use `--check`.

## Verify documentation changes

Follow [Documentation](Documentation.md) and the [system contract](Documentation-System.md). The configured lint plane runs the locked site audit and full checks; public examples use actual available observations or explicitly require user-owned input.
Preserve source authority and the Autonomio visual adaptation. Country metadata is a retained snapshot, not a current geopolitical authority.

## Completion boundary

Report the exact candidate and successful or unresolved checks. Live rules, approvals, release tags, publisher configuration, attestations, and hosted-site behavior require their own evidence. A policy file does not authorize remote writes or messages; a local build does not establish publication.

Next: [constitution](../../CLAUDE.md), [configuration](Configuration.md), or [documentation workflow](Documentation.md).
