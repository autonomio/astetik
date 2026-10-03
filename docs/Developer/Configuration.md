# Governance configuration

This page owns the configuration and ratchet contract. [CLAUDE.md](../../CLAUDE.md) owns the eleven laws; executable gates and their focused tests determine how each declaration is checked.

## Prerequisites and ownership

Use Python 3.13 and the hash-pinned gate toolchain from `requirements/ci/gate-tools.txt`. Configuration is parsed safely through `governance/_common.py`.

| Source | Owns | Change boundary |
| --- | --- | --- |
| [governance.yml](../../governance.yml) | Repository identity, package/test layout, gate switches, authority, policy thresholds | May change through an explicitly reviewed scope |
| [.github/budgets.json](../../.github/budgets.json) | Typing, fail-loud, per-module, coverage, and runtime baselines | Ratchets against the real base ref |
| [pyproject.toml](../../pyproject.toml) | Hatch metadata, runtime dependencies, Ruff/Pyright configuration | Mirrored tool settings must match governance contracts |
| [.github/rulesets/master.json](../../.github/rulesets/master.json) | Intended `Protect-Master` rules and ten required contexts | Must agree with laws/config; live agreement needs separate proof |

Absent optional settings use gate defaults; present settings override them; malformed values fail. Required scan targets have no empty-tree fallback. Unknown or unread configuration is checked by contract tests rather than treated as useful policy.

## Astetik layout and interpreter boundary

```yaml
layout:
  package_root: astetik
  test_paths:
    - tests
  gate_test_paths:
    - governance/tests
  coverage_source: astetik
runtime:
  python_version: '3.13'
review:
  approving_authority: mikkokotila
```

Governance Python 3.13 is the reproducible gate environment. Astetik's `requires-python >=3.11` is its installed-library floor; the product/install matrices check Python 3.11, 3.12, and 3.13 separately. A governance interpreter change does not silently raise the public runtime floor.

Repository excludes and gate-specific excludes are combined. Typing/fail-loud ratchets compare the complete scan surface against the base ref; narrowing `package_root` or adding excludes cannot conceal new escape hatches.

## Gate controls

A gate's `enabled` flag controls execution and `required` controls merge blocking. Only gates that run and block owe one of the ten law annotations and one required ruleset context. Packaging and package-install checks are configured as advisory workflows; they do not create an eleventh required status context. The required `pr_checks_honesty` context deterministically checks the bijection among enabled required gates, written laws, and protected status contexts through `governance/tests/test_repository_law.py`. The ruleset automatically requests advisory Copilot review; provider completion, quota, and file-capacity responses are not additional merge gates. Eligible independent reviewer/code-owner approval, approval of the latest reviewable push, and resolved review threads remain required server-side protections.

Astetik's actual thresholds live in the linked config. Ruff `0.16.1` and Pyright `1.1.408` are pinned. The full configured Ruff scan passes with zero retained findings; the ratchet rejects every new diagnostic, baseline increase and configuration relaxation. Strict Pyright resolves the actual installed interpreter with `python -m pyright --pythonpath "$(command -v python)" --outputjson`; errors, warnings, AST dynamic-typing references and regex suppression escapes are all zero. Unsupported Pyright settings are absent; the AST gate independently enforces explicit dynamic-typing rejection.

Coherent module decomposition restored the template file-balance ceiling of 16; actual module paths each have a measured line cap. Product test/code ratio keeps the declared 0.33 minimum and remains an explicit [test-density limitation](Technical-Debt.md), rather than being called zero debt. All shape gates remain enabled.

All seven fail-loud categories remain zero. Coverage floors and runtime ceilings are measured and banked in [the budget JSON](../../.github/budgets.json); current gate reports determine whether the exact candidate passes. GitHub protection is independently verified as described in [activation](../../SETUP.md); a local static result does not prove live CI or required approval.

A dependency-bot exemption applies only when both the actual PR author is listed in `automation.bot_authors` and the gate is listed in `automation.exempt_gates`. The configured slice/version exemptions do not excuse the remaining laws; skips must identify author and gate in output.

## Ratchet changes

| Budget | Restricted direction | Required declaration |
| --- | --- | --- |
| Module line budget | Raise | `[budget-raise: <path>: <reason>]` |
| Coverage line/branch floor | Lower | `[coverage-lower: <field>: <reason>]` |
| Runtime total ceiling | Raise | `[runtime-raise: <reason>]` |
| Typing escape/error budgets | Raise | Refused; no override marker |
| Silent-fallback budgets | Raise | Refused; no override marker |

Comparisons read the protected base, not a candidate-written substitute. Markers supply reviewable reasons; they do not automatically approve a change.

## Change and verification procedure

1. Identify the reader and contract test for every changed setting. Add the reader in the same change as a new key.
2. Keep configuration, laws, workflow mirrors, tool pins, and ruleset snapshot consistent.
3. Run `python -m pytest governance/tests -q` and the affected gate against the actual base/PR declarations.
4. For remote adoption, complete [SETUP.md](../../SETUP.md) before claiming live enforcement. A passing local bijection checks declarations, not GitHub activation.

### First-adoption proof

When the protected base has neither governance configuration nor budgets, the initial adoption requires an explicit `--bootstrap` path that verifies that missing state and the candidate's actual governance introduction. A missing file is not a silent ratchet skip.
For Ruff, append `--bootstrap` to `check_ruff_ratchet.py --base-ref origin/master` only for this verified first adoption. Typing and fail-loud gates likewise require `--bootstrap` together with `--bootstrap-base-ref origin/master`; their regular path compares the actual extracted base budget/config. Once the base has governance, bootstrap arguments fail rather than bypass its ratchets.

Top-level policy is read through `section_setting`; gate-specific policy through `gate_setting`. Reading the wrong location must be caught by liveness tests that change a setting and observe the verdict.

Next: [maintenance](README.md), [technical debt](Technical-Debt.md), or [setup readiness](../../SETUP.md).

## CI runner allocation

`pr_checks_lint.yml` owns the separate required `pr_checks_tests` and
`pr_checks_lint` jobs. Product tests retain their runtime profile and ceiling;
governance contracts append coverage afterward. Lint consumes the successful
producer's immutable artifact ID from the same workflow run. Its receipt binds
the tested commit, run, attempt, lockfiles and coverage bytes; absent or changed
evidence fails. A failed consumer can rerun against the original successful producer attempt
and immutable artifact ID. The separate comment publisher never checks out pull-request code.

Scientific contracts run once per PR, across all three supported Python
versions; branch pushes run them only on `master`. Each lane checks installed
wheel imports and metadata outside the checkout and validates dependencies.
Packaging retains fixed-epoch reproducibility and distribution audits. The
required lint job owns PR documentation checks; master/manual runs retain the
scientific workflow's documentation job. Source checks cancel superseded heads,
use explicit total timeouts and cap the scientific matrix at two runners.

Title/body edits recheck commit-title, slice and version acceptance together
with budget, coverage and runtime waiver markers without repeating scientific
tests. Dependabot groups version and security updates separately, limits open
version PRs to one per ecosystem and staggers weekly version checks across
Thursday–Saturday at 04:00 Helsinki time. Security updates retain their
immediate advisory-driven behavior.

All PR-body waiver decisions belong to the metadata-sensitive version job.
Source-only tests enforce measured runtime; lint enforces measured coverage,
quality and vulnerability checks. Adding or removing a waiver therefore clears
or fails the required version status without leaving stale body-dependent
failures on the required test or lint statuses.
