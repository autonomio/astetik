# Governance activation

This runbook owns the transition from Astetik's local governance adoption to verified remote enforcement. It does not authorize that transition. Astetik is an existing repository; do not run the template bootstrap against its scientific package merely to activate settings. The retained manual bootstrap requires dispatch from `master` and an exact repository confirmation; those guards are not authorization.

The initial read-only audit found missing protection and broad Actions defaults. Authorized activation on 2026-10-01 established live `Protect-Master` ruleset `24307128`, recorded it in `RULESET_ID`, and passed the full privileged comparison including an empty `bypass_actors` list. Actions defaults are now read-only with PR approval disabled and full SHA pins required. Allowed actions are GitHub-owned actions and the exact workflow pins for the uv installer, Scorecard, and PyPI publisher. Secret scanning and push protection are enabled. `governance` and `release` require an eligible reviewer, prevent self-review, and accept only `master`; `pypi` applies the same review controls to `v*` tags. The audit credential is isolated in the `master`-only `ruleset-audit` environment. Actual required CI, independent approval, Copilot completion, and the persistent environment-token audit remain distinct verification steps; release/publication opt-in variables remain unset.

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
| Copilot review availability | Automatic review independently of human approval | Live ruleset support and an actual completed review |
| `mikkokotila` eligible approval | Declared human authority | `mikkokotila` and independent owner `EnergyGuy3` were verified administrators; recheck eligibility for activation |
| `RULESET_ID` variable | Identify `Protect-Master` | Matches the live ruleset id; never invent a placeholder id |
| `ruleset-audit` environment | Isolate the privileged audit credential | Created with a `master`-only branch policy; token visibility still requires a successful audit |
| `RULESET_AUDIT_TOKEN` environment secret | Read live protection including `bypass_actors` | Repository Administration read/write plus Metadata read, scoped to Astetik; the post-merge audit actually succeeds |
| `REPO_BOOTSTRAP_TOKEN` secret | Template bootstrap operations | Needed only if separately authorized bootstrap is intentionally used; not required for ordinary Astetik PRs |
| `.github/labels.json` | Source-controlled issue-label manifest | Validate the local semantic-color manifest; no external label-source repository is required |
| `RELEASE_ENABLED` variable | Opt in to tag/release creation | Leave unset until remote governance and release readiness are proven |
| `PYPI_PUBLISH_ENABLED` variable | Opt in to publication | Leave unset until publisher and release readiness are proven |
| `release` environment | Protect tag/release creation | Explicit approval/branch protections for the authorized release |
| `pypi` environment and PyPI trusted publisher | OIDC upload identity | Exact repository/workflow/environment registration and environment protections |

The retained manual workflow applies local labels, the reviewed ruleset, and its variable; it does not create a PR or rewrite package source. Its PAT/GitHub App credential requires Issues write for labels, Administration write for rulesets, Variables write for `RULESET_ID`, and Metadata read, scoped to this repository. The built-in `GITHUB_TOKEN` cannot administer rulesets. Do not inherit the template's broader PR/workflow/source-write scopes for operations this workflow does not perform.
The audit makes read-only API requests, but its fine-grained credential needs repository **Administration: Read and write** plus **Metadata: Read**. GitHub returns `bypass_actors` only with write access to the ruleset; updating a ruleset requires Administration write. This permission combination is therefore required for complete audit visibility. [GitHub ruleset API](https://docs.github.com/en/rest/repos/rules#get-a-repository-ruleset)

## Audit token setup

1. Open [the fine-grained token form](https://github.com/settings/personal-access-tokens/new?name=astetik-ruleset-audit&target_name=autonomio&expires_in=30&administration=write&metadata=read). Verify resource owner `autonomio`, a short expiration, repository Administration read/write, and Metadata read.
2. Under **Repository access**, choose **Only select repositories**, then `astetik`. Generate the token; complete organization approval if GitHub marks it pending. [GitHub token instructions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
3. Open [Astetik environment settings](https://github.com/autonomio/astetik/settings/environments), select `ruleset-audit`, then **Environment secrets → Add secret**. Name it `RULESET_AUDIT_TOKEN` and enter the token directly there. This environment already has a `master`-only branch policy; token functionality has not been verified. [GitHub environment-secret instructions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets#creating-secrets-for-an-environment)
4. Once the updated audit workflow is available on `master`, run it and retain a successful comparison including `bypass_actors`; HTTP 200 alone does not prove complete visibility. Renew the secret before token expiration.

An administrator can instead use the interactive CLI prompt without placing the token in a command argument:

```bash
gh secret set RULESET_AUDIT_TOKEN --env ruleset-audit --repo autonomio/astetik
```

Never print credential values or put them in issues, documentation, or commits.

## Activation procedure

1. Inspect the exact local candidate and run its declared checks. Verify the eleven laws, ten required contexts, configuration, and `Protect-Master` snapshot agree.
2. Read live repository settings, rulesets, collaborator access, Actions permissions, environments, variables, enabled security features, and publisher registration. Record missing prerequisites; a local snapshot is not evidence that settings are active.
3. Confirm one eligible non-author human approval can be obtained independently of automatic Copilot review. An author cannot approve their own PR; administrator access alone does not satisfy that review.
4. Once explicitly authorized, establish only the missing secrets/variables/environments/settings and apply the reviewed snapshot. Reconcile broad Actions defaults with the adopted least-privilege policy; checked-in action SHA pins and workflow permissions apply to these workflows, not the repository-wide live settings. Record the actual ruleset id in `RULESET_ID`.
5. Verify live protection against [.github/rulesets/master.json](.github/rulesets/master.json), including `bypass_actors`, strict up-to-date checks, required reviews, all ten contexts, no force-push, and no branch deletion.
6. Verify a real authorized PR receives all required checks and review requirements. Confirm `pr_checks_honesty` and `pr_checks_ruleset` pass, and the privileged post-merge audit can read the complete protection state.
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
| Audit cannot read `bypass_actors` | Recheck repository Administration read/write, selected repository, token approval/expiration, and the `ruleset-audit` environment secret; fail visibly |
| Human approval does not count | Reviewer lacks write access, is the PR author, or violates live review rules |
| Copilot review unavailable | Required review prerequisite is missing; report the gap rather than dropping the requirement |
| CodeQL unavailable | Reconcile law, config, workflow, snapshot, and tests in a separately authorized change; never remove one surface alone |
| Upload or attestation unverified | Leave publication disabled; do not claim release provenance |

Next: [constitution](CLAUDE.md), [configuration](docs/Developer/Configuration.md), or [release policy](docs/Developer/Release-Policy.md).
