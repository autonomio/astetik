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

The fixed manual workflow [sign_legacy_release.yml](../../.github/workflows/sign_legacy_release.yml) provides keyless retrospective approval. It requires the reviewed workflow on protected `master`, the unchanged source tag, exact stable release identity, both fixed PyPI URLs and index digests, and matching downloaded bytes. A read-only runner performs that verification in isolated Python. A separate runner under the existing protected `release` environment signs only the retained wheel and sdist with a short-lived Sigstore identity. A third protected runner verifies both signatures and the approval predicate, then attaches those same bytes and their shared bundle to the existing release without replacing assets. It never builds, creates a tag/release, uploads to PyPI, enables a publisher, or requires a local private key.

The custom predicate `urn:autonomio:astetik:legacy-approval:v1` binds the exact artifact URLs, digests and sizes to tag `v1.16`, source commit `11fb4ab8defa2799b0bcc4760620fb715377e93c`, and the trusted approving workflow revision. Its `historical_build_provenance` is explicitly `false`. Signing records approval at execution time; it does not claim a 2024 signature, a signed historical tag, or a reproducible historical build. Signatures remain pending until an actual approved run publishes and verifies them.

After this workflow merges and its checks pass, an authorized maintainer dispatches only the fixed legacy tag:

```bash
gh workflow run sign_legacy_release.yml --repo autonomio/astetik \
  --ref master -f release_tag=v1.16
```

Both signing and asset publication require their existing `release` environment approval. The environment permits only `master` and prevents self-review; retain those controls and never use administrator bypass. An eligible independent approval of the PR's latest push remains a prerequisite for merge. A failed or partial asset upload requires inspection; existing names cause failure because the workflow does not clobber them.

For an actually published bundle, download the unchanged distributions and signature from the existing release. Set `RUN_ID` to the inspected successful approval run and confirm its `headSha` is the reviewed protected workflow revision before verification:

```bash
gh release download v1.16 --repo autonomio/astetik \
  --pattern 'astetik-1.16*'
WORKFLOW_SHA="$(gh run view "$RUN_ID" --repo autonomio/astetik --json headSha --jq .headSha)"
printf '%s  %s\n' \
  850fca54fa5c72b78e1f19c4cf1599d69870bb2a02bc4bf450297a5c317bb835 astetik-1.16-py2.py3-none-any.whl \
  c43fcdc927c66aee498241c1948958e87fc8df8651bd4baf4483510d639859cd astetik-1.16.tar.gz \
  | shasum -a 256 -c -
gh attestation trusted-root > sigstore-trusted-root.jsonl
for artifact in astetik-1.16-py2.py3-none-any.whl astetik-1.16.tar.gz; do
  gh attestation verify "$artifact" --repo autonomio/astetik \
    --bundle astetik-1.16.legacy-approval.sigstore.json \
    --custom-trusted-root sigstore-trusted-root.jsonl --digest-alg sha256 \
    --cert-identity https://github.com/autonomio/astetik/.github/workflows/sign_legacy_release.yml@refs/heads/master \
    --cert-oidc-issuer https://token.actions.githubusercontent.com \
    --source-ref refs/heads/master --source-digest "$WORKFLOW_SHA" \
    --signer-digest "$WORKFLOW_SHA" --deny-self-hosted-runners \
    --predicate-type urn:autonomio:astetik:legacy-approval:v1 \
    --format json > "$artifact.verification.json"
  jq -e --arg workflow "$WORKFLOW_SHA" '
    length == 1 and (.[0].verificationResult.statement.predicate |
      .approval == "retrospective approval of unchanged published distributions" and
      .historical_build_provenance == false and
      .repository == "https://github.com/autonomio/astetik" and .tag == "v1.16" and
      .source_commit == "11fb4ab8defa2799b0bcc4760620fb715377e93c" and
      .workflow_commit == $workflow and
      (.artifacts | keys) == ["astetik-1.16-py2.py3-none-any.whl", "astetik-1.16.tar.gz"] and
      .artifacts["astetik-1.16-py2.py3-none-any.whl"].sha256 == "850fca54fa5c72b78e1f19c4cf1599d69870bb2a02bc4bf450297a5c317bb835" and
      .artifacts["astetik-1.16.tar.gz"].sha256 == "c43fcdc927c66aee498241c1948958e87fc8df8651bd4baf4483510d639859cd")
  ' "$artifact.verification.json"
done
```

Require both checksum checks, both signature verifications and both predicate comparisons to succeed. The CLI recomputes each artifact digest and verifies the signed subject, exact workflow certificate identity, GitHub OIDC issuer, protected execution ref/revision, signature, certificate chain and transparency evidence. The certificate source SHA identifies the approving workflow; the historical source SHA belongs in the signed predicate. Users may download the same wheel/sdist bytes from PyPI. GitHub-generated source archives are distinct bytes outside this approval.

The [Sigstore bundle](https://github.com/actions/attest/blob/daf44fb950173508f38bd2406030372c1d1162b1/README.md) contains the ephemeral public signing certificate, signature and transparency evidence. Inspect its certificate and public key without treating display as verification:

```bash
jq -r '.verificationMaterial.certificate.rawBytes // .verificationMaterial.x509CertificateChain.certificates[0].rawBytes' \
  astetik-1.16.legacy-approval.sigstore.json | base64 --decode \
  | openssl x509 -inform DER -pubkey -text -noout
```

Retrieve trust roots through `gh attestation trusted-root`, using the CLI's authenticated Sigstore trust-root distribution rather than trusting a public key supplied by the release itself. [GitHub CLI verification](https://cli.github.com/manual/gh_attestation_verify) owns the supported flags and verification-result fields. A missing or invalid bundle prevents the signed-release claim.

## Recovery

For manual recovery before any index acceptance, dispatch the publisher from `master` with required input `release_tag=v<version>`. The candidate must match that published stable tag and remain an ancestor of the protected workflow commit. Automatic publication uses the exact successful release workflow SHA; later master commits do not change the selected release.

Read the actual failed step before retrying. An existing tag makes tag creation idempotent; a partial upload burns the version and requires a new version. Do not blindly rerun the complete publish path for filenames PyPI has accepted.
If only an independent post-upload evidence step failed, repair that step without reuploading existing files. Record the actual outcome and retained artifact identity.

Next: [making a release](Making-Release.md), [packaging](Packaging.md), or [security policy](../../SECURITY.md).
