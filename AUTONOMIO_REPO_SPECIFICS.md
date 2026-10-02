# Astetik repository specifics

This appendix to [AUTONOMIO_PR_GUIDELINE.md](AUTONOMIO_PR_GUIDELINE.md) owns repository-specific routing. It applies only to Astetik after reading [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md), not to other Autonomio projects.

## Authority and remote boundaries

- `[repo:review-authority]` `mikkokotila` is the declared human authority, verified as administrator during adoption; `bit-mis` is the independent code owner for enforcement surfaces, with repository write access verified on 2026-10-02. `EnergyGuy3` remains the verified administrator and recovery backup without a required review role. The operator's own PR requires an eligible independent owner approval and approval of the latest reviewable push. Automatic Copilot review requests are advisory and do not replace required approval or thread resolution.
- `[repo:activation]` Local standards are adopted; live branch protection, secrets, workflows, and publishers require [SETUP.md](SETUP.md) readiness evidence before activation.
- `[repo:protected-branch]` The protected base is `master`; its declared snapshot is `.github/rulesets/master.json`, named `Protect-Master`.
- `[repo:slice]` PRs satisfy the exact slice title, surfaces, exclusions, significance blocks, and Done Means required by the constitution.
- `[repo:messages]` Do not contact reviewers or post findings without human authorization.
- `[repo:acp]` Bash is hook-checked; other tools require `acp_check` approval before invocation, except the ACP meta-tools.

## Product and toolchain

- `[repo:runtime]` Astetik is a Hatch library with an installed Python floor of 3.11; the governance interpreter is 3.13. Product tests are in `tests/`; gate tests are in `governance/tests/`.
- `[repo:scientific-work]` Use the [agent workflow](docs/Developer/Agent-Workflow.md): finite declarations, centralized immutable design, explicit computation, sealed results, and bounded replay.
- `[repo:data]` Use actual retained metadata or user-owned observations. The bundled country/area snapshot is historical metadata, not current ISO authority or empirical research measurements.
- `[repo:provenance]` Preserve original-row mark origins and verified preparation receipts. Never loosen evidence checks to conceal a runtime defect.
- `[repo:manifest]` Figure design follows the centralized manifest and attached Autonomio style guide; web pixel geometry does not set publication figure size.

## Verification and documentation

- `[repo:ratchets]` Read actual configured budgets and the real protected base; no new escape hatches or narrowed scan surface.
- `[repo:docs]` Author product claims once in canonical Markdown and map maintained public sources in `docs-site/docs-map.json`.
- `[repo:policy-corpus]` Root governance and metadata files are repository policy sources outside the public docs map; the public maintenance page links them. Developer workflow pages are mapped.
- `[repo:release]` Publication is separately opt-in. No local adoption result establishes a release, publisher identity, attestation, SLSA level, or hosted site.

Next: [maintenance](docs/Developer/README.md), [configuration](docs/Developer/Configuration.md), or [release policy](docs/Developer/Release-Policy.md).
