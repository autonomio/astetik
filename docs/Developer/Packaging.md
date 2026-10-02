# Packaging

This page owns what Astetik distributions contain and how packaging proof differs from source-tree tests. Astetik uses `hatchling.build`; the template's setuptools archive-normalization backend is not adopted.

## Prerequisites

Use a clean candidate, Python 3.13 for packaging governance, and the hash-pinned build/packaging toolchains:

```bash
python -m pip install --require-hashes -r requirements/ci/build-tools.txt
python -m pip install --require-hashes -r requirements/ci/packaging-tools.txt
python -m pip install --require-hashes -r requirements/ci/gate-tools.txt
```

## Artifact boundary

The sdist is a consumer source-inspection bundle: runtime source/assets, public documentation, tests, required metadata, and license notices. It is not a full repository snapshot. Governance scripts, `.github/`, `docs-site/`, fuzzing machinery, and repository build scripts are enforcement sources, excluded from the consumer distribution.
The wheel contains the installed `astetik` package and package-level assets/docs, including the actual country metadata and Finlandica font/license. Repository tests and governance machinery are excluded.

[pyproject.toml](../../pyproject.toml) defines Hatch's actual include/exclude rules. `scripts/package_audit.py` checks required metadata paths, forbidden enforcement prefixes, and dependency bounds. A Markdown link to a repository policy does not imply that its target ships inside a wheel.

## Dependencies and reproducibility

Declared runtime and optional dependencies must have lower and upper bounds or an exact pin. Human-readable `requirements/constraints.txt` and `requirements/ci/*.in` describe tool envelopes; compiled `*.txt` sets are hash-pinned CI inputs.

```bash
SOURCE_DATE_EPOCH=1704067200 python -m build --outdir dist-first
SOURCE_DATE_EPOCH=1704067200 python -m build --outdir dist-second
```

Compare every wheel and sdist digest between the two builds. Hatch's source-date handling supplies the archive contract; no custom setuptools `build_backend.py` or `MANIFEST.in` claim applies here. Reproducibility is established by matching artifacts from the exact candidate, not by the backend's name.

## Required packaging proof

The configured `pr_checks_packaging` workflow:

1. Builds twice under a fixed source epoch and requires nonempty byte-identical artifact sets.
2. Audits distribution paths and dependency bounds.
3. Runs metadata/manifest checks and the configured Pyroma threshold.
4. Installs the actual wheel on supported product interpreters, imports from outside the checkout, checks installed metadata against `astetik.__version__`, and runs dependency consistency checks.

Packaging/install workflows are advisory in the required-status configuration, not one of the ten merge-gate annotations. Their results still form release readiness evidence; do not substitute an in-checkout source import for an installed-wheel test.

Failures require correcting metadata, Hatch content rules, bounded dependencies, or runtime installation. Never weaken archive checks to conceal an omitted asset.

Next: [release policy](Release-Policy.md), [making a release](Making-Release.md), or [maintenance](README.md).
