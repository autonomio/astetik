# Making a release

This page owns the release sequence after the controls in [Release Policy](Release-Policy.md) are satisfied. It does not authorize a release during local governance adoption.

## Prerequisites

- Explicit human authorization for tag, GitHub release, and any PyPI upload.
- Verified remote readiness from [SETUP.md](../../SETUP.md).
- Reviewed `master` commit with matching project version, changelog, and citation version.
- Packaging, installed-wheel, scientific, governance, and documentation evidence on the exact candidate.
- A previously unused version and valid publisher/environment configuration for any upload.

## Procedure

1. Inspect the candidate version, newest changelog section, tag history, and index history. Stop if a version was already tagged or any filename accepted.
2. Configure the `release` environment's protections, then enable `RELEASE_ENABLED` only when activation is authorized and ready. The configured `Automated Release` workflow runs on `master` and derives its tag and notes mechanically from reviewed source.
3. Verify the resulting tag, commit, GitHub release status, and retained workflow evidence. An existing tag is a tag-creation skip, not evidence of a newly published release.
4. Enable `PYPI_PUBLISH_ENABLED` only after the exact `pypi` environment and PyPI trusted publisher are verified. Its workflow executes only from protected `master`, selects the upstream release SHA or required manual `release_tag`, and validates it in isolated Python before project execution. The candidate must match the published stable version tag, identify the exact upstream release when present, and be an ancestor of the trusted workflow commit on master history. Align the protected `pypi` environment with the actual master execution ref before activation; the existing tag-only policy blocks it.
5. Verify wheel/sdist identity, artifact digest summary, actual GitHub release-source attestations using the [specified verifier and field comparisons](Release-Policy.md#deliverables-and-boundaries), and the index's accepted files. Complete citation release metadata only when the release date is established.
6. Report actual tag, commit, release, artifacts, and verification results. Leave an unproven step explicitly unresolved.

## Observable result and failures

Success means an actual authorized release with the exact retained artifact/provenance evidence, not merely a source version or a green skipped job. A missing variable, publisher, release/tag match, required review, or live rule proof prevents the corresponding step.
For partial upload recovery, follow [release policy](Release-Policy.md#recovery); never reuse a burned version. No reviewer message or publication follows from reading this runbook alone.

Next: [versioning](Semantic-Versioning.md), [packaging](Packaging.md), or [setup readiness](../../SETUP.md).
