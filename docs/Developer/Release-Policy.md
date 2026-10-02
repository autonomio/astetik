# Release policy

This page owns release controls. [Making a Release](Making-Release.md) owns the operational procedure. This local adoption does not establish a published 2.0 release or activate a publisher.

## Prerequisites and version identity

Require explicit human authorization, verified remote governance, eligible approval, passing candidate checks, and maintainer authority over the release and PyPI project. [Semantic Versioning](Semantic-Versioning.md) owns the bump.
A version ever tagged or uploaded is never reused. A deleted PyPI release is not proof that its filenames are available; bump past a partially accepted upload.

## Declared controls

| Control | Configured mechanism | Readiness proof |
| --- | --- | --- |
| Reviewed source | `Protect-Master` and ten contexts | Activated live ruleset and actual passing PR |
| Tag/release enablement | `RELEASE_ENABLED == 'true'` on `master`, protected `release` environment | Explicitly authorized repository variable |
| Version/tag | `scripts/create_release.py`, `v<project.version>` | Exact tag resolves to intended reviewed commit |
| Release notes | Newest matching changelog section plus computed traceability | Reviewed source text; no release-time model authorship |
| PyPI enablement | `PYPI_PUBLISH_ENABLED == 'true'` | Verified repository variable and publisher readiness |
| Published-tag guard | A published stable GitHub release, strict version tag at HEAD, and ancestry on protected `master` | Actual release/tag/commit agreement before building |
| Upload identity | OIDC trusted publisher in the `pypi` environment | Verified repository/workflow/environment registration |
| Artifact identity | Fixed-epoch builds, digest summary, configured GitHub attestation | Successful exact-candidate build and retained published evidence |

Both enablement variables remain inactive unless explicitly configured. The template's automatic merge-to-release behavior is adapted behind release opt-in; a successful but skipped release job must not publish untagged source.

## Deliverables and boundaries

The configured publish path builds a wheel and sdist, creates GitHub build-provenance attestations, and records artifact SHA-256 digests in the run summary before OIDC upload. These are workflow capabilities, not proof that any Astetik 2.0 artifacts already carry them.
No SLSA level, CycloneDX SBOM, offline `provenance.intoto.jsonl`, or release-attached asset contract is claimed. Scientific evidence-bundle receipts are application artifacts and do not replace software supply-chain provenance.

For an actually published attested artifact:

```bash
gh attestation verify ARTIFACT --repo autonomio/astetik
```

Compare its SHA-256 with retained publish evidence. A failed or missing attestation blocks a provenance claim; do not invent one in release prose.

## Recovery

Read the actual failed step before retrying. An existing tag makes tag creation idempotent; a partial upload burns the version and requires a new version. Do not blindly rerun the complete publish path for filenames PyPI has accepted.
If only an independent post-upload evidence step failed, repair that step without reuploading existing files. Record the actual outcome and retained artifact identity.

Next: [making a release](Making-Release.md), [packaging](Packaging.md), or [security policy](../../SECURITY.md).
