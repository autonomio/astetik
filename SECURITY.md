# Security policy

This policy covers Astetik runtime code, evidence readers/writers, dependencies, governance scripts, workflows, packaging, and maintained documentation configuration. Astetik is a local scientific library, not a hosted account service.

## Supported source

Security work targets the current maintained source and the latest release maintainers explicitly support. Version `2.0.1` identifies this checkout; this document does not assert that it has been published or that historical releases receive fixes.

## Private reporting

No dedicated security inbox or enabled private-advisory channel has been verified by this adoption.
Use GitHub private vulnerability reporting only when the repository visibly offers it. Otherwise contact the [maintainer](MAINTAINERS.md) through the existing author contact to arrange a private channel before sending sensitive technical details. Do not put exploitable details or credentials in public issues.

A private report should include the affected version or commit, reproduction steps, expected impact, and logs or evidence safe to disclose to that recipient. Reporter attribution is agreed with the reporter when the fix is published.

## Verification and limits

The [assurance case](docs/Developer/Security-Assurance-Case.md) separates local controls, proposed remote enforcement, and residual risks. Dependency exceptions require a reason and expiry; a passing vulnerability check is limited to its database and declared scope.

The configured publication workflow can produce GitHub build-provenance attestations and artifact SHA-256 summaries after authorized activation. No such attestation, SLSA level, SBOM, offline provenance bundle, or published 2.0 artifact is established by this local adoption.
For an actually attested artifact, verification is:

```bash
gh attestation verify ARTIFACT --repo autonomio/astetik
```

Use [release policy](docs/Developer/Release-Policy.md) to interpret provenance and publication boundaries; scientific bundle receipts are a separate application contract.

Next: [support](SUPPORT.md) or [security assurance](docs/Developer/Security-Assurance-Case.md).
