# Governance activation

This runbook owns the transition from Astetik's local governance adoption to verified remote enforcement. It does not authorize that transition. Astetik is an existing repository; do not run the template bootstrap against its scientific package merely to activate settings. The retained manual bootstrap requires dispatch from `master` and an exact repository confirmation; those guards are not authorization.

The initial read-only audit found missing protection and broad Actions defaults. Authorized activation on 2026-10-01 established live `Protect-Master` ruleset `24307128`, recorded it in `RULESET_ID`, and passed the full privileged comparison including an empty `bypass_actors` list. Actions defaults are now read-only with PR approval disabled and full SHA pins required. Allowed actions are GitHub-owned actions and the exact workflow pins for the uv installer, Scorecard, and PyPI publisher. Secret scanning and push protection are enabled. `governance` and `release` require an eligible reviewer, prevent self-review, and accept only `master`; `pypi` applies the same review controls to `v*` tags. The repaired publisher runs on `master`; this existing tag-only policy blocks its deployment and must be reconciled before activation. The `master`-only `ruleset-audit` environment is created. `RULESET_AUDIT_TOKEN` was verified visible to Astetik as an organization secret on 2026-10-01, with no same-named repository or environment override; the actual protected-master privileged audit [run 36969583756](https://github.com/autonomio/astetik/actions/runs/36969583756) subsequently passed the complete comparison, including bypass actors, on 2026-10-02. That success proves the credential could perform this audit; it does not disclose its permission flags. Required PR62 CI and independent review completed before merge; later candidates require their own checks and review. Automatic Copilot requests are advisory; release/publication opt-in variables remain unset.

## Prerequisites

- Explicit human authorization for remote configuration and writes.
- Repository administration access and an authenticated GitHub CLI.
- All local policy, configuration, workflow, packaging, and documentation checks passed on the exact candidate.
- A separately reviewed adoption PR; preserve the existing scientific runtime and the current working branch until authorized otherwise.

[governance.yml](governance.yml) names the exact authority, secrets, variables, and required contexts. Do not rename them independently from workflows and contract tests.

## Declared remote requirements

| Requirement | Purpose | Verification boundary |
| --- | --- | --- |
| GitHub Actions | Run the required checks | Actual successful runs; explicitly review write-token/PR-approval defaults, allowed-action policy, and SHA-pinning policy before activation |
| `governance` environment | Protect manual labels/ruleset activation | Establish human approval and branch protections for the confirmed `master` dispatch |
| CodeQL availability | Required Python security analysis | Public-repository availability or appropriate security entitlement; an actual run |
| Automatic Copilot request | Advisory review independently of required human approval | Verify the live auto-request rule; service availability and completion are not required status checks |
| `mikkokotila` eligible approval | Declared human authority | `mikkokotila` and independent owner `EnergyGuy3` were verified administrators; recheck eligibility for activation |
| `RULESET_ID` variable | Identify `Protect-Master` | Matches the live ruleset id; never invent a placeholder id |
| `ruleset-audit` environment | Restrict the audit job to `master` | Created with a `master`-only branch policy; organization-secret access is separate from this job restriction |
| `RULESET_AUDIT_TOKEN` organization secret | Share one read-only audit credential across Autonomio repositories | Metadata read only; the exact credential must expose `bypass_actors` and pass the complete audit |
| `REPO_BOOTSTRAP_TOKEN` secret | Template bootstrap operations | Needed only if separately authorized bootstrap is intentionally used; not required for ordinary Astetik PRs |
| `.github/labels.json` | Source-controlled issue-label manifest | Validate the local semantic-color manifest; no external label-source repository is required |
| `RELEASE_ENABLED` variable | Opt in to tag/release creation | Leave unset until remote governance and release readiness are proven |
| `PYPI_PUBLISH_ENABLED` variable | Opt in to publication | Leave unset until publisher and release readiness are proven |
| `release` environment | Protect tag/release creation | Explicit approval/branch protections for the authorized release |
| `pypi` environment and PyPI trusted publisher | OIDC upload identity | Exact repository/workflow/environment registration and environment protections |

The retained manual workflow applies local labels, the reviewed ruleset, and its variable; it does not create a PR or rewrite package source. Its PAT/GitHub App credential requires Issues write for labels, Administration write for rulesets, Variables write for `RULESET_ID`, and Metadata read, scoped to this repository. The built-in `GITHUB_TOKEN` cannot administer rulesets. Do not inherit the template's broader PR/workflow/source-write scopes for operations this workflow does not perform.
The audit makes only read requests. GitHub documents **Metadata: Read** as the minimum token permission for getting a repository ruleset, and separately restricts `bypass_actors` visibility to callers with write access to the ruleset. These are separate conditions: the endpoint documentation does not prove that a restricted token exposes that field. Start with a Metadata-only token created by a verified administrator and test the exact credential. [GitHub ruleset API](https://docs.github.com/en/rest/repos/rules#get-a-repository-ruleset)

Do not grant Administration write by default to this persistent audit credential. That permission allows changing protection and can authorize deleting the selected repository; repository scoping does not remove those capabilities. If the restricted token cannot observe `bypass_actors`, leave the complete audit blocked and obtain a separately reviewed credential design. Never treat a hidden field as an empty bypass list. [GitHub repository deletion permissions](https://docs.github.com/en/rest/repos/repos#delete-a-repository)

## Audit token setup

1. Open [the prefilled organization-wide token form](https://github.com/settings/personal-access-tokens/new?name=Autonomio%20ruleset%20audit&description=Read-only%20ruleset%20audit%20for%20Autonomio%20repositories&target_name=autonomio&expires_in=none&metadata=read). Verify resource owner `autonomio` and **Metadata: Read** only; leave Administration and all other permissions unselected. The form requests no expiration, subject to organization policy. A personal token remains tied to its creator even when its resource owner is the organization.
2. Under **Repository access**, choose **All repositories** for one Autonomio-wide setup. GitHub does not support prefilling that selection. Generate the token using a verified repository administrator's account; complete organization approval if GitHub marks it pending. [GitHub token instructions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
3. Test the exact token locally with `privileged_ruleset_audit.py` before installing it. The complete audit must succeed and observe the actual `bypass_actors`; HTTP 200 alone is insufficient. The retained successful privileged run proves complete visibility for the installed credential on that run; renewed credentials need their own proof. If the field is hidden, stop without broadening permissions.
4. After successful verification, open [Autonomio's organization secret form](https://github.com/organizations/autonomio/settings/secrets/actions/new). Name it `RULESET_AUDIT_TOKEN`, enter only the raw generated token without quotes or `Bearer`, and choose **All repositories** as its access policy. Organization-owner access is required. Create the secret once; updating it updates the shared credential. Avoid a same-named repository or environment secret, which would override it. Organization secrets are unavailable to private repositories on GitHub Free. [GitHub organization-secret instructions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets#creating-secrets-for-an-organization)
5. Once the updated audit workflow is available on `master`, run it and retain a successful complete comparison. Each repository still needs its own ruleset id and audit workflow; token and secret creation are shared. Renew the organization secret when its credential expires or is revoked.

In a local zsh terminal, this prompt keeps the token out of shell history and command arguments:

```bash
read -s 'astetik_audit_token?Audit token: '
GH_TOKEN="$astetik_audit_token" .venv/bin/python governance/privileged_ruleset_audit.py --ruleset-file .github/rulesets/master.json --repo autonomio/astetik --ruleset-id 24307128 --output-dir output/governance/token-audit
unset astetik_audit_token
```

An administrator can instead use the interactive CLI prompt without placing the token in a command argument:

```bash
gh secret set RULESET_AUDIT_TOKEN --org autonomio --visibility all
```

Never print credential values or put them in issues, documentation, or commits.

## Activation procedure

1. Inspect the exact local candidate and run its declared checks. Verify the eleven laws, ten required contexts, configuration, and `Protect-Master` snapshot agree.
2. Read live repository settings, rulesets, collaborator access, Actions permissions, environments, variables, enabled security features, and publisher registration. Record missing prerequisites; a local snapshot is not evidence that settings are active.
3. Confirm one eligible non-author human/code-owner approval and approval of the latest reviewable push can be obtained independently of advisory Copilot review. An author cannot approve their own PR; administrator access alone does not satisfy that review.
4. Once explicitly authorized, establish only the missing secrets/variables/environments/settings and apply the reviewed snapshot. Reconcile broad Actions defaults with the adopted least-privilege policy; checked-in action SHA pins and workflow permissions apply to these workflows, not the repository-wide live settings. Record the actual ruleset id in `RULESET_ID`.
5. Verify live protection against [.github/rulesets/master.json](.github/rulesets/master.json), including `bypass_actors`, strict up-to-date checks, required reviews, all ten contexts, no force-push, and no branch deletion.
6. Verify a real authorized PR receives all required checks and review requirements. Confirm all ten required contexts succeed, `pr_checks_honesty` checks the laws/configuration/ruleset bijection, and `pr_checks_ruleset` passes. Verify human/code-owner and latest-push approvals, resolved review threads, and complete protection visibility for the privileged post-merge audit.
7. Activate release or publication only through the separate [release readiness procedure](docs/Developer/Making-Release.md). Do not infer a published release from a successful static build.

Read-only examples, substituting the actual repository coordinates when necessary:

```bash
gh api repos/autonomio/astetik/rulesets
gh api repos/autonomio/astetik/collaborators/mikkokotila/permission
gh variable list --repo autonomio/astetik
gh secret list --repo autonomio/astetik
```

These commands inspect configuration names and access; they do not expose secret values or activate anything.

## Failure handling

| Symptom | Meaning and response |
| --- | --- |
| Required checks absent | Verify trigger branches, Actions availability, workflow permissions, and token-trigger behavior; do not declare readiness |
| `RULESET_ID` absent or stale | Establish the actual live id after authorized activation |
| Audit cannot read `bypass_actors` | Keep the audit blocked; verify caller eligibility, repository selection, token approval/expiration and the exact response. Do not add Administration write automatically |
| Human approval does not count | Reviewer lacks write access, is the PR author, or violates live review rules |
| Copilot review unavailable, quota exhausted, or file limit exceeded | Advisory review is unavailable; this does not add a required gate or satisfy human approval. Keep all ten required contexts, human/code-owner and latest-push approvals, and thread resolution in force |
| CodeQL unavailable | Reconcile law, config, workflow, snapshot, and tests in a separately authorized change; never remove one surface alone |
| Upload or attestation unverified | Leave publication disabled; do not claim release provenance |

Next: [constitution](CLAUDE.md), [configuration](docs/Developer/Configuration.md), or [release policy](docs/Developer/Release-Policy.md).
