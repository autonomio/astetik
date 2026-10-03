# Maintainers

Mikko Kotila (`mikkokotila`) is the primary maintainer. He owns product scope, issue priority, security triage, release approval, and merge decisions subject to the [constitution](CLAUDE.md). The existing author contact is `mailme@mikkokotila.com`; [SECURITY.md](SECURITY.md) owns the verified private reporting route.

`bit-mis` is the independent code owner for enforcement surfaces, with repository write access verified on 2026-10-02. The configured approving authority is `mikkokotila`; both the primary maintainer and recovery backup `EnergyGuy3` had GitHub administrator permissions independently verified on 2026-10-02. The primary maintainer's own PR requires an eligible independent owner approval; advisory Copilot review does not replace it. `EnergyGuy3` remains the release/PyPI recovery backup, without a required PR-review or signing-approval role.

## Continuity

On 2026-10-02, the maintainer confirmed that `EnergyGuy3` can recover Astetik release and PyPI access within one week if the primary maintainer becomes unavailable. The remaining administrator can manage issues and accept proposed changes; retain an eligible contributor and independent reviewer for protected changes, then use the reviewed [release procedure](docs/Developer/Making-Release.md). Loss of the backup leaves the primary maintainer's existing responsibilities and access in place.

Keep backup access, release environment eligibility, publisher access, and any necessary credentials and legal rights available to the continuing maintainer. Recover or rotate credentials through their owning platform, without placing secrets in this repository or weakening branch protection. Reconfirm this path when roles, publishers, credentials, or governance change.

The recovery capability is a maintainer attestation, distinct from the independently verified GitHub permissions. No recovery drill is claimed. Operational backup access does not establish that two people have equal knowledge of the compiler.

## Security competence

On 2026-10-02, Mikko Kotila confirmed knowledge of secure design principles and common coding security errors. The [assurance case](docs/Developer/Security-Assurance-Case.md) records how those principles apply to this code and where its guarantees end. This is a maintainer attestation; it does not claim an external course certificate or independent security review.

Live approval enforcement and publication readiness require [SETUP.md](SETUP.md) verification. Adding or changing maintainers updates policy, configuration, CODEOWNERS, and access evidence together.

Next: [governance](GOVERNANCE.md), [security](SECURITY.md), or [contributing](CONTRIBUTING.md).
