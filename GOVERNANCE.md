# Governance

Astetik is an Autonomio scientific Python library maintained by Mikko Kotila.
Maintainers decide product scope, issue priority, release timing, and contribution acceptance.

[CLAUDE.md](CLAUDE.md) owns the eleven laws and ten required workflow gates.
[governance.yml](governance.yml) and [.github/budgets.json](.github/budgets.json) own configuration and ratchets; [.github/rulesets/master.json](.github/rulesets/master.json) declares the intended protected-branch rules.
A maintainer cannot waive a failed gate. Law, configuration, and ruleset changes belong in one separately scoped change with matching proof.

## Authority and adoption

The approving authority is `mikkokotila`, verified as repository administrator during adoption. The template's `zero-bang` account has read access here and cannot provide the required write-access approval.
`EnergyGuy3` is also a verified administrator/code owner. Human approval and a completed current-head Copilot review are independent requirements under [the honesty contract](docs/Developer/Configuration.md#gate-controls); the primary operator's own PR requires an eligible independent owner approval, never self-approval.

This checkout adopts local policy and verification machinery. It does not establish that live branch protection, secrets, release enablement, or publisher identity are activated. [SETUP.md](SETUP.md) owns that readiness boundary.
Human task authorization remains necessary for remote writes, messages, releases, and settings changes.

## Decision records

Record material decisions in issues, pull requests, reviewed documentation, or release notes. Never describe a local candidate as merged, deployed, attested, or published without the corresponding evidence.

Next: [maintainers](MAINTAINERS.md), [contribution](CONTRIBUTING.md), or [security](SECURITY.md).
