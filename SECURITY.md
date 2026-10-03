# Security policy

This policy covers Astetik runtime code, evidence readers/writers, dependencies, governance scripts, workflows, packaging, and maintained documentation configuration. Astetik is a local scientific library, not a hosted account service.

## Supported source

Security work targets the current maintained source and the latest release maintainers explicitly support. Version `2.0.3` identifies this checkout; this document does not assert that it has been published or that historical releases receive fixes.

## Private reporting

Report vulnerabilities through [GitHub private vulnerability reporting](https://github.com/autonomio/astetik/security/advisories/new), verified enabled on 2026-10-02. If that route is unavailable, contact the [maintainer](MAINTAINERS.md) to arrange a private channel before sending sensitive details. Do not publish exploitable details or credentials in issues.

Include the affected version or commit, reproduction steps, impact, and logs or evidence safe to disclose. Maintainers keep the report private while coordinating a fix and agree on attribution with the reporter, including anonymity when requested.

## Response procedure

Effective 2026-10-02, maintainers use this process for each vulnerability report:

1. Acknowledge receipt within 14 calendar days. Record the affected source/release, reporter contact, requested confidentiality, and an owner in the private advisory. If the primary maintainer is unavailable, use the [backup continuity path](MAINTAINERS.md#continuity).
2. Reproduce the report, identify affected versions and trust boundaries, and assess exploitability and severity. Record why a report is inapplicable or a dependency issue is unexploitable; a clean scanner result alone does not settle the report.
3. Give critical vulnerabilities immediate priority. Fix every known medium-or-higher vulnerability within 60 calendar days of becoming known, including a security update to the supported release or a documented safe upgrade path. Develop a mitigation promptly when a complete repair takes longer; a mitigation does not erase the repair deadline.
4. Add a meaningful regression test, run the relevant package and security checks, and review the repair through the protected contribution process. Coordinate disclosure timing with the reporter and affected downstream maintainers without exposing private reproduction details prematurely.
5. Publish the reviewed fix, affected-version guidance, and advisory when safe to disclose. Credit each reporter unless they requested anonymity. Verify that the distributed repair matches its documented source and signing evidence, then close the advisory with retained verification and follow-up actions.

These are prospective response obligations. On 2026-10-02 the maintainer confirmed no private vulnerability reports in the preceding 12 months, and the repository advisory inventory was empty. This dated record does not establish a past response-time measurement; update it when reports are resolved.

## Verification and limits

The [assurance case](docs/Developer/Security-Assurance-Case.md) separates local controls, proposed remote enforcement, and residual risks. Dependency exceptions require a reason and expiry; a passing vulnerability check is limited to its database and declared scope.

The configured publication workflow can sign release-source statements binding artifact SHA-256 digests to reviewed source after authorized activation. These custom attestations do not establish SLSA build provenance. No completed attestation, SLSA level, SBOM, offline provenance bundle, or published 2.0 artifact is established by this local adoption.

For an actually attested artifact, use the [release-policy verifier](docs/Developer/Release-Policy.md#deliverables-and-boundaries) and compare its signed source fields. The [legacy verifier](docs/Developer/Release-Policy.md#legacy-distribution-signing) applies separately to retrospective approval of unchanged 1.16 artifacts. Failed or missing signature, identity or predicate checks block the claim; scientific bundle receipts are a separate application contract.

Next: [support](SUPPORT.md) or [security assurance](docs/Developer/Security-Assurance-Case.md).
