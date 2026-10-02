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
| Published-tag guard | Trusted workflow on `master`; isolated validation pins the selected release SHA/tag and proves ancestry in protected master history | Actual release/tag/commit agreement before project execution |
| Upload identity | OIDC trusted publisher in the `pypi` environment | Verified repository/workflow/environment registration |
| Artifact identity | Fixed-epoch builds, digest summary, signed release-source identity | Successful exact-candidate build and retained published evidence |

Both enablement variables remain inactive unless explicitly configured. The live `pypi` environment currently permits tags only, while this workflow executes on `master`; reconcile that policy and verify the exact trusted publisher before activation. The template's automatic merge-to-release behavior is adapted behind release opt-in; a successful but skipped release job must not publish untagged source.

## Deliverables and boundaries

The configured publish path builds a wheel and sdist with read-only permissions and records SHA-256 digests. A separate runner downloads same-run artifacts and signs GitHub attestations binding artifact digests to the verified release source without checking out or executing project source. Protected PyPI publication depends on that signing job; the publisher also creates its index attestations. These are workflow capabilities, not proof that any Astetik 2.0 artifacts already carry them.
No SLSA level, CycloneDX SBOM, offline `provenance.intoto.jsonl`, or release-attached asset contract is claimed. Scientific evidence-bundle receipts are application artifacts and do not replace software supply-chain provenance.

For an actually published attested artifact:

```bash
gh attestation verify ARTIFACT --repo autonomio/astetik \
  --signer-workflow autonomio/astetik/.github/workflows/pr_publish_pypi.yml \
  --source-ref refs/heads/master \
  --predicate-type urn:autonomio:astetik:release-source:v1 --format json
```

Compare its SHA-256 with retained publish evidence. Inspect `verificationResult.statement.predicate`: `repository`, `commit` and `tag` must identify the expected release; `workflow_commit` identifies the trusted master workflow revision. The certificate source SHA identifies that workflow revision and can differ from the released source SHA. Signature verification authenticates the statement; it does not independently establish these release semantics. A failed or missing attestation blocks a provenance claim; do not invent one in release prose.

## Legacy distribution signing

The latest published PyPI version is 1.16 from 2024-04-20. Its retained wheel and source distribution match the index SHA-256 values, and all 55 package files match tag `v1.16` at `11fb4ab8defa2799b0bcc4760620fb715377e93c`. This comparison does not establish a reproducible historical build.

The existing maintainer OpenPGP primary fingerprint is `7814DF8A4969D30D2EBD795B2DBB46FE27DFCA48`, with identity `Mikko Kotila <mailme@mikkokotila.com>`, matching project metadata and that release's author. Private signing material stays on the maintainer's local machine, separate from GitHub and PyPI distribution. Its use requires the maintainer to unlock the existing key; no new signing identity or copied private key is needed.

For retrospective approval, sign the unchanged index artifacts, then attach their detached signatures, public key, checksums and verification instructions to the existing release. Such signatures record approval at signing time. They do not claim signing in 2024, sign the old Git tag, or establish historical build provenance. The signatures remain pending until this procedure succeeds; unsigned legacy bytes must not be presented as signed.

Once those assets are actually present, users retrieve the public key and signatures from the release and confirm the full fingerprint against this reviewed policy:

```bash
gh release download v1.16 --repo autonomio/astetik \
  --pattern 'astetik-1.16*' --pattern maintainer-public-key.asc --pattern SHA256SUMS
gpg --show-keys --with-fingerprint maintainer-public-key.asc
# Confirm the full primary fingerprint above before importing.
gpg --import maintainer-public-key.asc
gpg --verify astetik-1.16-py2.py3-none-any.whl.asc astetik-1.16-py2.py3-none-any.whl
gpg --verify astetik-1.16.tar.gz.asc astetik-1.16.tar.gz
shasum -a 256 -c SHA256SUMS
```

Both signatures must verify for that full fingerprint, and both checksums must report `OK`. Users may instead download the wheel/source from PyPI and verify the same detached signatures. The expected SHA-256 values are `850fca54fa5c72b78e1f19c4cf1599d69870bb2a02bc4bf450297a5c317bb835` for the wheel and `c43fcdc927c66aee498241c1948958e87fc8df8651bd4baf4483510d639859cd` for the source distribution. GitHub-generated source archives are distinct bytes and are outside these signatures.

## Recovery

For manual recovery before any index acceptance, dispatch the publisher from `master` with required input `release_tag=v<version>`. The candidate must match that published stable tag and remain an ancestor of the protected workflow commit. Automatic publication uses the exact successful release workflow SHA; later master commits do not change the selected release.

Read the actual failed step before retrying. An existing tag makes tag creation idempotent; a partial upload burns the version and requires a new version. Do not blindly rerun the complete publish path for filenames PyPI has accepted.
If only an independent post-upload evidence step failed, repair that step without reuploading existing files. Record the actual outcome and retained artifact identity.

Next: [making a release](Making-Release.md), [packaging](Packaging.md), or [security policy](../../SECURITY.md).
