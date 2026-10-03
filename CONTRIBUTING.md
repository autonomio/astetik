# Contributing

Read [AGENTS.md](AGENTS.md), then [CLAUDE.md](CLAUDE.md). This page owns contributor setup and verification; the constitution owns binding laws.

## Prerequisites and setup

Use Python 3.13 for the canonical governance environment. Astetik's installed runtime remains compatible with Python 3.11 and newer; CI separately tests 3.11, 3.12, and 3.13.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,polars]'
python -m pip install --require-hashes -r requirements/ci/gate-tools.txt
```

Documentation work also requires Node.js 20 or newer, npm, and Chromium; use the [documentation workflow](docs/Developer/Documentation.md).

## Contribution process

For authorized remote work, use the constitution's early-PR workflow and exactly one open slice-labelled issue. Stay inside the issue's surfaces, satisfy Done Means, and keep the branch current with `master`.
A local-only task produces a reviewable candidate and evidence without remote changes. Posting findings or requesting reviewers requires explicit human authorization.
Every non-exempt PR advances the version and adds a matching imperative changelog section, including documentation-only changes; see [versioning](docs/Developer/Semantic-Versioning.md).

Major new functionality and bug fixes must include meaningful automated tests in the same contribution. Reviewers verify the tests against the capability and retain regression tests for corrected failures.

## Contribution rights

Astetik accepts contributions through GitHub pull requests under its MIT license. [GitHub Terms of Service section D.6](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service#6-contributions-under-repository-license) requires each contributor to license contributed content under the repository license and agree they have the right to do so. This is our legal contribution mechanism; we do not claim historical DCO signoffs.

Preserve third-party licenses and attribution notices in [THIRD_PARTY.md](THIRD_PARTY.md) and accompanying assets. Do not submit work you lack authority to license. A nontrivial contribution received outside GitHub requires an equivalent explicit rights assertion before acceptance.

## Local proof

```bash
python -m pytest tests -q --maxfail=1
python -m pytest governance/tests -q
python governance/check_ruff_ratchet.py --base-ref origin/master
python governance/check_module_budgets.py
python governance/check_module_docstrings.py
python governance/check_docstrings.py
python scripts/build_catalog.py --check
```

The [maintenance entrypoint](docs/Developer/README.md) routes package, packaging, and documentation proof. The [verified first-adoption case](docs/Developer/Configuration.md#first-adoption-proof) requires explicit bootstrap arguments when the protected base has no governance; Git-dependent ratchets additionally need the real base ref and PR declarations; isolated passing commands do not establish merge readiness.

## Review and failures

Read [.github/copilot-instructions.md](.github/copilot-instructions.md) for the shared review standard. Read a failed gate's output and fix its named cause. An incorrect gate is corrected separately, never bypassed.

Next: [configuration](docs/Developer/Configuration.md), [package agent workflow](docs/Developer/Agent-Workflow.md), or [setup readiness](SETUP.md).
