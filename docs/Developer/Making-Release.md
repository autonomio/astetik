# Making a release

This page owns the release sequence after the controls in [Release Policy](Release-Policy.md) are satisfied. It does not authorize a release during local governance adoption.

## Prerequisites

- Authorized automatic publication policy; a manual recovery dispatch requires human authorization.
- Verified remote readiness from [SETUP.md](../../SETUP.md).
- Reviewed `master` commit with matching project version, changelog, and citation version.
- Packaging, installed-wheel, scientific, governance, and documentation evidence on the exact candidate.
- A previously unused version and valid publisher/environment configuration for any upload.

## Procedure

1. Inspect the candidate version, newest changelog section, tag history, and index history. Stop if a version was already tagged or any filename accepted.
2. Verify `release` and `pypi` permit only the exact `master` branch and have no additional job reviewers. Preserve all required PR checks, independent code-owner approval, latest-push approval, and resolved review threads.
3. `RELEASE_ENABLED=true` enables automatic GitHub release files. `PYPI_PUBLISH_ENABLED=false` keeps the separately rejected index upload inactive; a matching PyPI publisher permits later activation. These settings are not approvals repeated for each release.
4. After an approved merge, `Automated Release` derives the tag and notes from reviewed source. Its successful completion triggers publication of that exact release commit. The publisher validates the stable tag, release, and protected history before executing project source. Follow [Release Policy](Release-Policy.md#declared-controls) for the complete automatic sequence; no further approval button is required.
5. Verify the actual tag, commit, release status, wheel/sdist digests, public signature bundle, [release-source signature and field comparisons](Release-Policy.md#deliverables-and-boundaries), and accepted index files when that upload is enabled. Complete citation release metadata only when the release date is established.
6. Report actual tag, commit, release, artifacts, and verification results. Leave an unproven step explicitly unresolved.

The unchanged 1.16 distributions use the separately approved [keyless legacy procedure](Release-Policy.md#legacy-distribution-signing). That path adds retrospective signature evidence to the existing release and does not reuse the normal build or PyPI upload path.

## Observable result and failures

Success means an actual authorized release with the exact retained artifact/provenance evidence, not merely a source version or a green skipped job. A missing activation variable, publisher, release/tag match, required PR review, or live rule proof prevents the corresponding step.
For partial upload recovery, follow [release policy](Release-Policy.md#recovery); never reuse a burned version. No reviewer message or publication follows from reading this runbook alone.

Next: [versioning](Semantic-Versioning.md), [packaging](Packaging.md), or [setup readiness](../../SETUP.md).
