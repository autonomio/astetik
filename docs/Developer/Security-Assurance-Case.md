# Security assurance case

This page owns the argument and evidence boundaries for Astetik's security controls. [SECURITY.md](../../SECURITY.md) owns reporting. Local configuration and tests do not establish live enforcement, and no universal security or SLSA claim follows from template adoption.

## Prerequisites and system boundary

Astetik is an installed scientific library that accepts data, JSON-compatible specifications/manifests, and retained evidence bundles; it writes new local artifact directories. It has no maintained hosted account or authentication service.
Security-relevant repository surfaces also include issue/PR parsers, dependency metadata, governance scripts, GitHub workflows, packaging, and documentation configuration.

## Trust boundaries

| Boundary | Untrusted or privileged input | Evidence scope |
| --- | --- | --- |
| Scientific input and bundles | Tables, declarations, paths, retained metadata | Runtime validators, receipt integrity, sealed state, and focused tests |
| Issue/PR bodies | Contributor-authored text | Slice/parser tests and required gate behavior |
| Dependencies | Runtime, build, governance, and documentation packages | Bounds, pinned toolchain, vulnerability checks, reviewed exceptions |
| GitHub Actions | Workflow credentials, events, third-party actions | Permissions, pinned actions, credential handling, and contract tests |
| Release/index | Tag identity, artifacts, OIDC publisher | Opt-in controls, actual release/tag guard, digests, and real attestations |

## Requirements and evidence

| Requirement | Declared control | What local adoption does not prove |
| --- | --- | --- |
| Reviewed source reaches `master` | Eleven laws, ten contexts, `Protect-Master`, human approval plus Copilot | Activated protection, a successful non-author review, or unavailable review entitlements |
| Laws/config/checks agree | `pr_checks_honesty` bijection | That declared checks run or are required on GitHub |
| Live protection matches snapshot | `pr_checks_ruleset`; privileged `audit_master_ruleset` includes bypass actors | Live agreement before credentials and actual checks are verified |
| Known vulnerabilities remain visible | Python pip-audit; time-limited exceptions; zero-advisory production and development npm audits; update workflows | Absence of unknown vulnerabilities or future advisories |
| CI privilege is bounded | Minimum declared permissions, SHA-pinned actions, nonpersistent checkout credentials except justified tag push | Live token scopes, secret contents, or safety of a future workflow alteration |
| Consumers can inspect artifacts | Hatch content audit, double fixed-epoch builds, outside-checkout wheel imports | A reproducible or published artifact until the exact candidate is tested |
| Published artifact identity is verifiable | OIDC opt-in, published-tag guard, digest summary, configured GitHub attestation | Any current attestation, SLSA level, SBOM, or offline provenance bundle |
| Arbitrary issue text is handled | Hypothesis parser contracts in governance tests | Coverage of unrelated scientific or binary parsing surfaces |
| Static defect classes are checked | Required CodeQL, pinned Ruff/Pyright, measured ratchets | Complete semantic correctness or absence of unknown defect classes |

## Verification procedure

1. Run the current package/governance tests and the affected gate on the exact candidate.
2. Inspect configured budgets, exemptions, workflow permissions, action references, artifact content, and documentation audit thresholds.
3. For activation, verify live ruleset, bypass actors, access, secrets/variables, check runs, and review eligibility through [SETUP.md](../../SETUP.md).
4. For release provenance, verify the actual published artifact through [Release Policy](Release-Policy.md).
5. Retain the evidence and report missing proofs precisely; do not turn a configured capability into a completed fact.

```bash
python -m pytest tests governance/tests -q
gh api repos/autonomio/astetik/rulesets
```

The first exercises local contracts. The second lists remote declarations only; a full privileged comparison is required to establish enforcement. Verification commands are not permission to change live settings.

## Residual risks

The strict typing and lint baselines are zero after verified repair; module shape has the restored template ceiling. The adopted product test-density threshold remains explicitly recorded in the technical-debt register. Property tests explore bounded/generated input spaces and do not substitute for a coverage-guided native fuzzing claim. Runtime input validation and receipt checks do not prove the researcher's sampling, independence, causal interpretation, or study validity.
Authorized activation hardened the live Actions defaults: read-only token, PR approval disabled, selected fully pinned actions, and protected environments. The privileged live ruleset comparison passed, including its empty bypass list. Successful required CI, independent review, and the persistent audit credential remain separate proofs. [SETUP.md](../../SETUP.md) owns the verified activation state and remaining prerequisites.
A static site build does not prove deployed headers, redirects, availability, or transport policy. Maintainer continuity and eligible independent owner review remain operational responsibilities; `mikkokotila`'s own PR needs another eligible owner such as verified administrator `EnergyGuy3`, and self-approval cannot satisfy the ruleset.

Next: [security policy](../../SECURITY.md), [release policy](Release-Policy.md), or [maintenance](README.md).
